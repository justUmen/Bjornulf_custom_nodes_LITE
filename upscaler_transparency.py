import comfy
from comfy import model_management
import torch
import comfy.utils

class ImageUpscaleWithModelTransparency:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "upscale_model": ("UPSCALE_MODEL",),
                              "image": ("IMAGE",),
                              }}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "image/upscaling"

    def upscale(self, upscale_model, image):
        device = model_management.get_torch_device()

        # Check if image has alpha channel (4 channels)
        has_alpha = image.shape[-1] == 4
        
        if has_alpha:
            # Split RGB and alpha channels
            rgb_image = image[..., :3]
            alpha_channel = image[..., 3:4]
        else:
            rgb_image = image
            alpha_channel = None

        # Calculate memory requirements (based on RGB channels)
        memory_required = model_management.module_size(upscale_model.model)
        memory_required += (512 * 512 * 3) * rgb_image.element_size() * max(upscale_model.scale, 1.0) * 384.0
        memory_required += rgb_image.nelement() * rgb_image.element_size()
        
        # Add memory for alpha channel processing if present
        if has_alpha:
            memory_required += alpha_channel.nelement() * alpha_channel.element_size() * max(upscale_model.scale, 1.0) ** 2
        
        model_management.free_memory(memory_required, device)

        upscale_model.to(device)
        
        # Upscale RGB channels
        in_img = rgb_image.movedim(-1,-3).to(device)

        tile = 512
        overlap = 32

        oom = True
        while oom:
            try:
                steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=overlap)
                pbar = comfy.utils.ProgressBar(steps)
                upscaled_rgb = comfy.utils.tiled_scale(in_img, lambda a: upscale_model(a), tile_x=tile, tile_y=tile, overlap=overlap, upscale_amount=upscale_model.scale, pbar=pbar)
                oom = False
            except model_management.OOM_EXCEPTION as e:
                tile //= 2
                if tile < 128:
                    raise e

        upscale_model.to("cpu")
        upscaled_rgb = torch.clamp(upscaled_rgb.movedim(-3,-1), min=0, max=1.0)
        
        # Handle alpha channel if present
        if has_alpha:
            # Upscale alpha channel using simple interpolation
            alpha_upscaled = torch.nn.functional.interpolate(
                alpha_channel.movedim(-1,-3).to(device), 
                size=(upscaled_rgb.shape[1], upscaled_rgb.shape[2]), 
                mode='bilinear', 
                align_corners=False
            ).movedim(-3,-1).to(upscaled_rgb.device)
            
            # Clamp alpha values to [0, 1]
            alpha_upscaled = torch.clamp(alpha_upscaled, min=0, max=1.0)
            
            # Combine RGB and alpha channels
            result = torch.cat([upscaled_rgb, alpha_upscaled], dim=-1)
        else:
            result = upscaled_rgb

        return (result,)