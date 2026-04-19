import os
import time
import json
import folder_paths
import numpy as np
import torch
import subprocess
from PIL import Image
import scipy.io.wavfile


class SaveVideoAsImages:
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

    def save_video(self, images, fps, crop_first_frames=0, crop_last_frames=0, number_of_frames=0, audio=None, custom_path="", create_mp4=False):
        # Apply frame cropping (same logic as SaveVideoFFV1)
        if crop_first_frames > 0:
            images = images[crop_first_frames:]
        if number_of_frames > 0:
            images = images[:number_of_frames]
        if crop_last_frames > 0:
            images = images[:-crop_last_frames]
        if images.shape[0] == 0:
            return ("", torch.zeros(1, 8, 8, 3), "", torch.zeros(1, 8, 8, 3))

        output_dir = folder_paths.get_output_directory()

        # Determine base folder
        if custom_path and custom_path.strip() != "":
            custom_path = custom_path.strip()
            if os.path.isabs(custom_path):
                base_folder = custom_path
            else:
                base_folder = os.path.join(output_dir, custom_path)
        else:
            base_folder = output_dir

        os.makedirs(base_folder, exist_ok=True)

        # Find the next incremental folder name (0001, 0002, ...)
        existing = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d)) and d.isdigit()]
        next_num = 1
        for d in existing:
            next_num = max(next_num, int(d) + 1)
        folder_name = f"{next_num:04d}"
        frames_folder = os.path.join(base_folder, folder_name)
        os.makedirs(frames_folder, exist_ok=True)

        total_frames = images.shape[0]
        height = images.shape[1]
        width = images.shape[2]

        # Save all frames as numbered PNGs
        for i in range(total_frames):
            img_np = np.clip(images[i].cpu().numpy() * 255, 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np, "RGB")
            frame_path = os.path.join(frames_folder, f"frame_{i + 1:06d}.png")
            pil_img.save(frame_path, compress_level=0)  # Lossless PNG, fast write

        # Save audio if provided
        has_audio = audio is not None
        if has_audio:
            audio_path = os.path.join(frames_folder, "audio.wav")
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            if waveform.dim() == 3:
                waveform = waveform.squeeze(0)
            waveform_np = waveform.cpu().numpy().T  # (channels, samples) -> (samples, channels)
            waveform_int16 = np.clip(waveform_np * 32767, -32768, 32767).astype(np.int16)
            scipy.io.wavfile.write(audio_path, sample_rate, waveform_int16)

        # Save video_details.json
        details = {
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "has_audio": has_audio,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        json_path = os.path.join(frames_folder, "video_details.json")
        with open(json_path, "w") as f:
            json.dump(details, f, indent=2)

        # Save reconstruct.txt with ready-to-run ffmpeg commands
        self._write_reconstruct_txt(frames_folder, fps, has_audio)

        # Create mp4 if requested
        mp4_path = ""
        ui_dict = {}
        if create_mp4:
            mp4_filename = f"{folder_name}.mp4"
            mp4_filepath = os.path.join(base_folder, mp4_filename)
            
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", os.path.join(frames_folder, "frame_%06d.png")
            ]
            
            if has_audio:
                cmd.extend(["-i", audio_path])
                
            cmd.extend([
                "-c:v", "libx264",
                "-crf", "23",
                "-preset", "medium",
                "-pix_fmt", "yuv420p"
            ])
            
            if has_audio:
                cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            else:
                cmd.extend(["-an"])
                
            cmd.append(mp4_filepath)
            
            try:
                subprocess.run(cmd, check=True)
                mp4_path = mp4_filepath
                
                # Make it show up in the UI (like SaveVideoFFV1 does)
                mp4_subfolder = os.path.relpath(base_folder, output_dir)
                if mp4_subfolder == ".":
                    mp4_subfolder = ""
                ui_dict["video"] = [mp4_filename, mp4_subfolder]
            except subprocess.CalledProcessError as e:
                print(f"Error generating MP4: {e}")

        # Return values (same structure as SaveVideoFFV1)
        last_frame = images[-1:].clone()

        if images.shape[0] >= 25:
            frame_24_before_last = images[-25:-24].clone()
        else:
            frame_24_before_last = images[0:1].clone()

        return {
            "ui": ui_dict,
            "result": (mp4_path if mp4_path else frames_folder, last_frame, mp4_path, frame_24_before_last),
        }

    def _write_reconstruct_txt(self, frames_folder, fps, has_audio):
        if has_audio:
            audio_input = "-i audio.wav "
            audio_codec_aac = "-c:a aac -b:a 320k "
            audio_codec_aac_fast = "-c:a aac -b:a 192k "
            audio_codec_flac = "-c:a flac "
        else:
            audio_input = ""
            audio_codec_aac = "-an "
            audio_codec_aac_fast = "-an "
            audio_codec_flac = "-an "

        content = f"""# =============================================================
# Video Reconstruction Commands
# =============================================================
# Run these commands from INSIDE this folder:
#   cd "{frames_folder}"
# =============================================================

# --- Efficient MP4 (H.265, CRF 18, high quality, small size) ---
ffmpeg -framerate {fps} -i frame_%06d.png {audio_input}-c:v libx265 -crf 18 -preset veryslow -pix_fmt yuv420p {audio_codec_aac}output.mp4

# --- HQ Lossless FFV1 (MKV, lossless, large size) ---
ffmpeg -framerate {fps} -i frame_%06d.png {audio_input}-c:v ffv1 -level 3 -pix_fmt gbrp {audio_codec_flac}output.mkv

# --- Fast MP4 (H.264, CRF 23, good quality, fast encode) ---
ffmpeg -framerate {fps} -i frame_%06d.png {audio_input}-c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p {audio_codec_aac_fast}output_fast.mp4

# --- ProRes 422 HQ (MOV, broadcast quality, very large) ---
ffmpeg -framerate {fps} -i frame_%06d.png {audio_input}-c:v prores_ks -profile:v 3 -pix_fmt yuva444p10le {audio_codec_aac}output.mov
"""

        txt_path = os.path.join(frames_folder, "reconstruct.txt")
        with open(txt_path, "w") as f:
            f.write(content)
