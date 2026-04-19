import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "Bjornulf.LoadPickAudioFile",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Bjornulf_LoadPickAudioFile") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                if (onNodeCreated) {
                    onNodeCreated.apply(this);
                }

                const audioWidget = this.widgets.find(w => w.name === "audio");
                
                // Add a simple button to open the audio
                const openButton = this.addWidget("button", "Open Audio", null, () => {
                    if (this.audioUrl) {
                        window.open(this.audioUrl, '_blank');
                    }
                });

                // Modify the audio widget callback
                if (audioWidget) {
                    // Add upload button to the original widget
                    if (audioWidget.element) {
                        let uploadBtn = audioWidget.element.querySelector("button");
                        if (!uploadBtn) {
                            uploadBtn = document.createElement("button");
                            uploadBtn.innerText = "Upload Audio";
                            uploadBtn.style.marginLeft = "5px";
                            audioWidget.element.appendChild(uploadBtn);
                        }

                        uploadBtn.onclick = () => {
                            const input = document.createElement("input");
                            input.type = "file";
                            input.accept = "audio/*";
                            input.onchange = (e) => this.uploadFile(e.target.files[0]);
                            input.click();
                        };
                    }

                    // Set up audio URL on widget change
                    audioWidget.callback = () => {
                        const value = audioWidget.value;
                        if (!value) {
                            this.audioUrl = null;
                            return;
                        }

                        let subfolder = "";
                        let filename = value;
                        const lastSlash = value.lastIndexOf("/");
                        if (lastSlash !== -1) {
                            subfolder = value.substring(0, lastSlash);
                            filename = value.substring(lastSlash + 1);
                        }

                        this.audioUrl = `/view?filename=${encodeURIComponent(filename)}&subfolder=${encodeURIComponent(subfolder)}&type=input&t=${+new Date()}`;
                        
                        // Force redraw
                        app.graph.setDirtyCanvas(true);
                    };

                    // Initial call if value is set
                    if (audioWidget.value) {
                        audioWidget.callback();
                    }
                }

                // Enable drag and drop on the node
                this.onDragOver = function (e) {
                    if (e.dataTransfer && e.dataTransfer.items) {
                        for (let i = 0; i < e.dataTransfer.items.length; i++) {
                            if (e.dataTransfer.items[i].kind === "file" && e.dataTransfer.items[i].type.startsWith("audio/")) {
                                e.preventDefault();
                                e.stopPropagation();
                                return true;
                            }
                        }
                    }
                    return false;
                };

                this.onDragDrop = function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (e.dataTransfer && e.dataTransfer.files) {
                        for (let i = 0; i < e.dataTransfer.files.length; i++) {
                            const file = e.dataTransfer.files[i];
                            if (file.type.startsWith("audio/")) {
                                this.uploadFile(file);
                                break;
                            }
                        }
                    }
                    return true;
                };
            };

            nodeType.prototype.uploadFile = async function (file) {
                if (!file) return;

                const formData = new FormData();
                formData.append("image", file);
                formData.append("type", "input");
                formData.append("overwrite", "false");

                try {
                    const resp = await api.fetchApi("/upload/image", {
                        method: "POST",
                        body: formData
                    });
                    if (resp.status === 200) {
                        const data = await resp.json();
                        const audioWidget = this.widgets.find(w => w.name === "audio");
                        const path = data.subfolder ? data.subfolder + '/' + data.name : data.name;
                        audioWidget.value = path;
                        if (audioWidget && audioWidget.element) {
                            const select = audioWidget.element.querySelector("select");
                            if (select && !audioWidget.options.values.includes(path)) {
                                audioWidget.options.values.push(path);
                                audioWidget.options.values.sort();
                                select.innerHTML = "";
                                audioWidget.options.values.forEach(v => {
                                    const opt = document.createElement("option");
                                    opt.value = v;
                                    opt.innerHTML = v;
                                    select.appendChild(opt);
                                });
                                select.value = path;
                            }
                        }
                        // Trigger callback to update
                        audioWidget.callback();
                    } else {
                        alert("Upload failed");
                    }
                } catch (error) {
                    alert("Upload error: " + error);
                }
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }

                // Update after execution if needed
                const audioWidget = this.widgets.find(w => w.name === "audio");
                if (audioWidget && audioWidget.value) {
                    audioWidget.callback();
                }
            };
        }
    },
});