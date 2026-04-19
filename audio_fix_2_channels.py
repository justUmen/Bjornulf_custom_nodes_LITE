import torch

class AudioChannelFixer:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "fix_channels"
    CATEGORY = "Audio/Utils"

    def fix_channels(self, audio):
        # Extract waveform and sample_rate
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        
        # ComfyUI audio tensors are typically shaped [batch_size, channels, samples]
        # Example Mono: [1, 1, 240000]
        # Example Stereo: [1, 2, 240000]
        
        # Check if the tensor is 3-dimensional (batch, channels, samples)
        if waveform.dim() == 3:
            current_channels = waveform.shape[1]
            if current_channels == 1:
                # Convert Mono to Stereo: duplicate the channel data
                new_waveform = waveform.repeat(1, 2, 1)
            else:
                # Already stereo (or more), pass through
                new_waveform = waveform
                
        # Fallback for 2-dimensional tensors (channels, samples) just in case
        elif waveform.dim() == 2:
            current_channels = waveform.shape[0]
            if current_channels == 1:
                new_waveform = waveform.repeat(2, 1)
            else:
                new_waveform = waveform
        else:
            # Pass through if shape is unexpected to avoid breaking flow
            new_waveform = waveform

        return ({"waveform": new_waveform, "sample_rate": sample_rate},)