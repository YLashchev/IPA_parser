"""Helpers for reading and writing language config TOML files."""

from __future__ import annotations

import tomllib
import unicodedata


def load_language_config(config_path: str) -> tuple[bool, list[tuple[str, str, int]]]:
    """Load a language config and return ``(geminate, custom_chars)``."""
    with open(config_path, "rb") as handle:
        data = tomllib.load(handle)

    geminate = data.get("geminate", True)
    if not isinstance(geminate, bool):
        raise ValueError("'geminate' must be a boolean")

    custom_chars_raw = data.get("custom_chars", [])
    if not isinstance(custom_chars_raw, list):
        raise ValueError("'custom_chars' must be a list")

    custom_chars: list[tuple[str, str, int]] = []
    for entry in custom_chars_raw:
        if not isinstance(entry, dict):
            raise ValueError("Each custom_chars entry must be a table")
        sequence = entry.get("sequence")
        category = entry.get("category")
        p_weight = entry.get("weight", 1)

        if not isinstance(sequence, str) or not sequence:
            raise ValueError("custom_chars.sequence must be a non-empty string")
        if not isinstance(category, str) or not category:
            raise ValueError("custom_chars.category must be a non-empty string")
        if not isinstance(p_weight, int):
            raise ValueError("custom_chars.weight must be an int")

        custom_chars.append((unicodedata.normalize("NFD", sequence), category, p_weight))

    return geminate, custom_chars


def save_language_config(
    config_path: str, geminate: bool, custom_chars: list[tuple[str, str, int]]
) -> None:
    """Write a complete language config to disk."""
    lines = [f"geminate = {str(geminate).lower()}", ""]

    for sequence, category, p_weight in custom_chars:
        lines.append("[[custom_chars]]")
        lines.append(f'sequence = "{_escape_toml_string(sequence)}"')
        lines.append(f'category = "{_escape_toml_string(category)}"')
        lines.append(f"weight = {p_weight}")
        lines.append("")

    output = "\n".join(lines).rstrip() + "\n"
    with open(config_path, "w", encoding="utf-8") as handle:
        handle.write(output)


def append_custom_char(
    config_path: str, sequence: str, category: str, p_weight: int
) -> tuple[bool, list[tuple[str, str, int]]]:
    """Add or replace one custom character entry in a config file."""
    geminate, custom_chars = load_language_config(config_path)
    updated = False

    for index, (existing_sequence, _, _) in enumerate(custom_chars):
        if existing_sequence == sequence:
            custom_chars[index] = (sequence, category, p_weight)
            updated = True
            break

    if not updated:
        custom_chars.append((sequence, category, p_weight))

    save_language_config(config_path, geminate, custom_chars)
    return geminate, custom_chars


def remove_custom_char(config_path: str, sequence: str) -> tuple[bool, list[tuple[str, str, int]]]:
    """Remove one custom character entry from a config file."""
    geminate, custom_chars = load_language_config(config_path)

    filtered_chars = [(seq, cat, w) for seq, cat, w in custom_chars if seq != sequence]

    if len(filtered_chars) == len(custom_chars):
        raise ValueError(f"Sequence '{sequence}' not found in custom_chars")

    save_language_config(config_path, geminate, filtered_chars)
    return geminate, filtered_chars


def _escape_toml_string(value: str) -> str:
    """Escape a value for a TOML basic string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')
