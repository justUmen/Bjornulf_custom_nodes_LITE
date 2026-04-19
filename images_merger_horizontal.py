import torch
import numpy as np
from PIL import Image

class MergeImagesHorizontally:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
            },
            "optional": {
                "image3": ("IMAGE",),
                "image4": ("IMAGE",),
                "alignment": (["top", "center", "bottom"], {"default": "center"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "combine_images"

    CATEGORY = "Bjornulf"

    def combine_images(self, image1, image2, image3=None, image4=None, alignment="center"):
        # Collect all provided images
        images = [image1, image2]
        if image3 is not None:
            images.append(image3)
        if image4 is not None:
            images.append(image4)
        
        # Calculate the total width and maximum height
        total_width = sum(img.shape[2] for img in images)
        max_height = max(img.shape[1] for img in images)
        batch_size = images[0].shape[0]
        
        # Create a new tensor filled with zeros (black background)
        # Or you could use ones() for white, or fill with a specific color
        combined_image = torch.zeros(
            (batch_size, max_height, total_width, 3), 
            dtype=images[0].dtype, 
            device=images[0].device
        )
        
        # Paste images side by side with proper vertical alignment
        current_x = 0
        for img in images:
            b, h, w, c = img.shape
            
            # Calculate vertical offset based on alignment
            if alignment == "top":
                y_offset = 0
            elif alignment == "bottom":
                y_offset = max_height - h
            else:  # center
                y_offset = (max_height - h) // 2
            
            # Paste the image at the correct position
            combined_image[:, y_offset:y_offset+h, current_x:current_x+w, :] = img
            
            current_x += w
        
        return (combined_image,)


class MergeBatchImagesHorizontally:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),  # Single input that contains multiple images
            },
            "optional": {
                "max_images": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),  # 0 means use all
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "combine_batch_images"

    CATEGORY = "Bjornulf"

    def combine_batch_images(self, images, max_images=0):
        # images tensor shape: (batch_size, height, width, channels)
        batch_size, height, width, channels = images.shape
        
        # Determine how many images to use
        num_images = batch_size if max_images == 0 else min(max_images, batch_size)
        
        if num_images == 0:
            # Return empty image if no images
            return (torch.zeros((1, height, width, channels), dtype=images.dtype, device=images.device),)
        
        # Use only the specified number of images
        selected_images = images[:num_images]
        
        # Calculate the total width (sum of all image widths)
        total_width = width * num_images
        
        # Create a new tensor for the combined image
        # Output will have batch size of 1
        combined_image = torch.zeros((1, height, total_width, channels), dtype=images.dtype, device=images.device)
        
        # Paste images side by side
        current_x = 0
        for i in range(num_images):
            img = selected_images[i:i+1]  # Keep batch dimension
            combined_image[:, :, current_x:current_x+width, :] = img
            current_x += width
        
        return (combined_image,)

# Alternative version that handles variable image sizes within the batch
class MergeBatchImagesHorizontal:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),  # Single input that contains multiple images
            },
            "optional": {
                "max_images": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),  # 0 means use all
                "align_mode": (["top", "center", "bottom"], {"default": "center"}),  # How to align images vertically
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "combine_batch_images_advanced"

    CATEGORY = "Bjornulf"

    def combine_batch_images_advanced(self, images, max_images=0, align_mode="center"):
        # images tensor shape: (batch_size, height, width, channels)
        batch_size, height, width, channels = images.shape
        
        # Determine how many images to use
        num_images = batch_size if max_images == 0 else min(max_images, batch_size)
        
        if num_images == 0:
            # Return empty image if no images
            return (torch.zeros((1, height, width, channels), dtype=images.dtype, device=images.device),)
        
        # Use only the specified number of images
        selected_images = images[:num_images]
        
        # In this version, we assume all images in the batch have the same dimensions
        # If you need to handle different sizes, you'd need additional logic here
        
        # Calculate the total width
        total_width = width * num_images
        max_height = height  # All images have same height in a batch
        
        # Create a new tensor for the combined image
        combined_image = torch.zeros((1, max_height, total_width, channels), dtype=images.dtype, device=images.device)
        
        # Paste images side by side
        current_x = 0
        for i in range(num_images):
            img = selected_images[i]  # Shape: (height, width, channels)
            
            # Calculate vertical position based on alignment mode
            if align_mode == "top":
                y_offset = 0
            elif align_mode == "bottom":
                y_offset = max_height - height
            else:  # center
                y_offset = (max_height - height) // 2
            
            # Place the image
            combined_image[0, y_offset:y_offset+height, current_x:current_x+width, :] = img
            current_x += width
        
        return (combined_image,)