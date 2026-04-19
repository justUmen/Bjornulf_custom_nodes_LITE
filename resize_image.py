import numpy as np
import torch
from PIL import Image
import math

class ResizeImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {}),
                "width": ("INT", {"default": 256}),
                "height": ("INT", {"default": 256}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = "resize_image"
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def resize_image(self, image, width=256, height=256, prompt=None, extra_pnginfo=None):
        # Ensure the input image is on CPU and convert to numpy array
        image_np = image.cpu().numpy()
        
        # Get original dimensions
        if image_np.ndim == 4:
            orig_height, orig_width = image_np.shape[1:3]
        else:
            orig_height, orig_width = image_np.shape[:2]
        
        # Calculate new dimensions maintaining aspect ratio if needed
        aspect_ratio = orig_width / orig_height
        
        if width == 0 and height == 0:
            # If both are 0, use original dimensions
            new_width, new_height = orig_width, orig_height
        elif width == 0:
            # If width is 0, calculate it based on height
            new_height = height
            new_width = int(height * aspect_ratio)
        elif height == 0:
            # If height is 0, calculate it based on width
            new_width = width
            new_height = int(width / aspect_ratio)
        else:
            # Use provided dimensions
            new_width, new_height = width, height

        # Check if the image is in the format [batch, height, width, channel]
        if image_np.ndim == 4:
            # If so, we'll process each image in the batch
            resized_images = []
            for img in image_np:
                # Convert to PIL Image
                pil_img = Image.fromarray((img * 255).astype(np.uint8))
                # Resize
                resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)
                # Convert back to numpy and normalize
                resized_np = np.array(resized_pil).astype(np.float32) / 255.0
                resized_images.append(resized_np)
            
            # Stack the resized images back into a batch
            resized_batch = np.stack(resized_images)
            # Convert to torch tensor
            resized_tensor = torch.from_numpy(resized_batch)
        else:
            # If it's a single image, process it directly
            # Convert to PIL Image
            pil_img = Image.fromarray((image_np * 255).astype(np.uint8))
            # Resize
            resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)
            # Convert back to numpy and normalize
            resized_np = np.array(resized_pil).astype(np.float32) / 255.0
            # Add batch dimension if it was originally present
            if image.dim() == 4:
                resized_np = np.expand_dims(resized_np, axis=0)
            # Convert to torch tensor
            resized_tensor = torch.from_numpy(resized_np)

        # Update metadata if needed
        if extra_pnginfo is not None:
            extra_pnginfo["resized_width"] = new_width
            extra_pnginfo["resized_height"] = new_height

        return (resized_tensor, prompt, extra_pnginfo)

from PIL import Image
import numpy as np
import torch

class ImageResizer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {}),
                "resolution": (["240p", "360p", "480p", "576p", "720p", "1080p", "2160p"], {"default": "480p"}),
                "resize_mode": (["smallest_side", "largest_side"], {"default": "smallest_side"}),
                "scale_mode": (["both", "enlarge_only", "shrink_only"], {"default": "both"}),
                "multiplier": ([
                    "None",
                    "8 (SD1.5, SDXL, SD3, Cascade)",
                    "16 (Flux, Hunyuan, PixArt, AuraFlow)",
                    "32 (Wan, LTX, Wuerstchen, Mochi)",
                    "56 (Qwen 8 and 14 multiple)"
                ], {"default": "None"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = "resize_to_standard"
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def resize_to_standard(self, image, resolution="480p", resize_mode="smallest_side", scale_mode="both", multiplier="None", prompt=None, extra_pnginfo=None):
        # Define target resolutions
        resolution_map = {
            "240p": 240,
            "360p": 360,
            "480p": 480,
            "576p": 576,
            "720p": 720,
            "1080p": 1080,
            "2160p": 2160  # 4K is 3840x2160, so the smaller dimension is 2160
        }
        
        target_size = resolution_map[resolution]
        
        # Convert image to numpy for processing
        image_np = image.cpu().numpy()
        
        # Get original dimensions
        if image_np.ndim == 4:  # batch of images
            batch_size, orig_height, orig_width = image_np.shape[:3]
            has_batch = True
        else:  # single image
            orig_height, orig_width = image_np.shape[:2]
            has_batch = False
        
        # Calculate new dimensions maintaining aspect ratio
        aspect_ratio = orig_width / orig_height
        
        if resize_mode == "smallest_side":
            # Resize based on the smallest dimension
            if orig_width <= orig_height:  # width is smaller or equal
                new_width = target_size
                new_height = int(new_width / aspect_ratio)
            else:  # height is smaller
                new_height = target_size
                new_width = int(new_height * aspect_ratio)
        else:  # largest_side
            # Resize based on the largest dimension
            if orig_width >= orig_height:  # width is larger or equal
                new_width = target_size
                new_height = int(new_width / aspect_ratio)
            else:  # height is larger
                new_height = target_size
                new_width = int(new_height * aspect_ratio)
        
        # Calculate scale factor
        scale_factor = new_width / orig_width  # Since aspect ratio is preserved, this is the linear scale factor
        
        # Check if we should perform the resize based on scale_mode
        perform_resize = True
        if scale_mode == "enlarge_only" and scale_factor <= 1:
            perform_resize = False
        elif scale_mode == "shrink_only" and scale_factor >= 1:
            perform_resize = False
        
        if not perform_resize:
            # Return original image if resize condition not met
            if extra_pnginfo is not None:
                extra_pnginfo["resolution"] = resolution
                extra_pnginfo["resize_mode"] = resize_mode
                extra_pnginfo["scale_mode"] = scale_mode
                extra_pnginfo["multiplier"] = multiplier
                extra_pnginfo["resized_width"] = orig_width
                extra_pnginfo["resized_height"] = orig_height
                extra_pnginfo["original_width"] = orig_width
                extra_pnginfo["original_height"] = orig_height
            return (image,)
        
        # Extract the multiplier value (first part before space)
        if multiplier != "None":
            m = int(multiplier.split(" ")[0])
            crop_width = (new_width // m) * m
            crop_height = (new_height // m) * m
        else:
            crop_width = new_width
            crop_height = new_height
        
        # Process images
        if has_batch:
            # Process each image in the batch
            resized_images = []
            for img in image_np:
                # Convert to PIL Image
                pil_img = Image.fromarray((img * 255).astype(np.uint8))
                # Resize
                resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)
                # Crop if multiplier is set
                if multiplier != "None":
                    left = (new_width - crop_width) // 2
                    top = (new_height - crop_height) // 2
                    right = left + crop_width
                    bottom = top + crop_height
                    resized_pil = resized_pil.crop((left, top, right, bottom))
                # Convert back to numpy and normalize
                resized_np = np.array(resized_pil).astype(np.float32) / 255.0
                resized_images.append(resized_np)
            
            # Stack the resized images back into a batch
            resized_batch = np.stack(resized_images)
            # Convert to torch tensor
            resized_tensor = torch.from_numpy(resized_batch)
        else:
            # Process a single image
            # Convert to PIL Image
            pil_img = Image.fromarray((image_np * 255).astype(np.uint8))
            # Resize
            resized_pil = pil_img.resize((new_width, new_height), Image.LANCZOS)
            # Crop if multiplier is set
            if multiplier != "None":
                left = (new_width - crop_width) // 2
                top = (new_height - crop_height) // 2
                right = left + crop_width
                bottom = top + crop_height
                resized_pil = resized_pil.crop((left, top, right, bottom))
            # Convert back to numpy and normalize
            resized_np = np.array(resized_pil).astype(np.float32) / 255.0
            
            # Add batch dimension if it was originally present
            if image.dim() == 4:
                resized_np = np.expand_dims(resized_np, axis=0)
            
            # Convert to torch tensor
            resized_tensor = torch.from_numpy(resized_np)

        # Update metadata if needed
        if extra_pnginfo is not None:
            extra_pnginfo["resolution"] = resolution
            extra_pnginfo["resize_mode"] = resize_mode
            extra_pnginfo["scale_mode"] = scale_mode
            extra_pnginfo["multiplier"] = multiplier
            extra_pnginfo["resized_width"] = crop_width
            extra_pnginfo["resized_height"] = crop_height
            extra_pnginfo["original_width"] = orig_width
            extra_pnginfo["original_height"] = orig_height

        return (resized_tensor,)

# class ImageResizerAdvanced:
#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "image": ("IMAGE", {}),
#                 "resolution": ([
#                     "None",
#                     "240p_up", "240p_down",
#                     "360p_up", "360p_down",
#                     "480p_up", "480p_down",
#                     "576p_up", "576p_down",
#                     "720p_up", "720p_down",
#                     "1080p_up", "1080p_down",
#                     "2160p_up", "2160p_down"
#                 ], {"default": "480p_down"}),
#                 "resize_mode": (["smallest_side", "largest_side"], {"default": "smallest_side"}),
#                 "scale_mode": (["both", "enlarge_only", "shrink_only"], {"default": "both"}),
#                 "multiplier": ([
#                     "None",
#                     "8 (SD1.5, SDXL, SD3, Cascade)",
#                     "16 (Flux, Hunyuan, PixArt, AuraFlow)",
#                     "32 (Wan, LTX, Wuerstchen, Mochi)",
#                     "56 (Qwen 8 and 14 multiple)"
#                 ], {"default": "None"}),
#                 "aspect_ratio": (["None", "16:9", "9:16", "1:1", "4:3", "3:4"], {"default": "None"}),
#                 "adjust_mode": (["crop", "pad_black", "pad_white"], {"default": "pad_black"}),
#                 "crop_location": (["center", "left", "right", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"], {"default": "center"}),
#                 "custom_resolution": ("INT", {"default": 0, "min": 0, "step": 1}),
#             },
#             "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
#         }

#     FUNCTION = "resize_to_standard"
#     RETURN_TYPES = ("IMAGE",)
#     OUTPUT_NODE = True
#     CATEGORY = "Bjornulf"

#     def resize_to_standard(self, image, resolution="480p_down", resize_mode="smallest_side", scale_mode="both", multiplier="None", aspect_ratio="None", adjust_mode="pad_black", crop_location="center", prompt=None, extra_pnginfo=None, custom_resolution=0):
#         # Define target resolutions
#         resolution_map = {
#             "240p": 240,
#             "360p": 360,
#             "480p": 480,
#             "576p": 576,
#             "720p": 720,
#             "1080p": 1080,
#             "2160p": 2160  # 4K is 3840x2160, so the smaller dimension is 2160
#         }

#         # Determine target_size and rounding_mode
#         use_custom = custom_resolution > 0
#         if use_custom:
#             target_size = custom_resolution
#             rounding_mode = "down"
#         elif resolution != "None":
#             parts = resolution.rsplit("_", 1)
#             base_res = parts[0]
#             rounding_mode = "up" if len(parts) > 1 and parts[1] == "up" else "down"
#             target_size = resolution_map[base_res]
#         else:
#             target_size = None
#             rounding_mode = "down"

#         # Convert image to numpy for processing
#         image_np = image.cpu().numpy()

#         # Get original dimensions
#         if image_np.ndim == 4:  # batch of images
#             batch_size, orig_height, orig_width, _ = image_np.shape
#             has_batch = True
#         else:  # single image
#             orig_height, orig_width, _ = image_np.shape
#             has_batch = False

#         # Define aspect ratio map
#         aspect_map = {
#             "16:9": 16 / 9,
#             "9:16": 9 / 16,
#             "1:1": 1.0,
#             "4:3": 4 / 3,
#             "3:4": 3 / 4
#         }

#         # Define crop alignment map
#         align_map = {
#             "center": ("center", "center"),
#             "left": ("left", "center"),
#             "right": ("right", "center"),
#             "top": ("center", "top"),
#             "bottom": ("center", "bottom"),
#             "top_left": ("left", "top"),
#             "top_right": ("right", "top"),
#             "bottom_left": ("left", "bottom"),
#             "bottom_right": ("right", "bottom"),
#         }

#         # Get multiplier if set
#         if multiplier != "None":
#             m = int(multiplier.split(" ")[0])
#         else:
#             m = 1  # No adjustment

#         # Process images
#         resized_images = []
#         for img_idx, img in enumerate(image_np if has_batch else [image_np]):
#             # Convert to PIL Image
#             pil_img = Image.fromarray((img * 255).astype(np.uint8))

#             orig_aspect = float(orig_width) / orig_height

#             # Compute intended_w, intended_h and scale_factor
#             if aspect_ratio == "None":
#                 if target_size is None:
#                     intended_w = orig_width
#                     intended_h = orig_height
#                     scale_factor = 1.0
#                 else:
#                     aspect = orig_aspect
#                     if resize_mode == "smallest_side":
#                         if orig_width <= orig_height:
#                             intended_w = target_size
#                             intended_h = int(intended_w / aspect + 0.5)
#                         else:
#                             intended_h = target_size
#                             intended_w = int(intended_h * aspect + 0.5)
#                     else:  # largest_side
#                         if orig_width >= orig_height:
#                             intended_w = target_size
#                             intended_h = int(intended_w / aspect + 0.5)
#                         else:
#                             intended_h = target_size
#                             intended_w = int(intended_h * aspect + 0.5)
#                     scale_factor = float(intended_w) / orig_width
#             else:
#                 aspect = aspect_map[aspect_ratio]
#                 if target_size is None:
#                     # Use original dimensions to determine local target
#                     if resize_mode == "smallest_side":
#                         local_target = min(orig_width, orig_height)
#                     else:
#                         local_target = max(orig_width, orig_height)
#                 else:
#                     local_target = target_size
#                 if resize_mode == "smallest_side":
#                     if aspect >= 1:
#                         intended_h = local_target
#                         intended_w = int(intended_h * aspect + 0.5)
#                     else:
#                         intended_w = local_target
#                         intended_h = int(intended_w / aspect + 0.5)
#                 else:  # largest_side
#                     if aspect >= 1:
#                         intended_w = local_target
#                         intended_h = int(intended_w / aspect + 0.5)
#                     else:
#                         intended_h = local_target
#                         intended_w = int(intended_h * aspect + 0.5)
#                 if adjust_mode == "crop":
#                     scale_factor = max(float(intended_w) / orig_width, float(intended_h) / orig_height)
#                 elif "pad" in adjust_mode:
#                     scale_factor = min(float(intended_w) / orig_width, float(intended_h) / orig_height)
#                 else:
#                     scale_factor = 1.0

#             # Check if we should perform the resize based on scale_mode
#             is_size_targeted = (resolution != "None") or use_custom
#             perform_resize = True
#             if is_size_targeted:
#                 if scale_mode == "enlarge_only" and scale_factor <= 1:
#                     perform_resize = False
#                 elif scale_mode == "shrink_only" and scale_factor >= 1:
#                     perform_resize = False

#             if not perform_resize:
#                 resized_pil = pil_img
#                 final_w = orig_width
#                 final_h = orig_height
#             else:
#                 # Apply multiplier with rounding
#                 if rounding_mode == "up" and m > 1:
#                     target_w = math.ceil(intended_w / m) * m
#                     target_h = math.ceil(intended_h / m) * m
#                 else:  # down or m==1
#                     target_w = (intended_w // m) * m
#                     target_h = (intended_h // m) * m

#                 if aspect_ratio == "None":
#                     # Resize directly to target
#                     resized_pil = pil_img.resize((target_w, target_h), Image.LANCZOS)
#                 else:
#                     orig_aspect = float(orig_width) / orig_height
#                     if adjust_mode == "crop":
#                         # Resize to cover
#                         if orig_aspect > aspect:
#                             resize_h = target_h
#                             resize_w = int(resize_h * orig_aspect + 0.5)
#                         else:
#                             resize_w = target_w
#                             resize_h = int(resize_w / orig_aspect + 0.5)
#                         temp_pil = pil_img.resize((resize_w, resize_h), Image.LANCZOS)
#                         # Crop
#                         h_align, v_align = align_map[crop_location]
#                         if h_align == "left":
#                             left = 0
#                         elif h_align == "right":
#                             left = resize_w - target_w
#                         else:
#                             left = (resize_w - target_w) // 2
#                         if v_align == "top":
#                             top = 0
#                         elif v_align == "bottom":
#                             top = resize_h - target_h
#                         else:
#                             top = (resize_h - target_h) // 2
#                         right = left + target_w
#                         bottom = top + target_h
#                         resized_pil = temp_pil.crop((left, top, right, bottom))
#                     elif "pad" in adjust_mode:
#                         color = (0, 0, 0) if "black" in adjust_mode else (255, 255, 255)
#                         # Resize to fit
#                         if orig_aspect > aspect:
#                             resize_w = target_w
#                             resize_h = int(resize_w / orig_aspect + 0.5)
#                         else:
#                             resize_h = target_h
#                             resize_w = int(resize_h * orig_aspect + 0.5)
#                         temp_pil = pil_img.resize((resize_w, resize_h), Image.LANCZOS)
#                         # Pad
#                         new_img = Image.new("RGB", (target_w, target_h), color)
#                         left = (target_w - resize_w) // 2
#                         top = (target_h - resize_h) // 2
#                         new_img.paste(temp_pil, (left, top))
#                         resized_pil = new_img
#                     final_w = target_w
#                     final_h = target_h

#                 # Convert back to numpy and normalize
#                 resized_np = np.array(resized_pil).astype(np.float32) / 255.0
#                 resized_images.append(resized_np)

#         # Stack the resized images back into a batch
#         if has_batch:
#             resized_batch = np.stack(resized_images)
#         else:
#             resized_batch = resized_images[0]

#         # Convert to torch tensor
#         resized_tensor = torch.from_numpy(resized_batch)

#         # Add batch dimension if originally a single image but expected batch? Wait, original check
#         if image.dim() == 4 and not has_batch:
#             resized_tensor = resized_tensor.unsqueeze(0)

#         # Update metadata if needed
#         if extra_pnginfo is not None:
#             extra_pnginfo["resolution"] = resolution if not use_custom else f"{custom_resolution}p"
#             extra_pnginfo["resize_mode"] = resize_mode
#             extra_pnginfo["scale_mode"] = scale_mode
#             extra_pnginfo["multiplier"] = multiplier
#             extra_pnginfo["aspect_ratio"] = aspect_ratio
#             extra_pnginfo["adjust_mode"] = adjust_mode
#             extra_pnginfo["crop_location"] = crop_location
#             # Use the final size after all adjustments
#             final_width, final_height = resized_pil.size
#             extra_pnginfo["resized_width"] = final_width
#             extra_pnginfo["resized_height"] = final_height
#             extra_pnginfo["original_width"] = orig_width
#             extra_pnginfo["original_height"] = orig_height

#         return (resized_tensor,)

#### do not crash for "shrink_only"
class ImageResizerAdvanced:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {}),
                "resolution": ([
                    "None",
                    "240p_up", "240p_down",
                    "360p_up", "360p_down",
                    "480p_up", "480p_down",
                    "576p_up", "576p_down",
                    "720p_up", "720p_down",
                    "1080p_up", "1080p_down",
                    "2160p_up", "2160p_down"
                ], {"default": "480p_down"}),
                "resize_mode": (["smallest_side", "largest_side"], {"default": "smallest_side"}),
                "scale_mode": (["both", "enlarge_only", "shrink_only"], {"default": "both"}),
                "multiplier": ([
                    "None",
                    "8 (SD1.5, SDXL, SD3, Cascade)",
                    "16 (Flux, Hunyuan, PixArt, AuraFlow)",
                    "32 (Wan, LTX, Wuerstchen, Mochi)",
                    "56 (Qwen 8 and 14 multiple)"
                ], {"default": "None"}),
                "aspect_ratio": (["None", "16:9", "9:16", "1:1", "4:3", "3:4"], {"default": "None"}),
                "adjust_mode": (["crop", "pad_black", "pad_white"], {"default": "pad_black"}),
                "crop_location": (["center", "left", "right", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"], {"default": "center"}),
                "custom_resolution": ("INT", {"default": 0, "min": 0, "step": 1}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = "resize_to_standard"
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def resize_to_standard(self, image, resolution="480p_down", resize_mode="smallest_side", scale_mode="both", multiplier="None", aspect_ratio="None", adjust_mode="pad_black", crop_location="center", prompt=None, extra_pnginfo=None, custom_resolution=0):
        # Define target resolutions
        resolution_map = {
            "240p": 240,
            "360p": 360,
            "480p": 480,
            "576p": 576,
            "720p": 720,
            "1080p": 1080,
            "2160p": 2160  # 4K is 3840x2160, so the smaller dimension is 2160
        }

        # Determine target_size and rounding_mode
        use_custom = custom_resolution > 0
        if use_custom:
            target_size = custom_resolution
            rounding_mode = "down"
        elif resolution != "None":
            parts = resolution.rsplit("_", 1)
            base_res = parts[0]
            rounding_mode = "up" if len(parts) > 1 and parts[1] == "up" else "down"
            target_size = resolution_map[base_res]
        else:
            target_size = None
            rounding_mode = "down"

        # Convert image to numpy for processing
        image_np = image.cpu().numpy()

        # Get original dimensions
        if image_np.ndim == 4:  # batch of images
            batch_size, orig_height, orig_width, _ = image_np.shape
            has_batch = True
        else:  # single image
            orig_height, orig_width, _ = image_np.shape
            has_batch = False

        # Define aspect ratio map
        aspect_map = {
            "16:9": 16 / 9,
            "9:16": 9 / 16,
            "1:1": 1.0,
            "4:3": 4 / 3,
            "3:4": 3 / 4
        }

        # Define crop alignment map
        align_map = {
            "center": ("center", "center"),
            "left": ("left", "center"),
            "right": ("right", "center"),
            "top": ("center", "top"),
            "bottom": ("center", "bottom"),
            "top_left": ("left", "top"),
            "top_right": ("right", "top"),
            "bottom_left": ("left", "bottom"),
            "bottom_right": ("right", "bottom"),
        }

        # Get multiplier if set
        if multiplier != "None":
            m = int(multiplier.split(" ")[0])
        else:
            m = 1  # No adjustment

        # Process images
        resized_images = []
        for img_idx, img in enumerate(image_np if has_batch else [image_np]):
            # Convert to PIL Image
            pil_img = Image.fromarray((img * 255).astype(np.uint8))

            orig_aspect = float(orig_width) / orig_height

            # Compute intended_w, intended_h and scale_factor
            if aspect_ratio == "None":
                if target_size is None:
                    intended_w = orig_width
                    intended_h = orig_height
                    scale_factor = 1.0
                else:
                    aspect = orig_aspect
                    if resize_mode == "smallest_side":
                        if orig_width <= orig_height:
                            intended_w = target_size
                            intended_h = int(intended_w / aspect + 0.5)
                        else:
                            intended_h = target_size
                            intended_w = int(intended_h * aspect + 0.5)
                    else:  # largest_side
                        if orig_width >= orig_height:
                            intended_w = target_size
                            intended_h = int(intended_w / aspect + 0.5)
                        else:
                            intended_h = target_size
                            intended_w = int(intended_h * aspect + 0.5)
                    scale_factor = float(intended_w) / orig_width
            else:
                aspect = aspect_map[aspect_ratio]
                if target_size is None:
                    # Use original dimensions to determine local target
                    if resize_mode == "smallest_side":
                        local_target = min(orig_width, orig_height)
                    else:
                        local_target = max(orig_width, orig_height)
                else:
                    local_target = target_size
                if resize_mode == "smallest_side":
                    if aspect >= 1:
                        intended_h = local_target
                        intended_w = int(intended_h * aspect + 0.5)
                    else:
                        intended_w = local_target
                        intended_h = int(intended_w / aspect + 0.5)
                else:  # largest_side
                    if aspect >= 1:
                        intended_w = local_target
                        intended_h = int(intended_w / aspect + 0.5)
                    else:
                        intended_h = local_target
                        intended_w = int(intended_h * aspect + 0.5)
                if adjust_mode == "crop":
                    scale_factor = max(float(intended_w) / orig_width, float(intended_h) / orig_height)
                elif "pad" in adjust_mode:
                    scale_factor = min(float(intended_w) / orig_width, float(intended_h) / orig_height)
                else:
                    scale_factor = 1.0

            # Check if we should perform the resize based on scale_mode
            is_size_targeted = (resolution != "None") or use_custom
            perform_resize = True
            if is_size_targeted:
                if scale_mode == "enlarge_only" and scale_factor <= 1:
                    perform_resize = False
                elif scale_mode == "shrink_only" and scale_factor >= 1:
                    perform_resize = False

            if not perform_resize:
                resized_pil = pil_img
            else:
                # Apply multiplier with rounding
                if rounding_mode == "up" and m > 1:
                    target_w = math.ceil(intended_w / m) * m
                    target_h = math.ceil(intended_h / m) * m
                else:  # down or m==1
                    target_w = (intended_w // m) * m
                    target_h = (intended_h // m) * m

                if aspect_ratio == "None":
                    # Resize directly to target
                    resized_pil = pil_img.resize((target_w, target_h), Image.LANCZOS)
                else:
                    orig_aspect = float(orig_width) / orig_height
                    target_aspect = float(target_w) / target_h

                    if adjust_mode == "crop":
                        # Resize to cover
                        if orig_aspect > target_aspect:
                            resize_h = target_h
                            resize_w = int(resize_h * orig_aspect + 0.5)
                        else:
                            resize_w = target_w
                            resize_h = int(resize_w / orig_aspect + 0.5)
                        temp_pil = pil_img.resize((resize_w, resize_h), Image.LANCZOS)
                        # Crop
                        h_align, v_align = align_map[crop_location]
                        if h_align == "left":
                            left = 0
                        elif h_align == "right":
                            left = resize_w - target_w
                        else:
                            left = (resize_w - target_w) // 2
                        if v_align == "top":
                            top = 0
                        elif v_align == "bottom":
                            top = resize_h - target_h
                        else:
                            top = (resize_h - target_h) // 2
                        right = left + target_w
                        bottom = top + target_h
                        resized_pil = temp_pil.crop((left, top, right, bottom))
                    elif "pad" in adjust_mode:
                        color = (0, 0, 0) if "black" in adjust_mode else (255, 255, 255)
                        # Resize to fit
                        if orig_aspect > target_aspect:
                            resize_w = target_w
                            resize_h = int(resize_w / orig_aspect + 0.5)
                        else:
                            resize_h = target_h
                            resize_w = int(resize_h * orig_aspect + 0.5)
                        temp_pil = pil_img.resize((resize_w, resize_h), Image.LANCZOS)
                        # Pad
                        new_img = Image.new("RGB", (target_w, target_h), color)
                        left = (target_w - resize_w) // 2
                        top = (target_h - resize_h) // 2
                        new_img.paste(temp_pil, (left, top))
                        resized_pil = new_img

            # Convert back to numpy and normalize
            resized_np = np.array(resized_pil).astype(np.float32) / 255.0
            resized_images.append(resized_np)

        # Stack the resized images back into a batch
        if has_batch:
            resized_batch = np.stack(resized_images)
        else:
            resized_batch = resized_images[0]

        # Convert to torch tensor
        resized_tensor = torch.from_numpy(resized_batch)

        # Add batch dimension if originally a single image but expected batch? Wait, original check
        if image.dim() == 4 and not has_batch:
            resized_tensor = resized_tensor.unsqueeze(0)

        # Update metadata if needed
        if extra_pnginfo is not None:
            extra_pnginfo["resolution"] = resolution if not use_custom else f"{custom_resolution}p"
            extra_pnginfo["resize_mode"] = resize_mode
            extra_pnginfo["scale_mode"] = scale_mode
            extra_pnginfo["multiplier"] = multiplier
            extra_pnginfo["aspect_ratio"] = aspect_ratio
            extra_pnginfo["adjust_mode"] = adjust_mode
            extra_pnginfo["crop_location"] = crop_location
            # Use the final size after all adjustments
            final_width, final_height = resized_pil.size
            extra_pnginfo["resized_width"] = final_width
            extra_pnginfo["resized_height"] = final_height
            extra_pnginfo["original_width"] = orig_width
            extra_pnginfo["original_height"] = orig_height

        return (resized_tensor,)


import torch
import numpy as np
from PIL import Image
import cv2

class ImageResizerToReference:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {}),
                "reference_image": ("IMAGE", {}),
                "pad_mode": (["pad_black", "pad_white"], {"default": "pad_black"}),
                "alignment": (["center", "left", "right", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"], {"default": "center"}),
                "position_mode": (["standard_alignment", "face_position"], {"default": "standard_alignment"}),
            },
            "optional": {
                "resize_percentage": ("FLOAT", {"default": 100.0, "min": 1.0, "max": 500.0, "step": 1.0}),
                "offset_x": ("FLOAT", {"default": 0.0, "min": -2000.0, "max": 2000.0, "step": 1.0}),
                "offset_y": ("FLOAT", {"default": 0.0, "min": -2000.0, "max": 2000.0, "step": 1.0}),
                "input_dwpose": ("IMAGE", {}),
                "reference_dwpose": ("IMAGE", {}),
                "face_keypoint_threshold": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 1.0, "step": 0.1}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    FUNCTION = "resize_to_reference"
    RETURN_TYPES = ("IMAGE",)
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def extract_face_keypoints(self, dwpose_image, face_keypoint_threshold=0.5):
        """Extract face keypoints from DWPose image (white dots on black background)."""
        # Convert to numpy
        if dwpose_image.dim() == 4:
            img_np = dwpose_image[0].cpu().numpy()
        else:
            img_np = dwpose_image.cpu().numpy()
        
        # Convert to grayscale and find white points
        if img_np.shape[-1] == 3:
            gray = np.mean(img_np, axis=-1)
        else:
            gray = img_np
        
        # Find white keypoints (threshold for white dots)
        keypoints = np.where(gray > face_keypoint_threshold)
        
        if len(keypoints[0]) == 0:
            return None
        
        # Get bounding box of all keypoints
        min_y, max_y = np.min(keypoints[0]), np.max(keypoints[0])
        min_x, max_x = np.min(keypoints[1]), np.max(keypoints[1])
        
        # Calculate face dimensions
        face_width = max_x - min_x
        face_height = max_y - min_y
        face_size = max(face_width, face_height)  # Use larger dimension
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        return {
            'bbox': (min_x, min_y, face_width, face_height),
            'center': (center_x, center_y),
            'size': face_size,
            'width': face_width,
            'height': face_height
        }

    def resize_to_reference(self, image, reference_image, pad_mode="pad_black", alignment="center", position_mode="standard_alignment", resize_percentage=100.0, offset_x=0.0, offset_y=0.0, input_dwpose=None, reference_dwpose=None, face_keypoint_threshold=0.5, prompt=None, extra_pnginfo=None):
        # Get target dimensions from reference_image
        if reference_image.dim() == 4:
            _, target_h, target_w, _ = reference_image.shape
        else:
            target_h, target_w, _ = reference_image.shape

        # Convert image to numpy for processing
        image_np = image.cpu().numpy()

        # Get original dimensions
        if image_np.ndim == 4:  # batch of images
            batch_size, orig_h, orig_w, _ = image_np.shape
            has_batch = True
        else:  # single image
            orig_h, orig_w, _ = image_np.shape
            has_batch = False

        # Calculate face-based positioning if DWPose images are provided and we're in face_position mode
        calculated_offset_x = offset_x
        calculated_offset_y = offset_y
        
        if position_mode == "face_position" and input_dwpose is not None and reference_dwpose is not None:
            # Extract face keypoints from both DWPose images
            input_face = self.extract_face_keypoints(input_dwpose, face_keypoint_threshold)
            reference_face = self.extract_face_keypoints(reference_dwpose, face_keypoint_threshold)
            
            if input_face is not None and reference_face is not None:
                # Calculate the offset needed to move the input face to the reference face position
                # After scaling, the input face center will be at a new location
                scale_factor = resize_percentage / 100.0
                input_scaled_center_x = input_face['center'][0] * scale_factor
                input_scaled_center_y = input_face['center'][1] * scale_factor
                
                # Calculate how much to offset the entire image to align face centers
                calculated_offset_x = reference_face['center'][0] - input_scaled_center_x
                calculated_offset_y = reference_face['center'][1] - input_scaled_center_y
                
                print(f"Auto-calculated face positioning:")
                print(f"Input face center: ({input_face['center'][0]:.1f}, {input_face['center'][1]:.1f})")
                print(f"After scaling, input face center will be at: ({input_scaled_center_x:.1f}, {input_scaled_center_y:.1f})")
                print(f"Reference face center: ({reference_face['center'][0]:.1f}, {reference_face['center'][1]:.1f})")
                print(f"Auto-calculated offset: ({calculated_offset_x:.1f}, {calculated_offset_y:.1f})")
            else:
                print("Warning: Could not detect faces in DWPose images. Using manual offset values.")

        # Define alignment map
        align_map = {
            "center": ("center", "center"),
            "left": ("left", "center"),
            "right": ("right", "center"),
            "top": ("center", "top"),
            "bottom": ("center", "bottom"),
            "top_left": ("left", "top"),
            "top_right": ("right", "top"),
            "bottom_left": ("left", "bottom"),
            "bottom_right": ("right", "bottom"),
        }

        h_align, v_align = align_map[alignment]

        # Process images
        resized_images = []
        for img_idx, img in enumerate(image_np if has_batch else [image_np]):
            # Convert to PIL Image
            pil_img = Image.fromarray((img * 255).astype(np.uint8))
            orig_w, orig_h = pil_img.size  # PIL uses (w, h)

            color = (0, 0, 0) if "black" in pad_mode else (255, 255, 255)
            
            # Apply resize percentage
            scale_factor = resize_percentage / 100.0
            
            # Calculate new size after percentage scaling
            scaled_w = int(orig_w * scale_factor + 0.5)
            scaled_h = int(orig_h * scale_factor + 0.5)
            
            # For standard alignment, ensure image fits inside by applying additional scaling if needed
            if position_mode == "standard_alignment":
                # Check if scaled image is too big for target canvas
                if scaled_w > target_w or scaled_h > target_h:
                    # Apply additional scaling to fit inside
                    fit_scale = min(target_w / scaled_w, target_h / scaled_h)
                    scaled_w = int(scaled_w * fit_scale + 0.5)
                    scaled_h = int(scaled_h * fit_scale + 0.5)
            
            # Resize the image
            scaled_pil = pil_img.resize((scaled_w, scaled_h), Image.LANCZOS)
            
            # Create target canvas
            new_img = Image.new("RGB", (target_w, target_h), color)
            
            # Calculate position based on mode
            if position_mode == "face_position":
                # Apply the calculated offset to move the entire image
                left = int(calculated_offset_x)
                top = int(calculated_offset_y)
                
                print(f"Face position mode: offsetting image by ({calculated_offset_x:.1f}, {calculated_offset_y:.1f})")
                
                # Handle cropping when image goes outside bounds
                # Calculate source crop coordinates
                src_left = max(0, -left)
                src_top = max(0, -top)
                src_right = min(scaled_w, src_left + target_w - max(0, left))
                src_bottom = min(scaled_h, src_top + target_h - max(0, top))
                
                # Calculate destination paste coordinates
                dst_left = max(0, left)
                dst_top = max(0, top)
                
                # Crop and paste if there's valid area
                if src_right > src_left and src_bottom > src_top:
                    if src_left > 0 or src_top > 0 or src_right < scaled_w or src_bottom < scaled_h:
                        # Need to crop the scaled image
                        cropped_pil = scaled_pil.crop((src_left, src_top, src_right, src_bottom))
                        new_img.paste(cropped_pil, (dst_left, dst_top))
                    else:
                        # No cropping needed
                        new_img.paste(scaled_pil, (dst_left, dst_top))
            else:
                # Standard alignment - image always fits inside, no cropping
                if h_align == "left":
                    left = 0
                elif h_align == "right":
                    left = target_w - scaled_w
                else:
                    left = (target_w - scaled_w) // 2
                    
                if v_align == "top":
                    top = 0
                elif v_align == "bottom":
                    top = target_h - scaled_h
                else:
                    top = (target_h - scaled_h) // 2
                
                # Since we ensured the image fits, just paste it directly
                new_img.paste(scaled_pil, (left, top))
            
            resized_pil = new_img

            # Convert back to numpy and normalize
            resized_np = np.array(resized_pil).astype(np.float32) / 255.0
            resized_images.append(resized_np)

        # Stack the resized images back into a batch
        if has_batch:
            resized_batch = np.stack(resized_images)
        else:
            resized_batch = resized_images[0]

        # Convert to torch tensor
        resized_tensor = torch.from_numpy(resized_batch)

        # Add batch dimension if originally a batch
        if image.dim() == 4 and not has_batch:
            resized_tensor = resized_tensor.unsqueeze(0)

        # Update metadata if needed
        if extra_pnginfo is not None:
            extra_pnginfo["pad_mode"] = pad_mode
            extra_pnginfo["alignment"] = alignment
            extra_pnginfo["position_mode"] = position_mode
            extra_pnginfo["resize_percentage"] = resize_percentage
            extra_pnginfo["offset_x"] = calculated_offset_x
            extra_pnginfo["offset_y"] = calculated_offset_y
            extra_pnginfo["manual_offset_x"] = offset_x
            extra_pnginfo["manual_offset_y"] = offset_y
            extra_pnginfo["resized_width"] = target_w
            extra_pnginfo["resized_height"] = target_h
            extra_pnginfo["original_width"] = orig_w
            extra_pnginfo["original_height"] = orig_h

        return (resized_tensor,)


class DWPoseFaceScaleCalculator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_dwpose": ("IMAGE", {}),
                "reference_dwpose": ("IMAGE", {}),
                "face_keypoint_threshold": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 1.0, "step": 0.1}),
                "output_mode": (["scale_only", "scale_and_position"], {"default": "scale_only"}),
            }
        }

    FUNCTION = "calculate_face_scale"
    RETURN_TYPES = ("FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("resize_percentage", "offset_x", "offset_y")
    OUTPUT_NODE = False
    CATEGORY = "Bjornulf"

    def calculate_face_scale(self, input_dwpose, reference_dwpose, face_keypoint_threshold=0.5, output_mode="scale_only"):
        """Calculate resize percentage and face position based on face keypoint sizes from DWPose images."""
        
        def extract_face_keypoints(dwpose_image):
            """Extract face keypoints from DWPose image (white dots on black background)."""
            # Convert to numpy
            if dwpose_image.dim() == 4:
                img_np = dwpose_image[0].cpu().numpy()
            else:
                img_np = dwpose_image.cpu().numpy()
            
            # Convert to grayscale and find white points
            if img_np.shape[-1] == 3:
                gray = np.mean(img_np, axis=-1)
            else:
                gray = img_np
            
            # Find white keypoints (threshold for white dots)
            keypoints = np.where(gray > face_keypoint_threshold)
            
            if len(keypoints[0]) == 0:
                return None
            
            # Get bounding box of all keypoints
            min_y, max_y = np.min(keypoints[0]), np.max(keypoints[0])
            min_x, max_x = np.min(keypoints[1]), np.max(keypoints[1])
            
            # Calculate face dimensions
            face_width = max_x - min_x
            face_height = max_y - min_y
            face_size = max(face_width, face_height)  # Use larger dimension
            
            # Calculate center
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            return {
                'bbox': (min_x, min_y, face_width, face_height),
                'center': (center_x, center_y),
                'size': face_size,
                'width': face_width,
                'height': face_height
            }
        
        # Extract face keypoints from both images
        input_face = extract_face_keypoints(input_dwpose)
        reference_face = extract_face_keypoints(reference_dwpose)
        
        if input_face is None or reference_face is None:
            print("Warning: Could not detect face keypoints in one or both images. Returning default values.")
            return (100.0, 0.0, 0.0)
        
        # Calculate scale factor to match face sizes
        scale_factor = reference_face['size'] / input_face['size']
        resize_percentage = scale_factor * 100.0
        
        # Clamp to reasonable bounds
        resize_percentage = max(10.0, min(500.0, resize_percentage))
        
        # Calculate face position offset if requested
        if output_mode == "scale_and_position":
            # Calculate the offset needed to move the input face to the reference face position
            # After scaling, the input face center will be at a new location
            input_scaled_center_x = input_face['center'][0] * scale_factor
            input_scaled_center_y = input_face['center'][1] * scale_factor
            
            # Calculate how much to offset the entire image to align face centers
            offset_x = reference_face['center'][0] - input_scaled_center_x
            offset_y = reference_face['center'][1] - input_scaled_center_y
            
            print(f"Input face center: ({input_face['center'][0]:.1f}, {input_face['center'][1]:.1f})")
            print(f"After scaling, input face center will be at: ({input_scaled_center_x:.1f}, {input_scaled_center_y:.1f})")
            print(f"Reference face center: ({reference_face['center'][0]:.1f}, {reference_face['center'][1]:.1f})")
            print(f"Offset needed: ({offset_x:.1f}, {offset_y:.1f})")
        else:
            offset_x = 0.0
            offset_y = 0.0
        
        print(f"Input face size: {input_face['size']:.1f}, Reference face size: {reference_face['size']:.1f}")
        print(f"Calculated resize percentage: {resize_percentage:.1f}%")
        
        return (resize_percentage, offset_x, offset_y)