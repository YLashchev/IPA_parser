
from .ipa_char import IPA_CHAR, CustomCharacter
from .debug import ValidationError
import re
import unicodedata


class IPAString:
    def __init__(self, string, geminate=True):
        self.string = string.strip()
        self.geminate = geminate
        processed_string = self.process_string()
        self.segments = self.segments = self._maximal_munch(processed_string)
        self._validate_string()

    @property
    def segment_type(self):
        types = []
        for segment in self.segments:
            if CustomCharacter.is_valid_char(segment):
                types.append(CustomCharacter.get_char(segment)['category'])
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
    def coda(self):
        last_syllable = self.syllables[-1]
        consonant_count = 0
        
        # Create a temporary IPAString object with just the last syllable
        temp_ipa = IPAString(last_syllable, geminate=self.geminate)
        # Apply char_only to clean the syllable
        temp_ipa.char_only()
        # Get the cleaned syllable
        cleaned_syllable = temp_ipa.string
        
        # Now process the cleaned syllable
        for char in reversed(cleaned_syllable):
            if IPA_CHAR.is_valid_char(char):
                phone_type = IPA_CHAR.category(char)
            elif CustomCharacter.is_valid_char(char):
                phone_type = CustomCharacter.get_char(char)['category']
            else:
                print(f"Undefined segment: {char}")
                break
    
            if phone_type == 'CONSONANT':
                consonant_count += 1
            elif phone_type == 'PAUSE':
                return 'OP' if consonant_count == 0 and char == 'O' else 'SP'
            else:
                break
                
        return consonant_count


    #def remove_diacritics(self):
        

    def stress(self):
        syllable = self.string
        stress = "ˈ"  # IPA symbol for primary stress
        secondary_stress = "ˌ"  # IPA symbol for secondary stress
        if stress in syllable:
            return "STRESSED"
        elif secondary_stress in syllable:
            return "STRESSED_2"
        else:
            return "UNSTRESSED"

    def process_string(self):
        processed_string = self.string

        if self.geminate:
            def replace_geminate_if_consonant(match):
                char = match.group(1)
                if IPA_CHAR.category(char) == "CONSONANT":
                    return char
                return match.group(0)
            processed_string = re.sub(r'(.)\1+', replace_geminate_if_consonant, processed_string)

        return processed_string

    def total_length(self):
        processed_str = self.process_string()
        self.segments = self._maximal_munch(processed_str)

        total = 0
        for segment in self.segments:
            if CustomCharacter.is_valid_char(segment):
                total += CustomCharacter.get_char(segment)['rank']
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
            for custom_ipa in CustomCharacter._custom_chars:
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
        invalid_segments = []
        for segment in self.segments:
            if not CustomCharacter.is_valid_char(segment) and not IPA_CHAR.is_valid_char(segment):
                invalid_segments.append(segment)
        if invalid_segments:
            raise ValidationError("INVALID_SEGMENT", segment=", ".join(invalid_segments), string=self.string)

        
    def char_only(self):
        categories_to_remove = {'DIACRITIC', 'SUPRASEGMENTAL', 'TONE-ACCENT'}
        
        def is_valid_and_retainable(segment):
            if IPA_CHAR.is_valid_char(segment):
                return IPA_CHAR.category(segment) not in categories_to_remove
            elif CustomCharacter.is_valid_char(segment):
                return True
            raise ValidationError("INVALID_SEGMENT", segment=segment, string=self.string)
            
        cleaned_string = ''.join(segment for segment in self.segments if is_valid_and_retainable(segment))
        
        self.string = cleaned_string
        self.segments = self._maximal_munch(cleaned_string)

        return cleaned_string  # returning the cleaned string



