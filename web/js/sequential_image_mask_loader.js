import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "Bjornulf.SequentialImageMaskLoader",
    async nodeCreated(node) {
        if (node.comfyClass !== "Bjornulf_SequentialImageMaskLoader") return;

        // Add a reset button widget
        const resetButton = node.addWidget(
            "button",
            "Reset Counter",
            null,
            async () => {
                try {
                    const response = await fetch("/reset_image_loader_counter", {
                        method: "POST",
                    });
                    const data = await response.json();
                    // if (data.success) {
                    //     app.ui.dialog.show("[SequentialImageLoader] Counter reset successfully.");
                    //     updateResetButtonText();
                    // } else {
                    //     app.ui.dialog.show(
                    //         `[SequentialImageLoader] Failed to reset counter: ${data.error || "Unknown error"}`
                    //     );
                    // }
                } catch (error) {
                    app.ui.dialog.show(
                        "[SequentialImageLoader] Error occurred while resetting counter."
                    );
                }
            }
        );

        // Function to update the button text with the next frame number
        const updateResetButtonText = () => {
            fetch("/get_image_loader_counter", {
                method: "POST",
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        const startIndexWidget = node.widgets.find((w) => w.name === "start_index");
                        const startIndex = startIndexWidget ? startIndexWidget.value : 1;
                        const nextFrame = data.value === 0 ? startIndex : data.value;
                        resetButton.name = `Reset Counter (next: ${nextFrame})`;
                    } else {
                        resetButton.name = "Reset Counter (Error)";
                    }
                })
                .catch((error) => {
                    resetButton.name = "Reset Counter (Error)";
                });
        };

        // Initial button text update
        setTimeout(updateResetButtonText, 0);

        // Update button text after each execution
        api.addEventListener("executed", async () => {
            updateResetButtonText();
        });
    },
});