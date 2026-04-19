import os
import shutil

class SaveTmpText:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "slot": ("INT", {"default": 1, "min": 1, "max": 100}),
            },
            "optional": {
                "text": ("STRING", {"multiline": True}),
                "text_path": ("STRING",),
            },
        }

    FUNCTION = "save_text"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def save_text(self, slot, text=None, text_path=None):
        # Ensure the output directory exists
        os.makedirs("./output", exist_ok=True)

        # Check if neither input is provided
        if text is None and text_path is None:
            raise ValueError("Either 'text' or 'text_path' must be provided")

        # Determine the filename based on slot
        if slot == 1:
            filename = "./output/tmp_api.txt"
        else:
            filename = f"./output/tmp_api{slot}.txt"

        # Case 1: Handle text input if provided
        if text is not None:
            # Ensure text is a string
            if not isinstance(text, str):
                raise ValueError("text input must be a string")
            
            # Save as TXT file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)

        # Case 2: Handle text_path input if text is not provided
        elif text_path is not None:
            # Verify the file exists
            if not os.path.exists(text_path):
                raise FileNotFoundError(f"Text file not found: {text_path}")
            
            # Check for supported file extensions
            ext = os.path.splitext(text_path)[1].lower()
            if ext not in ('.txt'):
                raise ValueError("text_path must be a .txt file")
            
            # Copy the file to the output directory
            shutil.copy(text_path, filename)

        print(f"Temporary text saved as: {filename}")

        # Return UI information for ComfyUI
        return {"ui": {"text": [{"filename": filename, "type": "output"}]}}

class LoadTmpText:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "slot": ("INT", {"default": 1, "min": 1, "max": 100}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "load_text"
    CATEGORY = "Bjornulf"

    def load_text(self, slot):
        # Determine the filename based on slot
        if slot == 1:
            filename = "./output/tmp_api.txt"
        else:
            filename = f"./output/tmp_api{slot}.txt"

        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return (content,)