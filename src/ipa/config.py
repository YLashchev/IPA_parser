"""TOML-based language configuration loader and writer for ipa-parser.

This module provides functions for reading, writing, and updating per-language
configuration files stored in TOML format. Each config file controls geminate
handling and defines custom character sequences (affricates, diphthongs, or
language-specific clusters) that extend the base IPA symbol set.

Typical config file structure::

    geminate = true

    [[custom_chars]]
    sequence = "ts"
    category = "CONSONANT"
    rank = 1

    [[custom_chars]]
    sequence = "OP"
    category = "PAUSE"
    rank = 0

See ``data/language_settings/README.md`` for the full TOML schema reference.
"""

from __future__ import annotations

import tomllib


def load_language_config(config_path: str) -> tuple[bool, list[tuple[str, str, int]]]:
    """Load and validate a TOML language configuration file.

    Reads the given TOML file and extracts the ``geminate`` flag and the list
    of custom character definitions. Each entry in the ``[[custom_chars]]``
    array must supply a ``sequence`` (non-empty string), a ``category``
    (non-empty string), and an optional integer ``rank`` (defaults to ``1``).

    Args:
        config_path: Filesystem path to the ``.toml`` configuration file.
            The file is opened in binary mode as required by ``tomllib``.

    Returns:
        A two-element tuple ``(geminate, custom_chars)`` where:

        - ``geminate`` (bool): Whether geminate consonant handling is enabled.
        - ``custom_chars`` (list[tuple[str, str, int]]): Ordered list of
          ``(sequence, category, rank)`` triples representing custom characters
          to register with ``CustomCharacter``.

    Raises:
        ValueError: If ``geminate`` is not a boolean, ``custom_chars`` is not
            a list, or any entry within ``custom_chars`` is missing required
            fields or has incorrect types.
        FileNotFoundError: If ``config_path`` does not point to an existing
            file (propagated from ``open``).
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
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
        rank = entry.get("rank", 1)

        if not isinstance(sequence, str) or not sequence:
            raise ValueError("custom_chars.sequence must be a non-empty string")
        if not isinstance(category, str) or not category:
            raise ValueError("custom_chars.category must be a non-empty string")
        if not isinstance(rank, int):
            raise ValueError("custom_chars.rank must be an int")

        custom_chars.append((sequence, category, rank))

    return geminate, custom_chars


def save_language_config(
    config_path: str, geminate: bool, custom_chars: list[tuple[str, str, int]]
) -> None:
    """Write a complete language configuration to a TOML file.

    Serializes ``geminate`` and the full list of custom character entries to
    the file at ``config_path``, overwriting any previous content. Each entry
    in ``custom_chars`` is written as a separate ``[[custom_chars]]`` table.
    String values are escaped via ``_escape_toml_string`` before writing.

    Args:
        config_path: Filesystem path where the TOML file will be written.
            The file is created or truncated. Directories must already exist.
        geminate: The geminate-handling flag to persist (``true``/``false``
            in the resulting TOML).
        custom_chars: Ordered list of ``(sequence, category, rank)`` triples
            to write as ``[[custom_chars]]`` entries.

    Returns:
        None

    Raises:
        OSError: If the file cannot be opened for writing (e.g., permissions
            error or missing parent directory).
    """
    lines = [f"geminate = {str(geminate).lower()}", ""]

    for sequence, category, rank in custom_chars:
        lines.append("[[custom_chars]]")
        lines.append(f'sequence = "{_escape_toml_string(sequence)}"')
        lines.append(f'category = "{_escape_toml_string(category)}"')
        lines.append(f"rank = {rank}")
        lines.append("")

    output = "\n".join(lines).rstrip() + "\n"
    with open(config_path, "w", encoding="utf-8") as handle:
        handle.write(output)


def append_custom_char(
    config_path: str, sequence: str, category: str, rank: int
) -> tuple[bool, list[tuple[str, str, int]]]:
    """Append or update a single custom character entry in an existing TOML config.

    Loads the current configuration from ``config_path``, then either replaces
    the existing entry whose ``sequence`` matches the provided value or appends
    a new entry if no match is found. The updated configuration is written back
    to the same file via ``save_language_config``.

    Args:
        config_path: Filesystem path to the existing ``.toml`` configuration
            file. The file must already exist and be valid TOML.
        sequence: The character sequence to add or update (e.g., ``"ts"``).
        category: The phonological category to assign (e.g., ``"CONSONANT"``).
        rank: The weight rank for the character. Use ``1`` for phonemes that
            count toward phonological length, ``0`` for non-phonemes such as
            pauses or diacritics.

    Returns:
        A two-element tuple ``(geminate, custom_chars)`` reflecting the state
        of the configuration after the update, in the same format as
        ``load_language_config``.

    Raises:
        ValueError: Propagated from ``load_language_config`` if the existing
            config file is structurally invalid.
        OSError: Propagated from ``save_language_config`` if the file cannot
            be written.
        tomllib.TOMLDecodeError: If the existing file is not valid TOML.
    """
    geminate, custom_chars = load_language_config(config_path)
    updated = False

    for index, (existing_sequence, _, _) in enumerate(custom_chars):
        if existing_sequence == sequence:
            custom_chars[index] = (sequence, category, rank)
            updated = True
            break

    if not updated:
        custom_chars.append((sequence, category, rank))

    save_language_config(config_path, geminate, custom_chars)
    return geminate, custom_chars


def remove_custom_char(config_path: str, sequence: str) -> tuple[bool, list[tuple[str, str, int]]]:
    """Remove a single custom character entry from an existing TOML config.

    Loads the current configuration from ``config_path``, filters out the entry
    whose ``sequence`` matches the provided value, and writes the updated
    configuration back to the same file via ``save_language_config``.

    Args:
        config_path: Filesystem path to the existing ``.toml`` configuration
            file. The file must already exist and be valid TOML.
        sequence: The character sequence to remove (e.g., ``"ts"``).

    Returns:
        A two-element tuple ``(geminate, custom_chars)`` reflecting the state
        of the configuration after removal, in the same format as
        ``load_language_config``.

    Raises:
        ValueError: If ``sequence`` is not found in the current custom_chars
            list, or propagated from ``load_language_config`` if the existing
            config file is structurally invalid.
        OSError: Propagated from ``save_language_config`` if the file cannot
            be written.
        tomllib.TOMLDecodeError: If the existing file is not valid TOML.
    """
    geminate, custom_chars = load_language_config(config_path)

    filtered_chars = [(seq, cat, rank) for seq, cat, rank in custom_chars if seq != sequence]

    if len(filtered_chars) == len(custom_chars):
        raise ValueError(f"Sequence '{sequence}' not found in custom_chars")

    save_language_config(config_path, geminate, filtered_chars)
    return geminate, filtered_chars


def _escape_toml_string(value: str) -> str:
    """Escape a string value for safe embedding in a TOML basic string.

    Replaces backslashes with double-backslashes and double-quote characters
    with escaped double-quotes so that the result can be safely placed between
    TOML double-quote delimiters without breaking the file syntax.

    Args:
        value: The raw string to escape.

    Returns:
        A new string with ``\\`` replaced by ``\\\\`` and ``"`` replaced by
        ``\\"``.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')
