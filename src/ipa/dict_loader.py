"""Singleton loader and normalizer for the bundled ipa_symbols.json data."""

import json
import os
from .debug import ValidationError

class DictionaryLoader:
    """Lazy singleton for loading and caching the IPA symbol data file."""

    _data = None
    _weights = None
    DEFAULT_RELATIVE_PATH = 'data/ipa_symbols.json'

    @classmethod
    def load_data(cls, relative_path=None):
        """Read, parse, and cache the IPA symbol data file.

        This method is idempotent: if ``_data`` is already populated it
        returns immediately without re-reading the file.

        The resolved file path is built by joining the directory of this
        module with ``relative_path`` (or ``DEFAULT_RELATIVE_PATH`` when
        ``relative_path`` is ``None``).

        Args:
            relative_path (str | None, optional): Path to the JSON data file
                relative to the module directory.  Defaults to
                ``'data/ipa_symbols.json'``.

        Raises:
            ValidationError: With type ``'FILE_NOT_FOUND'`` when the resolved
                path does not exist.
            ValidationError: With type ``'INVALID_JSON'`` when the file
                cannot be decoded as JSON.
            ValidationError: With type ``'INVALID_SCHEMA'`` when the JSON
                structure is not recognized as a valid IPA symbol file.
        """
        if cls._data is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            target_path = relative_path or cls.DEFAULT_RELATIVE_PATH
            file_path = os.path.join(base_dir, target_path)
            try:
                raw_data = cls._read_json(file_path)
            except FileNotFoundError:
                raise ValidationError("FILE_NOT_FOUND", file_path=file_path)

            normalized_data, weights = cls._normalize_data(raw_data, file_path)
            cls._data = normalized_data
            cls._weights = weights

    @staticmethod
    def _read_json(file_path):
        """Read and parse a JSON file from disk.

        Args:
            file_path (str): Absolute path to the JSON file.

        Returns:
            dict | list: The deserialized JSON content.

        Raises:
            FileNotFoundError: Re-raised when the file does not exist (caught
                and converted to ``ValidationError`` by the caller).
            ValidationError: With type ``'INVALID_JSON'`` when the file
                content cannot be parsed as JSON.
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise
        except json.JSONDecodeError:
            raise ValidationError("INVALID_JSON", file_path=file_path)

    @classmethod
    def _normalize_data(cls, data, file_path):
        """Dispatch raw JSON data to the appropriate normalizer.

        Currently only the official ``ipa_symbols.json`` schema is supported.
        The schema is detected by ``_looks_like_official``.

        Args:
            data (dict): The raw deserialized JSON object.
            file_path (str): Path used in the error message when the schema
                is not recognized.

        Returns:
            tuple[dict, dict]: A ``(normalized_data, weights)`` pair as
                returned by ``_normalize_official_data``.

        Raises:
            ValidationError: With type ``'INVALID_SCHEMA'`` when the data
                does not match any known schema.
        """
        if cls._looks_like_official(data):
            return cls._normalize_official_data(data)
        raise ValidationError("INVALID_SCHEMA", file_path=file_path)

    @staticmethod
    def _looks_like_official(data):
        """Check whether raw JSON data matches the official IPA symbol schema.

        The official schema is identified by the presence of at least one of
        the top-level category keys: ``'consonants'``, ``'vowels'``,
        ``'diacritics'``, ``'suprasegmentals'``, ``'tones'``, or
        ``'accent_marks'``.

        Args:
            data (object): The deserialized JSON value to inspect.

        Returns:
            bool: ``True`` if ``data`` is a dict containing at least one
                recognized top-level key, ``False`` otherwise.
        """
        if not isinstance(data, dict):
            return False
        official_keys = {
            'consonants',
            'vowels',
            'diacritics',
            'suprasegmentals',
            'tones',
            'accent_marks'
        }
        return any(key in data for key in official_keys)

    @classmethod
    def _normalize_official_data(cls, data):
        """Transform the official JSON structure into the normalized internal format.

        Iterates over the known top-level category keys, maps each to its
        uppercase internal name, and collects all symbol entries into a flat
        dict keyed by uppercase symbol name.

        Args:
            data (dict): Raw deserialized JSON whose top-level keys follow the
                official ``ipa_symbols.json`` schema.

        Returns:
            tuple[dict, dict]: A two-element tuple:
                - ``normalized`` -- nested dict of the form
                  ``{CATEGORY: {NAME: {"IPA": str, "code": str}, ...}, ...}``.
                - ``weights`` -- per-category weight map as returned by
                  ``_category_weights()``.
        """
        category_map = {
            'consonants': 'CONSONANT',
            'vowels': 'VOWEL',
            'diacritics': 'DIACRITIC',
            'suprasegmentals': 'SUPRASEGMENTAL',
            'tones': 'TONE',
            'accent_marks': 'ACCENT_MARK'
        }
        normalized = {}
        weights = cls._category_weights()
        for source_category, target_category in category_map.items():
            if source_category not in data:
                continue
            normalized.setdefault(target_category, {})
            cls._collect_symbols(data[source_category], normalized[target_category])
        return normalized, weights

    @staticmethod
    def _category_weights():
        """Return the fixed per-category phonological weight map."""
        return {
            'CONSONANT': 1,
            'VOWEL': 1,
            'DIACRITIC': 0,
            'SUPRASEGMENTAL': 0,
            'TONE': 0,
            'ACCENT_MARK': 0
        }

    @classmethod
    def _collect_symbols(cls, node, output):
        """Recursively traverse a JSON sub-tree and collect symbol entries.

        The JSON data file uses a nested structure with arbitrary grouping
        levels (e.g. ``pulmonic -> plosive -> [...]``).  This method walks the
        tree depth-first, delegating to ``_add_symbol_entry`` whenever a dict
        with a ``'symbol'`` key is found.

        Args:
            node (list | dict | object): The current JSON node to process.
                Lists are iterated element-by-element.  Dicts that contain a
                ``'symbol'`` key are treated as leaf symbol entries.  Dicts
                without ``'symbol'`` are traversed recursively (the ``'weight'``
                key is skipped).  Any other type is silently ignored.
            output (dict): The accumulator dict mapping uppercase symbol names
                to ``{"IPA": str, "code": str}`` entries.
        """
        if isinstance(node, list):
            for item in node:
                cls._collect_symbols(item, output)
            return

        if not isinstance(node, dict):
            return

        if 'symbol' in node:
            cls._add_symbol_entry(node, output)
            return

        for key, value in node.items():
            if key == 'weight':
                continue
            cls._collect_symbols(value, output)

    @classmethod
    def _add_symbol_entry(cls, node, output):
        """Register a single symbol node and any of its alternates.

        Reads the ``'symbol'``, ``'name'``, and ``'alternates'`` fields from a
        leaf JSON node, stores the primary symbol via ``_store_symbol``, and
        then stores each alternate with a name in the form
        ``'<NAME> ALT <alternate>'``.

        Args:
            node (dict): A JSON symbol entry dict.  Must contain ``'symbol'``;
                ``'name'`` and ``'alternates'`` are optional.
            output (dict): The accumulator dict to write into.
        """
        symbol = node.get('symbol')
        name = node.get('name') or symbol
        cls._store_symbol(name, symbol, output)

        alternates = node.get('alternates', [])
        for alternate in alternates:
            alt_name = f"{name} ALT {alternate}"
            cls._store_symbol(alt_name, alternate, output)

    @staticmethod
    def _store_symbol(name, symbol, output):
        """Write a single symbol entry into the output dict.

        Converts ``name`` to uppercase, computes the concatenated four-digit
        hex code for every code point in ``symbol``, and inserts an entry into
        ``output``.  If the uppercase name already exists, a numeric suffix is
        appended (``'(2)'``, ``'(3)'``, ...) until a unique key is found.

        Args:
            name (str): Human-readable symbol name, which may come from the
                ``'name'`` field of the JSON entry or from the symbol itself.
            symbol (str): The IPA character (or multi-codepoint sequence) to
                store.
            output (dict): The accumulator dict to write the entry into.
                Entries have the form ``{"IPA": str, "code": str}``.

        Returns:
            None: Silently returns without writing when ``symbol`` is empty
                or falsy.
        """
        if not symbol:
            return
        base_name = str(name).upper()
        code = ''.join(format(ord(char), '04x') for char in symbol)
        final_name = base_name
        suffix = 2
        while final_name in output:
            final_name = f"{base_name} ({suffix})"
            suffix += 1
        output[final_name] = {'IPA': symbol, 'code': code}

    @classmethod
    def get_data(cls):
        """Return the normalized IPA symbol table, loading it on first access.

        If ``_data`` is ``None``, ``load_data()`` is called with no arguments
        to read from the default ``ipa_symbols.json`` path.

        Returns:
            dict: The nested symbol table of the form
                ``{CATEGORY: {NAME: {"IPA": str, "code": str}, ...}, ...}``.

        Raises:
            ValidationError: Propagated from ``load_data()`` if the data file
                is missing, malformed, or uses an unrecognized schema.
        """
        if cls._data is None:
            cls.load_data()
        return cls._data

    @classmethod
    def get_weights(cls):
        """Return the per-category phonological weight map, loading it on first access.

        If ``_weights`` is ``None``, ``load_data()`` is called with no
        arguments to read from the default ``ipa_symbols.json`` path.

        Returns:
            dict[str, int]: Mapping of uppercase category name to integer
                weight (``1`` for CONSONANT and VOWEL, ``0`` for all others).

        Raises:
            ValidationError: Propagated from ``load_data()`` if the data file
                is missing, malformed, or uses an unrecognized schema.
        """
        if cls._weights is None:
            cls.load_data()
        return cls._weights
