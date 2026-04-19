import os
import shutil
import numpy as np
import soundfile as sf
import torch

class SaveTmpAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "audio": ("AUDIO",),
                "audio_path": ("STRING",),
            },
        }

    FUNCTION = "save_audio"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"

    def save_audio(self, audio=None, audio_path=None):
        # Ensure the output directory exists
        os.makedirs("./output", exist_ok=True)

        # Check if neither input is provided
        if audio is None and audio_path is None:
            raise ValueError("Either 'audio' or 'audio_path' must be provided")

        # Case 1: Handle AUDIO input if provided
        if audio is not None:
            # Validate that audio is a dictionary with required keys
            if not isinstance(audio, dict):
                raise ValueError("AUDIO input must be a dictionary with 'waveform' and 'sample_rate'")
            if 'waveform' not in audio or 'sample_rate' not in audio:
                raise ValueError("AUDIO dictionary must contain 'waveform' and 'sample_rate' keys")
            
            # Extract waveform and sample rate
            waveform = audio['waveform']
            sample_rate = audio['sample_rate']
            
            # Ensure waveform is a PyTorch tensor
            if not isinstance(waveform, torch.Tensor):
                raise TypeError(f"Waveform must be a PyTorch tensor, got {type(waveform)}")
            
            # ComfyUI audio is typically (batch, channels, samples). Take the first batch.
            if waveform.ndim == 3:
                waveform = waveform[0]
            elif waveform.ndim > 3:
                waveform = waveform.squeeze()
                if waveform.ndim == 3:
                    waveform = waveform[0]
            
            # Convert to NumPy array
            audio_np = waveform.cpu().numpy()
            
            # SoundFile expects (frames, channels), but ComfyUI gives (channels, frames)
            if audio_np.ndim == 2:
                # If 1st param is small (channels), transpose to (frames, channels)
                if audio_np.shape[0] <= 8 and audio_np.shape[0] < audio_np.shape[1]:
                    audio_np = audio_np.transpose(1, 0)
            elif audio_np.ndim > 2:
                raise ValueError(f"Audio data has too many dimensions: {audio_np.shape}")
            
            # Scale floating-point data to 16-bit integers (assuming range [-1, 1])
            if np.issubdtype(audio_np.dtype, np.floating):
                audio_np = np.clip(audio_np, -1.0, 1.0)
                audio_np = (audio_np * 32767).astype(np.int16)
            
            # Save as WAV file
            filename = "./output/tmp_api.wav"
            sf.write(filename, audio_np, sample_rate)

        # Case 2: Handle audio_path input if audio is not provided
        elif audio_path is not None:
            # Verify the file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Check for supported file extensions
            ext = os.path.splitext(audio_path)[1].lower()
            if ext not in ('.wav', '.mp3'):
                raise ValueError("audio_path must be a .wav or .mp3 file")
            
            # Copy the file to the output directory
            filename = f"./output/tmp_api{ext}"
            shutil.copy(audio_path, filename)

        # Return UI information for ComfyUI
        return {"ui": {"audio": [{"filename": filename, "type": "output"}]}}