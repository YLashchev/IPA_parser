"""ipa: A library for parsing and analyzing UTF-8 International Phonetic Alphabet (IPA) strings.

This package provides tools for tokenizing IPA transcriptions into phonological
segments, querying symbol metadata (category, name, Unicode code point, weight),
defining language-specific custom characters (affricates, diphthongs, clusters),
and computing a range of phonological metrics including segment counts, syllable
structure, stress, coda complexity, and total phonological length.

The single source of truth for all built-in IPA symbols is the bundled data file
``src/ipa/data/ipa_symbols.json``.  Custom, language-specific sequences are
stored in per-language TOML configuration files under ``data/language_settings/``.

Public API:
    IPA_CHAR: Class-based lookup interface for built-in IPA symbols.
    CustomCharacter: Registry for user-defined multi-character sequences.
    IPAString: Tokenizes and analyzes a full IPA transcription string.
    DictionaryLoader: Singleton that loads and normalizes ``ipa_symbols.json``.
    ValidationError: Custom exception raised on all validation failures.
    load_language_config: Parses a TOML language configuration file.

Example:
    >>> from ipa import IPAString, CustomCharacter, load_language_config
    >>> geminate, custom_chars = load_language_config("data/language_settings/Northwest_Sahaptin.toml")
    >>> for sequence, category, rank in custom_chars:
    ...     CustomCharacter.add_char(sequence, category, rank)
    >>> word = IPAString("bə.ˈnæ.nə", geminate=geminate)
    >>> word.segment_count
    {'V': 3, 'C': 3}
    >>> word.stress()
    'STRESSED'
"""

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
