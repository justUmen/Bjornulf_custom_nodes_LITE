import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Bjornulf.TextGeneratorStyle",
    async nodeCreated(node) {
        if (node.comfyClass === "Bjornulf_TextGeneratorStyle") {
            // Find the category and style widgets
            const categoryWidget = node.widgets.find(w => w.name === "category");
            const styleWidget = node.widgets.find(w => w.name === "style");

            // Define categories and branches (must match Python's SharedLists)
            const CATEGORIES = [
                "Painting", "Photography", "Digital Art", "3D Rendering", "Illustration"
            ];
            const BRANCHES = {
                "Painting": [
                    "Renaissance", "Baroque", "Rococo", "Neoclassicism",
                    "Romanticism", "Realism", "Impressionism", "Post-Impressionism",
                    "Expressionism", "Fauvism", "Cubism", "Futurism", "Dadaism",
                    "Surrealism", "Abstract Expressionism", "Pop Art", "Op Art",
                    "Minimalism"
                ],
                "Photography": [
                    "Black and White", "Color", "Vintage", "Sepia Tone", "HDR",
                    "Long Exposure", "Macro", "Portrait", "Landscape", "Street",
                    "Fashion", "Analog Film", "Cinematic"
                ],
                "Digital Art": [
                    "Digital Painting", "Vector Art", "Pixel Art", "Fractal Art",
                    "Algorithmic Art", "Glitch Art"
                ],
                "3D Rendering": [
                    "Low Poly", "Voxel", "Isometric", "Ray Tracing"
                ],
                "Illustration": [
                    "Line Art", "Cartoon", "Comic Book", "Manga", "Anime",
                    "Technical Illustration", "Botanical Illustration",
                    "Architectural Rendering", "Concept Art", "Storyboard Art"
                ],
            };

            // Convert category widget to a dropdown
            categoryWidget.type = "combo";
            categoryWidget.options = { values: CATEGORIES };
            // Ensure the initial value is valid
            if (!CATEGORIES.includes(categoryWidget.value)) {
                categoryWidget.value = CATEGORIES[0];
            }

            // Convert style widget to a dropdown
            styleWidget.type = "combo";

            // Function to update style options based on selected category
            const updateStyleOptions = () => {
                const selectedCategory = categoryWidget.value;
                const availableStyles = BRANCHES[selectedCategory] || [];
                styleWidget.options = { values: availableStyles };
                // Ensure the style value is valid
                if (!availableStyles.includes(styleWidget.value)) {
                    styleWidget.value = availableStyles[0] || "";
                }
            };

            // Initial update of style options
            updateStyleOptions();

            // Update style options when category changes
            categoryWidget.callback = updateStyleOptions;
        }
    }
});