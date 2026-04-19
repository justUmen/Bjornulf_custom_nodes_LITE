import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function computeAudioHash(audioBuffer) {
    return new Promise(async (resolve) => {
        try {
            const audioCtx = new AudioContext();
            const buffer = await audioCtx.decodeAudioData(audioBuffer.slice(0)); // Create a copy
            let data = buffer.getChannelData(0);
            if (buffer.numberOfChannels > 1) {
                const ch2 = buffer.getChannelData(1);
                for (let i = 0; i < data.length; i++) {
                    data[i] = (data[i] + ch2[i]) / 2;
                }
            }

            const targetLength = 1024;
            const step = Math.max(1, Math.floor(data.length / targetLength));
            const downsampled = new Float32Array(targetLength);
            for (let i = 0; i < targetLength; i++) {
                let sum = 0;
                const end = Math.min(i * step + step, data.length);
                for (let j = i * step; j < end; j++) {
                    sum += Math.abs(data[j]);
                }
                downsampled[i] = sum / (end - i * step);
            }

            let hash = '';
            for (let i = 0; i < targetLength - 1; i++) {
                hash += downsampled[i] > downsampled[i + 1] ? '1' : '0';
            }
            resolve(hash);
        } catch (error) {
            console.warn("Failed to compute audio hash:", error);
            resolve('');
        }
    });
}

function hammingDistance(h1, h2) {
    if (h1.length !== h2.length) return Infinity;
    let dist = 0;
    for (let i = 0; i < h1.length; i++) {
        if (h1[i] !== h2[i]) dist++;
    }
    return dist;
}

const DUPLICATE_THRESHOLD = 5; // Allow for slight variations in audio

// Helper function to upload audio files
async function uploadAudioFile(file, subfolder = "custom_holder") {
    const formData = new FormData();
    formData.append("image", file); // ComfyUI uses "image" field for all uploads
    formData.append("subfolder", subfolder);
    formData.append("type", "input");
    formData.append("overwrite", "false");
    
    try {
        const response = await api.fetchApi("/upload/image", {
            method: "POST",
            body: formData
        });
        
        if (response.status === 200) {
            const result = await response.json();
            return result;
        } else {
            throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        console.error("Upload error:", error);
        throw error;
    }
}

app.registerExtension({
    name: "Bjornulf.BasketMultipleAudioHolder",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Bjornulf_BasketMultipleAudioHolder") {
            const origOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = async function (message) {
                if (origOnExecuted) {
                    origOnExecuted.apply(this, arguments);
                }

                // Remove default preview widgets
                if (this.widgets) {
                    this.widgets = this.widgets.filter(w => w.type !== "custom");
                }

                if (message.audios && message.audios.length > 0) {
                    for (const audData of message.audios) {
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", audData.filename);
                        if (audData.subfolder) baseUrl.searchParams.set("subfolder", audData.subfolder);
                        if (audData.type) baseUrl.searchParams.set("type", audData.type);
                        const audUrl = baseUrl.toString();

                        let buffer;
                        try {
                            const resp = await fetch(audUrl);
                            if (!resp.ok) continue;
                            buffer = await resp.arrayBuffer();
                        } catch (error) {
                            console.warn(`Failed to load audio from ${audUrl}`);
                            continue;
                        }

                        await this.hashesLoaded;

                        const hash = await computeAudioHash(buffer);
                        if (!hash) continue;
                        const isSimilar = this.audioHashes.some(existing => 
                            hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD
                        );
                        if (isSimilar) {
                            console.log("Similar audio detected, skipping...");
                            continue;
                        }

                        this.audioHashes.push(hash);
                        this.properties.audioFiles.push(audData.filename);
                        this.combo.options.values = [...this.properties.audioFiles];
                        this.properties.selectedIndex = this.properties.audioFiles.length - 1;
                        this.combo.value = this.properties.audioFiles[this.properties.selectedIndex];
                        this.updatePreview();
                        app.graph.setDirtyCanvas(true, true);
                    }
                }
            };

            nodeType.prototype.onNodeCreated = function () {
                this.properties = this.properties || {};
                this.properties.audioFiles = this.properties.audioFiles || [];
                this.properties.selectedIndex = this.properties.selectedIndex !== undefined ? 
                    this.properties.selectedIndex : 
                    (this.properties.audioFiles.length > 0 ? 0 : -1);
                this.audioHashes = [];

                this.hashesLoaded = new Promise(async (resolve) => {
                    const validFiles = [];
                    const validHashes = [];
                    const loadPromises = this.properties.audioFiles.map(async (filename) => {
                        const url = `/view?filename=${encodeURIComponent(filename)}&subfolder=custom_holder&type=input`;
                        try {
                            const resp = await fetch(url);
                            if (!resp.ok) throw new Error("Fetch failed");
                            const buffer = await resp.arrayBuffer();
                            const hash = await computeAudioHash(buffer);
                            if (hash) {
                                validFiles.push(filename);
                                validHashes.push(hash);
                            } else {
                                throw new Error("Hash computation failed");
                            }
                        } catch (error) {
                            console.warn(`Failed to load audio: ${filename}`, error);
                        }
                    });
                    await Promise.all(loadPromises);
                    this.properties.audioFiles = validFiles;
                    this.audioHashes = validHashes;

                    if (this.properties.audioFiles.length > 0) {
                        this.properties.selectedIndex = Math.min(
                            Math.max(this.properties.selectedIndex, 0), 
                            this.properties.audioFiles.length - 1
                        );
                    } else {
                        this.properties.selectedIndex = -1;
                    }

                    resolve();
                });

                // Add combo widget for selection
                const comboValues = this.properties.audioFiles.length > 0 ? 
                    [...this.properties.audioFiles] : ["No audios"];
                const initialValue = this.properties.audioFiles.length > 0 ? 
                    this.properties.audioFiles[this.properties.selectedIndex] : "No audios";
                
                this.combo = this.addWidget("combo", "selected_audio", initialValue, (value) => {
                    if (value !== "No audios") {
                        this.properties.selectedIndex = this.properties.audioFiles.indexOf(value);
                    } else {
                        this.properties.selectedIndex = -1;
                    }
                    this.updatePreview();
                }, { values: comboValues });

                // Add upload button
                this.addWidget("button", "📤 Upload Audio", "upload", () => {
                    const input = document.createElement("input");
                    input.type = "file";
                    input.accept = "audio/*,.wav,.mp3,.flac,.ogg,.m4a";
                    input.style.display = "none";
                    input.onchange = (event) => {
                        if (event.target.files?.length) {
                            this.handleAddFile(event.target.files[0]);
                        }
                    };
                    document.body.appendChild(input);
                    input.click();
                    document.body.removeChild(input);
                });

                // Add remove button
                this.addWidget("button", "🗑️ Remove Selected", "remove", () => {
                    if (this.combo.value === "No audios") return;
                    if (this.properties.audioFiles.length === 0) return;
                    
                    const idx = this.properties.selectedIndex;
                    if (idx >= 0 && idx < this.properties.audioFiles.length) {
                        this.audioHashes.splice(idx, 1);
                        this.properties.audioFiles.splice(idx, 1);
                        
                        if (this.properties.audioFiles.length === 0) {
                            this.combo.options.values = ["No audios"];
                            this.combo.value = "No audios";
                            this.properties.selectedIndex = -1;
                        } else {
                            if (this.properties.selectedIndex >= this.properties.audioFiles.length) {
                                this.properties.selectedIndex = Math.max(0, this.properties.audioFiles.length - 1);
                            }
                            this.combo.options.values = [...this.properties.audioFiles];
                            this.combo.value = this.properties.audioFiles[this.properties.selectedIndex];
                        }
                        this.updatePreview();
                        app.graph.setDirtyCanvas(true, true);
                    }
                });

                // Add clear all button
                this.addWidget("button", "🗑️ Clear All", "clear", () => {
                    this.audioHashes = [];
                    this.properties.audioFiles = [];
                    this.combo.options.values = ["No audios"];
                    this.combo.value = "No audios";
                    this.properties.selectedIndex = -1;
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                });

                // Create audio preview element
                const audio = document.createElement("audio");
                audio.controls = true;
                audio.style.width = "100%";
                audio.style.maxHeight = "100%";
                audio.preload = "none";

                // Add drag and drop functionality to the audio element
                audio.ondragover = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.dataTransfer.dropEffect = "copy";
                    audio.style.backgroundColor = "#4CAF50";
                    audio.style.opacity = "0.7";
                };

                audio.ondragleave = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    audio.style.backgroundColor = "";
                    audio.style.opacity = "1";
                };

                audio.ondrop = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    audio.style.backgroundColor = "";
                    audio.style.opacity = "1";
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        const file = files[0];
                        if (file.type.startsWith('audio/')) {
                            this.handleAddFile(file);
                        } else {
                            alert("Please drop an audio file.");
                        }
                    }
                };

                // Enable dragging from audio element
                audio.draggable = true;
                audio.addEventListener("dragstart", (e) => {
                    if (audio.src) {
                        e.dataTransfer.setData("text/uri-list", audio.src);
                        e.dataTransfer.effectAllowed = "copy";
                    }
                });

                this.previewWidget = this.addDOMWidget(
                    "preview_audio_" + Math.random().toString(36).slice(2), 
                    "audio", 
                    audio, 
                    { serialize: false }
                );

                // Style the preview widget container
                if (this.previewWidget.parentEl) {
                    this.previewWidget.parentEl.style.background = "transparent";
                    this.previewWidget.parentEl.style.padding = "4px";
                    this.previewWidget.parentEl.style.textAlign = "center";
                    this.previewWidget.parentEl.style.border = "2px dashed #ccc";
                    this.previewWidget.parentEl.style.borderRadius = "4px";
                }

                // Set fixed size
                this.setSize([320, 200]);

                // Update preview function
                this.updatePreview = function () {
                    if (this.combo.value !== "No audios" && 
                        this.properties.audioFiles.length > 0 && 
                        this.properties.selectedIndex >= 0 && 
                        this.properties.selectedIndex < this.properties.audioFiles.length) {
                        
                        const filename = this.properties.audioFiles[this.properties.selectedIndex];
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", filename);
                        baseUrl.searchParams.set("subfolder", "custom_holder");
                        baseUrl.searchParams.set("type", "input");
                        baseUrl.searchParams.set("t", Date.now()); // Cache busting
                        audio.src = baseUrl.toString();
                    } else {
                        audio.src = "";
                    }
                    app.graph.setDirtyCanvas(true, true);
                };

                this.updatePreview();
            };

            // Handle file addition
            nodeType.prototype.handleAddFile = async function (file) {
                try {
                    if (!file.type.startsWith('audio/')) {
                        alert("Please select an audio file.");
                        return;
                    }

                    // Read file for hash computation
                    const buffer = await file.arrayBuffer();
                    
                    await this.hashesLoaded;

                    const hash = await computeAudioHash(buffer);
                    if (!hash) {
                        alert("Failed to compute audio hash.");
                        return;
                    }
                    
                    const isSimilar = this.audioHashes.some(existing => 
                        hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD
                    );
                    
                    if (isSimilar) {
                        alert("Identical or similar audio already exists.");
                        return;
                    }

                    // Generate unique filename
                    const extension = file.name.split('.').pop() || 'wav';
                    const uniqueFilename = `node_${this.id}_${Date.now()}.${extension}`;
                    const renamedFile = new File([buffer], uniqueFilename, { type: file.type });
                    
                    // Upload the file
                    const uploadResult = await uploadAudioFile(renamedFile, "custom_holder");
                    
                    // Add to our lists
                    this.audioHashes.push(hash);
                    this.properties.audioFiles.push(uniqueFilename);
                    this.combo.options.values = [...this.properties.audioFiles];
                    this.properties.selectedIndex = this.properties.audioFiles.length - 1;
                    this.combo.value = this.properties.audioFiles[this.properties.selectedIndex];
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                    
                    console.log(`Successfully added audio: ${uniqueFilename}`);
                    
                } catch (error) {
                    console.error("Error adding audio file:", error);
                    alert(`Upload error: ${error.message}`);
                }
            };
        }
    },
});