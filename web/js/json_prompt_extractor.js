import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
  name: "Bjornulf.JSONImagePromptExtractor",
  async nodeCreated(node) {
    if (node.comfyClass !== "Bjornulf_JSONImagePromptExtractor") return;

    // Function to update the Reset Button text
    const updateResetButtonTextNode = () => {
      console.log("[json_extractor]=====> updateResetButtonTextNode");
      if (!node.graph) return;

      const jsonPathWidget = node.widgets.find((w) => w.name === "json_file_path");
      if (!jsonPathWidget || !jsonPathWidget.value) {
        resetButton.name = "Reset Counter (No JSON file)";
        return;
      }

      fetch("/get_json_extractor_counter", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          json_file_path: jsonPathWidget.value
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (!node.graph) return;

          if (data.success) {
            const jumpWidget = node.widgets.find((w) => w.name === "jump");

            if (data.value === 0) {
              resetButton.name = "Reset Counter (Empty)";
            } else {
              // Try to get entry count from the last execution or estimate
              let next_value = data.value + jumpWidget.value;
              resetButton.name = `Reset Counter (next: ${next_value})`;
            }
          } else if (node.graph) {
            resetButton.name = "Reset Counter (Error)";
          }
        })
        .catch((error) => {
          if (node.graph) {
            resetButton.name = "Reset Counter (Error)";
          }
        });
    };

    // Add reset button
    const resetButton = node.addWidget(
      "button",
      "Reset Counter",
      null,
      async () => {
        if (!node.graph) return;

        const jsonPathWidget = node.widgets.find((w) => w.name === "json_file_path");
        if (!jsonPathWidget || !jsonPathWidget.value) {
          app.ui.dialog.show("[JSON Extractor] No JSON file path specified.");
          return;
        }

        try {
          const response = await fetch("/reset_json_extractor_counter", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              json_file_path: jsonPathWidget.value
            }),
          });
          const data = await response.json();

          if (!node.graph) return;

          if (data.success) {
            app.ui.dialog.show(`[JSON Extractor] Reset counter successfully.`);
            updateResetButtonTextNode();
          } else {
            app.ui.dialog.show(
              `[JSON Extractor] Failed to reset counter: ${
                data.error || "Unknown error"
              }`
            );
          }
        } catch (error) {
          if (node.graph) {
            app.ui.dialog.show(
              "[JSON Extractor] An error occurred while resetting the counter."
            );
          }
        }
      }
    );

    api.addEventListener("executed", async () => {
      const contextWidget = node.widgets.find(
        (w) => w.name === "LOOP_SEQUENTIAL"
      );
      if (contextWidget && contextWidget.value) {
        updateResetButtonTextNode();
      }
    });

    // Override the original execute function
    const originalExecute = node.execute;
    node.execute = function () {
      const result = originalExecute.apply(this, arguments);
      if (result instanceof Promise) {
        return result.catch((error) => {
          if (error.message.includes("Counter has reached") && node.graph) {
            app.ui.dialog.show(`Execution blocked: ${error.message}`);
          }
          throw error;
        });
      }
      return result;
    };

    // Setup widget handlers for updating counter display
    const setupWidgetHandler = (widgetName) => {
      const widget = node.widgets.find((w) => w.name === widgetName);
      if (widget) {
        const originalOnChange = widget.callback;
        widget.callback = function (v) {
          if (originalOnChange) {
            originalOnChange.call(this, v);
          }
          if (node.widgets.find((w) => w.name === "LOOP_SEQUENTIAL")?.value) {
            updateResetButtonTextNode();
          }
        };
      }
    };

    setupWidgetHandler("jump");
    setupWidgetHandler("json_file_path");
    setupWidgetHandler("LOOP_SEQUENTIAL");

    // Update button visibility based on LOOP_SEQUENTIAL
    const updateButtonVisibility = () => {
      const loopSeqWidget = node.widgets.find(
        (w) => w.name === "LOOP_SEQUENTIAL"
      );
      if (loopSeqWidget) {
        if (loopSeqWidget.value) {
          resetButton.type = "button";
          updateResetButtonTextNode();
        } else {
          resetButton.type = "hidden";
        }
      }
    };

    // Setup visibility handler for LOOP_SEQUENTIAL
    const loopSeqWidget = node.widgets.find(
      (w) => w.name === "LOOP_SEQUENTIAL"
    );
    if (loopSeqWidget) {
      const originalOnChange = loopSeqWidget.callback;
      loopSeqWidget.callback = function (v) {
        if (originalOnChange) {
          originalOnChange.call(this, v);
        }
        updateButtonVisibility();
      };
    }

    // Initial update
    setTimeout(updateButtonVisibility, 0);
  },
});
