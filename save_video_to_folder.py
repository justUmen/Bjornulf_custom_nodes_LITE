import os
import folder_paths
import shutil

class SaveVideoToFolder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
                "folder_name": ("STRING", {"default": "my_videos"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "save_video"
    CATEGORY = "Bjornulf"
    OUTPUT_NODE = True

    def save_video(self, video_path, folder_name):
        try:
            full_path = os.path.abspath(video_path)
            if not os.path.exists(full_path):
                return {"ui": {"text": "Video path does not exist"}, "result": (None,) }

            input_dir = folder_paths.get_input_directory()
            output_dir = folder_paths.get_output_directory()
            temp_dir = folder_paths.get_temp_directory()

            filename = os.path.basename(full_path)
            custom_folder = os.path.join(output_dir, folder_name)
            dest_path = os.path.join(custom_folder, filename)

            if full_path.startswith(output_dir):
                rel_path = os.path.relpath(full_path, output_dir)
                current_subfolder = os.path.dirname(rel_path)
                if current_subfolder == folder_name.replace('\\', '/'):  # Normalize slashes
                    # Already in the correct folder
                    pass
                else:
                    # Copy to the specified folder
                    os.makedirs(custom_folder, exist_ok=True)
                    shutil.copy(full_path, dest_path)

            elif full_path.startswith(temp_dir):
                # Move from temp to output folder
                os.makedirs(custom_folder, exist_ok=True)
                shutil.move(full_path, dest_path)

            elif full_path.startswith(input_dir):
                # Copy from input to output folder
                os.makedirs(custom_folder, exist_ok=True)
                shutil.copy(full_path, dest_path)

            else:
                return {"ui": {"text": "Video path not in input, output, or temp directories."}, "result": (None,) }

            ui = {"videos": [{"filename": filename, "subfolder": folder_name, "type": "output"}] }

            return {"ui": ui, "result": (dest_path,) }

        except Exception as e:
            return {"ui": {"text": f"Error: {str(e)}"}, "result": (None,) }