import base64
import cv2
import numpy as np
import torch

class loadImageBase64Transparency:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "base64_data": ("STRING", {"default": ""}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "EasyUse/Image/LoadImage"

    def convert_color(self, image):
        """Convert image color space while preserving alpha channel"""
        if len(image.shape) > 2 and image.shape[2] >= 4:
            # Handle BGRA to RGBA conversion
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        elif len(image.shape) > 2 and image.shape[2] == 3:
            # Handle BGR to RGB conversion
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            # Grayscale image
            return image

    def load_image(self, base64_data, prompt=None, extra_pnginfo=None):
        # Decode base64 data to image
        nparr = np.frombuffer(base64.b64decode(base64_data), np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        # Split channels to check for alpha
        channels = cv2.split(result)
        has_alpha = len(channels) > 3
        
        if has_alpha:
            # Extract alpha channel as mask
            mask = channels[3].astype(np.float32) / 255.0
            mask = torch.from_numpy(mask)
        else:
            # Create full opacity mask if no alpha channel
            mask = torch.ones(channels[0].shape, dtype=torch.float32, device="cpu")

        # Convert color space while preserving channels
        result = self.convert_color(result)
        
        # Normalize to 0-1 range
        result = result.astype(np.float32) / 255.0
        
        # Convert to tensor and add batch dimension
        if has_alpha:
            # Keep all 4 channels (RGBA)
            new_images = torch.from_numpy(result)[None,]
        else:
            # RGB only
            new_images = torch.from_numpy(result)[None,]

        # Ensure mask has batch dimension
        mask = mask.unsqueeze(0)

        return (new_images, mask)