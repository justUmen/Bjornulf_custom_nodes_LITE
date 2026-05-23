import json


class JsonParser:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "json_string": ("STRING", {
                    "multiline": True,
                    "forceInput": True
                }),
                "path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "e.g. metadata.setting or items.0.name"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    FUNCTION = "parse_json"
    CATEGORY = "Bjornulf"

    def parse_json(self, json_string, path):
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return (f"ERROR: Invalid JSON - {e}",)

        if not path.strip():
            # No path given, return the whole JSON pretty-printed
            return (json.dumps(data, indent=2, ensure_ascii=False),)

        # Walk the dot-separated path
        keys = path.strip().split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    return (f"ERROR: Key '{key}' not found. Available keys: {list(current.keys())}",)
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return (f"ERROR: Invalid list index '{key}' (list length: {len(current)})",)
            else:
                return (f"ERROR: Cannot traverse into {type(current).__name__} with key '{key}'",)

        # Convert the result to string
        if isinstance(current, (dict, list)):
            return (json.dumps(current, indent=2, ensure_ascii=False),)
        else:
            return (str(current),)
