
import os
import random
import shutil
import urllib.request
import folder_paths

class ApiDynamicTextInputsv2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0}),
                "prompt_1": ("STRING", {"default": ""}),
                "prompt_2": ("STRING", {"default": ""}),
                "prompt_3": ("STRING", {"default": ""}),
                "prompt_4": ("STRING", {"default": ""}),
                "prompt_5": ("STRING", {"default": ""}),
                "neg_prompt": ("STRING", {"default": ""}),
                "denoise": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "upscale": ("FLOAT", {"default": 2.0, "min": 1.0, "max": 4.0, "step": 0.1}),
                "audio_input_path": ("STRING", {"default": "tmp_api.mp3"}),
                "video_input_path": ("STRING", {"default": "tmp_api.mp4"}),
                "api_url_HERE": ("STRING", {"default": "http://192.168.1.23:8188"}),
                "int_1": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_2": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_3": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_4": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_5": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_6": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_7": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "int_8": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "float_1": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "float_2": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "float_3": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "float_4": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "float_5": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "text_1": ("STRING", {"default": ""}),
                "text_2": ("STRING", {"default": ""}),
                "text_3": ("STRING", {"default": ""}),
                "text_4": ("STRING", {"default": ""}),
                "text_5": ("STRING", {"default": ""}),
                "text_6": ("STRING", {"default": ""}),
                "text_7": ("STRING", {"default": ""}),
                "text_8": ("STRING", {"default": ""}),
                "model_sampling": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "scheduler": ("STRING", {"default": ""}),
                "sampler": ("STRING", {"default": ""}),
                "lora_high_noise_path_1": ("STRING", {"default": ""}),
                "lora_high_noise_path_2": ("STRING", {"default": ""}),
                "lora_high_noise_path_3": ("STRING", {"default": ""}),
                "lora_high_noise_path_4": ("STRING", {"default": ""}),
                "lora_high_noise_path_5": ("STRING", {"default": ""}),
                "lora_high_noise_strength_1": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_high_noise_strength_2": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_high_noise_strength_3": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_high_noise_strength_4": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_high_noise_strength_5": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_low_noise_path_1": ("STRING", {"default": ""}),
                "lora_low_noise_path_2": ("STRING", {"default": ""}),
                "lora_low_noise_path_3": ("STRING", {"default": ""}),
                "lora_low_noise_path_4": ("STRING", {"default": ""}),
                "lora_low_noise_path_5": ("STRING", {"default": ""}),
                "lora_low_noise_strength_1": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_low_noise_strength_2": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_low_noise_strength_3": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_low_noise_strength_4": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_low_noise_strength_5": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01}),
                "lora_trigger_words_1": ("STRING", {"default": ""}),
                "lora_trigger_words_2": ("STRING", {"default": ""}),
                "lora_trigger_words_3": ("STRING", {"default": ""}),
                "lora_trigger_words_4": ("STRING", {"default": ""}),
                "lora_trigger_words_5": ("STRING", {"default": ""}),
                "width": ("INT", {"default": 704, "min": 0, "max": 9999}),
                "height": ("INT", {"default": 1280, "min": 0, "max": 9999}),
                "frames": ("INT", {"default": 1, "min": 0, "max": 9999}),
                "fps": ("FLOAT", {
                    "default": 16.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1
                }),
                "image_1_base64": ("STRING", {"default": ""}),
                "image_2_base64": ("STRING", {"default": ""}),
                "image_3_base64": ("STRING", {"default": ""}),
                "image_4_base64": ("STRING", {"default": ""}),
                "image_5_base64": ("STRING", {"default": ""}),
                "video_1_base64": ("STRING", {"default": ""}),
                "video_2_base64": ("STRING", {"default": ""}),
                "video_3_base64": ("STRING", {"default": ""}),
                "video_4_base64": ("STRING", {"default": ""}),
                "video_5_base64": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (
        "INT",     # seed
        "STRING",  # prompt_1
        "STRING",  # prompt_2
        "STRING",  # prompt_3
        "STRING",  # prompt_4
        "STRING",  # prompt_5
        "STRING",  # neg_prompt
        "FLOAT",   # denoise
        "FLOAT",   # upscale
        "STRING",  # audio_full_path
        "STRING",  # video_full_path
        "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT",  # int_1 → int_8
        "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT",             # float_1 → float_5
        "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING",  # text_1 → text_8
        "FLOAT",   # model_sampling
        "STRING",  # scheduler
        "STRING",  # sampler
        "STRING", "STRING", "STRING", "STRING", "STRING",        # lora_high_noise_path_1 → 5
        "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT",             # lora_high_noise_strength_1 → 5
        "STRING", "STRING", "STRING", "STRING", "STRING",        # lora_low_noise_path_1 → 5
        "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT",             # lora_low_noise_strength_1 → 5
        "STRING", "STRING", "STRING", "STRING", "STRING",        # lora_trigger_words_1 → 5
        "INT",     # width
        "INT",     # height
        "INT",     # frames
        "FLOAT",   # fps
        "STRING", "STRING", "STRING", "STRING", "STRING",         # image_1_base64 → image_5_base64
        "STRING", "STRING", "STRING", "STRING", "STRING"          # video_1_base64 → video_5_base64
    )

    RETURN_NAMES = ("seed", "prompt_1", "prompt_2", "prompt_3", "prompt_4", "prompt_5", "neg_prompt", "denoise", "upscale", "audio_input_path", "video_input_path", "int_1", "int_2", "int_3", "int_4", "int_5", "int_6", "int_7", "int_8", "float_1", "float_2", "float_3", "float_4", "float_5", "text_1", "text_2", "text_3", "text_4", "text_5", "text_6", "text_7", "text_8", "model_sampling", "scheduler", "sampler", "lora_high_noise_path_1", "lora_high_noise_path_2", "lora_high_noise_path_3", "lora_high_noise_path_4", "lora_high_noise_path_5", "lora_high_noise_strength_1", "lora_high_noise_strength_2", "lora_high_noise_strength_3", "lora_high_noise_strength_4", "lora_high_noise_strength_5", "lora_low_noise_path_1", "lora_low_noise_path_2", "lora_low_noise_path_3", "lora_low_noise_path_4", "lora_low_noise_path_5", "lora_low_noise_strength_1", "lora_low_noise_strength_2", "lora_low_noise_strength_3", "lora_low_noise_strength_4", "lora_low_noise_strength_5", "lora_trigger_words_1", "lora_trigger_words_2", "lora_trigger_words_3", "lora_trigger_words_4", "lora_trigger_words_5", "width", "height", "frames", "fps", "image_1_base64", "image_2_base64", "image_3_base64", "image_4_base64", "image_5_base64", "video_1_base64", "video_2_base64", "video_3_base64", "video_4_base64", "video_5_base64")
    FUNCTION = "get_texts"
    CATEGORY = "Bjornulf"

    def get_texts(self, api_url_HERE, seed, prompt_1, prompt_2, prompt_3, prompt_4, prompt_5, neg_prompt, denoise, upscale, audio_input_path, video_input_path, int_1, int_2, int_3, int_4, int_5, int_6, int_7, int_8, float_1, float_2, float_3, float_4, float_5, text_1, text_2, text_3, text_4, text_5, text_6, text_7, text_8, model_sampling, scheduler, sampler, lora_high_noise_path_1, lora_high_noise_path_2, lora_high_noise_path_3, lora_high_noise_path_4, lora_high_noise_path_5, lora_high_noise_strength_1, lora_high_noise_strength_2, lora_high_noise_strength_3, lora_high_noise_strength_4, lora_high_noise_strength_5, lora_low_noise_path_1, lora_low_noise_path_2, lora_low_noise_path_3, lora_low_noise_path_4, lora_low_noise_path_5, lora_low_noise_strength_1, lora_low_noise_strength_2, lora_low_noise_strength_3, lora_low_noise_strength_4, lora_low_noise_strength_5, lora_trigger_words_1, lora_trigger_words_2, lora_trigger_words_3, lora_trigger_words_4, lora_trigger_words_5, width, height, frames, fps, image_1_base64, image_2_base64, image_3_base64, image_4_base64, image_5_base64, video_1_base64, video_2_base64, video_3_base64, video_4_base64, video_5_base64):
        # Replace literal \n with actual newlines in prompts
        prompt_1 = prompt_1.replace('\\n', '\n')
        prompt_2 = prompt_2.replace('\\n', '\n')
        prompt_3 = prompt_3.replace('\\n', '\n')
        prompt_4 = prompt_4.replace('\\n', '\n')
        prompt_5 = prompt_5.replace('\\n', '\n')
        neg_prompt = neg_prompt.replace('\\n', '\n')
        
        # List of files to delete at the start of every run
        files_to_delete = ["tmp_api.mp4", "tmp_api.mkv", "tmp_api.webm", "tmp_api.mp3", "tmp_api.wav", "tmp_api.txt"]
        
        # Get the output directory from ComfyUI
        output_dir = folder_paths.get_output_directory()
        
        # Delete each temporary file if it exists in the output directory
        for file in files_to_delete:
            file_path = os.path.join(output_dir, file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        rand = random.random()
        timeout_sec = 1  # Adjustable timeout in seconds
        
        # Handle audio download
        audio_full_path = ""
        if audio_input_path:
            _, ext = os.path.splitext(audio_input_path)
            ext = ext.lower()
            local_filename = f"tmp_api{ext}" if ext in ['.mp3', '.wav'] else "tmp_api.mp3"
            audio_url = f"{api_url_HERE}/api/view?filename={audio_input_path}&type=output&subfolder=&rand={rand}"
            audio_full_path = os.path.join(output_dir, local_filename)
            try:
                req = urllib.request.Request(
                    audio_url,
                    headers={"ngrok-skip-browser-warning": "true"}
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                    with open(audio_full_path, 'wb') as f:
                        shutil.copyfileobj(response, f)
                print(f"Audio downloaded as: {audio_full_path}")
            except Exception as e:
                print(f"Error downloading audio: {e}")
                audio_full_path = ""
        
        # Handle video download
        video_full_path = ""
        if video_input_path:
            _, ext = os.path.splitext(video_input_path)
            ext = ext.lower()
            local_filename = f"tmp_api{ext}" if ext in ['.mp4', '.mkv', '.webm'] else "tmp_api.mp4"
            video_url = f"{api_url_HERE}/api/view?filename={video_input_path}&type=output&subfolder=&rand={rand}"
            video_full_path = os.path.join(output_dir, local_filename)
            try:
                req = urllib.request.Request(
                    video_url,
                    headers={"ngrok-skip-browser-warning": "true"}
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                    with open(video_full_path, 'wb') as f:
                        shutil.copyfileobj(response, f)
                print(f"Video downloaded as: {video_full_path}")
            except Exception as e:
                print(f"Error downloading video: {e}")
                video_full_path = ""
        
        return (seed, prompt_1, prompt_2, prompt_3, prompt_4, prompt_5, neg_prompt, denoise, upscale, audio_full_path, video_full_path, int_1, int_2, int_3, int_4, int_5, int_6, int_7, int_8, float_1, float_2, float_3, float_4, float_5, text_1, text_2, text_3, text_4, text_5, text_6, text_7, text_8, model_sampling, scheduler, sampler, lora_high_noise_path_1, lora_high_noise_path_2, lora_high_noise_path_3, lora_high_noise_path_4, lora_high_noise_path_5, lora_high_noise_strength_1, lora_high_noise_strength_2, lora_high_noise_strength_3, lora_high_noise_strength_4, lora_high_noise_strength_5, lora_low_noise_path_1, lora_low_noise_path_2, lora_low_noise_path_3, lora_low_noise_path_4, lora_low_noise_path_5, lora_low_noise_strength_1, lora_low_noise_strength_2, lora_low_noise_strength_3, lora_low_noise_strength_4, lora_low_noise_strength_5, lora_trigger_words_1, lora_trigger_words_2, lora_trigger_words_3, lora_trigger_words_4, lora_trigger_words_5, width, height, frames, fps, image_1_base64, image_2_base64, image_3_base64, image_4_base64, image_5_base64, video_1_base64, video_2_base64, video_3_base64, video_4_base64, video_5_base64)
