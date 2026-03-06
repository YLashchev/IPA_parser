"""Singleton loader and normalizer for the bundled ipa_symbols.json data."""

import json
import os
import unicodedata

from .debug import ValidationError


class DictionaryLoader:
    """Lazy singleton for loading and caching the IPA symbol data file."""

    _data = None
    _weights = None
    DEFAULT_RELATIVE_PATH = "data/ipa_symbols.json"

    @classmethod
    def load_data(cls, relative_path=None):
        """Read, parse, and cache the IPA symbol data file (idempotent)."""
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
        """Read and parse a JSON file from disk."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise
        except json.JSONDecodeError:
            raise ValidationError("INVALID_JSON", file_path=file_path)

    @classmethod
    def _normalize_data(cls, data, file_path):
        """Dispatch raw JSON to the appropriate normalizer."""
        if cls._looks_like_official(data):
            return cls._normalize_official_data(data)
        raise ValidationError("INVALID_SCHEMA", file_path=file_path)

    @staticmethod
    def _looks_like_official(data):
        """Return True if data has recognized top-level IPA category keys."""
        if not isinstance(data, dict):
            return False
        official_keys = {
            "consonants",
            "vowels",
            "diacritics",
            "suprasegmentals",
            "tones",
            "accent_marks",
        }
        return any(key in data for key in official_keys)

    @classmethod
    def _normalize_official_data(cls, data):
        """Transform the official JSON structure into ``{CATEGORY: {NAME: entry}}``."""
        category_map = {
            "consonants": "CONSONANT",
            "vowels": "VOWEL",
            "diacritics": "DIACRITIC",
            "suprasegmentals": "SUPRASEGMENTAL",
            "tones": "TONE",
            "accent_marks": "ACCENT_MARK",
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
            "CONSONANT": 1,
            "VOWEL": 1,
            "DIACRITIC": 0,
            "SUPRASEGMENTAL": 0,
            "TONE": 0,
            "ACCENT_MARK": 0,
        }

    @classmethod
    def _collect_symbols(cls, node, output):
        """Recursively walk a JSON sub-tree and collect symbol entries."""
        if isinstance(node, list):
            for item in node:
                cls._collect_symbols(item, output)
            return

        if not isinstance(node, dict):
            return

        if "symbol" in node:
            cls._add_symbol_entry(node, output)
            return

        for key, value in node.items():
            if key == "weight":
                continue
            cls._collect_symbols(value, output)

    @classmethod
    def _add_symbol_entry(cls, node, output):
        """Store a symbol node and its alternates into output."""
        symbol = node.get("symbol")
        name = node.get("name") or symbol
        cls._store_symbol(name, symbol, output)

        alternates = node.get("alternates", [])
        for alternate in alternates:
            alt_name = f"{name} ALT {alternate}"
            cls._store_symbol(alt_name, alternate, output)

    @staticmethod
    def _store_symbol(name, symbol, output):
        """NFD-normalize symbol, compute hex code, and write to output."""
        if not symbol:
            return
        symbol = unicodedata.normalize("NFD", symbol)
        base_name = str(name).upper()
        code = "".join(format(ord(char), "04x") for char in symbol)
        final_name = base_name
        suffix = 2
        while final_name in output:
            final_name = f"{base_name} ({suffix})"
            suffix += 1
        output[final_name] = {"IPA": symbol, "code": code}

    @classmethod
    def get_data(cls):
        """Return the normalized IPA symbol table, loading on first access."""
        if cls._data is None:
            cls.load_data()
        return cls._data

    @classmethod
    def get_weights(cls):
        """Return the per-category weight map, loading on first access."""
        if cls._weights is None:
            cls.load_data()
        return cls._weights
