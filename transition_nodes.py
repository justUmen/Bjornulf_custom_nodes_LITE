import torch
import imageio.v3 as imageio
import os
from comfy import folder_paths

class ImageTransition:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "frames": ("INT", {"default": 30, "min": 2, "max": 1024, "step": 1}),
                "fps": ("INT", {"default": 16, "min": 1, "max": 60, "step": 1}),
                "filename_prefix": ("STRING", {"default": "ComfyUI_transition", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "create_transition"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def create_transition(self, image1, image2, frames, fps, filename_prefix):
        # Clone inputs to avoid modifying originals
        image1 = image1.clone()
        image2 = image2.clone()

        # Assume single batch; take first if batched
        if image1.shape[0] > 1:
            image1 = image1[:1]
        if image2.shape[0] > 1:
            image2 = image2[:1]

        # Check dimensions
        if image1.shape != image2.shape:
            raise ValueError("Input images must have the same dimensions and batch size (1).")

        h, w, c = image1.shape[1:]
        device = image1.device
        dtype = image1.dtype

        # Generate transition frames
        transition_frames = []
        for i in range(frames):
            alpha = i / (frames - 1.0) if frames > 1 else 0.0
            # Linear interpolation
            frame = (1 - alpha) * image1[0] + alpha * image2[0]
            # Clamp to [0, 1]
            frame = torch.clamp(frame, 0.0, 1.0)
            # Convert to uint8
            frame_uint8 = (frame * 255.0).to(torch.uint8)
            # To numpy (HWC)
            frame_np = frame_uint8.cpu().numpy()
            transition_frames.append(frame_np)

        # Output directory
        out_dir = folder_paths.get_output_directory()
        # Ensure unique filename
        base_name = f"{filename_prefix}_{frames}f_{fps}fps"
        video_path = os.path.join(out_dir, f"{base_name}.mp4")
        counter = 1
        while os.path.exists(video_path):
            video_path = os.path.join(out_dir, f"{base_name}_{counter}.mp4")
            counter += 1

        # Save as MP4 using imageio (requires ffmpeg backend)
        imageio.mimwrite(video_path, transition_frames, fps=fps, quality=8, macro_block_size=1)

        print(f"Transition video saved to: {video_path}")
        return (video_path,)