import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "Bjornulf.CustomImageHolder",
    async nodeCreated(node) {
        if (node.comfyClass === "Bjornulf_CustomImageHolder") {
            const imageWidget = node.widgets.find(w => w.name === "image");
            if (imageWidget) {
                // Override callback to force preview reload
                const originalCallback = imageWidget.callback;
                imageWidget.callback = function(value) {
                    if (originalCallback) originalCallback.call(this, value);
                    const previewImg = this.inputEl.nextSibling;
                    if (previewImg && previewImg.tagName === "IMG") {
                        const url = new URL(previewImg.src);
                        url.searchParams.set('rand', Math.random());
                        previewImg.src = url.toString();
                    }
                };

                // Upload button to special folder
                const uploadButton = node.inputsDiv.querySelector("button");
                if (uploadButton && uploadButton.textContent === "📤") {
                    uploadButton.onclick = async () => {
                        const input = document.createElement("input");
                        input.type = "file";
                        input.accept = "image/png,image/jpeg,image/webp";
                        input.style.display = "none";
                        input.onchange = async (event) => {
                            if (!event.target.files?.length) return;
                            const file = event.target.files[0];
                            const formData = new FormData();
                            formData.append("image", file);
                            formData.append("overwrite", false);
                            try {
                                const resp = await api.fetchApi("/upload/image?type=input&subfolder=custom_holder", {
                                    method: "POST",
                                    body: formData
                                });
                                if (resp.status === 200) {
                                    const data = await resp.json();
                                    imageWidget.value = `custom_holder/${data.name}`;
                                    if (imageWidget.callback) imageWidget.callback(imageWidget.value);
                                } else {
                                    alert(`Upload failed: ${resp.statusText}`);
                                }
                            } catch (error) {
                                alert(`Upload error: ${error}`);
                            }
                        };
                        document.body.appendChild(input);
                        input.click();
                        document.body.removeChild(input);
                    };
                }

                // Drag-drop to special folder
                const previewImg = imageWidget.inputEl.nextSibling;
                if (previewImg && previewImg.tagName === "IMG") {
                    previewImg.ondragover = (e) => {
                        e.preventDefault();
                        e.dataTransfer.dropEffect = "copy";
                    };
                    previewImg.ondrop = async (e) => {
                        e.preventDefault();
                        if (!e.dataTransfer.files?.length) return;
                        const file = e.dataTransfer.files[0];
                        const formData = new FormData();
                        formData.append("image", file);
                        formData.append("overwrite", false);
                        try {
                            const resp = await api.fetchApi("/upload/image?type=input&subfolder=custom_holder", {
                                method: "POST",
                                body: formData
                            });
                            if (resp.status === 200) {
                                const data = await resp.json();
                                imageWidget.value = `custom_holder/${data.name}`;
                                if (imageWidget.callback) imageWidget.callback(imageWidget.value);
                            } else {
                                alert(`Upload failed: ${resp.statusText}`);
                            }
                        } catch (error) {
                            alert(`Upload error: ${error}`);
                        }
                    };
                }
            }
        }
    },
    setup() {
        const updateHandler = (event) => {
            const data = event.detail;
            const node = app.graph.getNodeById(parseInt(data.node_id));
            if (!node) return;
            const widget = node.widgets.find(w => w.name === "image");
            if (!widget) return;
            widget.value = data.filename;
            if (widget.callback) widget.callback(widget.value);
        };
        api.addEventListener("customimageholder.update", updateHandler);
    }
});