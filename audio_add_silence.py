import torch
import torchaudio

class AddSilenceToAudio:
    CATEGORY = "audio"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "start_silence_duration": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 3600.0, "step": 0.1}),
                "end_silence_duration": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.1}),
            },
            "optional": {
                "audio_path": ("STRING", {"default": ""}),
                "audio": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "add_silence"

    def add_silence(self, start_silence_duration, end_silence_duration, audio_path="", audio=None):
        if audio is None and not audio_path:
            raise ValueError("Either 'audio_path' or 'audio' must be provided.")

        if audio is None:
            waveform, sample_rate = torchaudio.load(audio_path)
        else:
            if isinstance(audio, dict):
                waveform = audio["waveform"]
                sample_rate = audio["sample_rate"]
            elif isinstance(audio, tuple) and len(audio) == 2:
                waveform, sample_rate = audio
            else:
                raise ValueError("Invalid AUDIO type.")

        # Handle dimensions
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)  # Assume mono
        elif waveform.dim() == 3:
            if waveform.shape[0] != 1:
                raise ValueError("Batch size > 1 not supported.")
            waveform = waveform[0]
        elif waveform.dim() != 2:
            raise ValueError("Invalid waveform dimensions.")

        channels = waveform.shape[0]
        device = waveform.device
        dtype = waveform.dtype

        new_waveform = waveform

        if start_silence_duration > 0:
            start_silence_samples = int(start_silence_duration * sample_rate)
            start_silence = torch.zeros(channels, start_silence_samples, dtype=dtype, device=device)
            new_waveform = torch.cat([start_silence, new_waveform], dim=1)

        if end_silence_duration > 0:
            end_silence_samples = int(end_silence_duration * sample_rate)
            end_silence = torch.zeros(channels, end_silence_samples, dtype=dtype, device=device)
            new_waveform = torch.cat([new_waveform, end_silence], dim=1)

        # Standardize to 3D [1, channels, samples]
        if new_waveform.dim() == 2:
            new_waveform = new_waveform.unsqueeze(0)

        return ({"waveform": new_waveform, "sample_rate": sample_rate},)

class PadAudioToDuration:
    CATEGORY = "audio"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_duration": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 3600.0, "step": 0.1}),
            },
            "optional": {
                "start_silence_duration": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 3600.0, "step": 0.1}),
                "audio_path": ("STRING", {"default": ""}),
                "audio": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "pad_to_duration"

    def pad_to_duration(self, target_duration, start_silence_duration=0.0, audio_path="", audio=None):
        if audio is None and not audio_path:
            raise ValueError("Either 'audio_path' or 'audio' must be provided.")

        if audio is None:
            waveform, sample_rate = torchaudio.load(audio_path)
        else:
            if isinstance(audio, dict):
                waveform = audio["waveform"]
                sample_rate = audio["sample_rate"]
            elif isinstance(audio, tuple) and len(audio) == 2:
                waveform, sample_rate = audio
            else:
                raise ValueError("Invalid AUDIO type.")

        # Handle dimensions
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)  # Assume mono
        elif waveform.dim() == 3:
            if waveform.shape[0] != 1:
                raise ValueError("Batch size > 1 not supported.")
            waveform = waveform[0]
        elif waveform.dim() != 2:
            raise ValueError("Invalid waveform dimensions.")

        channels = waveform.shape[0]
        current_samples = waveform.shape[1]
        device = waveform.device
        dtype = waveform.dtype

        current_duration = current_samples / sample_rate
        total_after_start = current_duration + start_silence_duration

        if total_after_start > target_duration:
            raise ValueError("Total duration after adding start silence exceeds target duration.")

        end_silence_duration = target_duration - total_after_start

        new_waveform = waveform

        if start_silence_duration > 0:
            start_silence_samples = int(start_silence_duration * sample_rate)
            start_silence = torch.zeros(channels, start_silence_samples, dtype=dtype, device=device)
            new_waveform = torch.cat([start_silence, new_waveform], dim=1)

        if end_silence_duration > 0:
            end_silence_samples = int(end_silence_duration * sample_rate)
            end_silence = torch.zeros(channels, end_silence_samples, dtype=dtype, device=device)
            new_waveform = torch.cat([new_waveform, end_silence], dim=1)

        # Standardize to 3D [1, channels, samples]
        if new_waveform.dim() == 2:
            new_waveform = new_waveform.unsqueeze(0)

        return ({"waveform": new_waveform, "sample_rate": sample_rate},)