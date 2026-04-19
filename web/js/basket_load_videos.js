import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function computeVideoDHash(videoUrl) {
    return new Promise((resolve, reject) => {
        const video = document.createElement('video');
        video.src = videoUrl;
        video.muted = true;
        video.crossOrigin = "anonymous";
        video.onloadeddata = () => {
            video.currentTime = 0;
        };
        video.onseeked = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 9;
            canvas.height = 8;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 9, 8);
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
        };
        video.onerror = reject;
        video.load();
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

const DUPLICATE_THRESHOLD = 0; // Adjust this value to allow for near-duplicates (e.g., 2-5 for similar videos based on first frame)

app.registerExtension({
    name: "Bjornulf.BasketMultipleVideosHolder",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Bjornulf_BasketMultipleVideosHolder") {
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
                const lockWidget = this.widgets.find(w => w.name === "lock");
                if (lockWidget && lockWidget.value) {
                    return;
                }
                if (message.videos && message.videos.length > 0) {
                    for (const videoData of message.videos) {
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", videoData.filename);
                        if (videoData.subfolder) baseUrl.searchParams.set("subfolder", videoData.subfolder);
                        if (videoData.type) baseUrl.searchParams.set("type", videoData.type);
                        const videoUrl = baseUrl.toString();
                        let hash = null;
                        try {
                            hash = await computeVideoDHash(videoUrl);
                        } catch (error) {
                            console.warn(`Failed to compute hash for video from ${videoUrl}: ${error}`);
                        }
                        const isSimilar = hash !== null && this.videoHashes.some(existing => hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD);
                        if (isSimilar) continue;
                        this.videoHashes.push(hash);
                        this.properties.videoFiles.push(videoData.filename);
                        this.combo.options.values = [...this.properties.videoFiles];
                        this.properties.selectedIndex = this.properties.videoFiles.length - 1;
                        this.combo.value = this.properties.videoFiles[this.properties.selectedIndex];
                        this.updatePreview();
                        app.graph.setDirtyCanvas(true, true);
                    }
                }
            };
            nodeType.prototype.onNodeCreated = function () {
                this.properties = this.properties || {};
                this.properties.videoFiles = this.properties.videoFiles || [];
                this.properties.selectedIndex = this.properties.selectedIndex !== undefined ? this.properties.selectedIndex : (this.properties.videoFiles.length > 0 ? 0 : -1);
                this.videoHashes = [];
                this.hashesLoaded = new Promise(async (resolve) => {
                    const validFiles = [];
                    const validHashes = [];
                    const loadPromises = this.properties.videoFiles.map(async (filename) => {
                        const url = `/view?filename=${filename}&subfolder=custom_holder_videos&type=input`;
                        let hash = null;
                        try {
                            hash = await computeVideoDHash(url);
                        } catch (error) {
                            console.warn(`Failed to load or hash video: ${filename} - ${error}`);
                        }
                        validFiles.push(filename);
                        validHashes.push(hash);
                    });
                    await Promise.all(loadPromises);
                    this.properties.videoFiles = validFiles;
                    this.videoHashes = validHashes;
                    if (this.properties.videoFiles.length > 0) {
                        this.properties.selectedIndex = Math.min(Math.max(this.properties.selectedIndex, 0), this.properties.videoFiles.length - 1);
                    } else {
                        this.properties.selectedIndex = -1;
                    }
                    resolve();
                });
                this.defaultBoxcolor = this.boxcolor;
                this.defaultBgcolor = this.bgcolor;
                // Add lock toggle widget
                this.addWidget("toggle", "lock", false, (value) => {
                    this.updateVisual();
                }, { on: "Locked", off: "Unlocked" });
                // Add combo widget for selection
                const comboValues = this.properties.videoFiles.length > 0 ? [...this.properties.videoFiles] : ["No videos"];
                const initialValue = this.properties.videoFiles.length > 0 ? this.properties.videoFiles[this.properties.selectedIndex] : "No videos";
                this.combo = this.addWidget("combo", "selected_video", initialValue, (value) => {
                    if (value !== "No videos") {
                        this.properties.selectedIndex = this.properties.videoFiles.indexOf(value);
                    } else {
                        this.properties.selectedIndex = -1;
                    }
                    this.updatePreview();
                }, { values: comboValues });
                // Add remove button
                this.addWidget("button", "🗑️ Remove Selected", "remove", () => {
                    if (this.combo.value === "No videos") return;
                    if (this.properties.videoFiles.length === 0) return;
                    const idx = this.properties.selectedIndex;
                    this.videoHashes.splice(idx, 1);
                    this.properties.videoFiles.splice(idx, 1);
                    if (this.properties.videoFiles.length === 0) {
                        this.combo.options.values = ["No videos"];
                        this.combo.value = "No videos";
                        this.properties.selectedIndex = -1;
                    } else {
                        if (this.properties.selectedIndex >= this.properties.videoFiles.length) {
                            this.properties.selectedIndex = Math.max(0, this.properties.videoFiles.length - 1);
                        }
                        this.combo.options.values = [...this.properties.videoFiles];
                        this.combo.value = this.properties.videoFiles[this.properties.selectedIndex];
                    }
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                });
                // Add clear all button
                this.addWidget("button", "🗑️ Clear All", "clear", () => {
                    this.videoHashes = [];
                    this.properties.videoFiles = [];
                    this.combo.options.values = ["No videos"];
                    this.combo.value = "No videos";
                    this.properties.selectedIndex = -1;
                    this.updatePreview();
                    app.graph.setDirtyCanvas(true, true);
                });
                // Add preview video DOM widget
                const video = document.createElement("video");
                video.controls = true;
                video.style.maxWidth = "100%";
                video.style.maxHeight = "100%";
                video.style.objectFit = "contain";
                video.draggable = true;
                video.addEventListener("dragstart", (e) => {
                    e.dataTransfer.setData("text/uri-list", video.src);
                    e.dataTransfer.effectAllowed = "copy";
                });
                video.ondragover = (e) => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = "copy";
                };
                video.ondrop = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const files = e.dataTransfer.files;
                    if (files.length) this.handleAddFile(files[0]);
                };
                this.previewWidget = this.addDOMWidget("preview_video_" + Math.random().toString(36).slice(2), "video", video, {
                    serialize: false,
                });
                // Style the preview widget container
                if (this.previewWidget.parentEl) {
                    this.previewWidget.parentEl.style.background = "transparent";
                    this.previewWidget.parentEl.style.padding = "4px";
                    this.previewWidget.parentEl.style.textAlign = "center";
                }
                // Adjust node size based on video dimensions once loaded
                video.onloadedmetadata = () => {
                    const aspectRatio = video.videoHeight / video.videoWidth;
                    const targetWidth = Math.max(256, Math.min(video.videoWidth, this.size[0] - 20));
                    const targetHeight = targetWidth * aspectRatio;
                    this.setSize([targetWidth + 20, this.computeSize()[1] + targetHeight + 10]);
                    app.graph.setDirtyCanvas(true, true);
                };
                this.updatePreview = function () {
                    if (this.combo.value !== "No videos" && this.properties.videoFiles.length > 0 && this.properties.selectedIndex >= 0 && this.properties.selectedIndex < this.properties.videoFiles.length) {
                        const filename = this.properties.videoFiles[this.properties.selectedIndex];
                        const baseUrl = new URL("/view", window.location.origin);
                        baseUrl.searchParams.set("filename", filename);
                        baseUrl.searchParams.set("subfolder", "custom_holder_videos");
                        baseUrl.searchParams.set("type", "input");
                        video.src = baseUrl.toString();
                        video.load();
                    } else {
                        video.src = "";
                        this.setSize([300, 200]); // Reset to default size if no video
                        app.graph.setDirtyCanvas(true, true);
                    }
                };
                this.updateVisual = function () {
                    const lockWidget = this.widgets.find(w => w.name === "lock");
                    if (lockWidget && lockWidget.value) {
                        this.bgcolor = "#000";
                    } else {
                        this.boxcolor = this.defaultBoxcolor;
                        this.bgcolor = this.defaultBgcolor;
                    }
                    app.graph.setDirtyCanvas(true, true);
                };
                this.updateVisual();
                this.updatePreview();
            };
            nodeType.prototype.handleAddFile = async function (file) {
                if (!file.type.startsWith('video/')) {
                    alert("Invalid file type. Please upload an MP4 or MKV video.");
                    return;
                }
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const tempVideo = document.createElement('video');
                    tempVideo.src = e.target.result;
                    tempVideo.muted = true;
                    let loaded = false;
                    await new Promise((res) => {
                        tempVideo.onloadeddata = () => { loaded = true; res(); };
                        tempVideo.onerror = res;
                    });
                    if (!loaded) {
                        alert("Failed to load video for hashing.");
                        return;
                    }
                    await this.hashesLoaded;
                    let hash = null;
                    try {
                        tempVideo.currentTime = 0;
                        await new Promise((res) => { tempVideo.onseeked = res; });
                        const canvas = document.createElement('canvas');
                        canvas.width = 9;
                        canvas.height = 8;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(tempVideo, 0, 0, 9, 8);
                        const imageData = ctx.getImageData(0, 0, 9, 8).data;
                        hash = '';
                        for (let row = 0; row < 8; row++) {
                            for (let col = 0; col < 8; col++) {
                                const leftIdx = (row * 9 + col) * 4;
                                const leftGray = (imageData[leftIdx] + imageData[leftIdx + 1] + imageData[leftIdx + 2]) / 3;
                                const rightIdx = leftIdx + 4;
                                const rightGray = (imageData[rightIdx] + imageData[rightIdx + 1] + imageData[rightIdx + 2]) / 3;
                                hash += leftGray > rightGray ? '1' : '0';
                            }
                        }
                    } catch (error) {
                        console.warn(`Hash computation error: ${error}`);
                    }
                    const isSimilar = hash !== null && this.videoHashes.some(existing => hammingDistance(existing, hash) <= DUPLICATE_THRESHOLD);
                    if (isSimilar) {
                        alert("Identical or similar video (based on first frame) already exists.");
                        return;
                    }
                    const ext = file.name.slice(file.name.lastIndexOf('.'));
                    const uniqueFilename = `node_${this.id}_${Date.now()}${ext}`;
                    const renamedFile = new File([file], uniqueFilename, { type: file.type });
                    const formData = new FormData();
                    formData.append("image", renamedFile); // Using /upload/image, but for file save
                    formData.append("subfolder", "custom_holder_videos");
                    formData.append("type", "input");
                    try {
                        const resp = await api.fetchApi("/upload/image", {
                            method: "POST",
                            body: formData
                        });
                        if (resp.status === 200) {
                            this.videoHashes.push(hash);
                            this.properties.videoFiles.push(uniqueFilename);
                            this.combo.options.values = [...this.properties.videoFiles];
                            this.properties.selectedIndex = this.properties.videoFiles.length - 1;
                            this.combo.value = this.properties.videoFiles[this.properties.selectedIndex];
                            this.updatePreview();
                            app.graph.setDirtyCanvas(true, true);
                        } else {
                            alert(`Upload failed: ${resp.statusText}`);
                        }
                    } catch (error) {
                        alert(`Upload error: ${error}`);
                    }
                };
                reader.readAsDataURL(file);
            };
        }
    },
});