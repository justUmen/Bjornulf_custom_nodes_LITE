import re

class TextReplace:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_text": ("STRING", {"multiline": True, "forceInput": True}),
                "search_text": ("STRING", {"multiline": True}),
                "replace_text": ("STRING", {"multiline": True, "default": ""}),
                "replace_count": ("INT", {"default": 0, "min": 0, "max": 1000, 
                                          "display": "number", 
                                          "tooltip": "Number of replacements (0 = replace all)"}),
                "use_regex": ("BOOLEAN", {"default": False}),
                "case_sensitive": ("BOOLEAN", {"default": True, 
                                             "tooltip": "Whether the search should be case-sensitive"}),
                "trim_whitespace": (["none", "left", "right", "both"], {
                    "default": "none", 
                    "tooltip": "Remove whitespace around the found text"
                }),
                "multiline_regex": ("BOOLEAN", {"default": False, 
                                              "tooltip": "Make dot (.) match newlines in regex"})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "replace_text"
    CATEGORY = "Bjornulf"
    
    def replace_text(self, input_text, search_text, replace_text, replace_count, 
                    use_regex, multiline_regex, case_sensitive, trim_whitespace):
        try:
            # Convert input to string
            input_text = str(input_text)
            
            # Early exit if search_text is empty to prevent hanging
            if not search_text:
                return (input_text,)
            
            # Prepare regex flags
            regex_flags = 0
            if not case_sensitive:
                regex_flags |= re.IGNORECASE
            if multiline_regex and use_regex:
                regex_flags |= re.DOTALL
            
            if use_regex:
                try:
                    # Compile the regex pattern first
                    pattern = re.compile(search_text, flags=regex_flags)
                    
                    # Perform replacement
                    if replace_count == 0:
                        # Replace all instances
                        result = pattern.sub(replace_text, input_text)
                    else:
                        # Replace specific number of instances
                        result = pattern.sub(replace_text, input_text, count=replace_count)
                    
                    return (result,)
                
                except re.error as regex_compile_error:
                    return (input_text,)
            
            else:
                # Standard string replacement
                if not case_sensitive:
                    # Case-insensitive string replacement
                    result = input_text
                    count = 0
                    while search_text.lower() in result.lower() and (replace_count == 0 or count < replace_count):
                        # Find the index of the match
                        idx = result.lower().index(search_text.lower())
                        
                        # Determine left and right parts
                        left_part = result[:idx]
                        right_part = result[idx + len(search_text):]
                        
                        # Trim whitespace based on option
                        if trim_whitespace == "left":
                            left_part = left_part.rstrip()
                        elif trim_whitespace == "right":
                            right_part = right_part.lstrip()
                        elif trim_whitespace == "both":
                            left_part = left_part.rstrip()
                            right_part = right_part.lstrip()
                        
                        # Reconstruct the string
                        result = left_part + replace_text + right_part
                        count += 1
                else:
                    # Case-sensitive replacement
                    result = input_text
                    count = 0
                    while search_text in result and (replace_count == 0 or count < replace_count):
                        # Find the index of the match
                        idx = result.index(search_text)
                        
                        # Determine left and right parts
                        left_part = result[:idx]
                        right_part = result[idx + len(search_text):]
                        
                        # Trim whitespace based on option
                        if trim_whitespace == "left":
                            left_part = left_part.rstrip()
                        elif trim_whitespace == "right":
                            right_part = right_part.lstrip()
                        elif trim_whitespace == "both":
                            left_part = left_part.rstrip()
                            right_part = right_part.lstrip()
                        
                        # Reconstruct the string
                        result = left_part + replace_text + right_part
                        count += 1
            
            return (result,)
            
        except Exception as e:
            return (input_text,)

    @classmethod
    def IS_CHANGED(cls, search_text, replace_text, input_text, replace_count, use_regex, case_sensitive, trim_whitespace, multiline_regex, *args):
        return float("NaN")
    
class TextGrep:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_text": ("STRING", {"multiline": True, "forceInput": True}),
                "search_pattern": ("STRING", {"multiline": True, 
                                            "tooltip": "Text or regex pattern to search for"}),
                "filter_mode": (["keep_matching", "remove_matching"], {
                    "default": "keep_matching", 
                    "tooltip": "Keep lines that match or remove lines that match"
                }),
                "use_regex": ("BOOLEAN", {"default": False}),
                "case_sensitive": ("BOOLEAN", {"default": True, 
                                             "tooltip": "Whether the search should be case-sensitive"}),
                "match_whole_line": ("BOOLEAN", {"default": False, 
                                               "tooltip": "Pattern must match the entire line"}),
                "invert_match": ("BOOLEAN", {"default": False, 
                                           "tooltip": "Invert the matching logic (like grep -v)"}),
                "trim_lines": ("BOOLEAN", {"default": False, 
                                         "tooltip": "Remove leading/trailing whitespace from lines"}),
                "remove_empty_lines": ("BOOLEAN", {"default": False, 
                                                 "tooltip": "Remove empty lines from output"}),
                "max_matches": ("INT", {"default": 0, "min": 0, "max": 10000, 
                                      "display": "number", 
                                      "tooltip": "Maximum number of matching lines to return (0 = no limit)"})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "filter_lines"
    CATEGORY = "Bjornulf"
    
    def filter_lines(self, input_text, search_pattern, filter_mode, use_regex, 
                    case_sensitive, match_whole_line, invert_match, trim_lines, 
                    remove_empty_lines, max_matches):
        try:
            # Convert input to string
            input_text = str(input_text)
            
            # Early exit if search_pattern is empty
            if not search_pattern:
                return (input_text,)
            
            # Split input into lines
            lines = input_text.splitlines()
            
            # Prepare regex flags
            regex_flags = 0
            if not case_sensitive:
                regex_flags |= re.IGNORECASE
            
            # Compile regex pattern if needed
            if use_regex:
                try:
                    if match_whole_line:
                        # Anchor pattern to match whole line
                        pattern_str = f"^{search_pattern}$"
                    else:
                        pattern_str = search_pattern
                    
                    pattern = re.compile(pattern_str, flags=regex_flags)
                except re.error as regex_compile_error:
                    # If regex compilation fails, return original text
                    return (input_text,)
            
            # Filter lines
            filtered_lines = []
            match_count = 0
            
            for line in lines:
                # Trim line if requested
                processed_line = line.strip() if trim_lines else line
                
                # Skip empty lines if requested
                if remove_empty_lines and not processed_line.strip():
                    continue
                
                # Check if line matches pattern
                if use_regex:
                    matches = bool(pattern.search(processed_line))
                else:
                    # String matching
                    if case_sensitive:
                        matches = search_pattern in processed_line
                    else:
                        matches = search_pattern.lower() in processed_line.lower()
                    
                    # Whole line matching for string search
                    if match_whole_line:
                        if case_sensitive:
                            matches = processed_line == search_pattern
                        else:
                            matches = processed_line.lower() == search_pattern.lower()
                
                # Apply invert logic
                if invert_match:
                    matches = not matches
                
                # Apply filter mode logic
                should_include = False
                if filter_mode == "keep_matching":
                    should_include = matches
                elif filter_mode == "remove_matching":
                    should_include = not matches
                
                # Add line if it should be included
                if should_include:
                    filtered_lines.append(processed_line)
                    match_count += 1
                    
                    # Check max matches limit
                    if max_matches > 0 and match_count >= max_matches:
                        break
                elif filter_mode == "remove_matching" and not matches:
                    # For remove_matching mode, we need to include non-matching lines
                    filtered_lines.append(processed_line)
            
            # Join lines back together
            result = "\n".join(filtered_lines)
            
            return (result,)
            
        except Exception as e:
            return (input_text,)

    @classmethod
    def IS_CHANGED(cls, search_pattern, input_text, filter_mode, use_regex, 
                   case_sensitive, match_whole_line, invert_match, trim_lines, 
                   remove_empty_lines, max_matches, *args):
        return float("NaN")