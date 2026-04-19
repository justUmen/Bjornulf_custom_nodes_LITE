class WriteText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "lines": 10}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "write_text"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def write_text(self, text):
        return (text,)

class WriteTextAppend:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "lines": 10}),
            },
            "optional": {
                "text_input": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "append_text"
    OUTPUT_NODE = True
    CATEGORY = "Bjornulf"
    
    def append_text(self, text, text_input=None):
        if text_input is not None:
             # Ensure both are strings before concatenation
            text_input_str = str(text_input) if text_input is not None else ""
            text_str = str(text) if text is not None else ""
            
            # If text_input is empty, just return text
            if not text_input_str:
                return (text_str,)
                
            return (text_input_str + "\n" + text_str,)
        return (text,)