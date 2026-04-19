import { app } from "../../../scripts/app.js";

class PickMeNodeUI {
    constructor(node) {
        this.node = node;
        this.initialize();
    }

    initialize() {
        this.node.color = "";
        this.isSelected = false;
        
        this.createGroupWidget();
        this.createPickButton();
        this.setupEventHandlers();
        
        this.syncSelectionState();
    }

    createGroupWidget() {
        this.groupWidget = this.node.widgets.find(w => w.name === "group");
        this.originalGroup = this.normalizeGroup(this.groupWidget.value);
        
        this.groupWidget.onInput = async () => {
            const newGroup = this.normalizeGroup(this.groupWidget.value);
            const oldGroup = this.originalGroup;
            
            if (newGroup !== oldGroup) {
                // Deselect from old group if selected
                if (this.isSelected) {
                    await this.updateServerState(false, oldGroup)
                        .catch(error => console.error("Deselect failed:", error));
                }
                
                this.resetNodeState();
                this.originalGroup = newGroup;
                
                // Sync new group's selection
                await this.syncSelectionState();
            }
        };
    }

    createPickButton() {
        this.node.addWidget("button", "PICK ME !", null, () => this.handlePickClick());
    }

    setupEventHandlers() {
        const textWidget = this.node.widgets.find(w => w.name === "text");
        const originalCallback = textWidget.callback;
        
        textWidget.callback = (value) => {
            originalCallback?.(value);
            if (this.isSelected) {
                this.updateServerState(this.isSelected);
            }
        };
    }

    async handlePickClick() {
        try {
            const newIsSelected = !this.isSelected;
            await this.updateServerState(newIsSelected);
        } catch (error) {
            console.error("Selection failed:", error);
        }
    }

    async updateServerState(newIsSelected, targetGroup = null) {
        const group = targetGroup !== null ? 
            this.normalizeGroup(targetGroup) : 
            this.normalizeGroup(this.groupWidget.value);
            
        const nodeId = this.node.id.toString();
        const textWidget = this.node.widgets.find(w => w.name === "text");
        const currentText = textWidget.value;
        
        const payload = {
            group: group,
            nodeId: nodeId,
            text: currentText,
            isSelected: newIsSelected
        };

        try {
            const response = await fetch("/set_PickMe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || "Update failed");
            }

            // Update all nodes in the target group (captured in payload)
            app.graph._nodes.forEach(n => {
                if (n.comfyClass === "Bjornulf_WriteTextPickMe") {
                    const nGroup = this.normalizeGroup(n.widgets.find(w => w.name === "group")?.value);
                    if (nGroup === group) {
                        const ui = n.pickMeUI;
                        if (ui) {
                            ui.isSelected = (n.id.toString() === data.selectedNodeId);
                            ui.node.color = ui.isSelected ? "#006600" : "";
                            if (ui.isSelected) {
                                const textWidget = n.widgets.find(w => w.name === "text");
                                if (textWidget && textWidget.value !== data.text) {
                                    textWidget.value = data.text;
                                }
                            }
                        }
                    }
                }
            });

            app.graph.setDirtyCanvas(true, true);
        } catch (error) {
            console.error("Server update failed:", error);
            throw error;
        }
    }

    async syncSelectionState() {
      try {
          const group = this.normalizeGroup(this.groupWidget.value);
          const response = await fetch(`/get_PickMe?group=${encodeURIComponent(group)}`);
          
          if (!response.ok) {
              console.warn("Sync failed with status:", response.status);
              return;
          }

          const data = await response.json();
          const currentNodeId = this.node.id.toString();
          
          // Convert both IDs to string for reliable comparison
          this.isSelected = data.nodeId?.toString() === currentNodeId;
          this.node.color = this.isSelected ? "#006600" : "";
          
          const textWidget = this.node.widgets.find(w => w.name === "text");
          if (textWidget && this.isSelected && data.text && textWidget.value !== data.text) {
              textWidget.value = data.text;
          }
          
          app.graph.setDirtyCanvas(true, true);
      } catch (error) {
          console.error("Sync failed:", error);
      }
  }

    resetNodeState() {
        this.isSelected = false;
        this.node.color = "";
        app.graph.setDirtyCanvas(true, true);
    }

    normalizeGroup(name) {
        return (name || "").trim().toLowerCase();
    }
}

app.registerExtension({
  name: "Bjornulf.PickMe",
  async setup() {
      // Add global refresh handler
      const originalRefresh = app.graph.refresh;
      app.graph.refresh = function() {
          originalRefresh.call(this);
          // After graph loads, sync all PickMe nodes
          this._nodes.forEach(n => {
              if (n.comfyClass === "Bjornulf_WriteTextPickMe" && n.pickMeUI) {
                  n.pickMeUI.syncSelectionState();
              }
          });
      };
  },
  nodeCreated(node) {
      if (node.comfyClass === "Bjornulf_WriteTextPickMe") {
          node.pickMeUI = new PickMeNodeUI(node);
          // Immediate sync for new nodes
          queueMicrotask(() => node.pickMeUI.syncSelectionState());
      }
  }
});