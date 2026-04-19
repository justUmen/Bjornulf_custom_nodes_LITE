import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Bjornulf.CivitAILoraSelectorWanVideo",
    async nodeCreated(node) {
        // Check if this is our target node
        if (node.comfyClass === "Bjornulf_CivitAILoraSelectorWanVideo") {
            // Find the period and image widgets
            const periodWidget = node.widgets.find(w => w.name === "period");
            const imageWidget = node.widgets.find(w => w.name === "image");

            if (periodWidget && imageWidget) {
                // **Step 1: Keep the file input hidden**
                const originalDraw = imageWidget.draw;
                imageWidget.draw = function(ctx, node, width, pos, height) {
                    const result = originalDraw.call(this, ctx, node, width, pos, height);
                    const fileInputs = document.querySelectorAll(`input[type="file"][data-widget="${this.name}"]`);
                    fileInputs.forEach(input => {
                        input.style.display = 'none';
                    });
                    return result;
                };

                // **Step 2: Add a callback for period changes**
                periodWidget.callback = async () => {
                    const period = periodWidget.value; // Get the selected period (e.g., "Week")
                    try {
                        // Fetch images from the API
                        const response = await fetch(`/get_images_for_period?period=${period}`);
                        const data = await response.json();

                        if (data.success) {
                            // Update the image widget’s dropdown options
                            imageWidget.options.values = data.images;
                            // Set the default value to the first image (or "none" if empty)
                            imageWidget.value = data.images[0] || "none";
                            // Refresh the UI
                            node.setDirtyCanvas(true);
                        } else {
                            console.error("Failed to fetch images:", data.error);
                        }
                    } catch (error) {
                        console.error("Error fetching images:", error);
                    }
                };

                // **Step 3: Load images for the default period on startup**
                periodWidget.callback();
            }
        }
    }
});

function addHunyuanRefreshButton() {
    // Find all nodes of this type
    const nodes = app.graph._nodes.filter(n => n.type === "CivitAILoraSelectorHunyuan");
    
    nodes.forEach(node => {
        // Add refresh button if it doesn't exist
        if (!node.hunyuan_refresh_button) {
            node.hunyuan_refresh_button = node.addWidget("button", "Refresh Images", null, () => {
                // Get current period value
                const periodWidget = node.widgets.find(w => w.name === "period");
                const refreshWidget = node.widgets.find(w => w.name === "refresh");
                const imageWidget = node.widgets.find(w => w.name === "image");
                
                if (periodWidget && imageWidget) {
                    const currentPeriod = periodWidget.value;
                    
                    // Increment refresh counter to trigger IS_CHANGED
                    if (refreshWidget) {
                        refreshWidget.value = (refreshWidget.value || 0) + 1;
                    }
                    
                    // Fetch new images for the current period
                    fetch(`/get_hunyuan_images_for_period?period=${currentPeriod}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.images) {
                                // Update image widget options
                                imageWidget.options.values = data.images;
                                imageWidget.value = data.images[0] || "none";
                                
                                // Force node to update
                                node.setDirtyCanvas(true);
                                app.graph.setDirtyCanvas(true);
                            } else {
                                console.error("Failed to refresh images:", data.error);
                            }
                        })
                        .catch(error => {
                            console.error("Error refreshing images:", error);
                        });
                }
            });
        }
        
        // Add hide preview context menu option
        if (!node.hunyuan_context_added) {
            const originalGetExtraMenuOptions = node.getExtraMenuOptions;
            node.getExtraMenuOptions = function(canvas, options) {
                if (originalGetExtraMenuOptions) {
                    originalGetExtraMenuOptions.call(this, canvas, options);
                }
                
                const hidePreviewWidget = this.widgets.find(w => w.name === "hide_preview");
                const isHidden = hidePreviewWidget ? hidePreviewWidget.value : false;
                
                options.push({
                    content: isHidden ? "Show Image Preview" : "Hide Image Preview",
                    callback: () => {
                        if (hidePreviewWidget) {
                            hidePreviewWidget.value = !isHidden;
                            
                            // Toggle image widget visibility
                            const imageWidget = this.widgets.find(w => w.name === "image");
                            if (imageWidget) {
                                imageWidget.hidden = hidePreviewWidget.value;
                                this.setSize(this.computeSize());
                                this.setDirtyCanvas(true);
                            }
                        }
                    }
                });
            };
            node.hunyuan_context_added = true;
        }
        
        // Handle period changes to auto-refresh images
        const periodWidget = node.widgets.find(w => w.name === "period");
        if (periodWidget && !periodWidget.hunyuan_callback_added) {
            const originalCallback = periodWidget.callback;
            periodWidget.callback = function(value) {
                if (originalCallback) {
                    originalCallback.call(this, value);
                }
                
                // Auto-refresh images when period changes
                const imageWidget = node.widgets.find(w => w.name === "image");
                const refreshWidget = node.widgets.find(w => w.name === "refresh");
                
                if (imageWidget) {
                    // Increment refresh counter
                    if (refreshWidget) {
                        refreshWidget.value = (refreshWidget.value || 0) + 1;
                    }
                    
                    fetch(`/get_hunyuan_images_for_period?period=${value}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.images) {
                                imageWidget.options.values = data.images;
                                imageWidget.value = data.images[0] || "none";
                                node.setDirtyCanvas(true);
                            }
                        })
                        .catch(error => {
                            console.error("Error auto-refreshing images:", error);
                        });
                }
            };
            periodWidget.hunyuan_callback_added = true;
        }
        
        // Initially hide image preview if hide_preview is true
        const hidePreviewWidget = node.widgets.find(w => w.name === "hide_preview");
        const imageWidget = node.widgets.find(w => w.name === "image");
        if (hidePreviewWidget && hidePreviewWidget.value && imageWidget) {
            imageWidget.hidden = true;
            node.setSize(node.computeSize());
        }
    });
}

// Add the functionality when the extension loads
app.registerExtension({
    name: "Bjornulf.HunyuanLoraSelector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "CivitAILoraSelectorHunyuan") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                // Add functionality after a short delay to ensure widgets are created
                setTimeout(() => {
                    addHunyuanRefreshButton();
                }, 100);
            };
        }
    }
});

// Also run when nodes are loaded from saved workflows
app.registerExtension({
    name: "Bjornulf.HunyuanLoraSelector.Loaded",
    async loadedGraphNode(node) {
        if (node.type === "CivitAILoraSelectorHunyuan") {
            setTimeout(() => {
                addHunyuanRefreshButton();
            }, 100);
        }
    }
});