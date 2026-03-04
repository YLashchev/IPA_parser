"""Interactive menu-driven CLI for exploring and validating IPA data.

This module implements the interactive mode of the ``ipa-parser`` command.
It exposes a numbered menu loop that lets the user:

- Browse the deduplicated word list derived from the input DataFrame.
- Inspect individual words to see their segments, syllable structure, stress
  pattern, coda complexity, and phonological length.
- Explore unique graphemes and their frequencies across the corpus.
- Identify non-phoneme symbols (weight-0 marks) grouped by category.
- Detect unrecognized symbols that are absent from both the IPA symbol table
  and any registered custom characters.
- View, add, or update custom character definitions that extend the base IPA
  symbol set.
- Run the full processing pipeline and export results to CSV and XLSX.

All public and private functions in this module operate on a ``pandas``
``DataFrame`` whose schema matches ``DEFAULT_COLUMNS`` defined in
``pipeline.py``. The ``geminate`` flag is threaded through every
``IPAString`` call to ensure consistent phonological counting.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

import pandas as pd

from .config import append_custom_char
from .debug import ValidationError
from .ipa_char import IPA_CHAR, CustomCharacter
from .ipa_string import IPAString
from .pipeline import assign_pauses, build_final_dataframe, insert_sp


def run_interactive(
    df: pd.DataFrame,
    geminate: bool,
    config_path: str | None,
    output_csv: str,
    output_xlsx: str,
    output_format: str = "both",
) -> None:
    """Run the interactive menu loop for IPA data exploration.

    Displays a numbered option menu and dispatches to the appropriate helper
    function based on the user's input. The loop continues until the user
    selects option ``9`` (Quit). The word list is lazily built on first access
    and cached for subsequent menu options that require it; the cache is
    invalidated whenever a new custom character is added (option ``7``).

    Menu options:

    1. Show word list -- tabular display of all words with syllable count,
       phonological length, and stress pattern.
    2. Inspect word -- detailed segment-level breakdown of a single word.
    3. Show unique graphemes -- frequency-ranked list of every segment token
       occurring in the ``Phoneme`` column.
    4. Show non-phoneme marks (weight 0) -- symbols whose rank is ``0``,
       grouped by category.
    5. Show unrecognized symbols -- segments absent from the IPA table and
       all registered custom characters.
    6. Show custom characters -- currently registered ``CustomCharacter``
       entries with their categories and ranks.
    7. Add custom character -- interactive prompt to register a new custom
       character and optionally persist it to the TOML config file.
    8. Run pipeline and export -- executes ``build_final_dataframe`` and
       writes results in the format(s) specified by ``output_format``.
    9. Quit -- exits the loop.

    Args:
        df: Input ``DataFrame`` loaded from the Excel source file. Must
            contain at least a ``Phoneme`` column and the columns defined in
            ``DEFAULT_COLUMNS``.
        geminate: Whether geminate consonant handling is enabled. Passed
            through to all ``IPAString`` instantiations.
        config_path: Filesystem path to the active TOML language config, or
            ``None`` if no config was supplied. Used to persist new custom
            characters added during the session.
        output_csv: Destination path for the CSV export produced by option 8.
        output_xlsx: Destination path for the XLSX export produced by option 8.
        output_format: Output format selection. One of ``'csv'``, ``'xlsx'``,
            or ``'both'`` (default).

    Returns:
        None
    """
    words_cache: list[str] | None = None
    while True:
        print("\n=== IPA Parser ===")
        print("1) Show word list")
        print("2) Inspect word")
        print("3) Show unique graphemes")
        print("4) Show non-phoneme marks (weight 0)")
        print("5) Show unrecognized symbols")
        print("6) Show custom characters")
        print("7) Add custom character")
        print("8) Run pipeline and export")
        print("9) Quit")

        choice = input("Select option: ").strip()

        if choice == "1":
            words_cache = _build_word_list(df)
            _show_word_list_table(words_cache, geminate)
        elif choice == "2":
            if words_cache is None:
                words_cache = _build_word_list(df)
            _inspect_word(words_cache, geminate)
        elif choice == "3":
            grapheme_counts = _unique_graphemes(df, geminate)
            print(f"Total unique graphemes: {len(grapheme_counts)}")
            for symbol, count in grapheme_counts.most_common():
                print(f"{symbol}: {count}")
        elif choice == "4":
            non_phonemes = _non_phoneme_symbols_by_category(df, geminate)
            if not non_phonemes:
                print("No non-phoneme symbols found.")
            else:
                total = sum(len(values) for values in non_phonemes.values())
                print(f"Non-phoneme symbols found: {total}")
                for category in sorted(non_phonemes):
                    print(f"{category}: {non_phonemes[category]}")
        elif choice == "5":
            unrecognized = _unrecognized_symbols(df, geminate)
            if unrecognized:
                print(f"Unrecognized symbols: {len(unrecognized)}")
                print(sorted(unrecognized))
            else:
                print("No unrecognized symbols found.")
        elif choice == "6":
            _print_custom_characters()
        elif choice == "7":
            _add_custom_character(config_path)
            words_cache = None
            unrecognized = _unrecognized_symbols(df, geminate)
            if unrecognized:
                print("\nUnrecognized symbols after update:")
                print(sorted(unrecognized))
            else:
                print("\nNo unrecognized symbols found after update.")
        elif choice == "8":
            from .cli import _export
            final_df, mismatches = build_final_dataframe(df, geminate=geminate, fill_na=True)
            if mismatches:
                print(mismatches)
            print(final_df)
            exported = _export(final_df, output_csv, output_xlsx, output_format)
            print(f"\nExported {', '.join(exported)}")
        elif choice == "9":
            return
        else:
            print("Invalid choice. Please select 1-9.")


def _build_word_list(df: pd.DataFrame) -> list[str]:
    """Build an ordered, deduplicated list of words from the input DataFrame.

    Preprocesses the DataFrame by inserting SP (sentence-pause) rows between
    sentences and assigning pause labels to pause phonemes. Consecutive
    duplicate word values (which arise because each phoneme segment occupies
    its own row) are collapsed to a single entry. Missing ``Word`` values are
    treated as ``"SP"``.

    Args:
        df: Input ``DataFrame`` with at least ``Sentence``, ``Word``, and
            ``Phoneme`` columns in the schema expected by ``insert_sp`` and
            ``assign_pauses``.

    Returns:
        An ordered list of unique consecutive word strings, including ``"SP"``
        and ``"OP"`` markers that represent sentence and other pauses.
    """
    prepared = insert_sp(df)
    assign_pauses(prepared)
    words: list[str] = []
    last_word = None

    for _, row in prepared.iterrows():
        word = row.get("Word")
        if word is None or (isinstance(word, float) and pd.isna(word)):
            word = "SP"
        if word != last_word:
            words.append(str(word))
            last_word = word

    return words


def _show_word_list_table(words: list[str], geminate: bool) -> None:
    """Print a formatted table of words with their phonological metrics.

    For each word in ``words``, computes and displays:

    - 1-based index number.
    - Word string (left-aligned, padded to 30 characters).
    - Syllable count (or ``"-"`` for pause markers ``"OP"`` / ``"SP"``).
    - Phonological length returned by ``IPAString.total_length()``.
    - Stress pattern string returned by ``IPAString.stress()``.

    Words that raise ``ValidationError`` during parsing are shown with
    ``"ERR"`` in all metric columns. Pause markers (``"OP"``, ``"SP"``) are
    displayed with ``"-"`` syllables, ``0`` length, and ``"PAUSE"`` stress.

    Args:
        words: Ordered list of word strings as produced by ``_build_word_list``.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        None
    """
    print(f"Total words: {len(words)}")
    header = f"{'#':>4}  {'Word':<30}  {'Syllables':>9}  {'Length':>6}  {'Stress':<10}"
    print(header)
    print("-" * len(header))
    for index, word in enumerate(words, start=1):
        try:
            if word in {"OP", "SP"}:
                syllable_count: int | str = "-"
                length: int | str = 0
                stress: str = "PAUSE"
            else:
                ipa = IPAString(word, geminate=geminate)
                syllable_count = len(ipa.syllables)
                length = ipa.total_length()
                stress = ipa.stress()
        except ValidationError:
            syllable_count = "ERR"
            length = "ERR"
            stress = "ERR"
        print(f"{index:>4}  {word:<30}  {syllable_count:>9}  {length:>6}  {stress:<10}")


def _inspect_word(words: list[str], geminate: bool) -> None:
    """Prompt the user to select a word and print its full phonological breakdown.

    Accepts either a 1-based integer index into ``words`` or a raw IPA string
    typed directly by the user. For the selected word, displays:

    - The original word string.
    - The result of ``IPAString.process_string()`` (canonical form with
      tie-bars and diacritics stripped based on char-only filtering).
    - The list of parsed segments.
    - The per-segment type list (raw category names).
    - The CV-reduced type list (``"C"`` for CONSONANT, ``"V"`` for VOWEL,
      other values left as-is).
    - The syllable list from ``IPAString.syllables``.
    - Total phonological length.
    - Stress pattern.
    - Coda complexity value.
    - Whether geminate handling is currently active.

    If the index is out of range or the IPA string fails to parse, an
    informative error message is printed and the function returns without
    raising.

    Args:
        words: Ordered list of word strings as produced by ``_build_word_list``.
        geminate: Whether geminate consonant handling is enabled. Passed to
            the ``IPAString`` constructor.

    Returns:
        None
    """
    selection = input("Enter word number or IPA string: ").strip()
    if not selection:
        return

    if selection.isdigit():
        index = int(selection) - 1
        if index < 0 or index >= len(words):
            print("Invalid word index.")
            return
        word = words[index]
    else:
        word = selection

    try:
        ipa = IPAString(word, geminate=geminate)
    except ValidationError as exc:
        print(f"Invalid word: {exc}")
        return

    processed = ipa.process_string()
    segment_types = ipa.segment_type
    cv_types = [
        "C" if item == "CONSONANT" else "V" if item == "VOWEL" else item
        for item in segment_types
    ]

    print(f"\nWord: {word}")
    print(f"Processed: {processed}")
    print(f"Segments: {ipa.segments}")
    print(f"Types: {segment_types}")
    print(f"CV Types: {cv_types}")
    print(f"Syllables: {ipa.syllables}")
    print(f"Length: {ipa.total_length()}")
    print(f"Stress: {ipa.stress()}")
    print(f"Coda: {ipa.coda}")
    print(f"Geminate: {'on' if geminate else 'off'}")


def _iter_phoneme_segments(df: pd.DataFrame, geminate: bool) -> Iterable[str]:
    """Yield individual segment tokens from the ``Phoneme`` column of the DataFrame.

    Iterates over each non-null value in the ``Phoneme`` column. Pause markers
    (``"OP"``, ``"SP"``) are yielded as single tokens unchanged. All other
    values are parsed through ``IPAString`` and each resulting segment is
    yielded individually. If ``IPAString`` raises ``ValidationError`` for a
    phoneme entry, the raw Unicode codepoints of that string are yielded
    instead as individual characters.

    Args:
        df: Input ``DataFrame`` with a ``Phoneme`` column.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Yields:
        Individual segment strings -- either single IPA characters, multi-
        character custom sequences, or single-character fallbacks from failed
        parses.
    """
    for value in df["Phoneme"].dropna().tolist():
        phoneme = str(value).strip()
        if not phoneme:
            continue
        if phoneme in {"OP", "SP"}:
            yield phoneme
            continue
        try:
            segments = IPAString(phoneme, geminate=geminate).segments
        except ValidationError:
            segments = list(phoneme)
        for segment in segments:
            yield segment


def _unique_graphemes(df: pd.DataFrame, geminate: bool) -> Counter[str]:
    """Count the frequency of every unique segment token in the corpus.

    Consumes ``_iter_phoneme_segments`` and returns a ``Counter`` mapping each
    distinct segment string to the number of times it appears across all
    phoneme entries in the DataFrame.

    Args:
        df: Input ``DataFrame`` with a ``Phoneme`` column.
        geminate: Whether geminate consonant handling is enabled. Passed
            through to ``_iter_phoneme_segments``.

    Returns:
        A ``Counter[str]`` where keys are segment strings and values are their
        occurrence counts, suitable for ``most_common()`` ranking.
    """
    return Counter(_iter_phoneme_segments(df, geminate))


def _non_phoneme_symbols_by_category(
    df: pd.DataFrame, geminate: bool
) -> dict[str, list[str]]:
    """Collect all weight-0 (non-phoneme) symbols grouped by their category.

    Iterates over every unique segment in the corpus and retains only those
    whose rank is ``0`` -- i.e., symbols that do not contribute to
    phonological length (diacritics, pause markers, tone marks, etc.). Custom
    characters registered with ``CustomCharacter`` are checked first; then the
    base IPA symbol table via ``IPA_CHAR`` is consulted.

    Args:
        df: Input ``DataFrame`` with a ``Phoneme`` column.
        geminate: Whether geminate consonant handling is enabled. Passed
            through to ``_unique_graphemes``.

    Returns:
        A ``dict`` mapping category name strings (e.g., ``"PAUSE"``,
        ``"DIACRITIC"``) to sorted lists of symbol strings belonging to that
        category whose rank is ``0``. Returns an empty dict if no such symbols
        are found.
    """
    categories: dict[str, set[str]] = {}
    for symbol in _unique_graphemes(df, geminate):
        if CustomCharacter.is_valid_char(symbol):
            custom_char = CustomCharacter.get_char(symbol)
            if custom_char and custom_char["rank"] == 0:
                category = str(custom_char["category"])
                categories.setdefault(category, set()).add(symbol)
            continue

        if IPA_CHAR.is_valid_char(symbol) and IPA_CHAR.rank(symbol) == 0:
            category = IPA_CHAR.category(symbol)
            categories.setdefault(category, set()).add(symbol)

    return {category: sorted(symbols) for category, symbols in categories.items()}


def _unrecognized_symbols(df: pd.DataFrame, geminate: bool) -> set[str]:
    """Return the set of segment tokens that are not recognized by any symbol table.

    A symbol is considered unrecognized if it is absent from both
    ``CustomCharacter`` and the base ``IPA_CHAR`` lookup. This is useful for
    catching typos, unsupported diacritics, or sequences that need to be
    registered as custom characters before the pipeline can process them.

    Args:
        df: Input ``DataFrame`` with a ``Phoneme`` column.
        geminate: Whether geminate consonant handling is enabled. Passed
            through to ``_iter_phoneme_segments``.

    Returns:
        A ``set[str]`` of unrecognized segment strings. Returns an empty set
        if every segment in the corpus is recognized.
    """
    unknown = set()
    for symbol in _iter_phoneme_segments(df, geminate):
        if CustomCharacter.is_valid_char(symbol):
            continue
        if IPA_CHAR.is_valid_char(symbol):
            continue
        unknown.add(symbol)
    return unknown


def _print_custom_characters() -> None:
    """Print all currently registered custom characters to standard output.

    Reads the internal ``CustomCharacter._custom_chars`` mapping and prints
    each entry in alphabetical sequence order with its category and rank.
    If no custom characters have been registered, prints an informative
    message instead.

    Returns:
        None
    """
    custom_chars = CustomCharacter._custom_chars
    if not custom_chars:
        print("No custom characters registered.")
        return

    for sequence, data in sorted(custom_chars.items()):
        print(f"{sequence}: {data['category']} (rank={data['rank']})")


def _add_custom_character(config_path: str | None) -> None:
    """Interactively prompt the user to register a new custom character.

    Collects the character sequence, category, and rank from standard input,
    registers the entry with ``CustomCharacter.add_char``, and -- if a config
    path is available -- persists the change to the TOML file via
    ``append_custom_char``. If no config path is provided, the registration
    applies only for the current session and is lost when the process exits.

    Input prompts:

    - **Sequence**: Non-empty string (e.g., ``"ts"``). Required; returns early
      if empty.
    - **Category**: Non-empty string, converted to uppercase (e.g.,
      ``"CONSONANT"``). Required; returns early if empty.
    - **Rank**: Integer (default ``1``). Non-integer input falls back to ``1``
      with a warning message.

    Args:
        config_path: Filesystem path to the active TOML language config, or
            ``None`` if no config was supplied at startup. When ``None``, the
            new character is registered in memory only.

    Returns:
        None
    """
    sequence = input("Sequence: ").strip()
    if not sequence:
        print("Sequence is required.")
        return

    category = input("Category (e.g., CONSONANT, VOWEL): ").strip().upper()
    if not category:
        print("Category is required.")
        return

    rank_input = input("Rank [1]: ").strip()
    rank = 1
    if rank_input:
        try:
            rank = int(rank_input)
        except ValueError:
            print("Rank must be an integer; using 1.")
            rank = 1

    CustomCharacter.add_char(sequence, category, rank=rank)

    if config_path:
        try:
            append_custom_char(config_path, sequence, category, rank)
            print(f"Saved to {config_path}")
        except (OSError, ValueError) as exc:
            print(f"Failed to update config: {exc}")
    else:
        print("No config path provided; change is session-only.")
