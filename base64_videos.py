import os
import base64
import uuid

class VideoToBase64:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("base64_video",)
    FUNCTION = "encode_video"
    CATEGORY = "Bjornulf"

    def encode_video(self, video_path):
        with open(video_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return (encoded,)


class Base64ToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "b64_data": ("STRING", {"multiline": True}),
                "output_dir": ("STRING", {"default": "/tmp"}),
            }
        }

    RETURN_TYPES = ("STRING",)  # returns video_path
    RETURN_NAMES = ("video_path",)
    FUNCTION = "decode_video"
    CATEGORY = "Bjornulf"

    def decode_video(self, b64_data, output_dir="/tmp"):
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"restored_{uuid.uuid4().hex}.mp4")
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        return (out_path,)