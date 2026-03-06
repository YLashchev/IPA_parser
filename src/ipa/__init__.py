"""Public API for the IPA parser package."""

from .ipa_char import IPA_CHAR, CustomCharacter, COMMON_AFFRICATES, COMMON_DIPHTHONGS
from .ipa_string import IPAString
from .dict_loader import DictionaryLoader
from .debug import ValidationError
from .config import load_language_config

__all__ = [
    "IPA_CHAR",
    "CustomCharacter",
    "IPAString",
    "DictionaryLoader",
    "ValidationError",
    "load_language_config",
    "COMMON_AFFRICATES",
    "COMMON_DIPHTHONGS",
]
