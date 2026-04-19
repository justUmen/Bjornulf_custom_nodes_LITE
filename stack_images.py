import torch

class StackImages:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "bottom_image": ("IMAGE",),
                "top_image": ("IMAGE",),
            },
            "optional": {
                "bottom_mask": ("MASK",),
                "top_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "composite"

    def composite(self, bottom_image, top_image, bottom_mask=None, top_mask=None):
        B, H, W, C_bottom = bottom_image.shape
        _, _, _, C_top = top_image.shape
        device = bottom_image.device

        # Process bottom_image
        if C_bottom == 4:
            if bottom_mask is None:
                bottom_mask = bottom_image[:, :, :, 3]  # Use alpha as mask
                bottom_image = bottom_image[:, :, :, :3]  # Keep RGB
            else:
                bottom_image = bottom_image[:, :, :, :3]  # Use provided mask, keep RGB
        elif C_bottom != 3:
            raise ValueError("bottom_image must have 3 or 4 channels")

        # Process top_image
        if C_top == 4:
            if top_mask is None:
                top_mask = top_image[:, :, :, 3]  # Use alpha as mask
                top_image = top_image[:, :, :, :3]  # Keep RGB
            else:
                top_image = top_image[:, :, :, :3]  # Use provided mask, keep RGB
        elif C_top != 3:
            raise ValueError("top_image must have 3 or 4 channels")

        # Default masks if still None
        if bottom_mask is None:
            bottom_mask = torch.ones((B, H, W), device=device)
        if top_mask is None:
            top_mask = torch.ones((B, H, W), device=device)

        # Proceed with compositing
        bottom_rgb = bottom_image.permute(0, 3, 1, 2)  # (B, 3, H, W)
        top_rgb = top_image.permute(0, 3, 1, 2)        # (B, 3, H, W)
        bottom_alpha = bottom_mask.unsqueeze(1)        # (B, 1, H, W)
        top_alpha = top_mask.unsqueeze(1)              # (B, 1, H, W)
        alpha_out = top_alpha + bottom_alpha * (1 - top_alpha)
        numerator = top_alpha * top_rgb + bottom_alpha * (1 - top_alpha) * bottom_rgb
        color_out = numerator / (alpha_out + 1e-6)
        output_image = color_out.permute(0, 2, 3, 1)  # (B, H, W, 3)
        output_mask = alpha_out.squeeze(1)            # (B, H, W)
        return (output_image, output_mask)