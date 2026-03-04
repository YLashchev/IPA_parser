"""Data processing pipeline for IPA phonological analysis.

This module transforms a raw Excel-derived ``DataFrame`` into a fully annotated
phonological dataset ready for statistical analysis. It is the computational
core of the ``ipa-parser`` package and is invoked from both the CLI batch mode
and the interactive menu (option 8).

Pipeline stages (in order as executed by ``build_final_dataframe``):

1. **Preprocessing** -- insert SP rows between sentences, assign pause labels.
2. **Word columns** -- expand word-level metadata (word number, word length by
   phoneme and syllable, word duration).
3. **Syllable columns** -- expand syllable-level metadata (syllable number,
   syllable length, syllable duration).
4. **Segment annotation** -- compute segment type (C/V/pause), coda complexity,
   and stress per syllable.
5. **Sentence metrics** -- sentence duration, sentence length by phoneme and
   syllable.
6. **ISI (Inter-Stress Interval) metrics** -- identify stressed syllable
   boundaries, compute interval durations with and without pauses, segment and
   syllable counts per interval, and pause classification.
7. **Finalization** -- remove pause rows, format ``WordNumber`` / ``SyllableNumber``
   labels, select ``FINAL_COLUMNS``, and optionally fill ``NA`` pause values.

Column constants:

- ``DEFAULT_COLUMNS``: Expected column names after loading the Excel file.
- ``FINAL_COLUMNS``: Ordered set of columns present in the returned DataFrame.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

import pandas as pd

from .ipa_char import CustomCharacter
from .ipa_string import IPAString


DEFAULT_COLUMNS = [
    "Filename",
    "Sentence",
    "Word",
    "Phoneme",
    "Begin",
    "End",
    "Duration (ms.)",
]

FINAL_COLUMNS = [
    "Filename",
    "Sentence",
    "WordNumber",
    "Word",
    "SyllableNumber",
    "Phoneme",
    "SegmentType",
    "CodaComplexity",
    "Stress",
    "SyllableLengthByPhoneme",
    "WordLengthByPhoneme",
    "SentenceLengthByPhoneme",
    "SentenceLengthBySyllable",
    "WordLengthBySyllable",
    "Begin",
    "End",
    "Duration (ms.)",
    "SyllableDuration",
    "WordDuration",
    "SentenceDuration",
    "InterStressDuration",
    "ISIDurationNoPause",
    "ISIPause",
    "ISIBySegment",
    "ISIBySyllable",
    "ISIByConsonant",
    "ISIByVowel",
    "OtherPauses",
    "SentencePauses",
]


def load_excel(file_path: str, columns: Iterable[str] = DEFAULT_COLUMNS) -> pd.DataFrame:
    """Load an Excel file and rename its columns to the standard pipeline schema.

    Reads the first sheet of the workbook using ``openpyxl`` and replaces the
    existing column headers with ``columns`` positionally. The length of
    ``columns`` must match the number of columns in the spreadsheet.

    Args:
        file_path: Filesystem path to the ``.xlsx`` input file.
        columns: An iterable of column name strings used to rename the
            DataFrame's columns in order. Defaults to ``DEFAULT_COLUMNS``::

                ["Filename", "Sentence", "Word", "Phoneme",
                 "Begin", "End", "Duration (ms.)"]

    Returns:
        A ``pandas.DataFrame`` with columns renamed according to ``columns``
        and rows corresponding to individual phoneme segments as they appear
        in the workbook.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
        ValueError: If the number of provided ``columns`` does not match the
            number of columns in the spreadsheet (propagated from pandas).
    """
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = list(columns)
    return df


def insert_sp(df: pd.DataFrame) -> pd.DataFrame:
    """Insert SP (sentence-pause) rows between sentences.

    Two different input formats are handled:

    - **NaN-delimited format**: If the ``Sentence`` column already contains
      ``NaN`` values (used as sentence separators), those rows are not removed;
      instead their ``Sentence`` values are filled with ``"SP"`` and the
      original ``DataFrame`` (copied) is returned.
    - **Contiguous-sentence format**: If there are no ``NaN`` values, an SP
      row is injected between every pair of consecutive rows that belong to
      different sentences. The injected row sets ``"Sentence"`` to ``"SP"``,
      ``"Duration (ms.)"`` to ``0``, and all other columns to ``"SP"``.

    Args:
        df: Input ``DataFrame`` with at least ``Sentence`` and
            ``Duration (ms.)`` columns.

    Returns:
        A new ``DataFrame`` (always a fresh object) with SP boundary rows
        inserted and the index reset to a contiguous integer range.
    """
    if df["Sentence"].isna().to_numpy().any():
        df = df.copy()
        df["Sentence"] = df["Sentence"].fillna("SP")
        return df

    rows = []
    for i in range(len(df) - 1):
        current_row = df.iloc[i].to_dict()
        next_row = df.iloc[i + 1].to_dict()

        rows.append(current_row)

        if current_row["Sentence"] != next_row["Sentence"]:
            sp_row = {"Sentence": "SP", "Duration (ms.)": 0}
            for key in current_row:
                if key not in sp_row:
                    sp_row[key] = "SP"
            rows.append(sp_row)

    rows.append(df.iloc[-1].to_dict())

    return pd.DataFrame(rows).reset_index(drop=True)


def assign_pauses(df: pd.DataFrame, phoneme_column: str = "Phoneme", word_column: str = "Word") -> None:
    """Overwrite the ``Word`` column with the pause label for pause-phoneme rows.

    For every row where the phoneme value is ``"OP"`` (other pause) or ``"SP"``
    (sentence pause), sets the corresponding ``Word`` cell to that same pause
    label. This ensures that downstream word-grouping logic treats pause rows
    as their own distinct "word" tokens rather than inheriting whatever word
    value was carried over from adjacent content rows.

    Modifies ``df`` in-place.

    Args:
        df: ``DataFrame`` to modify. Must contain the columns named by
            ``phoneme_column`` and ``word_column``.
        phoneme_column: Name of the column containing phoneme labels.
            Defaults to ``"Phoneme"``.
        word_column: Name of the column whose values will be overwritten for
            pause rows. Defaults to ``"Word"``.

    Returns:
        None
    """
    pause_mask = df[phoneme_column].isin(["OP", "SP"])
    df.loc[pause_mask, word_column] = df.loc[pause_mask, phoneme_column]


def get_word_list_and_indices(df: pd.DataFrame, word_column: str = "Word") -> tuple[list[str], list[int]]:
    """Extract the ordered unique word list and the DataFrame index of each word's first row.

    Iterates through the DataFrame in order and records each word string
    together with the DataFrame index of the row where that word first appears,
    skipping runs of identical consecutive values.

    Args:
        df: ``DataFrame`` with a column named ``word_column``. The ``Word``
            column should already have pause labels assigned (via
            ``assign_pauses``) before calling this function.
        word_column: Name of the column containing word labels.
            Defaults to ``"Word"``.

    Returns:
        A two-element tuple ``(unique_words, indices)`` where:

        - ``unique_words`` (list[str]): Ordered list of unique consecutive word
          strings (including ``"SP"`` and ``"OP"`` markers).
        - ``indices`` (list[int]): DataFrame index values of the first row
          belonging to each word in ``unique_words``. Has the same length as
          ``unique_words``.

        Returns ``([], [])`` for an empty DataFrame.
    """
    if df.empty:
        return [], []

    unique_words: list[str] = []
    indices: list[Any] = []
    last_word = None

    for idx, row in df.iterrows():
        word: str = str(row[word_column])
        if word != last_word:
            unique_words.append(word)
            indices.append(idx)
            last_word = word

    return unique_words, indices


def collapse_nested_list(nested_list: list) -> list:
    """Flatten a one-level-deep nested list into a single flat list.

    Iterates over ``nested_list``; elements that are themselves ``list``
    instances are extended into the output, while non-list elements are
    appended directly. Only one level of nesting is removed -- nested lists
    within nested lists are not recursively flattened.

    Args:
        nested_list: A list whose elements may be either plain values or
            inner lists of plain values.

    Returns:
        A new flat list containing all elements from ``nested_list`` in order,
        with one level of list wrapping removed.
    """
    return [
        element
        for item in nested_list
        for element in (item if isinstance(item, list) else [item])
    ]


def word_columns(original_word_list: list[str], geminate: bool = True) -> tuple[list, list, list]:
    """Expand each word into per-phoneme rows and compute word-level index columns.

    For each non-pause word, determines its phonological length via
    ``IPAString.total_length()`` and repeats word-level labels that many times
    so that one entry exists per phoneme segment. Pause markers (``"OP"``,
    ``"SP"``) contribute exactly one row each with no replication.

    The ``word_labels`` counter resets to ``1`` after each ``"SP"`` boundary,
    so it represents the within-sentence word position. The ``unique_idx``
    counter never resets and provides a corpus-wide unique word identifier.

    Args:
        original_word_list: Ordered list of unique consecutive words as
            returned by ``get_word_list_and_indices``, including pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A three-element tuple ``(repeated_word_list, word_labels, unique_idx)``
        where each element is a flat list of length equal to the total
        phonological token count across all words:

        - ``repeated_word_list``: Word string repeated for every phoneme
          belonging to that word (pause markers appear once).
        - ``word_labels``: Within-sentence 1-based word position index repeated
          per phoneme. Pause markers carry their pause label.
        - ``unique_idx``: Corpus-wide 1-based word position index repeated per
          phoneme. Pause markers carry their pause label.
    """
    j = 1
    repeated_word_list: list[Any] = []
    word_labels: list[Any] = []
    unique_idx: list[Any] = []
    i = 1
    for word in original_word_list:
        if word == "OP":
            repeated_word_list.append(word)
            word_labels.append(word)
            unique_idx.append(word)
        elif word == "SP":
            i = 0
            repeated_word_list.append(word)
            word_labels.append(word)
            unique_idx.append(word)
        else:
            phonological_length = IPAString(word, geminate=geminate).total_length()
            repeated_word_list.append([word] * phonological_length)
            word_labels.append([i] * phonological_length)
            unique_idx.append([j] * phonological_length)
        i += 1
        j += 1

    repeated_word_list = collapse_nested_list(repeated_word_list)
    word_labels = collapse_nested_list(word_labels)
    unique_idx = collapse_nested_list(unique_idx)

    return repeated_word_list, word_labels, unique_idx


def pre_syllable_columns(original_word_list: list[str], geminate: bool = True) -> list:
    """Build a list mapping each word to its syllable segments.

    For each non-pause word, retrieves the syllable breakdown from
    ``IPAString.syllables``. Pause markers (``"OP"``, ``"SP"``) are passed
    through unchanged as single-element entries. The result is a list parallel
    to ``original_word_list``, where each entry is either a pause string or the
    list of syllable strings for that word.

    This intermediate structure is consumed by ``syllable_columns`` and
    ``collapse_nested_list`` to produce per-phoneme syllable labels.

    Args:
        original_word_list: Ordered list of unique consecutive words including
            pause markers, as returned by ``get_word_list_and_indices``.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``original_word_list`` where each element
        is either a pause string (``"OP"`` or ``"SP"``) or a list of syllable
        strings for the corresponding word.
    """
    syllable_list: list[Any] = []

    for word in original_word_list:
        if word == "OP" or word == "SP":
            syllable_list.append(word)
        else:
            syllables = IPAString(word, geminate=geminate).syllables
            syllable_list.append(syllables)

    return syllable_list


def syllable_columns(original_syllable_list: list, geminate: bool = True) -> list:
    """Produce a per-phoneme syllable number list from the nested syllable structure.

    Iterates over the output of ``pre_syllable_columns``. For pause entries
    (``"OP"``, ``"SP"``), appends the pause string once. For each word's list
    of syllables, computes the phonological length of each syllable via
    ``IPAString.total_length()`` and appends the 1-based within-word syllable
    number that many times, yielding one entry per phoneme segment.

    Args:
        original_syllable_list: The nested list as returned by
            ``pre_syllable_columns``. Each element is either a pause string or
            a list of syllable strings.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A flat list where each element is either a pause string or a 1-based
        integer syllable number. The list length equals the total phonological
        token count across all words and pauses.
    """
    syllable_labels: list[int | str] = []

    for item in original_syllable_list:
        if item == "OP" or item == "SP":
            syllable_labels.append(item)
            continue

        syllable_count = 1
        for syllable in item:
            phonological_length = IPAString(syllable, geminate=geminate).total_length()
            syllable_labels.extend([syllable_count] * phonological_length)
            syllable_count += 1

    return syllable_labels


def segment_type(segments: list[str], geminate: bool = True) -> list:
    """Compute a per-phoneme segment type label (C, V, or pause) for each row.

    For each element in ``segments``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are stripped of non-character marks via
      ``IPAString.char_only()``, reparsed, and each resulting segment's
      category is looked up. ``"CONSONANT"`` maps to ``"C"``, ``"VOWEL"``
      maps to ``"V"``, and all other categories are kept as-is.

    The two-step parse (``char_only`` then re-parse) ensures that diacritics
    and suprasegmentals attached to the raw phoneme entry do not interfere with
    segment type classification.

    Args:
        segments: List of raw phoneme strings from the ``Phoneme`` column,
            including pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A flat list of segment type strings (``"C"``, ``"V"``, ``"OP"``,
        ``"SP"``, or other IPA category names) with one entry per phoneme
        token.
    """
    segment_type_list: list[Any] = []
    for segment in segments:
        if segment == "OP" or segment == "SP":
            segment_type_list.append(segment)
        else:
            temp = IPAString(segment, geminate=geminate).char_only()
            types = IPAString(temp, geminate=geminate).segment_type
            segment_type_list.append(types)

    temp = collapse_nested_list(segment_type_list)
    segment_type_column = [
        "C" if item == "CONSONANT" else "V" if item == "VOWEL" else item for item in temp
    ]
    return segment_type_column


def _apply_to_words(
    items: list[str],
    geminate: bool,
    getter: Callable[[IPAString], Any],
) -> list:
    """Apply a getter to each non-pause item while preserving pause markers."""
    result: list[Any] = []
    for item in items:
        if item == "OP" or item == "SP":
            result.append(item)
        else:
            result.append(getter(IPAString(item, geminate=geminate)))
    return result


def coda_column(syllable_list_flat: list[str], geminate: bool = True) -> list:
    """Compute the coda complexity value for each syllable token.

    For each element in ``syllable_list_flat``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are parsed by ``IPAString`` and their ``coda``
      attribute is appended.

    Args:
        syllable_list_flat: Flat list of syllable strings (one per phoneme
            position) as produced by the syllable expansion step in
            ``build_final_dataframe``. Includes pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``syllable_list_flat`` where each element
        is either a pause string or an integer coda complexity value.
    """
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.coda)


def stress_column(syllable_list_flat: list[str], geminate: bool = True) -> list:
    """Compute the stress classification for each syllable token.

    For each element in ``syllable_list_flat``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are parsed by ``IPAString`` and their ``stress()``
      result is appended (e.g., ``"STRESSED"``, ``"STRESSED_2"``,
      ``"UNSTRESSED"``).

    Args:
        syllable_list_flat: Flat list of syllable strings (one per phoneme
            position) as produced by the syllable expansion step in
            ``build_final_dataframe``. Includes pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``syllable_list_flat`` where each element
        is either a pause string or a stress label string.
    """
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.stress())


def syllable_length_by_phoneme(syllable_list_flat: list[str], geminate: bool = True) -> list:
    """Compute the phonological length of the syllable for each phoneme position.

    For each element in ``syllable_list_flat``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are parsed by ``IPAString`` and their
      ``total_length()`` is appended, giving the number of phonologically
      weighted segments in that syllable.

    Args:
        syllable_list_flat: Flat list of syllable strings (one per phoneme
            position) as produced by the syllable expansion step in
            ``build_final_dataframe``. Includes pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``syllable_list_flat`` where each element
        is either a pause string or an integer phonological length.
    """
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.total_length())


def word_length_by_phoneme(repeated_word_list: list[str], geminate: bool = True) -> list:
    """Compute the phonological length of each word, repeated per phoneme position.

    For each element in ``repeated_word_list``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are parsed by ``IPAString`` and their
      ``total_length()`` is appended, giving the total number of
      phonologically weighted segments in the whole word.

    Because ``repeated_word_list`` already repeats the word string for every
    phoneme it contains (see ``word_columns``), the result is a column where
    every row belonging to a given word holds that word's total phonological
    length.

    Args:
        repeated_word_list: Flat list of word strings (one entry per phoneme
            position), as returned by ``word_columns``. Includes pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``repeated_word_list`` where each element
        is either a pause string or an integer phonological word length.
    """
    return _apply_to_words(repeated_word_list, geminate, lambda ipa: ipa.total_length())


def word_length_by_syllable(repeated_word_list: list[str], geminate: bool = True) -> list:
    """Compute the syllable count of each word, repeated per phoneme position.

    For each element in ``repeated_word_list``:

    - Pause markers (``"OP"``, ``"SP"``) are passed through unchanged.
    - All other values are parsed by ``IPAString`` and the length of their
      ``syllables`` list is appended.

    Because ``repeated_word_list`` already repeats the word string once per
    phoneme, the result is a column where every row belonging to a given word
    holds that word's syllable count.

    Args:
        repeated_word_list: Flat list of word strings (one entry per phoneme
            position), as returned by ``word_columns``. Includes pause markers.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of the same length as ``repeated_word_list`` where each element
        is either a pause string or an integer syllable count.
    """
    return _apply_to_words(repeated_word_list, geminate, lambda ipa: len(ipa.syllables))


def sentence_duration(df: pd.DataFrame) -> list:
    """Compute the total acoustic duration of each sentence, repeated per phoneme.

    Iterates over the DataFrame rows using the ``Word`` and ``Duration (ms.)``
    columns. Accumulates durations until an ``"SP"`` boundary is encountered,
    at which point the running sum is broadcast across all rows belonging to
    that sentence and the accumulator resets. Any trailing phonemes after the
    last ``"SP"`` boundary are handled as a final sentence.

    The ``"SP"`` row itself is appended to the output as its own entry (using
    the string ``"SP"`` rather than a duration value) unless it is the very
    last row of the DataFrame.

    Args:
        df: ``DataFrame`` with at least ``Word`` and ``Duration (ms.)``
            columns, including SP boundary rows.

    Returns:
        A flat list of the same length as the DataFrame where each element is
        either a float sentence-total duration (for content rows) or ``"SP"``
        (for sentence-boundary rows).
    """
    sentence_unique_durations: list[Any] = []
    sentence_duration_value = 0.0
    counter = 0
    for index, (duration, word) in enumerate(
        zip(df["Duration (ms.)"].tolist(), df["Word"].tolist())
    ):
        if word == "SP" and counter > 0:
            sentence_unique_durations.append([sentence_duration_value] * counter)
            if index != len(df["Word"]) - 1:
                sentence_unique_durations.append(word)
            sentence_duration_value = 0
            counter = 0
        else:
            duration_value = duration
            sentence_duration_value += duration_value
            counter += 1
    if counter > 0:
        sentence_unique_durations.extend([sentence_duration_value] * counter)

    return collapse_nested_list(sentence_unique_durations)


def process_durations(df: pd.DataFrame, unique_list: str) -> list:
    """Sum and broadcast durations for each unique group (word or syllable).

    Groups consecutive rows that share the same value in the ``unique_list``
    column, sums their ``Duration (ms.)`` values, and writes that total back
    to every row in the group. Pause rows (``"OP"`` or ``"SP"`` in
    ``unique_list``) are not grouped; their individual duration is written
    directly and any in-progress group is finalized first.

    This function is used twice in ``build_final_dataframe``:

    - With ``"unique_word_idx"`` to produce ``WordDuration``.
    - With ``"unique_syll_idx"`` to produce ``SyllableDuration``.

    Args:
        df: ``DataFrame`` with at least a ``Duration (ms.)`` column and the
            column named by ``unique_list``.
        unique_list: Name of the column whose values identify the grouping
            unit (e.g., ``"unique_word_idx"`` or ``"unique_syll_idx"``).

    Returns:
        A list of the same length as ``df`` where each element holds the
        summed duration for the group that row belongs to (or the individual
        duration for pause rows).
    """
    durations_output: list[Any] = []

    current_word = None
    current_sum = 0
    current_count = 0

    for _, row in df.iterrows():
        idx_number = row[unique_list]
        duration = row["Duration (ms.)"]

        if idx_number == "OP" or idx_number == "SP":
            if current_word is not None:
                durations_output.extend([current_sum] * current_count)
                current_word = None
                current_sum = 0
                current_count = 0
            durations_output.append(duration)
            continue

        if current_word == idx_number:
            current_sum += duration
            current_count += 1
        else:
            if current_word is not None:
                durations_output.extend([current_sum] * current_count)
            current_word = idx_number
            current_sum = duration
            current_count = 1

    if current_word is not None:
        durations_output.extend([current_sum] * current_count)

    return durations_output


def by_sentence_count(syllable_indices: list) -> tuple[list, list]:
    """Compute per-sentence phoneme and syllable length, broadcast per phoneme position.

    Splits ``syllable_indices`` into per-sentence segments at ``"SP"``
    boundaries. For each sentence segment, computes:

    - **Phoneme length**: total number of non-``"OP"`` entries in the segment.
    - **Syllable length**: number of unique syllable indices (excluding ``"OP"``
      entries) plus the count of ``"OP"`` entries (other-pause tokens each
      count as one unit).

    Both values are broadcast across all rows of that sentence. An ``"SP"``
    string is inserted between sentences to maintain alignment with the
    full-length DataFrame (the final sentence receives no trailing ``"SP"``).

    Args:
        syllable_indices: Flat list of unique syllable index values (one per
            phoneme position), as built during the syllable expansion stage.
            ``"SP"`` marks sentence boundaries; ``"OP"`` marks other pauses.

    Returns:
        A two-element tuple ``(sentence_length_by_phoneme, sentence_length_by_syllable)``
        where each is a list of the same length as ``syllable_indices`` (plus
        inter-sentence ``"SP"`` separators). Each element is either an integer
        length value or the string ``"SP"``.
    """
    splits: list[list[Any]] = []
    current_split: list[Any] = []

    for idx in syllable_indices:
        if idx == "SP":
            if current_split:
                splits.append(current_split)
            current_split = []
        else:
            current_split.append(idx)

    if current_split:
        splits.append(current_split)

    sentence_length_by_phoneme_repeated: list[int | str] = []
    sentence_length_by_syllable_repeated: list[int | str] = []

    for i, split in enumerate(splits):
        phoneme_length = len(split)
        syllable_length = len(set(idx for idx in split if idx != "OP"))

        op_count = split.count("OP")
        syllable_length += op_count

        sentence_length_by_phoneme_repeated.extend(
            [phoneme_length - split.count("OP")] * phoneme_length
        )
        sentence_length_by_syllable_repeated.extend(
            [syllable_length - split.count("OP")] * phoneme_length
        )

        if i < len(splits) - 1:
            sentence_length_by_phoneme_repeated.append("SP")
            sentence_length_by_syllable_repeated.append("SP")

    return sentence_length_by_phoneme_repeated, sentence_length_by_syllable_repeated


def create_isi_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """Annotate the DataFrame with ISI block boundaries based on stressed syllables.

    Adds a boolean ``new_block`` column to ``df``. A row is marked
    ``True`` (i.e., starts a new ISI block) when:

    - It carries a ``"STRESSED"`` or ``"STRESSED_2"`` stress label AND its
      ``unique_syll_idx`` differs from the preceding row (i.e., it is the
      first phoneme of a new stressed syllable).
    - It is the very first row and that row itself is stressed.

    A zero-duration ``"SP"`` row resets the ``encountered_stressed_syllable``
    flag; if the row immediately following that SP is stressed, it is also
    marked as a new block.

    Modifies ``df`` in-place and returns it.

    Args:
        df: ``DataFrame`` that must already contain ``Stress``,
            ``unique_syll_idx``, ``Duration (ms.)``, and ``syllables``
            columns, as assembled during ``build_final_dataframe``.

    Returns:
        The same ``DataFrame`` with a ``new_block`` boolean column added.
    """
    df["new_block"] = False
    encountered_stressed_syllable = False

    for i in range(1, len(df)):
        curr_stress = df.at[i, "Stress"]
        prev_syll_idx = df.at[i - 1, "unique_syll_idx"]
        curr_syll_idx = df.at[i, "unique_syll_idx"]
        curr_duration = df.at[i, "Duration (ms.)"]

        if curr_stress in ["STRESSED", "STRESSED_2"]:
            encountered_stressed_syllable = True

        if encountered_stressed_syllable and (
            (curr_stress in ["STRESSED", "STRESSED_2"]) and curr_syll_idx != prev_syll_idx
        ):
            df.at[i, "new_block"] = True
        elif curr_syll_idx == "SP" and curr_duration == 0:
            encountered_stressed_syllable = False
            if (i + 1 < len(df)) and (df.at[i + 1, "Stress"] in ["STRESSED", "STRESSED_2"]):
                df.at[i + 1, "new_block"] = True
        else:
            df.at[i, "new_block"] = False

    df.at[0, "new_block"] = df.at[0, "Stress"] in ["STRESSED", "STRESSED_2"]

    return df


def get_isi_idx(df: pd.DataFrame) -> list[int]:
    """Return the DataFrame row indices where ISI blocks begin.

    Delegates to ``create_isi_blocks`` to compute the ``new_block`` column,
    then collects the integer positions of all rows marked ``True``. A
    sentinel value equal to ``len(df)`` is appended to simplify downstream
    slice arithmetic (so every start index has a paired end index).

    Args:
        df: ``DataFrame`` with the columns required by ``create_isi_blocks``.

    Returns:
        A list of integer row indices (0-based positions in ``df``) at which
        new ISI blocks start, with ``len(df)`` appended as a terminal
        sentinel.
    """
    df = create_isi_blocks(df)
    isi_idx = [int(i) for i in df.index[df["new_block"]].tolist()]
    isi_idx.append(len(df))
    return isi_idx


def calculate_interstress_duration(
    df: pd.DataFrame, isi_idx: list[int], summed_col_name: str = "", excluded_words: set | None = None
) -> pd.DataFrame:
    """Sum and broadcast ``Duration (ms.)`` over each ISI block into a new column.

    For each ISI block defined by consecutive pairs in ``isi_idx``, sums the
    ``Duration (ms.)`` values of all rows in that block (optionally excluding
    rows whose ``Word`` value appears in ``excluded_words``) and writes that
    sum to every row in the block under the column named ``summed_col_name``.

    Called twice in ``build_final_dataframe``:

    - As ``"InterStressDuration"`` with ``excluded_words=None`` (all rows
      included).
    - As ``"ISIDurationNoPause"`` with ``excluded_words={"OP", "SP"}``
      (pause rows excluded from the sum).

    The column is initialized from ``SyllableDuration`` before block sums are
    written, ensuring rows that fall outside any ISI block retain a sensible
    default.

    Args:
        df: ``DataFrame`` with ``Duration (ms.)``, ``Word``, and
            ``SyllableDuration`` columns.
        isi_idx: List of block-start row indices as returned by
            ``get_isi_idx``, with a terminal sentinel equal to ``len(df)``.
            The sentinel is handled by the loop's ``range_end`` fallback.
        summed_col_name: Name of the output column to create or overwrite.
        excluded_words: Optional set of ``Word`` values whose rows should be
            excluded from the duration sum (but still receive the block sum
            in the output column). Defaults to ``None`` (no exclusion).

    Returns:
        The same ``DataFrame`` with ``summed_col_name`` added or updated.
    """
    df[summed_col_name] = df["SyllableDuration"]

    for start, end in zip(isi_idx, isi_idx[1:] + [None]):
        range_end = end or len(df)

        df_slice = df[start:range_end]

        if excluded_words:
            word_series = pd.Series(df_slice["Word"])
            sum_duration = df_slice.loc[
                ~word_series.isin(list(excluded_words)), "Duration (ms.)"
            ].sum()
        else:
            sum_duration = df_slice["Duration (ms.)"].sum()

        df.loc[start : range_end - 1, summed_col_name] = sum_duration

    return df


def ISI_Pause(df: pd.DataFrame, isi_idx: list[int]) -> pd.DataFrame:
    """Classify whether each ISI block contains a pause.

    Adds an ``ISIPause`` column to ``df``. For each ISI block, compares
    ``InterStressDuration`` (which includes pause durations) with
    ``ISIDurationNoPause`` (which excludes them). If they differ, the block
    contains at least one pause:

    - ``"yes(SP)"`` -- the block contains a sentence-pause (``"SP"`` in the
      ``syllables`` column).
    - ``"yes"`` -- the block contains a pause of another type.
    - ``"No"`` -- no pause detected.

    Args:
        df: ``DataFrame`` with ``InterStressDuration``, ``ISIDurationNoPause``,
            and ``syllables`` columns, and ``isi_idx``-aligned rows.
        isi_idx: List of block-start row indices as returned by
            ``get_isi_idx``, with a terminal sentinel equal to ``len(df)``.

    Returns:
        The same ``DataFrame`` with the ``ISIPause`` column added.
    """
    df["ISIPause"] = "No"

    for start, end in zip(isi_idx, isi_idx[1:] + [None]):
        range_end = end if end is not None else len(df)
        df_slice = df.iloc[start:range_end]

        difference = df_slice["InterStressDuration"] != df_slice["ISIDurationNoPause"]

        if difference.any():
            if "SP" in df_slice["syllables"].values:
                df.loc[start : range_end - 1, "ISIPause"] = "yes(SP)"
            else:
                df.loc[start : range_end - 1, "ISIPause"] = "yes"

    return df


def ISI_By_Segment(df: pd.DataFrame, isi_idx: list[int], segment_col: str = "SegmentType") -> tuple[list, list, list]:
    """Count consonants and vowels in each ISI interval, broadcast per row.

    Divides the DataFrame into intervals using ``[0] + isi_idx`` as
    boundaries, so the first interval covers rows before the first stressed
    syllable. For each interval, counts the number of rows with
    ``SegmentType == "C"`` and ``"V"`` separately, then broadcasts those
    counts across all rows in the interval.

    Args:
        df: ``DataFrame`` with a segment type column named by ``segment_col``.
        isi_idx: List of block-start row indices as returned by
            ``get_isi_idx``, with a terminal sentinel equal to ``len(df)``.
        segment_col: Name of the column containing ``"C"`` / ``"V"`` labels.
            Defaults to ``"SegmentType"``.

    Returns:
        A three-element tuple ``(ISI_segment_count, ISI_consonant_count, ISI_vowel_count)``
        where each is a list of the same length as ``df``:

        - ``ISI_segment_count``: Total phoneme count (consonants + vowels) per
          interval, repeated for each row.
        - ``ISI_consonant_count``: Consonant count per interval, repeated.
        - ``ISI_vowel_count``: Vowel count per interval, repeated.
    """
    intervals = [0] + list(isi_idx)
    ISI_consonant_count = []
    ISI_vowel_count = []

    for start, end in zip(intervals, intervals[1:] + [None]):
        range_end = end if end is not None else len(df)
        df_slice = df.iloc[start:range_end]

        consonant_count = (df_slice[segment_col] == "C").sum()
        vowel_count = (df_slice[segment_col] == "V").sum()

        interval_length = range_end - start

        ISI_consonant_count.extend([consonant_count] * interval_length)
        ISI_vowel_count.extend([vowel_count] * interval_length)

    ISI_segment_count = [x + y for x, y in zip(ISI_consonant_count, ISI_vowel_count)]

    return ISI_segment_count, ISI_consonant_count, ISI_vowel_count


def ISI_By_Syllable(
    df: pd.DataFrame, intervals: list[int], unique_syll_col: str = "unique_syll_idx", word_column: str = "Word"
) -> list:
    """Count unique syllables in each ISI interval, broadcast per row.

    Divides the DataFrame into intervals using ``[0] + intervals`` as
    boundaries. For each interval, counts the number of distinct values in
    ``unique_syll_col``, excluding rows whose ``word_column`` value is
    ``"SP"`` or ``"OP"``. The count is broadcast across all rows in the
    interval.

    Args:
        df: ``DataFrame`` with the columns named by ``unique_syll_col`` and
            ``word_column``.
        intervals: List of block-start row indices as returned by
            ``get_isi_idx``, with a terminal sentinel equal to ``len(df)``.
        unique_syll_col: Name of the column holding unique syllable index
            values. Defaults to ``"unique_syll_idx"``.
        word_column: Name of the column used to filter out pause rows.
            Defaults to ``"Word"``.

    Returns:
        A list of the same length as ``df`` where each element is an integer
        count of unique syllables in the ISI interval that row belongs to.
    """
    intervals = [0] + list(intervals)
    repeated_syllable_counts = []

    for start, end in zip(intervals, intervals[1:] + [None]):
        range_end = end if end is not None else len(df)
        df_slice = df.iloc[start:range_end]

        unique_syllables = set(df_slice[~df_slice[word_column].isin(["SP", "OP"])][unique_syll_col])
        unique_syllable_count = len(unique_syllables)

        repeated_syllable_counts.extend([unique_syllable_count] * (range_end - start))

    return repeated_syllable_counts


def fill_pause_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Propagate the most recent pause duration backwards into content rows.

    Adds two columns to ``df``:

    - ``OtherPauses``: For each content row, holds the duration of the next
      ``"OP"`` (other pause) row encountered when scanning forward (i.e.,
      looking backwards from the end). Resets to ``pd.NA`` after each ``"SP"``
      boundary.
    - ``SentencePauses``: For each content row, holds the duration of the next
      ``"SP"`` (sentence pause) row encountered when scanning forward, but only
      if that SP duration is greater than zero (zero-duration SPs are treated
      as ``pd.NA``).

    The scan proceeds from the last row to the first (reverse iteration) so
    that each content row naturally inherits the duration of the pause that
    follows it. ``"SP"`` rows themselves also receive their own duration in
    ``SentencePauses`` (or ``pd.NA`` if zero-duration).

    Modifies ``df`` in-place and returns it.

    Args:
        df: ``DataFrame`` with ``Word`` and ``Duration (ms.)`` columns.

    Returns:
        The same ``DataFrame`` with ``OtherPauses`` and ``SentencePauses``
        columns added.
    """
    df["OtherPauses"] = pd.NA
    df["SentencePauses"] = pd.NA

    last_op_duration = pd.NA
    last_sp_duration = pd.NA

    for i in range(len(df) - 1, -1, -1):
        word = df.at[i, "Word"]
        duration = df.at[i, "Duration (ms.)"]

        if word == "OP":
            last_op_duration = duration
        elif word == "SP":
            last_sp_duration = duration if duration > 0 else pd.NA
            last_op_duration = pd.NA

        if pd.notna(last_op_duration):
            df.at[i, "OtherPauses"] = last_op_duration

        if pd.notna(last_sp_duration):
            df.at[i, "SentencePauses"] = last_sp_duration

    df.loc[df["Word"] == "SP", "SentencePauses"] = df.loc[
        df["Word"] == "SP", "Duration (ms.)"
    ].where(df.loc[df["Word"] == "SP", "Duration (ms.)"] > 0, pd.NA)

    return df


def find_mismatches_with_phoneme_alignment(
    df: pd.DataFrame,
    original_word_list: list[str],
    word_start_indices: list[int],
    phoneme_column: str = "Phoneme",
    geminate: bool = True,
) -> list[tuple[int, str]]:
    """Detect words whose phoneme rows do not concatenate to match the word string.

    For each word in ``original_word_list``, concatenates the ``char_only()``
    forms of all phoneme entries belonging to that word (identified by the
    slice ``[word_start_indices[i] : word_start_indices[i+1]]``) and compares
    the result with the ``char_only()`` form of the word string itself. Any
    discrepancy is recorded as a mismatch, which may indicate segmentation
    errors or transcription inconsistencies in the input data.

    Row numbers reported in mismatches are 1-based and offset by 2 to account
    for the header row and 0-to-1 index conversion (i.e.,
    ``start_idx + 2`` is the Excel row number of the first phoneme row for
    that word).

    Args:
        df: ``DataFrame`` whose rows contain individual phoneme segments. The
            index must be a contiguous integer range starting from 0.
        original_word_list: Ordered list of unique consecutive words as
            returned by ``get_word_list_and_indices``.
        word_start_indices: DataFrame index positions of each word's first row,
            as returned by ``get_word_list_and_indices``.
        phoneme_column: Name of the column containing raw phoneme strings.
            Defaults to ``"Phoneme"``.
        geminate: Whether geminate consonant handling is enabled. Passed to
            each ``IPAString`` constructor.

    Returns:
        A list of ``(row_number, word)`` tuples for every word where the
        concatenated phoneme characters do not match the word's canonical
        character-only form. Returns an empty list if all words align
        correctly.
    """
    mismatches = []
    num_words = len(original_word_list)

    for i in range(num_words):
        word = original_word_list[i]
        start_idx = word_start_indices[i]
        end_idx = word_start_indices[i + 1] if i + 1 < num_words else len(df)

        concatenated_phoneme = "".join(
            [
                IPAString(df.at[idx, phoneme_column].strip(), geminate=geminate).char_only()
                for idx in range(start_idx, end_idx)
            ]
        )

        if IPAString(word.strip(), geminate=geminate).char_only() != concatenated_phoneme:
            mismatches.append((start_idx + 2, word))

    return mismatches


def remove_pause_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop all pause rows (``"OP"`` and ``"SP"``) from the DataFrame.

    Identifies rows where the ``Word`` column is ``"OP"`` or ``"SP"``, drops
    them, and resets the index to a contiguous integer range. This step is
    performed at the end of ``build_final_dataframe`` after all ISI and pause
    metrics have been computed, so that the final output contains only content
    (phoneme) rows.

    Args:
        df: ``DataFrame`` with a ``Word`` column. Must have a default integer
            index.

    Returns:
        A new ``DataFrame`` with all ``"OP"`` and ``"SP"`` rows removed and
        the index reset.
    """
    op_sp_indices = df.index[df["Word"].isin(["OP", "SP"])].tolist()
    df_cleaned = df.drop(op_sp_indices).reset_index(drop=True)

    return df_cleaned


def build_final_dataframe(
    df: pd.DataFrame,
    geminate: bool = True,
    fill_na: bool = True,
) -> tuple[pd.DataFrame, list[tuple[int, str]]]:
    """Execute the complete IPA phonological processing pipeline.

    Transforms the raw input ``DataFrame`` into a fully annotated output
    ``DataFrame`` containing all word, syllable, segment, sentence, and ISI
    metrics. The pipeline proceeds through the following stages in order:

    1. Copy the input to avoid mutating the caller's DataFrame.
    2. Insert SP boundary rows (``insert_sp``) and assign pause labels
       (``assign_pauses``).
    3. Build the unique word list and detect phoneme-alignment mismatches.
    4. Expand word-level columns: ``WordNumber``, ``WordLengthByPhoneme``,
       ``WordLengthBySyllable``, ``WordDuration``.
    5. Expand syllable-level columns: ``SyllableNumber``,
       ``SyllableLengthByPhoneme``, ``SyllableDuration``.
    6. Annotate segments: ``SegmentType``, ``CodaComplexity``, ``Stress``.
    7. Compute sentence metrics: ``SentenceDuration``,
       ``SentenceLengthByPhoneme``, ``SentenceLengthBySyllable``.
    8. Compute ISI metrics: ``InterStressDuration``, ``ISIDurationNoPause``,
       ``ISIPause``, ``ISIBySegment``, ``ISIByConsonant``, ``ISIByVowel``,
       ``ISIBySyllable``.
    9. Fill pause look-ahead columns: ``OtherPauses``, ``SentencePauses``.
    10. Remove pause rows, format ``WordNumber`` / ``SyllableNumber`` labels,
        select ``FINAL_COLUMNS``, and optionally fill ``NA`` pause values with
        the string ``"N/A"``.

    Args:
        df: Raw input ``DataFrame`` as returned by ``load_excel``. Must
            contain the columns defined in ``DEFAULT_COLUMNS``.
        geminate: Whether geminate consonant handling is enabled throughout
            the pipeline. Defaults to ``True``.
        fill_na: When ``True``, ``pd.NA`` values in ``OtherPauses`` and
            ``SentencePauses`` are replaced with the string ``"N/A"`` before
            returning. Defaults to ``True``.

    Returns:
        A two-element tuple ``(final_df, mismatches)`` where:

        - ``final_df`` (``pd.DataFrame``): Fully annotated output DataFrame
          containing only the columns listed in ``FINAL_COLUMNS``, with pause
          rows removed. Column order matches ``FINAL_COLUMNS``.
        - ``mismatches`` (list[tuple[int, str]]): List of
          ``(excel_row_number, word)`` pairs for words whose phoneme rows do
          not align with the word string. Empty if all words are consistent.
    """
    df = df.copy()

    df = insert_sp(df)
    assign_pauses(df)

    original_word_list, word_start_indices = get_word_list_and_indices(df)
    mismatches = find_mismatches_with_phoneme_alignment(
        df, original_word_list, word_start_indices, geminate=geminate
    )
    repeated_word_list, word_labels, unique_word_idx = word_columns(
        original_word_list, geminate=geminate
    )

    df["WordLengthByPhoneme"] = word_length_by_phoneme(repeated_word_list, geminate=geminate)
    df["WordLengthBySyllable"] = word_length_by_syllable(repeated_word_list, geminate=geminate)
    df["WordNumber"] = word_labels
    df["unique_word_idx"] = unique_word_idx

    df["WordDuration"] = process_durations(df, "unique_word_idx")

    syllable_list = pre_syllable_columns(original_word_list, geminate=geminate)
    syllable_column_flat = collapse_nested_list(syllable_list)
    syllable_list_flat, _, unique_syll_idx = word_columns(
        syllable_column_flat, geminate=geminate
    )
    syllable_labels = syllable_columns(syllable_list, geminate=geminate)

    df["SyllableLengthByPhoneme"] = syllable_length_by_phoneme(
        syllable_list_flat, geminate=geminate
    )
    df["syllables"] = syllable_list_flat
    df["SyllableNumber"] = syllable_labels
    df["unique_syll_idx"] = unique_syll_idx
    df["SyllableDuration"] = process_durations(df, "unique_syll_idx")

    segment_type_column = segment_type(df["Phoneme"].tolist(), geminate=geminate)
    df["SegmentType"] = segment_type_column

    df["SentenceDuration"] = sentence_duration(df)
    sentence_length_by_phoneme, sentence_length_by_syllable = by_sentence_count(unique_syll_idx)
    df["SentenceLengthByPhoneme"] = sentence_length_by_phoneme
    df["SentenceLengthBySyllable"] = sentence_length_by_syllable

    df["CodaComplexity"] = coda_column(syllable_list_flat, geminate=geminate)
    df["Stress"] = stress_column(syllable_list_flat, geminate=geminate)

    isi_idx = get_isi_idx(df)
    df = calculate_interstress_duration(df, isi_idx, "InterStressDuration", excluded_words=None)
    df = calculate_interstress_duration(
        df, isi_idx, "ISIDurationNoPause", excluded_words={"OP", "SP"}
    )
    df = ISI_Pause(df, isi_idx)

    by_segment, by_consonant, by_vowel = ISI_By_Segment(df, isi_idx)
    ISIBySyllable = ISI_By_Syllable(df, isi_idx)

    df["ISIBySyllable"] = ISIBySyllable
    df["ISIBySegment"] = by_segment
    df["ISIByConsonant"] = by_consonant
    df["ISIByVowel"] = by_vowel

    df = fill_pause_columns(df)
    df = remove_pause_rows(df)
    df["WordNumber"] = ["W" + str(i) for i in df["WordNumber"]]
    df["SyllableNumber"] = ["SYLL" + str(i) for i in df["SyllableNumber"]]

    final_df = pd.DataFrame(df.loc[:, FINAL_COLUMNS].copy())
    if fill_na:
        pause_df = final_df.loc[:, ["OtherPauses", "SentencePauses"]]
        final_df.loc[:, ["OtherPauses", "SentencePauses"]] = pause_df.fillna("N/A")

    return final_df, mismatches


def configure_custom_characters(custom_chars: list[tuple[str, str, int]]) -> None:
    """Reset the registry and register ``custom_chars`` in order.

    Args:
        custom_chars: List of ``(sequence, category, rank)`` triples to register.
    """
    CustomCharacter.clear_all_chars()
    for sequence, category, rank in custom_chars:
        CustomCharacter.add_char(sequence, category, rank=rank)
