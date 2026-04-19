import random

class VideoTextGenerator:
    """
    A class to generate cinematic text prompts for Hunyuan video generation.
    Combines scene descriptions, character actions, camera movements, and styles into a fluid, detailed prompt.
    """

    # Predefined lists for actions, camera movements, and shot types
    SHARED_ACTIONS = [
        "walking", "running", "dancing", "jumping", "sitting", "standing",
        "talking", "laughing", "singing", "fighting", "climbing", "swimming",
        "eating", "drinking", "writing", "reading", "painting", "cooking",
        "driving", "shouting", "whispering", "pointing", "waving", "sleeping"
    ]

    INTERACTIVE_ACTIONS = [
        "giving to", "slapping", "hugging", "kissing", "shaking hands with",
        "arguing with", "dancing with", "fighting with", "playing with",
        "talking to", "listening to"
    ]

    CAMERA_MOVEMENTS = [
        "pan left", "pan right", "zoom in", "zoom out",
        "tilt up", "tilt down", "track forward", "track backward",
        "circle around", "dolly in", "dolly out", "swivel", "sweep across"
    ]

    SHOT_TYPES = [
        "close-up", "wide shot", "medium shot", "over-the-shoulder shot",
        "aerial shot", "low-angle shot", "high-angle shot", "profile shot"
    ]

    ADVERBS = [
        "smoothly", "slowly", "quickly", "steadily", "dramatically", "gently"
    ]

    PLURAL_FORMS = {
        "woman": "women",
        "man": "men",
        "girl": "girls",
        "boy": "boys"
    }

    NUMBER_WORDS = {
        2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "action_general": (["NONE", "RANDOM", "CUSTOM"] + cls.SHARED_ACTIONS, {"default": "NONE"}),
                "custom_action_general": ("STRING", {"default": "", "multiline": False}),
                "action_2_characters": (["NONE", "RANDOM", "CUSTOM"] + cls.INTERACTIVE_ACTIONS, {"default": "NONE"}),
                "custom_action_2_characters": ("STRING", {"default": "", "multiline": False}),
                "camera_movement": (["NONE", "RANDOM"] + cls.CAMERA_MOVEMENTS, {"default": "NONE"}),
                "shot_type": (["NONE", "RANDOM"] + cls.SHOT_TYPES, {"default": "NONE"}),
                "CUSTOM_PROMPT": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "GEN_CHARACTER": ("GEN_CHARACTER",),
                "GEN_SCENE": ("GEN_SCENE",),
                "GEN_STYLE": ("GEN_STYLE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"
    CATEGORY = "Bjornulf/Video"

    def select_value(self, options, current_value, rng, custom_value=None):
        """
        Selects a value from options, handling RANDOM and CUSTOM cases.
        Returns None for "NONE" to omit it from the prompt.
        """
        if current_value == "RANDOM":
            valid_options = [opt for opt in options if opt not in ["NONE", "RANDOM", "CUSTOM"]]
            return rng.choice(valid_options) if valid_options else None
        elif current_value == "CUSTOM" and custom_value and custom_value.strip():
            return custom_value.strip()
        elif current_value == "NONE":
            return None
        return current_value

    def parse_characters(self, gen_character):
        """
        Parses GEN_CHARACTER input into a list of dictionaries with position, gender, and details.
        """
        characters = []
        if not gen_character:
            return characters
        for line in gen_character.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                line = line[2:].strip()
                position = None
                if ': ' in line:
                    position, desc = line.split(': ', 1)
                    position = position.lower().replace("of the image", "").strip()
                else:
                    desc = line
                if ', ' in desc:
                    gender_part, details = desc.split(', ', 1)
                    gender = gender_part.strip()
                    if gender.startswith("one "):
                        gender = gender[4:].strip()  # Remove "one "
                    details = details.strip()
                else:
                    gender = desc.strip()
                    details = ""
                characters.append({'position': position, 'gender': gender, 'details': details})
        return characters

    def format_details(self, details):
        """
        Formats multiple details into a natural phrase, e.g., "with a toned build and red dress".
        """
        if not details:
            return ""
        detail_list = details.split(', ')
        if len(detail_list) > 1:
            return ', '.join(detail_list[:-1]) + ' and ' + detail_list[-1]
        return detail_list[0]

    def describe_characters(self, characters, action=None, action_type="shared"):
        """
        Creates a detailed description of characters, adjusting for shared or interactive actions.
        Enhanced to provide a collective introduction followed by individual descriptions when
        multiple characters with positions perform a shared action.
        """
        if not characters:
            return "someone" + (f" {action}" if action else "")

        if len(characters) == 1:
            char = characters[0]
            gender = char['gender']
            details = self.format_details(char['details'])
            position = char['position']
            base_desc = f"a {gender}"
            if details:
                base_desc += f" {details}"
                # base_desc += f" with {details}"
            if position:
                base_desc += f" {position}"
            if action:
                base_desc += f" {action}"
            return base_desc

        if len(characters) > 1 and action and action_type == "shared" and all(char['position'] for char in characters):
            # Collective introduction
            genders = set(char['gender'] for char in characters)
            if len(genders) == 1:
                gender = list(genders)[0]
                num_str = self.NUMBER_WORDS.get(len(characters), str(len(characters)))
                plural_gender = self.PLURAL_FORMS.get(gender, gender + "s")
                collective = f"{num_str} {plural_gender} {action}"
            else:
                collective = f"multiple characters {action}"

            # Individual descriptions
            individual_descs = []
            for char in characters:
                desc = f"{char['position']} is a {char['gender']}"
                # desc = f"On the {char['position']} is a {char['gender']}"
                if char['details']:
                    desc += f" {self.format_details(char['details'])}."
                individual_descs.append(desc)

            return f"{collective}. {' '.join(individual_descs)}"

        if action_type == "interactive" and len(characters) == 2:
            subject, obj = characters
            subject_desc = f"a {subject['gender']}"
            if subject['details']:
                subject_desc += f" {self.format_details(subject['details'])}"
            if subject['position']:
                subject_desc += f" {subject['position']}"
            obj_desc = f"a {obj['gender']}"
            if obj['details']:
                obj_desc += f" {self.format_details(obj['details'])}"
            if obj['position']:
                obj_desc += f" {obj['position']}"
            return f"{subject_desc} {action} {obj_desc}."

        # Fallback for other cases
        char_descs = []
        for char in characters:
            gender = char['gender']
            details = self.format_details(char['details'])
            position = char['position']
            desc = f"a {gender}"
            if details:
                desc += f" {details}"
            if position:
                desc += f" {position}"
            char_descs.append(desc)
        character_part = " and ".join(char_descs)
        if action and action_type == "shared":
            character_part += f", both {action}"
        return character_part

    def generate(self, seed, action_general, custom_action_general, action_2_characters, custom_action_2_characters,
                 camera_movement, shot_type, CUSTOM_PROMPT, GEN_CHARACTER=None, GEN_SCENE=None, GEN_STYLE=None):
        """
        Generates a complete cinematic prompt based on all inputs.
        """
        rng = random.Random(seed)

        # Select values for shot type, camera movement, and actions
        selected_shot = self.select_value(self.SHOT_TYPES + ["NONE", "RANDOM"], shot_type, rng)
        selected_camera = self.select_value(self.CAMERA_MOVEMENTS + ["NONE", "RANDOM"], camera_movement, rng)
        selected_general_action = self.select_value(self.SHARED_ACTIONS + ["NONE", "RANDOM", "CUSTOM"], action_general, rng, custom_action_general)
        selected_2_char_action = self.select_value(self.INTERACTIVE_ACTIONS + ["NONE", "RANDOM", "CUSTOM"], action_2_characters, rng, custom_action_2_characters)

        # Parse characters
        characters = self.parse_characters(GEN_CHARACTER)
        num_chars = len(characters)

        # Determine action and type
        action = None
        action_type = "shared"
        if num_chars == 2 and selected_2_char_action:
            action = selected_2_char_action
            action_type = "interactive"
        elif selected_general_action:
            action = selected_general_action
            action_type = "shared"

        # Describe characters with action
        character_part = self.describe_characters(characters, action, action_type)

        # Construct the main sentence
        if selected_shot:
            main_sentence = f"A {selected_shot} captures {character_part}"
        else:
            main_sentence = f"The scene shows {character_part}"

        # Add camera movement
        if selected_camera:
            parts = selected_camera.split(' ', 1)
            verb = parts[0]
            direction = parts[1] if len(parts) > 1 else ""
            conjugated_verb = verb + ('s' if not verb.endswith('y') else 'ies' if verb[-2] not in 'aeiou' else 's')
            camera_action = f"{conjugated_verb} {direction}".strip()
            adverb = rng.choice(self.ADVERBS)
            main_sentence += f" as the camera {adverb} {camera_action}"

        # Assemble the final prompt
        prompt_parts = []
        if CUSTOM_PROMPT and CUSTOM_PROMPT.strip():
            prompt_parts.append(CUSTOM_PROMPT.strip())
        prompt_parts.append(main_sentence) #"The scene shows {character_part}"
        if GEN_SCENE and GEN_SCENE.strip():
            prompt_parts.append(GEN_SCENE.strip())
        if GEN_STYLE and GEN_STYLE.strip():
            prompt_parts.append(GEN_STYLE.strip())

        final_prompt = ". ".join(prompt_parts)
        if final_prompt and not final_prompt.endswith('.'):
            final_prompt += '.'

        return (final_prompt or "A basic video scene.",)