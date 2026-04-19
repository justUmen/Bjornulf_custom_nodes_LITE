import random

class TextToStringAndSeed:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "seed": ("INT", {"default": 1}),
            },
        }

    RETURN_NAMES = ("text", "random_seed")
    RETURN_TYPES = ("STRING", "INT")
    FUNCTION = "text_with_random_seed"
    CATEGORY = "Bjornulf"

    def text_with_random_seed(self, text, seed):
        # Create a local random number generator seeded with the input seed
        rng = random.Random(seed)
        # Generate a 64-bit random integer
        random_seed = rng.getrandbits(64)
        return (text, random_seed)
