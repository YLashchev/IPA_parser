
from .ipa_char import IPA_CHAR, CustomCharacter
from .debug import ValidationError
import re


class IPAString:
    def __init__(self, string):
        self.string = string.strip()
        self.segments = self._maximal_munch(self.string)
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
    def stress(self):
        return [("STRESSED" if self.is_stressed(syllable) else "UNSTRESSED") for syllable in self.syllables]

    @property
    def coda(self):
        ultimate = self.syllables[-1][-1]  # Get the last character of the last syllable.

        if IPA_CHAR.is_valid_char(ultimate):
            phone_type = IPA_CHAR.category(ultimate)
        elif CustomCharacter.is_valid_char(ultimate):
            phone_type = CustomCharacter.get_char(ultimate)['category']
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

        
        