import { app } from "../../../scripts/app.js";
app.registerExtension({
    name: "Bjornulf.PauseResume",
    async nodeCreated(node) {
        if (node.comfyClass === "Bjornulf_PauseResume") {
            const resumeButton = node.addWidget("button", "▶ Resume", "▶ Resume", () => {
                fetch('/bjornulf_resume', { method: 'GET' })
                    .then(response => response.text())
                    .then(data => {
                        console.log('Resume response:', data);
                    })
                    .catch(error => console.error('Error:', error));
            });
            const stopButton = node.addWidget("button", "⏹️ Stop", "⏹️ Stop", () => {
                fetch('/bjornulf_stop', { method: 'GET' })
                    .then(response => response.text())
                    .then(data => {
                        console.log('Stop response:', data);
                    })
                    .catch(error => console.error('Error:', error));
            });
            const rerunButton = node.addWidget("button", "Rerun with 🧺 Basket", "Rerun with input 🧺 Basket", () => {
                        fetch('/bjornulf_resume', { method: 'GET' })
                            .then(resumeResponse => resumeResponse.text())
                            .then(resumeData => {
                                console.log('Resume for rerun:', resumeData);
                                setTimeout(() => {
                                    // Get all upstream nodes recursively, excluding the starting node
                                    function getAllUpstreamNodesExcludingStart(currentNode, visited = new Set()) {
                                        if (visited.has(currentNode)) return [];
                                        visited.add(currentNode);
                                        let upstream = [];
                                        if (currentNode.inputs) {
                                            for (let input of currentNode.inputs) {
                                                if (input.link != null) {
                                                    const link = app.graph.links[input.link];
                                                    if (link) {
                                                        const originNode = app.graph.getNodeById(link.origin_id);
                                                        upstream.push(originNode);
                                                        upstream = upstream.concat(getAllUpstreamNodesExcludingStart(originNode, visited));
                                                    }
                                                }
                                            }
                                        }
                                        return upstream;
                                    }
                                    // Find direct upstream for "input" slot
                                    let directUpstream = null;
                                    const inputSlot = node.inputs.find(i => i.name === "input");
                                    if (inputSlot && inputSlot.link != null) {
                                        const link = app.graph.links[inputSlot.link];
                                        if (link) {
                                            directUpstream = app.graph.getNodeById(link.origin_id);
                                        }
                                    }
                                    let nodesToDisable = [];
                                    if (directUpstream) {
                                        nodesToDisable = getAllUpstreamNodesExcludingStart(directUpstream);
                                    }
                                    // Store previous modes only if not already stored
                                    if (!node.previousModes) {
                                        node.previousModes = nodesToDisable.map(n => ({node: n, mode: n.mode}));
                                    }
                                    // Disable (mute) them
                                    nodesToDisable.forEach(n => n.mode = 4);
                                    app.graph.setDirtyCanvas(true);
                                    app.queuePrompt();
                                    setTimeout(() => {
                                        if (node.previousModes) {
                                            node.previousModes.forEach(pm => pm.node.mode = pm.mode);
                                            delete node.previousModes;
                                            app.graph.setDirtyCanvas(true);
                                        }
                                    }, 5000);
                                }, 2000); // Delay to allow the old execution to fully stop
                            })
                            .catch(error => console.error('Error in resume for rerun:', error));
                        });
            const disableButton = node.addWidget("button", "🖐️ manual disable 🧺 Basket", "🖐️ manual disable 🧺 Basket", () => {
                // Get all upstream nodes recursively, excluding the starting node
                function getAllUpstreamNodesExcludingStart(currentNode, visited = new Set()) {
                    if (visited.has(currentNode)) return [];
                    visited.add(currentNode);
                    let upstream = [];
                    if (currentNode.inputs) {
                        for (let input of currentNode.inputs) {
                            if (input.link != null) {
                                const link = app.graph.links[input.link];
                                if (link) {
                                    const originNode = app.graph.getNodeById(link.origin_id);
                                    upstream.push(originNode);
                                    upstream = upstream.concat(getAllUpstreamNodesExcludingStart(originNode, visited));
                                }
                            }
                        }
                    }
                    return upstream;
                }
                // Find direct upstream for "input" slot
                let directUpstream = null;
                const inputSlot = node.inputs.find(i => i.name === "input");
                if (inputSlot && inputSlot.link != null) {
                    const link = app.graph.links[inputSlot.link];
                    if (link) {
                        directUpstream = app.graph.getNodeById(link.origin_id);
                    }
                }
                let nodesToDisable = [];
                if (directUpstream) {
                    nodesToDisable = getAllUpstreamNodesExcludingStart(directUpstream);
                }
                // Store previous modes only if not already stored
                if (!node.previousModes) {
                    node.previousModes = nodesToDisable.map(n => ({node: n, mode: n.mode}));
                }
                // Disable (mute) them
                nodesToDisable.forEach(n => n.mode = 4);
                app.graph.setDirtyCanvas(true);
            });
            const undoButton = node.addWidget("button", "🖐️ manual re-enable 🧺 Basket", "🖐️ manual re-enable 🧺 Basket", () => {
                if (node.previousModes) {
                    node.previousModes.forEach(pm => pm.node.mode = pm.mode);
                    delete node.previousModes;
                    app.graph.setDirtyCanvas(true);
                }
            });
            // Set seed widget to hidden input
            const seedWidget = node.widgets.find((w) => w.name === "seed");
            if (seedWidget) {
              seedWidget.type = "HIDDEN";
            }
        }
    }
});