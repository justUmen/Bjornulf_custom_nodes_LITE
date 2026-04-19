# import random
# import os
# import folder_paths
# from PIL import Image, ImageOps
# import numpy as np
# import torch

# class WriteImagePickMeGlobal:
#     @classmethod
#     def INPUT_TYPES(cls):
#         input_dir = folder_paths.get_input_directory()
#         files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
#         return {
#             "required": {
#                 "global_pickme_id": ("STRING", {"default": "default"}),  # Custom text global_pickme_id
#                 "picked": ("BOOLEAN", {"default": False}),         # Picked state
#                 "image": (sorted(files), {"image_upload": True}),
#                 "note": ("STRING", {"multiline": True, "lines": 10})  # Multiline note input
#             },
#         }
    
#     RETURN_TYPES = ("IMAGE", "STRING")
#     RETURN_NAMES = ("image", "note")
#     FUNCTION = "write_image_note"
#     OUTPUT_NODE = True
#     CATEGORY = "Bjornulf"
    
#     def write_image_note(self, global_pickme_id, picked, image, note, **kwargs):
#         if not image:
#             img = torch.zeros(1, 8, 8, 3)
#         else:
#             try:
#                 full_path = folder_paths.get_annotated_filepath(image)
#                 i = Image.open(full_path)
#                 i = ImageOps.exif_transpose(i)
#                 img = i.convert("RGB")
#                 img = np.array(img).astype(np.float32) / 255.0
#                 img = torch.from_numpy(img)[None,]
#             except Exception:
#                 img = torch.zeros(1, 8, 8, 3)
#         return (img, note)

# class LoadImagePickMeGlobal:
#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "global_pickme_id": ("STRING", {"default": "default"})
#             },
#             "hidden": {"prompt": "PROMPT"}  # For accessing the graph state
#         }
    
#     # Outputs: picked_image (IMAGE), picked_note (STRING), picked_image_as_variable (STRING), picked_note_as_variable (STRING),
#     # random_image (IMAGE), random_note (STRING), random_image_as_variable (STRING), random_note_as_variable (STRING)
#     RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "IMAGE", "STRING", "STRING", "STRING")
#     RETURN_NAMES = (
#         "picked_image", "picked_note", "picked_image_as_variable", "picked_note_as_variable",
#         "random_image", "random_note", "random_image_as_variable", "random_note_as_variable"
#     )
#     FUNCTION = "load_image_note"
#     CATEGORY = "Bjornulf"
    
#     def load_image_note(self, global_pickme_id, prompt=None):
#         pairs = []
#         picked_filename = ""
#         picked_note = ""
#         if prompt:
#             for node_id, node_data in prompt.items():
#                 if node_data.get("class_type") == "Bjornulf_WriteImagePickMeGlobal":
#                     inputs = node_data.get("inputs", {})
#                     node_global_pickme_id = inputs.get("global_pickme_id", "default")
#                     if node_global_pickme_id == global_pickme_id:
#                         filename = inputs.get("image", "")
#                         note = inputs.get("note", "") 
#                         pairs.append((filename, note))
#                         if inputs.get("picked", False):
#                             picked_filename = filename
#                             picked_note = note
#         random_filename, random_note = random.choice(pairs) if pairs else ("", "")
        
#         def load_img(filename):
#             if not filename:
#                 return torch.zeros(1, 8, 8, 3)
#             try:
#                 full_path = folder_paths.get_annotated_filepath(filename)
#                 i = Image.open(full_path)
#                 i = ImageOps.exif_transpose(i)
#                 img = i.convert("RGB")
#                 img = np.array(img).astype(np.float32) / 255.0
#                 return torch.from_numpy(img)[None,]
#             except Exception:
#                 return torch.zeros(1, 8, 8, 3)
        
#         picked_image = load_img(picked_filename)
#         random_image = load_img(random_filename)
        
#         picked_image_var = f"global_pickme_image_{global_pickme_id} = {picked_filename}"
#         picked_note_var = f"global_pickme_note_{global_pickme_id} = {picked_note}"
#         random_image_var = f"global_pickme_image_{global_pickme_id} = {random_filename}"
#         random_note_var = f"global_pickme_note_{global_pickme_id} = {random_note}"
        
#         return (
#             picked_image, picked_note, picked_image_var, picked_note_var,
#             random_image, random_note, random_image_var, random_note_var
#         )
    
#     @classmethod
#     def IS_CHANGED(cls, global_pickme_id, prompt=None):
#         return float("NaN")

import os
import torch
import numpy as np
from PIL import Image, ImageOps
import folder_paths
import random
import hashlib  # For simple hash in IS_CHANGED

def get_recursive_images(input_dir):
    """Recursively list image files in input directory."""
    images = []
    supported_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif')
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(supported_exts):
                rel_path = os.path.relpath(os.path.join(root, file), input_dir).replace(os.sep, '/')
                images.append(rel_path)
    return sorted(images)

class WriteImagePickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        images = get_recursive_images(input_dir)
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"}),  # Custom text global_pickme_id
                "picked": ("BOOLEAN", {"default": False}),         # Picked state
                "image": (images, {"image_upload": True}),
                "note": ("STRING", {"multiline": True, "lines": 10})  # Multiline note input
            },
            "optional": {
                "custom_image": ("IMAGE",)
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "note", "image_path")
    FUNCTION = "write_image_note"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def write_image_note(self, global_pickme_id, picked, image, note, custom_image=None, **kwargs):
        print(f"[DEBUG Write] global_pickme_id: {global_pickme_id}, picked: {picked}, image: '{image}', note len: {len(note) if note else 0}")
        # Determine the image tensor to use
        if custom_image is not None and custom_image.shape[0] > 0:
            print(f"[DEBUG Write] Using custom_image with shape: {custom_image.shape}")
            img = custom_image
            # Replace the selected image file in input directory with the custom image
            try:
                save_path = folder_paths.get_annotated_filepath(image)
                print(f"[DEBUG Write] Saving custom to: {save_path}")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                p = (img[0] * 255).clamp(0, 255).round().cpu().numpy().astype(np.uint8)
                p = Image.fromarray(p, 'RGB')
                p.save(save_path, compress_level=4)
                print(f"[DEBUG Write] Successfully replaced '{image}' with custom image at {save_path}")
            except Exception as e:
                print(f"[WARNING Write] Failed to replace image file '{image}' with custom image: {e}")
                # Fallback to loading the original if save failed
                if not image:
                    img = torch.zeros(1, 8, 8, 3)
                else:
                    try:
                        full_path = folder_paths.get_annotated_filepath(image)
                        i = Image.open(full_path)
                        i = ImageOps.exif_transpose(i)
                        img_pil = i.convert("RGB")
                        img_np = np.array(img_pil).astype(np.float32) / 255.0
                        img = torch.from_numpy(img_np)[None,]
                        print(f"[DEBUG Write] Fallback loaded original with shape: {img.shape}")
                    except Exception as e2:
                        print(f"[WARNING Write] Fallback load failed: {e2}")
                        img = torch.zeros(1, 8, 8, 3)
        else:
            print(f"[DEBUG Write] No custom_image, loading from '{image}'")
            # Load from selected image file
            if not image:
                img = torch.zeros(1, 8, 8, 3)
                print("[DEBUG Write] No image selected, using zero tensor")
            else:
                try:
                    full_path = folder_paths.get_annotated_filepath(image)
                    print(f"[DEBUG Write] Loading from: {full_path}")
                    i = Image.open(full_path)
                    i = ImageOps.exif_transpose(i)
                    img_pil = i.convert("RGB")
                    img_np = np.array(img_pil).astype(np.float32) / 255.0
                    img = torch.from_numpy(img_np)[None,]
                    print(f"[DEBUG Write] Loaded image with shape: {img.shape}")
                except Exception as e:
                    print(f"[WARNING Write] Failed to load '{image}': {e}")
                    img = torch.zeros(1, 8, 8, 3)

        # Save the image to temp for display (unchanged)
        p = (img[0] * 255).clamp(0, 255).cpu().numpy().astype(np.uint8)
        p = Image.fromarray(p, 'RGB')
        filename_prefix = f"Bjornulf_PickMe_{global_pickme_id}"
        output_dir = folder_paths.get_temp_directory()
        subfolder = os.path.normpath(filename_prefix)
        full_output_folder = os.path.join(output_dir, subfolder)
        os.makedirs(full_output_folder, exist_ok=True)

        # Manual counter calculation in the correct folder
        matching_files = [
            f for f in os.listdir(full_output_folder)
            if f.startswith(filename_prefix + "_")
            and f[len(filename_prefix) + 1 :].rstrip(".png").isdigit()
        ]
        if matching_files:
            counters = [
                int(f[len(filename_prefix) + 1 :].rstrip(".png"))
                for f in matching_files
            ]
            counter = max(counters) + 1
        else:
            counter = 1

        file = f"{filename_prefix}_{counter:05}.png"
        output_file = os.path.join(full_output_folder, file)
        p.save(output_file, compress_level=4)
        image_path = output_file
        results = [{"filename": file, "subfolder": subfolder, "type": "temp"}]

        print(f"[DEBUG Write] Temp saved to: {output_file}")

        return {
            "ui": {"images": results},
            "result": (img, note, image_path)
        }

class WriteImagePickMeGlobalInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"}),  # Custom text global_pickme_id
                "picked": ("BOOLEAN", {"default": False}),         # Picked state
                "filename": ("STRING", {"default": ""}),            # Filename to save the input image to (relative path)
                "image": ("IMAGE",),                                # Required IMAGE input
                "note": ("STRING", {"multiline": True, "lines": 10})  # Multiline note input
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "note", "image_path")
    FUNCTION = "write_image_note"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def write_image_note(self, global_pickme_id, picked, filename, image, note, **kwargs):
        # Use the provided IMAGE tensor
        if image is None or image.shape[0] == 0:
            img = torch.zeros(1, 8, 8, 3)
        else:
            img = image

        # Attempt to save the image to the specified filename path
        saved = False
        if filename:
            try:
                save_path = folder_paths.get_annotated_filepath(filename)
                if save_path is not None:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    p = (img[0] * 255).clamp(0, 255).round().cpu().numpy().astype(np.uint8)
                    p = Image.fromarray(p, 'RGB')
                    p.save(save_path, compress_level=4)
                    saved = True
            except Exception as e:
                print(f"Warning: Failed to save input image to '{filename}': {e}")
        if not saved:
            print(f"Warning: Input image not saved to persistent location (filename empty or invalid). Load recovery will show black.")

        # Save the image to temp for display (unchanged)
        p = (img[0] * 255).clamp(0, 255).cpu().numpy().astype(np.uint8)
        p = Image.fromarray(p, 'RGB')
        filename_prefix = f"Bjornulf_PickMe_{global_pickme_id}"
        output_dir = folder_paths.get_temp_directory()
        subfolder = os.path.normpath(filename_prefix)
        full_output_folder = os.path.join(output_dir, subfolder)
        os.makedirs(full_output_folder, exist_ok=True)

        # Manual counter calculation in the correct folder
        matching_files = [
            f for f in os.listdir(full_output_folder)
            if f.startswith(filename_prefix + "_")
            and f[len(filename_prefix) + 1 :].rstrip(".png").isdigit()
        ]
        if matching_files:
            counters = [
                int(f[len(filename_prefix) + 1 :].rstrip(".png"))
                for f in matching_files
            ]
            counter = max(counters) + 1
        else:
            counter = 1

        file = f"{filename_prefix}_{counter:05}.png"
        output_file = os.path.join(full_output_folder, file)
        p.save(output_file, compress_level=4)
        image_path = output_file
        results = [{"filename": file, "subfolder": subfolder, "type": "temp"}]

        return {
            "ui": {"images": results},
            "result": (img, note, image_path)
        }

class LoadImagePickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"})
            },
            "optional": {
                "trigger": ("STRING", {"default": ""})  # Connect image_path from Write to enforce order
            },
            "hidden": {"prompt": "PROMPT"}  # For accessing the graph state
        }
    
    # Outputs: picked_image (IMAGE), picked_note (STRING), picked_image_as_variable (STRING), picked_note_as_variable (STRING),
    # random_image (IMAGE), random_note (STRING), random_image_as_variable (STRING), random_note_as_variable (STRING)
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "picked_image", "picked_note", "picked_image_as_variable", "picked_note_as_variable",
        "random_image", "random_note", "random_image_as_variable", "random_note_as_variable"
    )
    FUNCTION = "load_image_note"
    CATEGORY = "Bjornulf"
    
    def load_image_note(self, global_pickme_id, trigger="", prompt=None):
        pairs = []
        picked_filename = ""
        picked_note = ""
        if prompt:
            for node_id, node_data in prompt.items():
                class_type = node_data.get("class_type")
                if class_type in ["Bjornulf_WriteImagePickMeGlobal", "Bjornulf_WriteImagePickMeGlobalInput"]:
                    inputs = node_data.get("inputs", {})
                    node_global_pickme_id = inputs.get("global_pickme_id", "default")
                    if node_global_pickme_id == global_pickme_id:
                        if class_type == "Bjornulf_WriteImagePickMeGlobal":
                            filename = inputs.get("image", "")
                        else:
                            filename = inputs.get("filename", "")
                        note = inputs.get("note", "") 
                        pairs.append((filename, note))
                        if inputs.get("picked", False):
                            picked_filename = filename
                            picked_note = note
        random_filename, random_note = random.choice(pairs) if pairs else ("", "")
        
        def load_img(filename):
            if not filename:
                return torch.zeros(1, 8, 8, 3)
            try:
                full_path = folder_paths.get_annotated_filepath(filename)
                if full_path is None:
                    raise ValueError("Invalid image path")
                i = Image.open(full_path)
                i = ImageOps.exif_transpose(i)
                img = i.convert("RGB")
                img = np.array(img).astype(np.float32) / 255.0
                return torch.from_numpy(img)[None,]
            except Exception:
                return torch.zeros(1, 8, 8, 3)
        
        picked_image = load_img(picked_filename)
        random_image = load_img(random_filename)
        
        picked_image_var = f"global_pickme_image_{global_pickme_id} = {picked_filename!r}"
        picked_note_var = f"global_pickme_note_{global_pickme_id} = {picked_note!r}"
        random_image_var = f"global_pickme_image_{global_pickme_id} = {random_filename!r}"
        random_note_var = f"global_pickme_note_{global_pickme_id} = {random_note!r}"
        
        return (
            picked_image, picked_note, picked_image_var, picked_note_var,
            random_image, random_note, random_image_var, random_note_var
        )
    
    @classmethod
    def IS_CHANGED(cls, global_pickme_id, trigger="", prompt=None):
        # If trigger is provided and non-empty, hash it for change detection
        if trigger:
            return float(hashlib.md5(trigger.encode()).hexdigest(), 16) % 10000  # Simple float hash
        # Otherwise, use NaN (recompute always on prompt change, but since prompt hidden, fallback)
        return float("NaN")