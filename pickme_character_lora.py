import os
import random
import folder_paths
from PIL import Image, ImageOps
import numpy as np
import torch

class WriteCharacterPickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"}),  # Custom text global_pickme_id, represents MOVIE
                "picked": ("BOOLEAN", {"default": False}),         # Picked state
                "lora_path_high_noise": ("STRING", {"default": "", "multiline": False}),
                "lora_path_low_noise": ("STRING", {"default": "", "multiline": False}),
                "CHARACTER": ("STRING", {"default": "", "multiline": False}),
                "CHARNAME": ("STRING", {"default": "", "multiline": False}),
                "OUTFITNAME": ("STRING", {"default": "", "multiline": False}),
                "BASIC_DESCRIPTION": ("STRING", {"default": "", "multiline": False}),
                "image": (sorted(files), {"image_upload": True}),
                "prompt": ("STRING", {"multiline": True, "lines": 10})  # Multiline prompt input
            },
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "prompt", "image_path", "variables", "lora_path_high_noise", "lora_path_low_noise")
    FUNCTION = "write_character"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def write_character(self, global_pickme_id, picked, lora_path_high_noise, lora_path_low_noise, CHARACTER, CHARNAME, OUTFITNAME, BASIC_DESCRIPTION, image, prompt, **kwargs):
        image_path = ""
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

        # Save the image to temp for display
        p = (img[0] * 255).clamp(0, 255).cpu().numpy().astype(np.uint8)
        p = Image.fromarray(p, 'RGB')
        filename_prefix = f"Bjornulf_Character_{global_pickme_id}"
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

        variables = (
            f"MOVIE = {global_pickme_id}\n"
            f"CHARACTER = {CHARACTER}\n"
            f"CHARNAME = {CHARNAME}\n"
            f"OUTFITNAME = {OUTFITNAME}\n"
            f"BASIC_DESCRIPTION = {BASIC_DESCRIPTION}\n"
            f"LORA_HIGH = {lora_path_high_noise}\n"
            f"LORA_LOW = {lora_path_low_noise}\n"
            f"IMAGE = {image}\n"
            f"PROMPT = {prompt}"
        )

        return {
            "ui": {"images": results},
            "result": (img, prompt, image_path, variables, lora_path_high_noise, lora_path_low_noise)
        }

class LoadCharacterPickMeGlobal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "global_pickme_id": ("STRING", {"default": "default"})
            },
            "hidden": {"prompt": "PROMPT"}  # For accessing the graph state
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = (
        "picked_image", "picked_prompt", "picked_variables",
        "random_image", "random_prompt", "random_variables"
    )
    FUNCTION = "load_character"
    CATEGORY = "Bjornulf"
    
    def load_character(self, global_pickme_id, prompt=None):
        entries = []
        picked_entry = None
        if prompt:
            for node_id, node_data in prompt.items():
                if node_data.get("class_type") == "WriteCharacterPickMeGlobal":
                    inputs = node_data.get("inputs", {})
                    node_global_pickme_id = inputs.get("global_pickme_id", "default")
                    if node_global_pickme_id == global_pickme_id:
                        entry = {
                            "lora_path_high_noise": inputs.get("lora_path_high_noise", ""),
                            "lora_path_low_noise": inputs.get("lora_path_low_noise", ""),
                            "CHARACTER": inputs.get("CHARACTER", ""),
                            "CHARNAME": inputs.get("CHARNAME", ""),
                            "OUTFITNAME": inputs.get("OUTFITNAME", ""),
                            "BASIC_DESCRIPTION": inputs.get("BASIC_DESCRIPTION", ""),
                            "image_filename": inputs.get("image", ""),
                            "prompt": inputs.get("prompt", "")
                        }
                        entries.append(entry)
                        if inputs.get("picked", False):
                            picked_entry = entry
        
        def format_variables(entry, movie):
            if not entry:
                return ""
            return (
                f"MOVIE = {movie}\n"
                f"CHARACTER = {entry['CHARACTER']}\n"
                f"CHARNAME = {entry['CHARNAME']}\n"
                f"OUTFITNAME = {entry['OUTFITNAME']}\n"
                f"BASIC_DESCRIPTION = {entry['BASIC_DESCRIPTION']}\n"
                f"LORA_HIGH = {entry['lora_path_high_noise']}\n"
                f"LORA_LOW = {entry['lora_path_low_noise']}\n"
                f"IMAGE = {entry['image_filename']}\n"
                f"PROMPT = {entry['prompt']}"
            )
        
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
        
        random_entry = random.choice(entries) if entries else None
        
        picked_image = load_img(picked_entry['image_filename']) if picked_entry else torch.zeros(1, 8, 8, 3)
        picked_prompt = picked_entry['prompt'] if picked_entry else ""
        picked_variables = format_variables(picked_entry, global_pickme_id) if picked_entry else ""
        
        random_image = load_img(random_entry['image_filename']) if random_entry else torch.zeros(1, 8, 8, 3)
        random_prompt = random_entry['prompt'] if random_entry else ""
        random_variables = format_variables(random_entry, global_pickme_id) if random_entry else ""
        
        return (
            picked_image, picked_prompt, picked_variables,
            random_image, random_prompt, random_variables
        )
    
    @classmethod
    def IS_CHANGED(cls, global_pickme_id, prompt=None):
        return float("NaN")