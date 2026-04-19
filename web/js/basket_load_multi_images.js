import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function computeDHash(img) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = 9;
        canvas.height = 8;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, 9, 8);
        const imageData = ctx.getImageData(0, 0, 9, 8).data;
        let hash = '';
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const leftIdx = (row * 9 + col) * 4;
                const leftGray = (imageData[leftIdx] + imageData[leftIdx + 1] + imageData[leftIdx + 2]) / 3;
                const rightIdx = leftIdx + 4;
                const rightGray = (imageData[rightIdx] + imageData[rightIdx + 1] + imageData[rightIdx + 2]) / 3;
                hash += leftGray > rightGray ? '1' : '0';
            }
        }
        resolve(hash);
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

const DUPLICATE_THRESHOLD = 0; // Adjust this value to allow for near-duplicates (e.g., 2-5 for similar images)

app.registerExtension({
    name: "Bjornulf.BasketMultipleImagesHolder",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Bjornulf_BasketMultipleImagesHolder") {
            const origOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = async function (message) {
                if (origOnExecuted) {
                    origOnExecuted.apply(this, arguments);
                }
                // Remove default canvas preview widgets
                if (this.widgets) {
                    this.widgets = this.widgets.filter(w => w.type !== "custom");
                }
                await this.hashesLoaded;
                if (this.properties.locked) {
                    return;
                }
                if (message.images && message.images.length > 0) {
                    for (const imgData of message.images) {
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", imgData.filename);
                        if (imgData.subfolder) baseUrl.searchParams.set("subfolder", imgData.subfolder);
                        if (imgData.type) baseUrl.searchParams.set("type", imgData.type);
                        const imgUrl = baseUrl.toString();
                        const tempImg = new Image();
                        tempImg.crossOrigin = "anonymous";
                        tempImg.src = imgUrl;
                        let loaded = false;
                        await new Promise((resolve) => {
                            tempImg.onload = () => { loaded = true; resolve(); };
                            tempImg.onerror = resolve;
                        });
                        if (!loaded) {
                            console.warn(`Failed to load image from ${imgUrl}`);
                            continue;
                        }
                        const hash = await computeDHash(tempImg);
                        const isSimilar = this.imageHashes.some(existing => hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD);
                        if (isSimilar) continue;
                        let uniqueFilename;
                        try {
                            const resp = await fetch(imgUrl);
                            if (!resp.ok) continue;
                            const blob = await resp.blob();
                            uniqueFilename = `node_${this.id}_${Date.now()}.png`;
                            const file = new File([blob], uniqueFilename, { type: blob.type });
                            const formData = new FormData();
                            formData.append("image", file);
                            formData.append("subfolder", "custom_holder");
                            formData.append("type", "input");
                            const uploadResp = await api.fetchApi("/upload/image", { method: "POST", body: formData });
                            if (uploadResp.status !== 200) continue;
                        } catch (error) {
                            console.error("Error adding image:", error);
                            continue;
                        }
                        this.imageHashes.push(hash);
                        this.properties.imageFiles.push(uniqueFilename);
                        this.combo.options.values = [...this.properties.imageFiles];
                        this.properties.selectedIndex = this.properties.imageFiles.length - 1;
                        this.combo.value = this.properties.imageFiles[this.properties.selectedIndex];
                        this.updatePreview();
                        app.graph.setDirtyCanvas(true, true);
                    }
                }
            };
            nodeType.prototype.onNodeCreated = function () {
                this.properties = this.properties || {};
                this.properties.imageFiles = this.properties.imageFiles || [];
                this.properties.selectedIndex = this.properties.selectedIndex !== undefined ? this.properties.selectedIndex : (this.properties.imageFiles.length > 0 ? 0 : -1);
                this.properties.locked = this.properties.locked || false;
                this.imageHashes = [];
                this.hashesLoaded = new Promise(async (resolve) => {
                    const validFiles = [];
                    const validHashes = [];
                    const loadPromises = this.properties.imageFiles.map(async (filename) => {
                        const url = `/view?filename=${filename}&subfolder=custom_holder&type=input`;
                        const tempImg = new Image();
                        tempImg.crossOrigin = "anonymous";
                        tempImg.src = url;
                        let loaded = false;
                        await new Promise((res) => {
                            tempImg.onload = () => { loaded = true; res(); };
                            tempImg.onerror = () => { res(); };
                        });
                        if (loaded) {
                            const hash = await computeDHash(tempImg);
                            validFiles.push(filename);
                            validHashes.push(hash);
                        } else {
                            console.warn(`Failed to load image: ${filename}`);
                        }
                    });
                    await Promise.all(loadPromises);
                    this.properties.imageFiles = validFiles;
                    this.imageHashes = validHashes;
                    if (this.properties.imageFiles.length > 0) {
                        this.properties.selectedIndex = Math.min(Math.max(this.properties.selectedIndex, 0), this.properties.imageFiles.length - 1);
                    } else {
                        this.properties.selectedIndex = -1;
                    }
                    resolve();
                });
                this.defaultBoxcolor = this.boxcolor;
                this.defaultBgcolor = this.bgcolor;
                // Add lock toggle widget
                this.addWidget("toggle", "lock", this.properties.locked, (value) => {
                    this.properties.locked = value;
                    this.updateVisual();
                }, { on: "Locked", off: "Unlocked" });
                // Add combo widget for selection
                const comboValues = this.properties.imageFiles.length > 0 ? [...this.properties.imageFiles] : ["No images"];
                const initialValue = this.properties.imageFiles.length > 0 ? this.properties.imageFiles[this.properties.selectedIndex] : "No images";
                this.combo = this.addWidget("combo", "selected_image", initialValue, (value) => {
                    if (value !== "No images") {
                        this.properties.selectedIndex = this.properties.imageFiles.indexOf(value);
                    } else {
                        this.properties.selectedIndex = -1;
                    }
                    this.updatePreview();
                }, { values: comboValues });
                // Add upload button
                this.addWidget("button", "📤 Upload Image", "upload", () => {
                    const input = document.createElement("input");
                    input.type = "file";
                    input.accept = "image/png,image/jpeg,image/webp";
                    input.style.display = "none";
                    input.onchange = (event) => {
                        if (event.target.files?.length) this.handleAddFile(event.target.files[0]);
                    };
                    document.body.appendChild(input);
                    input.click();
                    document.body.removeChild(input);
                });
                // Add remove button
                this.addWidget("button", "🗑️ Remove Selected", "remove", () => {
                    if (this.combo.value === "No images") return;
                    if (this.properties.imageFiles.length === 0) return;
                    const idx = this.properties.selectedIndex;
                    this.imageHashes.splice(idx, 1);
                    this.properties.imageFiles.splice(idx, 1);
                    if (this.properties.imageFiles.length === 0) {
                        this.combo.options.values = ["No images"];
                        this.combo.value = "No images";
                        this.properties.selectedIndex = -1;
                    } else {
                        if (this.properties.selectedIndex >= this.properties.imageFiles.length) {
                            this.properties.selectedIndex = Math.max(0, this.properties.imageFiles.length - 1);
                        }
                        this.combo.options.values = [...this.properties.imageFiles];
                        this.combo.value = this.properties.imageFiles[this.properties.selectedIndex];
                    }
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                });
                // Add clear all button
                this.addWidget("button", "🗑️ Clear All", "clear", () => {
                    this.imageHashes = [];
                    this.properties.imageFiles = [];
                    this.combo.options.values = ["No images"];
                    this.combo.value = "No images";
                    this.properties.selectedIndex = -1;
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                });
                // Add download button
                this.addWidget("button", "💾 Download", "download", () => {
                    if (this.combo.value === "No images") return;
                    const filename = this.properties.imageFiles[this.properties.selectedIndex];
                    const baseUrl = new URL("/view", window.location.origin);
                    baseUrl.searchParams.set("filename", filename);
                    baseUrl.searchParams.set("subfolder", "custom_holder");
                    baseUrl.searchParams.set("type", "input");
                    const link = document.createElement('a');
                    link.href = baseUrl.toString();
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
                // Add preview image DOM widget
                const img = document.createElement("img");
                img.style.maxWidth = "100%";
                img.style.maxHeight = "100%";
                img.style.objectFit = "contain";
                img.draggable = true;
                img.addEventListener("dragstart", (e) => {
                    e.dataTransfer.setData("text/uri-list", img.src);
                    e.dataTransfer.effectAllowed = "copy";
                });
                img.ondragover = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    e.dataTransfer.dropEffect = "copy";
                };
                img.ondrop = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const files = e.dataTransfer.files;
                    if (files.length && !this.properties.locked) this.handleAddFile(files[0]);
                };
                this.previewWidget = this.addDOMWidget("preview_img_" + Math.random().toString(36).slice(2), "image", img, {
                    serialize: false,
                });
                // Style the preview widget container
                if (this.previewWidget.parentEl) {
                    this.previewWidget.parentEl.style.background = "transparent";
                    this.previewWidget.parentEl.style.padding = "4px";
                    this.previewWidget.parentEl.style.textAlign = "center";
                }
                // Adjust node size based on image dimensions once loaded
                img.onload = () => {
                    const aspectRatio = img.naturalHeight / img.naturalWidth;
                    const targetWidth = Math.max(256, Math.min(img.naturalWidth, this.size[0] - 20));
                    const targetHeight = targetWidth * aspectRatio;
                    this.setSize([targetWidth + 20, this.computeSize()[1] + targetHeight + 10]);
                    app.graph.setDirtyCanvas(true, true);
                };
                this.updatePreview = function () {
                    if (this.combo.value !== "No images" && this.properties.imageFiles.length > 0 && this.properties.selectedIndex >= 0 && this.properties.selectedIndex < this.properties.imageFiles.length) {
                        const filename = this.properties.imageFiles[this.properties.selectedIndex];
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", filename);
                        baseUrl.searchParams.set("subfolder", "custom_holder");
                        baseUrl.searchParams.set("type", "input");
                        img.src = baseUrl.toString();
                    } else {
                        img.src = "";
                        this.setSize([300, 200]); // Reset to default size if no image
                        app.graph.setDirtyCanvas(true, true);
                    }
                };
                this.updateVisual = function () {
                    if (this.properties.locked) {
                        this.bgcolor = "#000";
                    } else {
                        this.boxcolor = this.defaultBoxcolor;
                        this.bgcolor = this.defaultBgcolor;
                    }
                    app.graph.setDirtyCanvas(true, true);
                };
                this.updateVisual();
                this.updatePreview();

                // Add drop handlers to the entire node to prevent workflow loading
                setTimeout(() => {
                    if (this.previewWidget && this.previewWidget.parentEl) {
                        let nodeEl = this.previewWidget.parentEl;
                        while (nodeEl && !nodeEl.classList.contains('lgraph_node')) {
                            nodeEl = nodeEl.parentNode;
                        }
                        if (nodeEl) {
                            nodeEl.addEventListener('dragover', (e) => {
                                if (this.properties.locked) return;
                                e.preventDefault();
                                e.stopPropagation();
                            });
                            nodeEl.addEventListener('drop', (e) => {
                                if (this.properties.locked) return;
                                e.preventDefault();
                                e.stopPropagation();
                                const files = e.dataTransfer.files;
                                if (files.length) {
                                    this.handleAddFile(files[0]);
                                }
                            });
                        }
                    }
                }, 100);
            };
            nodeType.prototype.handleAddFile = async function (file) {
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const tempImg = new Image();
                    tempImg.onload = async () => {
                        await this.hashesLoaded;
                        const hash = await computeDHash(tempImg);
                        const isSimilar = this.imageHashes.some(existing => hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD);
                        if (isSimilar) {
                            alert("Identical or similar image already exists.");
                            return;
                        }
                        const uniqueFilename = `node_${this.id}_${Date.now()}.png`;
                        const renamedFile = new File([file], uniqueFilename, { type: file.type });
                        const formData = new FormData();
                        formData.append("image", renamedFile);
                        formData.append("subfolder", "custom_holder");
                        formData.append("type", "input");
                        try {
                            const resp = await api.fetchApi("/upload/image", {
                                method: "POST",
                                body: formData
                            });
                            if (resp.status === 200) {
                                this.imageHashes.push(hash);
                                this.properties.imageFiles.push(uniqueFilename);
                                this.combo.options.values = [...this.properties.imageFiles];
                                this.properties.selectedIndex = this.properties.imageFiles.length - 1;
                                this.combo.value = this.properties.imageFiles[this.properties.selectedIndex];
                                this.updatePreview();
                                app.graph.setDirtyCanvas(true, true);
                            } else {
                                alert(`Upload failed: ${resp.statusText}`);
                            }
                        } catch (error) {
                            alert(`Upload error: ${error}`);
                        }
                    };
                    tempImg.src = e.target.result;
                };
                reader.readAsDataURL(file);
            };
        }
    },
});