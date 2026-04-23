"""Pipeline helpers for turning aligned IPA data into analysis tables."""

from __future__ import annotations

from typing import Any, Callable, Iterable, cast

import pandas as pd

from .debug import LengthMismatchError
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
    """Load an Excel sheet and rename its columns to the pipeline schema."""
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = list(columns)
    return df


def insert_sp(df: pd.DataFrame) -> pd.DataFrame:
    """Insert sentence-pause rows between sentence boundaries."""
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


def assign_pauses(
    df: pd.DataFrame, phoneme_column: str = "Phoneme", word_column: str = "Word"
) -> None:
    """Copy pause labels from the phoneme column into the word column."""
    pause_mask = df[phoneme_column].isin(["OP", "SP"])
    df.loc[pause_mask, word_column] = df.loc[pause_mask, phoneme_column]


def get_word_list_and_indices(
    df: pd.DataFrame, word_column: str = "Word"
) -> tuple[list[str], list[int]]:
    """Return unique consecutive words and their first row indices."""
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
    """Flatten a list by one nesting level."""
    return [
        element for item in nested_list for element in (item if isinstance(item, list) else [item])
    ]


def word_columns(original_word_list: list[str], geminate: bool = True) -> tuple[list, list, list]:
    """Expand each word into per-phoneme rows; return (words, word_labels, unique_idx).

    word_labels reset to 1 after each SP boundary (within-sentence position).
    unique_idx never resets (corpus-wide word identifier).
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
            phonological_length = cast(int, IPAString(word, geminate=False).total_length())
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
    """Map each word to its syllable list; pauses pass through as strings."""
    syllable_list: list[Any] = []

    for word in original_word_list:
        if word == "OP" or word == "SP":
            syllable_list.append(word)
        else:
            syllables = IPAString(word, geminate=geminate).syllables
            syllable_list.append(syllables)

    return syllable_list


def syllable_columns(original_syllable_list: list, geminate: bool = True) -> list:
    """Produce per-phoneme 1-based syllable number list from nested syllable structure."""
    syllable_labels: list[int | str] = []

    for item in original_syllable_list:
        if item == "OP" or item == "SP":
            syllable_labels.append(item)
            continue

        syllable_count = 1
        for syllable in item:
            phonological_length = cast(int, IPAString(syllable, geminate=False).total_length())
            syllable_labels.extend([syllable_count] * phonological_length)
            syllable_count += 1

    return syllable_labels


def segment_type(segments: list[str], geminate: bool = True) -> list:
    """Compute per-phoneme segment type (C, V, or pause) for each row."""
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
        "C"
        if item in ("CONSONANT", "AFFRICATE")
        else "V"
        if item in ("VOWEL", "DIPHTHONG")
        else item
        for item in temp
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
    """Compute coda complexity for each syllable token."""
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.coda)


def stress_column(syllable_list_flat: list[str], geminate: bool = True) -> list:
    """Compute stress classification for each syllable token."""
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.stress())


def syllable_length_by_phoneme(syllable_list_flat: list[str], geminate: bool = True) -> list:
    """Phonological length of each syllable, repeated per phoneme position."""
    return _apply_to_words(syllable_list_flat, geminate, lambda ipa: ipa.total_length())


def word_length_by_phoneme(repeated_word_list: list[str], geminate: bool = True) -> list:
    """Phonological length of each word, repeated per phoneme position."""
    return _apply_to_words(repeated_word_list, geminate, lambda ipa: ipa.total_length())


def word_length_by_syllable(repeated_word_list: list[str], geminate: bool = True) -> list:
    """Syllable count of each word, repeated per phoneme position."""
    return _apply_to_words(repeated_word_list, geminate, lambda ipa: len(ipa.syllables))


def sentence_duration(df: pd.DataFrame) -> list:
    """Total acoustic duration of each sentence, broadcast per phoneme row."""
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
    """Sum and broadcast durations for each unique word/syllable group."""
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
    """Per-sentence phoneme and syllable length, broadcast per phoneme position."""
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
    """Annotate DataFrame with ISI block boundaries based on stressed syllables."""
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
    """Return row indices where ISI blocks begin, with len(df) as sentinel."""
    df = create_isi_blocks(df)
    isi_idx = [int(i) for i in df.index[df["new_block"]].tolist()]
    isi_idx.append(len(df))
    return isi_idx


def calculate_interstress_duration(
    df: pd.DataFrame,
    isi_idx: list[int],
    summed_col_name: str = "",
    excluded_words: set | None = None,
) -> pd.DataFrame:
    """Sum and broadcast Duration over each ISI block into summed_col_name."""
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
    """Classify whether each ISI block contains a pause (yes/yes(SP)/No)."""
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


def ISI_By_Segment(
    df: pd.DataFrame, isi_idx: list[int], segment_col: str = "SegmentType"
) -> tuple[list, list, list]:
    """Count C and V segments per ISI interval, broadcast per row."""
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
    df: pd.DataFrame,
    intervals: list[int],
    unique_syll_col: str = "unique_syll_idx",
    word_column: str = "Word",
) -> list:
    """Count unique syllables per ISI interval, broadcast per row."""
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
    """Propagate the next OP/SP duration backwards into content rows."""
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


def _suggest_custom_registration(word: str, geminate: bool) -> str | None:
    """If the word contains modifier letters attached to bases, suggest
    registering the base+modifier as a custom character.

    Returns a hint string or ``None`` if no suggestion applies.
    """
    import unicodedata

    segs = IPAString(word, geminate=geminate).segments
    # Stress/length modifiers precede a base so they segment BEFORE a base,
    # not after. Skip those specific known-harmless codepoints explicitly.
    skip = {"\u02c8", "\u02cc", "\u02d0", "\u02d1", "."}
    for i in range(len(segs) - 1):
        base = segs[i]
        mod = segs[i + 1]
        if len(mod) != 1 or mod in skip:
            continue
        if unicodedata.category(mod) != "Lm":
            continue
        candidate = base + mod
        if CustomCharacter.is_valid_char(candidate):
            continue
        return (
            f"register {candidate!r} as a custom CONSONANT in your TOML config "
            f'([[custom_chars]] sequence = {candidate!r}, category = "CONSONANT", weight = 1)'
        )
    return None


def _detect_uncollapsed_modifier_geminate(word: str) -> str | None:
    """Detect word strings containing an unregistered modifier-letter geminate.

    Looks for the pattern ``[BASE_1, MOD_1, BASE_2, MOD_2]`` where
    ``BASE_1 == BASE_2`` and ``MOD_1 == MOD_2`` and ``MOD`` is any weight-0
    symbol (diacritic, suprasegmental modifier, tone mark, etc.). Such a
    sequence encodes a geminate phoneme that the parser cannot collapse at
    the word level because munch treats base and modifier as separate
    segments, leaving the two base tokens non-adjacent. Fix: register
    ``BASE+MOD`` as a custom CONSONANT so munch glues it into one segment.

    Returns the recommended custom sequence, or ``None`` if no such pattern.
    Lets any parser ``ValidationError`` propagate so unknown symbols in the
    word surface as explicit errors rather than being silently swallowed.
    """
    segs = IPAString(word, geminate=True).segments
    for i in range(len(segs) - 3):
        a, b, c, d = segs[i], segs[i + 1], segs[i + 2], segs[i + 3]
        if a != c or b != d:
            continue
        # Modifier must be a weight-0 symbol (DIACRITIC, SUPRASEGMENTAL,
        # TONE, ACCENT_MARK, etc.). Weight-1 bases don't qualify. All
        # segments that reach this point are valid (unknown diacritics
        # would have raised in ``_validate_string``), so weight is not None.
        if IPAString._segment_weight(b) != 0:
            continue
        candidate = a + b
        if CustomCharacter.is_valid_char(candidate):
            continue
        return candidate
    return None


def _cell_expansion_count(cell: str, geminate: bool) -> int:
    """Number of ``segment_type`` entries that ``cell`` will contribute.

    Mirrors the logic in ``segment_type`` so we can pre-check cells that
    would produce more (or fewer) entries than their single xlsx row.
    """
    if cell in ("OP", "SP"):
        return 1
    try:
        char_only_str = IPAString(cell, geminate=geminate).char_only()
        types = IPAString(char_only_str, geminate=geminate).segment_type
    except Exception:
        return 1
    return len(types) if isinstance(types, list) else 1


def find_length_mismatches(
    df: pd.DataFrame,
    original_word_list: list[str],
    word_start_indices: list[int],
    geminate: bool = True,
    phoneme_column: str = "Phoneme",
) -> list[tuple[int, str, int, int, str | None]]:
    """Return words whose xlsx rows don't align with pipeline expectations.

    Two independent checks:
      1. Row count vs. word phoneme count (``total_length`` at ``gem=False``).
      2. Row count vs. per-cell ``segment_type`` expansion at the pipeline's
         ``geminate`` flag. Catches cases where a cell like ``"pp"`` under
         ``gem=False`` inflates to 2 entries for 1 row.

    Each entry is ``(excel_row, word, expected_len, actual_rows, suggestion)``.
    Excel row numbers are 1-based including header (start_idx + 2).
    """
    results: list[tuple[int, str, int, int, str | None]] = []
    num_words = len(original_word_list)
    for i in range(num_words):
        word = original_word_list[i]
        if word in ("OP", "SP"):
            continue
        start_idx = word_start_indices[i]
        end_idx = word_start_indices[i + 1] if i + 1 < num_words else len(df)
        actual = end_idx - start_idx

        # Check 1: word phoneme count (always gem=False for raw count)
        expected = int(IPAString(word, geminate=False).total_length())
        if expected != actual:
            suggestion = _suggest_custom_registration(word, geminate=geminate)
            results.append((start_idx + 2, word, expected, actual, suggestion))
            continue

        # Check 2: cell expansion under the pipeline's geminate flag
        cell_total = 0
        for j in range(start_idx, end_idx):
            cell = str(df.at[j, phoneme_column]).strip()
            cell_total += _cell_expansion_count(cell, geminate=geminate)
        if cell_total != actual:
            suggestion = (
                "one or more cells contain a doubled-character geminate "
                "(e.g. 'pp' or 'mm') while geminate=false; either set "
                "geminate=true in your TOML config, or annotate each half of "
                "the geminate on its own row as single characters"
            )
            results.append((start_idx + 2, word, cell_total, actual, suggestion))
            continue

        # Check 3: word contains a modifier-letter geminate (e.g. tʰtʰ)
        # that won't collapse at word level unless base+modifier is registered.
        # Silently produces inflated WordLengthByPhoneme otherwise.
        if geminate:
            candidate = _detect_uncollapsed_modifier_geminate(word)
            if candidate is not None:
                collapsed = int(
                    IPAString(word.replace(candidate * 2, candidate), geminate=True).total_length()
                )
                suggestion = (
                    f"word contains an unregistered modifier-letter geminate "
                    f"{candidate * 2!r}; register {candidate!r} as a custom "
                    f"CONSONANT in your TOML config so the geminate collapses "
                    f"at the word level "
                    f"([[custom_chars]] sequence = {candidate!r}, "
                    f'category = "CONSONANT", weight = 1)'
                )
                results.append((start_idx + 2, word, collapsed, actual, suggestion))
    return results


def find_mismatches_with_phoneme_alignment(
    df: pd.DataFrame,
    original_word_list: list[str],
    word_start_indices: list[int],
    phoneme_column: str = "Phoneme",
    geminate: bool = True,
) -> list[tuple[int, str]]:
    """Detect words whose phoneme rows don't concatenate to match the word string.

    Row numbers are 1-based + header offset (start_idx + 2 = Excel row).
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
    """Drop all OP and SP rows and reset the index."""
    op_sp_indices = df.index[df["Word"].isin(["OP", "SP"])].tolist()
    df_cleaned = df.drop(op_sp_indices).reset_index(drop=True)

    return df_cleaned


def build_final_dataframe(
    df: pd.DataFrame,
    geminate: bool = True,
    fill_na: bool = True,
) -> tuple[pd.DataFrame, list[tuple[int, str]]]:
    """Execute the complete IPA phonological processing pipeline.

    Returns ``(final_df, mismatches)`` where final_df has FINAL_COLUMNS
    and mismatches lists words with phoneme alignment errors.
    """
    df = df.copy()

    df = insert_sp(df)
    assign_pauses(df)

    original_word_list, word_start_indices = get_word_list_and_indices(df)

    length_issues = find_length_mismatches(
        df, original_word_list, word_start_indices, geminate=geminate
    )
    if length_issues:
        raise LengthMismatchError(length_issues)

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
    syllable_list_flat, _, unique_syll_idx = word_columns(syllable_column_flat, geminate=geminate)
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
    """Reset the registry and register custom characters in order."""
    CustomCharacter.clear_all_chars()
    for sequence, category, p_weight in custom_chars:
        CustomCharacter.add_char(sequence, category, p_weight=p_weight)
