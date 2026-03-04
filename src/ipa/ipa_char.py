"""IPA character lookup and custom character registry.

This module exposes two classes:

- ``IPA_CHAR``: a class-based interface for querying metadata about any
  built-in IPA symbol loaded from ``ipa_symbols.json``.
- ``CustomCharacter``: a class-level registry for user-defined multi-character
  sequences (e.g. affricates, diphthongs, language-specific clusters) that
  are not present in the core IPA data file.

Both classes operate entirely through class methods and class-level state;
they are not meant to be instantiated.
"""

from .dict_loader import DictionaryLoader
from .debug import ValidationError



class IPA_CHAR:
    """Class-based lookup interface for built-in IPA symbols.

    Provides class methods to retrieve the category, human-readable name,
    Unicode hex code, phonological rank, and validity of any IPA character
    defined in ``ipa_symbols.json``.  All symbol data is loaded once at class
    definition time via ``DictionaryLoader`` and cached in class-level
    attributes.

    Class Attributes:
        _data (dict): Normalized symbol data keyed by category, then by
            symbol name.  Populated from ``DictionaryLoader.get_data()``.
        _weights (dict): Per-category phonological weight mapping populated
            from ``DictionaryLoader.get_weights()``.
        ranking_dictionary (dict): Combined weight map that extends
            ``_weights`` with AFFRICATE (1), DIPHTHONG (1), and PAUSE (0).
    """

    _data = DictionaryLoader.get_data() or {}
    _weights = DictionaryLoader.get_weights() or {}

    ranking_dictionary = {
        **_weights,
        'AFFRICATE': 1,
        'DIPHTHONG': 1,
        'PAUSE': 0
    }

    @classmethod
    def _char_data(cls, char):
        """Resolve a character to its (category, name, hex-code) tuple.

        Strips surrounding whitespace from ``char``, computes the concatenated
        Unicode hex representation of all its code points, and scans the
        loaded symbol table for a matching ``code`` field.

        Args:
            char (str): A single IPA character or multi-codepoint sequence
                (e.g. a base symbol combined with a diacritic).

        Returns:
            tuple[str, str, str]: A three-element tuple of
                ``(category, name, hex_code)`` where *category* is an
                uppercase string such as ``'CONSONANT'`` or ``'VOWEL'``,
                *name* is the full descriptive name of the symbol (e.g.
                ``'VOICELESS BILABIAL PLOSIVE'``), and *hex_code* is the
                concatenated four-digit hex representation of the character's
                code points (e.g. ``'0070'``).

        Raises:
            ValidationError: With type ``'EMPTY_INPUT_CHARACTER'`` when
                ``char`` is empty or contains only whitespace.
            ValidationError: With type ``'SYMBOL_NOT_FOUND'`` when the
                character is not present in the loaded symbol table.
        """
        char = char.strip()
        if not char:
            raise ValidationError("EMPTY_INPUT_CHARACTER")

        # Handle multi-codepoint characters
        char_codes = [format(ord(c), '04x') for c in char]
        char_code = ''.join(char_codes)

        for category, symbols in cls._data.items():
            for name, value in symbols.items():
                if value["code"] == char_code:
                    return category, name, value["code"]

        raise ValidationError("SYMBOL_NOT_FOUND", char=char)


    @classmethod
    def rank(cls, char):
        """Return the phonological rank (weight) of a character.

        The rank is determined by the character's category and the values
        defined in ``ranking_dictionary``.  Consonants and vowels have a
        rank of ``1``; diacritics, suprasegmentals, tones, accent marks,
        and pauses have a rank of ``0``.

        Args:
            char (str): A single IPA character or multi-codepoint sequence.

        Returns:
            int | None: The integer rank (``0`` or ``1``), or ``None`` if
                the category is not present in ``ranking_dictionary``.

        Raises:
            ValidationError: Propagated from ``_char_data`` when the
                character is empty or not found in the symbol table.
        """
        category, _, _ = cls._char_data(char)
        return cls.ranking_dictionary.get(category)

    @classmethod
    def name(cls, char):
        """Return the descriptive name of an IPA character.

        Args:
            char (str): A single IPA character or multi-codepoint sequence.

        Returns:
            str: The uppercase descriptive name of the symbol as stored in
                ``ipa_symbols.json`` (e.g. ``'VOICELESS BILABIAL PLOSIVE'``).

        Raises:
            ValidationError: Propagated from ``_char_data`` when the
                character is empty or not found in the symbol table.
        """
        _, name, _ = cls._char_data(char)
        return name

    @classmethod
    def category(cls, char):
        """Return the phonological category of an IPA character.

        Args:
            char (str): A single IPA character or multi-codepoint sequence.

        Returns:
            str: The uppercase category string (e.g. ``'CONSONANT'``,
                ``'VOWEL'``, ``'DIACRITIC'``, ``'SUPRASEGMENTAL'``,
                ``'TONE'``, or ``'ACCENT_MARK'``).

        Raises:
            ValidationError: Propagated from ``_char_data`` when the
                character is empty or not found in the symbol table.
        """
        category, _, _ = cls._char_data(char)
        return category

    @classmethod
    def code(cls, char):
        """Return the concatenated Unicode hex code of an IPA character.

        For single-codepoint characters the result is a four-character hex
        string (e.g. ``'0070'`` for ``'p'``).  For multi-codepoint
        characters the hex codes are concatenated without separators.

        Args:
            char (str): A single IPA character or multi-codepoint sequence.

        Returns:
            str: The concatenated four-digit hex code string.

        Raises:
            ValidationError: Propagated from ``_char_data`` when the
                character is empty or not found in the symbol table.
        """
        _, _, code = cls._char_data(char)
        return code

    @classmethod
    def is_valid_char(cls, char):
        """Check whether a character exists in the built-in IPA symbol table.

        Attempts to resolve the character via ``_char_data`` and catches any
        ``ValidationError`` to return a boolean result instead of raising.

        Args:
            char (str): A single IPA character or multi-codepoint sequence.

        Returns:
            bool: ``True`` if the character is found in the symbol table,
                ``False`` otherwise (including empty or whitespace-only input).
        """
        try:
            cls._char_data(char)
            return True
        except ValidationError:
            return False

class CustomCharacter:
    """Registry for user-defined multi-character IPA sequences.

    Stores language-specific character sequences — such as affricates (e.g.
    ``'ts'``), diphthongs (e.g. ``'aI'``), or other clusters — that are not
    present in the core ``ipa_symbols.json`` data file.  Entries are keyed by
    their character sequence and carry a phonological category and rank.

    This class operates entirely through class methods and a single class-level
    dictionary ``_custom_chars``.  It is not meant to be instantiated.

    The registry is populated from per-language TOML configuration files via
    ``load_language_config`` and the interactive CLI.  ``IPAString`` queries
    this registry during maximal-munch segmentation and metric computation.

    Class Attributes:
        _custom_chars (dict[str, dict[str, int | str]]): Internal store
            mapping each registered character sequence to a dict with keys
            ``'category'`` (str) and ``'rank'`` (int).
    """

    _custom_chars: dict[str, dict[str, int | str]] = {}

    @classmethod
    def add_char(cls, char_sequence, category, rank=1):
        """Register a custom character sequence in the registry.

        If ``char_sequence`` is already registered its entry is silently
        overwritten with the new ``category`` and ``rank`` values.

        Args:
            char_sequence (str): The multi-character (or single-character)
                string to register (e.g. ``'ts'``, ``'aI'``).
            category (str): The phonological category to assign, using the
                same uppercase conventions as built-in symbols (e.g.
                ``'AFFRICATE'``, ``'DIPHTHONG'``, ``'CONSONANT'``).
            rank (int, optional): The phonological weight of the sequence
                used by ``IPAString.total_length()``.  Defaults to ``1``.
        """
        cls._custom_chars[char_sequence] = {'category': category, 'rank': rank}

    @classmethod
    def remove_char(cls, char_sequence):
        """Remove a registered custom character sequence from the registry.

        Does nothing if ``char_sequence`` is not currently registered.

        Args:
            char_sequence (str): The sequence to remove.
        """
        if char_sequence in cls._custom_chars:
            del cls._custom_chars[char_sequence]

    @classmethod
    def get_char(cls, char_sequence):
        """Retrieve the metadata dict for a registered custom character sequence.

        Args:
            char_sequence (str): The sequence to look up.

        Returns:
            dict[str, int | str] | None: A dict with keys ``'category'``
                (str) and ``'rank'`` (int) if the sequence is registered,
                or ``None`` if it is not found.
        """
        return cls._custom_chars.get(char_sequence)

    @classmethod
    def clear_all_chars(cls):
        """Clear all registered custom character sequences."""
        cls._custom_chars.clear()

    @classmethod
    def is_valid_char(cls, char):
        """Return ``True`` if ``char`` is a registered custom sequence."""
        return char in cls._custom_chars
    
