import os
import folder_paths
from nodes import SaveImage

class SaveImageToFolder(SaveImage):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "folder_name": ("STRING", {"default": "my_folder"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = "save_images"
    CATEGORY = "Bjornulf"
    OUTPUT_NODE = True

    def save_images(self, images, folder_name, prompt=None, extra_pnginfo=None):
        # Create the custom folder within the output directory
        custom_folder = os.path.join(folder_paths.get_output_directory(), folder_name)
        os.makedirs(custom_folder, exist_ok=True)
        
        # Call the parent's save_images with filename_prefix set to "folder_name/"
        # This will make the parent class save to the custom folder
        if images is None:
            return (None,)
        else:
            return super().save_images(
                images=images,
                filename_prefix=f"{folder_name}/_",
                prompt=prompt,
                extra_pnginfo=extra_pnginfo
            )
class SaveImageWithTextToFolder(SaveImage):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "folder_name": ("STRING", {"default": "my_folder"}),
                "text": ("STRING", {"default": "", "multiline": True}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    CATEGORY = "Bjornulf"
    OUTPUT_NODE = True

    def save_images(self, images, folder_name, text, prompt=None, extra_pnginfo=None):
        # Create the custom folder within the output directory
        custom_folder = os.path.join(folder_paths.get_output_directory(), folder_name)
        os.makedirs(custom_folder, exist_ok=True)
        
        # Call the parent's save_images to save the images
        if images is None:
            return {"ui": {"images": []}}
        
        result = super().save_images(
            images=images,
            filename_prefix=f"{folder_name}/_",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo
        )
        
        # Only create text files if text is not empty
        if text.strip():
            # Get the saved image information from the result
            if "ui" in result and "images" in result["ui"]:
                for img_info in result["ui"]["images"]:
                    # img_info contains 'filename' and 'subfolder'
                    filename = img_info.get("filename", "")
                    if filename:
                        # Remove the image extension and create .txt filename
                        base_name = os.path.splitext(filename)[0]
                        text_filename = f"{base_name}.txt"
                        text_filepath = os.path.join(custom_folder, text_filename)
                        
                        # Write the text to the file
                        with open(text_filepath, 'w', encoding='utf-8') as f:
                            f.write(text)
        
        return result