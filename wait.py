import time
import random
class Everything(str):
    def __ne__(self, __value: object) -> bool:
        return False

class WaitingNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "delay_seconds": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 3600.0, "step": 0.01}),
                "use_random": ("BOOLEAN", {"default": False}),
                "min_seconds": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.01}),
                "max_seconds": ("FLOAT", {"default": 10.0, "min": 0.0, "max": 3600.0, "step": 0.01}),
            },
            "optional": {
                "input_any": (Everything("*"), {}),  # Pass-through any input type (image, latent, etc.)
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output_any",)
    FUNCTION = "execute"
    CATEGORY = "utils"

    def execute(self, delay_seconds=5.0, use_random=False, min_seconds=1.0, max_seconds=10.0, input_any=None):
        if use_random:
            wait_time = random.uniform(min_seconds, max_seconds)
        else:
            wait_time = delay_seconds
        
        if wait_time > 0:
            time.sleep(wait_time)  # This pauses execution for the specified seconds
        
        # Pass through the optional input unchanged
        return (input_any,)