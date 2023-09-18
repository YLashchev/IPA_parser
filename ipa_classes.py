import json
import re
import os
from collections import Counter


class ValidationError(Exception):
    pass


class IPA_CHAR:
    """
    Class to interact with a JSON dictionary containing IPA characters and their hex codes & characters.
    """
    _data = None

    ranking_dictionary = {
        'AFFRICATE': 1, 'DIPHTONG': 1, 'CONSONANT': 1,
        'VOWEL': 1, 'DIACRITIC': 0, 'SUPRASEGMENTAL': 0, 'TONE-ACCENT': 0
    }

    import os

# ... rest of your code ...

    @classmethod
    def load_data(cls, relative_path='data/IPA_Table.json'):
        if cls._data is None:
            # Get the current directory of this script/file
            base_dir = os.path.dirname(os.path.abspath(__file__))

            # Create the full path by joining base directory and the relative path
            file_path = os.path.join(base_dir, relative_path)

            try:
                with open(file_path, 'r') as f:
                    cls._data = json.load(f)
            except FileNotFoundError:
                raise ValidationError(f"Error: File {file_path} not found.")
            except json.JSONDecodeError:
                raise ValidationError(f"Error: File {file_path} is not a valid JSON.")


    @classmethod
    def _char_data(cls, char):
        char = char.strip()
        if not char:
            raise ValidationError("Error: Input character is empty or whitespace only.")

        char_code = format(ord(char), '04x')
        for category, symbols in cls._data.items():
            for name, value in symbols.items():
                if value["code"] == char_code:
                    return category, name, value["code"]
        raise ValidationError(f"Error: Symbol '{char}' does not exist in the dictionary.")

    @classmethod
    def rank(cls, char):
        category, _, _ = cls._char_data(char)
        return cls.ranking_dictionary.get(category)

    @classmethod
    def name(cls, char):
        _, name, _ = cls._char_data(char)
        return name

    @classmethod
    def category(cls, char):
        category, _, _ = cls._char_data(char)
        return category

    @classmethod
    def code(cls, char):
        _, _, code = cls._char_data(char)
        return code

    @classmethod
    def is_valid_char(cls, char):
        try:
            cls._char_data(char)
            return True
        except ValidationError:
            return False
    
    



class IPAString:
    
    
    
    CUSTOM_IPA = {}

    def __init__(self, string):
        self.string = string.strip()
        self.segments = self._maximal_munch(self.string)
        self._validate_string()


    @classmethod
    def add_custom_char(cls, char_sequence, category, rank=1):
        cls.CUSTOM_IPA[char_sequence] = {'category': category, 'rank': rank}

    @classmethod
    def remove_custom_char(cls, char_sequence):
        """
        Remove a custom IPA character from the dictionary.
        """
        if char_sequence in cls.CUSTOM_IPA:
            del cls.CUSTOM_IPA[char_sequence]
        else:
            print(f"Character sequence '{char_sequence}' not found in custom characters.")

    @classmethod
    def clear_all_custom_chars(cls):
        """
        Clear all custom IPA characters from the dictionary.
        """
        cls.CUSTOM_IPA.clear()


    @property
    def segment_type(self):
        types = []
        for segment in self.segments:
            if segment in self.CUSTOM_IPA:
                types.append(self.CUSTOM_IPA[segment]['category'])
            else:
                types.append(IPA_CHAR.category(segment))
        return types

    @property
    def segment_count(self):
        categories = self.segment_type
        return {'V': categories.count('VOWEL'), 'C': categories.count('CONSONANT')}

    @property
    def unicode_string(self):
        return ''.join(['\\u{:04x}'.format(ord(char)) for segment in self.segments for char in segment])

    @property
    def syllables(self):
        syllable_break = "."  # IPA symbol for syllable break
        return self.string.split(syllable_break)

    @property
    def stress(self):
        return [("STRESSED" if self.is_stressed(syllable) else "UNSTRESSED") for syllable in self.syllables]
    
    
    @property
    def coda(self):
        ultimate = self.syllables[-1][-1]  # Get the last character of the last syllable.
        
        if IPA_CHAR.is_valid_char(ultimate):
            phone_type = IPA_CHAR.category(ultimate)
            # If not in IPA_CHAR, check if it's in CUSTOM_IPA.
        elif ultimate in self.CUSTOM_IPA:
            phone_type = self.CUSTOM_IPA[ultimate]['category']
        # If not in both, it's an undefined segment and you should handle this case.
        else:
            print(f"Undefined segment: {ultimate}")
            return None
        
        if phone_type == 'CONSONANT':
            return 1
        return 0



    def is_stressed(self, syllable):
        stress = "ˈ"  # IPA symbol for primary stress
        secondary_stress = "ˌ"  # IPA symbol for secondary stress
        return stress in syllable or secondary_stress in syllable

    def process_string(self, geminate=True):
        processed_string = self.string
 
        if geminate:   
            def replace_geminate_if_consonant(match):
                char = match.group(1)
                if IPA_CHAR.category(char) == "CONSONANT":
                    return char
                return match.group(0)
            processed_string = re.sub(r'(.)\1+', replace_geminate_if_consonant, processed_string)

        return processed_string
    

    def total_length(self, geminate=True):
        processed_str = self.process_string(geminate=geminate)
        self.segments = self._maximal_munch(processed_str)
        
        total = 0
        for segment in self.segments:
            if segment in self.CUSTOM_IPA:
                total += self.CUSTOM_IPA[segment]['rank']
            else:
                rank = IPA_CHAR.rank(segment)
                if rank is not None:
                    total += rank
        return total
    
    

    def _maximal_munch(self, string):
        """Break down the string into segments using a maximal munch approach."""
        segments = []
        i = 0
        while i < len(string):
            max_match = ""
            for custom_ipa in self.CUSTOM_IPA:
                if string.startswith(custom_ipa, i):
                    if len(custom_ipa) > len(max_match):
                        max_match = custom_ipa

            if max_match:
                segments.append(max_match)
                i += len(max_match)
            else:
                segments.append(string[i])
                i += 1
        return segments

    def _validate_string(self):
        for segment in self.segments:
            if segment not in self.CUSTOM_IPA and not IPA_CHAR.is_valid_char(segment):
                raise ValidationError(f"Invalid segment '{segment}' in '{self.string}'.")


        
    

