import random
import os
import folder_paths
from PIL import Image, ImageOps
import numpy as np
import torch

class WriteImageVideoPromptPickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"}),  # Custom text global_pickme_id
                "picked": ("BOOLEAN", {"default": False}),         # Picked state
                "image": (sorted(files), {"image_upload": True}),
                "video_prompt": ("STRING", {"multiline": True, "lines": 10})  # Multiline video prompt input
            },
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "video_prompt")
    FUNCTION = "write_image_video_prompt"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def write_image_video_prompt(self, global_pickme_id, picked, image, video_prompt, **kwargs):
        if not image:
            img = torch.zeros(1, 8, 8, 3)
        else:
            try:
                full_path = folder_paths.get_annotated_filepath(image)
                i = Image.open(full_path)
                i = ImageOps.exif_transpose(i)
                img = i.convert("RGB")
                img = np.array(img).astype(np.float32) / 255.0
                img = torch.from_numpy(img)[None,]
            except Exception:
                img = torch.zeros(1, 8, 8, 3)
        return (img, video_prompt)

class LoadImageVideoPromptPickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"})
            },
            "hidden": {"prompt": "PROMPT"}  # For accessing the graph state
        }
    
    # Outputs: picked_image (IMAGE), picked_video_prompt (STRING), picked_image_as_variable (STRING), picked_video_prompt_as_variable (STRING),
    # random_image (IMAGE), random_video_prompt (STRING), random_image_as_variable (STRING), random_video_prompt_as_variable (STRING)
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "picked_image", "picked_video_prompt", "picked_image_as_variable", "picked_video_prompt_as_variable",
        "random_image", "random_video_prompt", "random_image_as_variable", "random_video_prompt_as_variable"
    )
    FUNCTION = "load_image_video_prompt"
    CATEGORY = "Bjornulf"
    
    def load_image_video_prompt(self, global_pickme_id, prompt=None):
        pairs = []
        picked_filename = ""
        picked_video_prompt = ""
        if prompt:
            for node_id, node_data in prompt.items():
                if node_data.get("class_type") == "WriteImageVideoPromptPickMeGlobal":
                    inputs = node_data.get("inputs", {})
                    node_global_pickme_id = inputs.get("global_pickme_id", "default")
                    if node_global_pickme_id == global_pickme_id:
                        filename = inputs.get("image", "")
                        video_prompt = inputs.get("video_prompt", "") 
                        pairs.append((filename, video_prompt))
                        if inputs.get("picked", False):
                            picked_filename = filename
                            picked_video_prompt = video_prompt
        random_filename, random_video_prompt = random.choice(pairs) if pairs else ("", "")
        
        def load_img(filename):
            if not filename:
                return torch.zeros(1, 8, 8, 3)
            try:
                full_path = folder_paths.get_annotated_filepath(filename)
                i = Image.open(full_path)
                i = ImageOps.exif_transpose(i)
                img = i.convert("RGB")
                img = np.array(img).astype(np.float32) / 255.0
                return torch.from_numpy(img)[None,]
            except Exception:
                return torch.zeros(1, 8, 8, 3)
        
        picked_image = load_img(picked_filename)
        random_image = load_img(random_filename)
        
        picked_image_var = f"global_pickme_image_{global_pickme_id} = {picked_filename}"
        picked_video_prompt_var = f"global_pickme_video_prompt_{global_pickme_id} = {picked_video_prompt}"
        random_image_var = f"global_pickme_image_{global_pickme_id} = {random_filename}"
        random_video_prompt_var = f"global_pickme_video_prompt_{global_pickme_id} = {random_video_prompt}"
        
        return (
            picked_image, picked_video_prompt, picked_image_var, picked_video_prompt_var,
            random_image, random_video_prompt, random_image_var, random_video_prompt_var
        )
    
    @classmethod
    def IS_CHANGED(cls, global_pickme_id, prompt=None):
        return float("NaN")