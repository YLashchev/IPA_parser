import re
import unicodedata

from .debug import ValidationError
from .ipa_char import IPA_CHAR, CustomCharacter


class IPAString:
    def __init__(self, string, geminate=True):
        self.string = string.strip()
        self.geminate = geminate
        processed_string = self.process_string()
        self.segments = self._maximal_munch(processed_string)
        self._validate_string()

    @property
    def segment_type(self):
        types = []
        for segment in self.segments:
            cat = self._segment_category(segment)
            if cat is not None:
                types.append(cat)
        return types

    @property
    def segment_count(self):
        categories = self.segment_type
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
        return self.string.split(".")

    @property
    def coda(self):
        last_syllable = self.syllables[-1]
        consonant_count = 0

        temp_ipa = IPAString(last_syllable, geminate=self.geminate)
        temp_ipa.char_only()
        cleaned_segments = temp_ipa.segments

        for segment in reversed(cleaned_segments):
            phone_type = self._segment_category(segment)
            if phone_type is None:
                break

            if phone_type in {"CONSONANT", "AFFRICATE"}:
                consonant_count += 1
            elif phone_type == "PAUSE":
                return "OP" if consonant_count == 0 and segment == "OP" else "SP"
            else:
                break

        return consonant_count

    def stress(self):
        if "ˈ" in self.string:
            return "STRESSED"
        if "ˌ" in self.string:
            return "STRESSED_2"
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
            p_weight = self._segment_weight(segment)
            if p_weight is not None:
                try:
                    total += float(p_weight)
                except (TypeError, ValueError):
                    pass
        if isinstance(total, float) and total.is_integer():
            return int(total)
        return total

    def _maximal_munch(self, string):
        # NFD-normalize so pre-composed characters (á → a+combining acute)
        # match custom sequences stored in decomposed form.
        string = unicodedata.normalize("NFD", string)
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
            if self._has_tiebar(segment) and not self._is_known_segment(segment):
                raise ValidationError("UNREGISTERED_TIE_BAR", segment=segment)

        invalid_segments = [
            segment for segment in self.segments if not self._is_valid_segment(segment)
        ]
        if invalid_segments:
            raise ValidationError(
                "INVALID_SEGMENT", segment=", ".join(invalid_segments), string=self.string
            )

    def _is_known_segment(self, segment):
        return CustomCharacter.is_valid_char(segment) or IPA_CHAR.is_valid_char(segment)

    @staticmethod
    def _base_char(segment):
        """Return the base character of a segment, stripping combining marks.

        Decomposes pre-composed characters (NFD) before stripping.
        """
        decomposed = unicodedata.normalize("NFD", segment)
        base = []
        for ch in decomposed:
            if unicodedata.category(ch) not in {"Mn", "Mc", "Me"}:
                base.append(ch)
        return "".join(base)

    @staticmethod
    def _segment_category(segment):
        """Return category for any valid segment (custom, exact, or base+diacritic)."""
        if CustomCharacter.is_valid_char(segment):
            custom = CustomCharacter.get_char(segment)
            return custom["category"] if custom else None
        if IPA_CHAR.is_valid_char(segment):
            return IPA_CHAR.category(segment)
        base = IPAString._base_char(segment)
        if base and IPA_CHAR.is_valid_char(base):
            return IPA_CHAR.category(base)
        return None

    @staticmethod
    def _segment_weight(segment):
        """Return phonological weight for any valid segment."""
        if CustomCharacter.is_valid_char(segment):
            custom = CustomCharacter.get_char(segment)
            return custom["p_weight"] if custom else None
        if IPA_CHAR.is_valid_char(segment):
            return IPA_CHAR.p_weight(segment)
        base = IPAString._base_char(segment)
        if base and IPA_CHAR.is_valid_char(base):
            return IPA_CHAR.p_weight(base)
        return None

    def _is_valid_segment(self, segment):
        if self._is_known_segment(segment):
            return True

        if not segment:
            return False

        # Decompose pre-composed characters (e.g. á -> a + combining acute)
        decomposed = unicodedata.normalize("NFD", segment)

        i = 0
        if len(decomposed) > 2 and decomposed[1] in {"\u0361", "\u035c"}:
            if not IPA_CHAR.is_valid_char(decomposed[0]) or not IPA_CHAR.is_valid_char(
                decomposed[2]
            ):
                return False
            i = 3
        else:
            if not IPA_CHAR.is_valid_char(decomposed[0]):
                return False
            i = 1

        while i < len(decomposed):
            if unicodedata.category(decomposed[i]) not in {"Mn", "Mc", "Me"}:
                return False
            i += 1

        return True

    @staticmethod
    def _has_tiebar(segment: str) -> bool:
        return len(segment) > 2 and segment[1] in {"\u0361", "\u035c"}

    def char_only(self):
        categories_to_remove = {"DIACRITIC", "SUPRASEGMENTAL", "TONE", "ACCENT_MARK"}

        def is_retainable(segment):
            cat = self._segment_category(segment)
            if cat is None:
                raise ValidationError("INVALID_SEGMENT", segment=segment, string=self.string)
            return cat not in categories_to_remove

        cleaned_string = "".join(segment for segment in self.segments if is_retainable(segment))

        self.string = cleaned_string
        self.segments = self._maximal_munch(cleaned_string)

        return cleaned_string
