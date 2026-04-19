import os
import time
import folder_paths
import numpy as np
import torch
import subprocess
from PIL import Image
import scipy.io.wavfile

class SaveVideoFFV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "fps": ("INT", {"default": 30, "min": 1, "max": 120}),
                "crop_first_frames": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "crop_last_frames": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "number_of_frames": ("INT", {"default": 0, "min": 0, "max": 9999}),
            },
            "optional": {
                "audio": ("AUDIO",),
                "custom_path": ("STRING", {"default": ""}),
                "create_mp4": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE", "STRING", "IMAGE",)
    RETURN_NAMES = ("video_path", "last_frame", "video_mp4_path", "frame_24_before_last",)
    FUNCTION = "save_video"
    OUTPUT_NODE = True
    CATEGORY = "video"

    def _create_smol_versions(self, ffv1_path, smol_dir, base_name, has_audio):
        """Re-encode the lossless FFV1 into 4 smaller files in smol_dir."""
        os.makedirs(smol_dir, exist_ok=True)

        variants = [
            # (suffix, extension, scale_filter)
            ("", ".mp4", None),
            #("_1080p", ".mp4", "scale=-2:'min(1080,ih)'"),
        ]

        for suffix, ext, scale_filter in variants:
            out_path = os.path.join(smol_dir, f"{base_name}{suffix}{ext}")
            cmd = ["ffmpeg", "-y", "-i", ffv1_path]

            if scale_filter:
                cmd.extend(["-vf", scale_filter])

            cmd.extend([
                "-c:v", "libx265",
                "-crf", "18",
                "-preset", "veryslow",
                "-pix_fmt", "yuv420p",
            ])

            if has_audio:
                cmd.extend(["-c:a", "aac", "-b:a", "320k"])
            else:
                cmd.extend(["-an"])

            cmd.append(out_path)
            subprocess.run(cmd, check=True)

    def save_video(self, images, fps, crop_first_frames=0, crop_last_frames=0, number_of_frames=0, audio=None, custom_path="", create_mp4=False):
        if crop_first_frames > 0:
            images = images[crop_first_frames:]
        if number_of_frames > 0:
            images = images[:number_of_frames]
        if crop_last_frames > 0:
            images = images[:-crop_last_frames]
        if images.shape[0] == 0:
            return ("", torch.zeros(1, 8, 8, 3), "", torch.zeros(1, 8, 8, 3))

        output_dir = folder_paths.get_output_directory()

        if custom_path and custom_path.strip() != "":
            custom_path = custom_path.strip()
            # Treat custom_path as a folder (relative to output_dir if not absolute)
            if os.path.isabs(custom_path):
                folder = custom_path
            else:
                folder = os.path.join(output_dir, custom_path)
            os.makedirs(folder, exist_ok=True)

            # Find the next incremental filename (0001.mkv, 0002.mkv, ...)
            existing = [f for f in os.listdir(folder) if f.endswith(".mkv")]
            next_num = 1
            for f in existing:
                name = os.path.splitext(f)[0]
                if name.isdigit():
                    next_num = max(next_num, int(name) + 1)
            video_name = f"{next_num:04d}.mkv"
            video_path = os.path.join(folder, video_name)
        else:
            video_name = f"video_{int(time.time() * 1000)}.mkv"
            video_path = os.path.join(output_dir, video_name)

        temp_dir = folder_paths.get_temp_directory()
        temp_prefix = os.path.join(temp_dir, f"frame_{os.path.basename(video_name)}_")

        os.makedirs(temp_dir, exist_ok=True)

        frame_files = []
        for i, img in enumerate(images):
            img_np = np.clip(img.cpu().numpy() * 255, 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np, "RGB")
            frame_path = f"{temp_prefix}{i:06d}.png"
            pil_img.save(frame_path, compress_level=0)  # Lossless PNG
            frame_files.append(frame_path)

        audio_path = None
        if audio is not None:
            audio_path = os.path.join(temp_dir, f"audio_{os.path.basename(video_name)}.wav")
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            if waveform.dim() == 3:
                waveform = waveform.squeeze(0)
            # Use scipy instead of torchaudio to avoid torchcodec/CUDA dependency issues
            waveform_np = waveform.cpu().numpy().T  # (channels, samples) -> (samples, channels)
            # Convert float [-1, 1] to int16
            waveform_int16 = np.clip(waveform_np * 32767, -32768, 32767).astype(np.int16)
            scipy.io.wavfile.write(audio_path, sample_rate, waveform_int16)

        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", f"{temp_prefix}%06d.png"
        ]

        if audio_path is not None:
            cmd.extend(["-i", audio_path])

        cmd.extend([
            "-c:v", "ffv1",
            "-level", "3",
            "-pix_fmt", "gbrp",  # For RGB lossless via RCT
        ])

        if audio_path is not None:
            cmd.extend(["-c:a", "flac"])

        cmd.append(video_path)

        subprocess.run(cmd, check=True)

        # Create smaller "smol" versions from the lossless FFV1 source
        video_dir = os.path.dirname(video_path)
        smol_dir = os.path.join(video_dir, "smol")
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        if create_mp4:
            self._create_smol_versions(video_path, smol_dir, base_name, has_audio=(audio_path is not None))

        # Clean up temp files
        for frame_path in frame_files:
            os.remove(frame_path)
            
        if audio_path is not None and os.path.exists(audio_path):
            os.remove(audio_path)

        last_frame = images[-1:].clone()  # Unsqueeze not needed, already [1, H, W, C]

        # Frame 24 before last (index -25 when last is -1)
        if images.shape[0] >= 25:
            frame_24_before_last = images[-25:-24].clone()
        else:
            frame_24_before_last = images[0:1].clone()  # Fallback to first frame

        # Save both frames as images in smol dir
        os.makedirs(smol_dir, exist_ok=True)
        for frame_tensor, suffix in [(last_frame, "_last_frame"), (frame_24_before_last, "_frame_24_before_last")]:
            frame_np = np.clip(frame_tensor[0].cpu().numpy() * 255, 0, 255).astype(np.uint8)
            frame_img = Image.fromarray(frame_np, "RGB")
            frame_img.save(os.path.join(smol_dir, f"{base_name}{suffix}.png"))

        if create_mp4:
            # Return ui dict so ComfyUI recognizes this as a saved asset
            # Point to the smol mp4 as the generated asset
            mp4_filename = f"{base_name}.mp4"
            mp4_subfolder = os.path.relpath(smol_dir, output_dir)
            video_mp4_path = os.path.join(smol_dir, mp4_filename)

            return {
                "ui": {
                    "video": [mp4_filename, mp4_subfolder],
                },
                "result": (video_path, last_frame, video_mp4_path, frame_24_before_last),
            }
        else:
            return {
                "ui": {},
                "result": (video_path, last_frame, "", frame_24_before_last),
            }