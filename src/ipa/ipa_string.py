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
                custom_char = CustomCharacter.get_char(segment)
                if custom_char is not None:
                    types.append(custom_char["category"])
            else:
                types.append(IPA_CHAR.category(segment))
        return types

    @property
    def segment_count(self):
        categories = self.segment_type
        # Normalize AFFRICATE to CONSONANT and DIPHTHONG to VOWEL for counting
        normalized = [
            cat
            if cat not in ("AFFRICATE", "DIPHTHONG")
            else ("CONSONANT" if cat == "AFFRICATE" else "VOWEL")
            for cat in categories
        ]
        return {"V": normalized.count("VOWEL"), "C": normalized.count("CONSONANT")}

    @property
    def unicode_string(self):
        return "".join(
            ["\\u{:04x}".format(ord(char)) for segment in self.segments for char in segment]
        )

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
        # Get the cleaned segments instead of string
        cleaned_segments = temp_ipa.segments

        # Now process the cleaned segments in reverse
        for segment in reversed(cleaned_segments):
            if IPA_CHAR.is_valid_char(segment):
                phone_type = IPA_CHAR.category(segment)
            elif CustomCharacter.is_valid_char(segment):
                custom_char = CustomCharacter.get_char(segment)
                if custom_char is None:
                    break
                phone_type = custom_char["category"]
            else:
                print(f"Undefined segment: {segment}")
                break

            if phone_type == "CONSONANT" or phone_type == "AFFRICATE":
                consonant_count += 1
            elif phone_type == "PAUSE":
                return "OP" if consonant_count == 0 and segment == "OP" else "SP"
            else:
                break

        return consonant_count

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

            processed_string = re.sub(r"(.)\1+", replace_geminate_if_consonant, processed_string)

        return processed_string

    def total_length(self):
        processed_str = self.process_string()
        self.segments = self._maximal_munch(processed_str)

        total = 0
        for segment in self.segments:
            if CustomCharacter.is_valid_char(segment):
                custom_char = CustomCharacter.get_char(segment)
                if custom_char is not None:
                    rank = custom_char["rank"]
                    try:
                        total += float(rank)
                    except (TypeError, ValueError):
                        pass
            else:
                rank = IPA_CHAR.rank(segment)
                if rank is not None:
                    total += rank
        if isinstance(total, float) and total.is_integer():
            return int(total)
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
                end = self._consume_grapheme_cluster(string, i)
                segments.append(string[i:end])
                i = end
        return segments

    def _consume_grapheme_cluster(self, string: str, start: int) -> int:
        if start >= len(string):
            return start

        i = start + 1

        if i < len(string) and string[i] in {"\u0361", "\u035c"}:
            i += 1
            if i < len(string):
                i += 1

        while i < len(string):
            if unicodedata.category(string[i]) in {"Mn", "Mc", "Me"}:
                i += 1
            else:
                break

        return i

    def _validate_string(self):
        for segment in self.segments:
            if self._has_tiebar(segment):
                if not CustomCharacter.is_valid_char(segment) and not IPA_CHAR.is_valid_char(
                    segment
                ):
                    raise ValidationError("UNREGISTERED_TIE_BAR", segment=segment)

        invalid_segments = []
        for segment in self.segments:
            if not self._is_valid_segment(segment):
                invalid_segments.append(segment)
        if invalid_segments:
            raise ValidationError(
                "INVALID_SEGMENT", segment=", ".join(invalid_segments), string=self.string
            )

    def _is_valid_segment(self, segment):
        if CustomCharacter.is_valid_char(segment) or IPA_CHAR.is_valid_char(segment):
            return True

        if not segment:
            return False

        i = 0
        if len(segment) > 2 and segment[1] in {"\u0361", "\u035c"}:
            if not IPA_CHAR.is_valid_char(segment[0]) or not IPA_CHAR.is_valid_char(segment[2]):
                return False
            i = 3
        else:
            if not IPA_CHAR.is_valid_char(segment[0]):
                return False
            i = 1

        while i < len(segment):
            if unicodedata.category(segment[i]) not in {"Mn", "Mc", "Me"}:
                return False
            i += 1

        return True

    @staticmethod
    def _has_tiebar(segment: str) -> bool:
        return len(segment) > 2 and segment[1] in {"\u0361", "\u035c"}

    def char_only(self):
        categories_to_remove = {"DIACRITIC", "SUPRASEGMENTAL", "TONE", "ACCENT_MARK"}

        def is_valid_and_retainable(segment):
            if IPA_CHAR.is_valid_char(segment):
                return IPA_CHAR.category(segment) not in categories_to_remove
            elif CustomCharacter.is_valid_char(segment):
                return True
            raise ValidationError("INVALID_SEGMENT", segment=segment, string=self.string)

        cleaned_string = "".join(
            segment for segment in self.segments if is_valid_and_retainable(segment)
        )

        self.string = cleaned_string
        self.segments = self._maximal_munch(cleaned_string)

        return cleaned_string  # returning the cleaned string
