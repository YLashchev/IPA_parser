"""IPA symbol lookup and custom character registration."""

import unicodedata

from .dict_loader import DictionaryLoader
from .debug import ValidationError


class IPA_CHAR:
    """Lookup helpers for built-in IPA symbols."""

    _data = DictionaryLoader.get_data() or {}
    _weights = DictionaryLoader.get_weights() or {}

    p_weight_dictionary = {**_weights, "AFFRICATE": 1, "DIPHTHONG": 1, "PAUSE": 0}

    @classmethod
    def _char_data(cls, char):
        """Return ``(category, name, code)`` for a built-in IPA symbol."""
        char = unicodedata.normalize("NFD", char.strip())
        if not char:
            raise ValidationError("EMPTY_INPUT_CHARACTER")

        # Handle multi-codepoint characters
        char_codes = [format(ord(c), "04x") for c in char]
        char_code = "".join(char_codes)

        for category, symbols in cls._data.items():
            for name, value in symbols.items():
                if value["code"] == char_code:
                    return category, name, value["code"]

        raise ValidationError("SYMBOL_NOT_FOUND", char=char)

    @classmethod
    def p_weight(cls, char):
        """Return the phonological weight for a built-in IPA symbol."""
        category, _, _ = cls._char_data(char)
        return cls.p_weight_dictionary.get(category)

    @classmethod
    def name(cls, char):
        """Return the descriptive name for a built-in IPA symbol."""
        _, name, _ = cls._char_data(char)
        return name

    @classmethod
    def category(cls, char):
        """Return the category for a built-in IPA symbol."""
        category, _, _ = cls._char_data(char)
        return category

    @classmethod
    def code(cls, char):
        """Return the concatenated hex code for a built-in IPA symbol."""
        _, _, code = cls._char_data(char)
        return code

    @classmethod
    def is_valid_char(cls, char):
        """Return ``True`` when the symbol exists in the built-in table."""
        try:
            cls._char_data(char)
            return True
        except ValidationError:
            return False


# Common IPA affricates and diphthongs with tie-bar U+0361
COMMON_AFFRICATES = {
    "t͡s": "voiceless alveolar affricate",
    "d͡z": "voiced alveolar affricate",
    "t͡ʃ": "voiceless postalveolar affricate",
    "d͡ʒ": "voiced postalveolar affricate",
    "t͡ɕ": "voiceless alveolo-palatal affricate",
    "d͡ʑ": "voiced alveolo-palatal affricate",
    "t͡θ": "voiceless dental affricate",
    "t͡ɬ": "voiceless alveolar lateral affricate",
}

COMMON_DIPHTHONGS = {
    "a͡ɪ": "open front to near-close near-front",
    "a͡ʊ": "open front to near-close near-back",
    "e͡ɪ": "close-mid front to near-close near-front",
    "o͡ɪ": "close-mid back to near-close near-front",
    "o͡ʊ": "close-mid back to near-close near-back",
}


class CustomCharacter:
    """Registry for user-defined multi-character sequences."""

    _custom_chars: dict[str, dict[str, int | str]] = {}

    VALID_CATEGORIES = {
        "CONSONANT",
        "VOWEL",
        "DIPHTHONG",
        "AFFRICATE",
        "PAUSE",
        "DIACRITIC",
        "SUPRASEGMENTAL",
        "TONE",
        "ACCENT_MARK",
    }

    @classmethod
    def add_char(cls, char_sequence, category, p_weight=1):
        """Register or replace a custom character sequence."""
        if category not in cls.VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {', '.join(sorted(cls.VALID_CATEGORIES))}"
            )
        # NFD-normalize so matching works regardless of input normalization form
        char_sequence = unicodedata.normalize("NFD", char_sequence)
        cls._custom_chars[char_sequence] = {"category": category, "p_weight": p_weight}

    @classmethod
    def remove_char(cls, char_sequence):
        """Remove a custom character sequence if it exists."""
        if char_sequence in cls._custom_chars:
            del cls._custom_chars[char_sequence]

    @classmethod
    def get_char(cls, char_sequence):
        """Return metadata for a registered custom sequence, if present."""
        return cls._custom_chars.get(char_sequence)

    @classmethod
    def clear_all_chars(cls):
        """Clear all registered custom character sequences."""
        cls._custom_chars.clear()

    @classmethod
    def is_valid_char(cls, char):
        """Return ``True`` if ``char`` is a registered custom sequence."""
        return char in cls._custom_chars

    @classmethod
    def register_common_affricates(cls, p_weight=1):
        """Register the built-in affricate set."""
        for sequence in COMMON_AFFRICATES:
            cls.add_char(sequence, "AFFRICATE", p_weight=p_weight)

    @classmethod
    def register_common_diphthongs(cls, p_weight=1):
        """Register the built-in diphthong set."""
        for sequence in COMMON_DIPHTHONGS:
            cls.add_char(sequence, "DIPHTHONG", p_weight=p_weight)
