// import { app } from "../../../scripts/app.js";

// app.registerExtension({
//     name: "ClearVRAM.Button",
//     async nodeCreated(node) {
//         if (node.comfyClass === "Bjornulf_ClearVRAM") {
//             // Create a button widget
//             // const clearButton = {
//             //     name: "clear_vram",
//             //     type: "button",
//             //     callback: () => {
//             //         // Execute the node directly
//             //         node.execute();
//             //     },
//             // };

//             // Add the button widget to the node
//             // node.addWidget("button", clearButton.name, "Clear VRAM", clearButton.callback);

//             node.addWidget("button", "clear_vram", "Clear VRAM", () => {
//                 clearButton.name = "Clearing...";
//                 node.setDirtyCanvas(true);

//                 api.fetchApi("/clear_vram", { method: "POST" })
//                     .then(response => {
//                         if (response.status === 200) {
//                             console.log("VRAM cleared successfully");
//                         } else {
//                             console.error("Failed to clear VRAM");
//                         }
//                     })
//                     .catch(error => {
//                         console.error("Error clearing VRAM:", error);
//                     })
//                     .finally(() => {
//                         clearButton.name = "Clear VRAM";
//                         node.setDirtyCanvas(true);
//                     });
//             });

//             // Resize the node
//             node.setSize(node.computeSize());

//             // Override the original execute function
//             const originalExecute = node.execute;
//             node.execute = function() {
//                 originalExecute.call(this);
//                 // Prevent propagation to connected nodes
//                 return {};
//             };
//         }
//     }
// });
// // // clear_vram_button.js

// // import { app } from "../../../scripts/app.js";

// // app.registerExtension({
// //     name: "Bjornulf.ClearVRAM",
// //     async nodeCreated(node) {
// //         if (node.comfyClass === "Bjornulf_ClearVRAM") {
// //             // Remove any existing inputs and outputs
// //             node.inputs = [];
// //             node.outputs = [];

// //             // Remove any existing widgets
// //             node.widgets.length = 0;

// //             // Create a button widget
// //             const clearButton = node.addWidget("button", "clear_vram", "Clear VRAM", () => {
// //                 clearButton.name = "Clearing...";
// //                 node.setDirtyCanvas(true);

// //                 api.fetchApi("/clear_vram", { method: "POST" })
// //                     .then(response => {
// //                         if (response.status === 200) {
// //                             console.log("VRAM cleared successfully");
// //                         } else {
// //                             console.error("Failed to clear VRAM");
// //                         }
// //                     })
// //                     .catch(error => {
// //                         console.error("Error clearing VRAM:", error);
// //                     })
// //                     .finally(() => {
// //                         clearButton.name = "Clear VRAM";
// //                         node.setDirtyCanvas(true);
// //                     });
// //             });

// //             // Set the node size
// //             node.setSize([150, 50]);
// //         }
// //     }
// // });