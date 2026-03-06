import pytest

from ipa import IPAString, CustomCharacter, ValidationError


def test_basic_segments():
    result = IPAString("pa")
    assert result.segments == ["p", "a"]


def test_syllable_split():
    result = IPAString("pa.ta")
    assert result.syllables == ["pa", "ta"]


def test_custom_char_segmentation():
    CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
    result = IPAString("t͡sa")
    assert result.segments[0] == "t͡s"


def test_maximal_munch_prefers_longest():
    CustomCharacter.add_char("ts", "CONSONANT", p_weight=1)
    CustomCharacter.add_char("t", "CONSONANT", p_weight=1)
    result = IPAString("tsa")
    assert result.segments == ["ts", "a"]


def test_invalid_segment_raises():
    with pytest.raises(ValidationError):
        IPAString("@")


def test_empty_string_total_length():
    result = IPAString("")
    assert result.total_length() == 0


def test_total_length_simple():
    result = IPAString("pa")
    assert result.total_length() == 2


def test_total_length_with_stress():
    result = IPAString("ˈpa")
    assert result.total_length() == 2


def test_total_length_returns_int():
    result = IPAString("pa")
    assert isinstance(result.total_length(), int)


def test_segment_count():
    result = IPAString("pa")
    assert result.segment_count == {"V": 1, "C": 1}


def test_segment_count_affricate_as_consonant():
    CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
    result = IPAString("t͡sa")
    assert result.segment_count == {"V": 1, "C": 1}


def test_segment_count_diphthong_as_vowel():
    CustomCharacter.add_char("ai", "DIPHTHONG", p_weight=1)
    result = IPAString("ai")
    assert result.segment_count == {"V": 1, "C": 0}


def test_stress_primary():
    result = IPAString("ˈpa")
    assert result.stress() == "STRESSED"


def test_stress_secondary():
    result = IPAString("ˌpa")
    assert result.stress() == "STRESSED_2"


def test_stress_unstressed():
    result = IPAString("pa")
    assert result.stress() == "UNSTRESSED"


def test_geminate_collapses_consonants():
    result = IPAString("ppa", geminate=True)
    assert result.segments == ["p", "a"]


def test_geminate_false_keeps_both():
    result = IPAString("ppa", geminate=False)
    assert result.segments == ["p", "p", "a"]


def test_coda_single_consonant():
    result = IPAString("pat")
    assert result.coda == 1


def test_coda_multiple_consonants_returns_int():
    result = IPAString("patk")
    assert result.coda == 2
    assert isinstance(result.coda, int)


def test_coda_affricate_counts_as_consonant():
    CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
    result = IPAString("pat͡s")
    assert result.coda == 1


def test_coda_pause_op():
    CustomCharacter.add_char("OP", "PAUSE", p_weight=0)
    result = IPAString("pa.OP")
    assert result.coda == "OP"


def test_coda_pause_sp():
    CustomCharacter.add_char("SP", "PAUSE", p_weight=0)
    result = IPAString("pa.SP")
    assert result.coda == "SP"


def test_char_only_removes_stress_and_diacritic():
    result = IPAString("ˈpʰa")
    cleaned = result.char_only()
    assert cleaned == "pa"
    assert result.segments == ["p", "a"]


def test_combining_accent_single_segment():
    s = "e" + "\u0301"
    result = IPAString(s)
    assert len(result.segments) == 1
    assert result.segments[0] == s


def test_tie_bar_joins_bases():
    s = "t" + "\u0361" + "\u0283"
    CustomCharacter.add_char(s, "AFFRICATE", p_weight=1)
    result = IPAString(s)
    assert len(result.segments) == 1
    assert result.segments[0] == s


def test_tie_bar_with_combining_mark_stays_single_segment():
    s = "t" + "\u0361" + "\u0283" + "\u0301"
    CustomCharacter.add_char(s, "AFFRICATE", p_weight=1)
    result = IPAString(s)
    assert result.segments == [s]


def test_custom_char_priority_over_grapheme():
    custom_sequence = "t\u0361\u0283"
    CustomCharacter.add_char(custom_sequence, "CONSONANT", p_weight=1)
    try:
        result = IPAString(custom_sequence + "a")
        assert result.segments == [custom_sequence, "a"]
    finally:
        CustomCharacter.remove_char(custom_sequence)


def test_plain_ascii_unchanged_with_grapheme_fallback():
    result = IPAString("pa")
    assert result.segments == ["p", "a"]


def test_regular_ipa_unchanged_with_grapheme_fallback():
    result = IPAString("bə.ˈnæ.nə")
    assert result.segments == ["b", "ə", ".", "ˈ", "n", "æ", ".", "n", "ə"]


# --- NFD normalization and base+diacritic tests ---


def test_precomposed_cedilla_lookup():
    """ç (U+00E7 NFC) should resolve to CONSONANT via NFD normalization."""
    from ipa import IPA_CHAR

    assert IPA_CHAR.category("ç") == "CONSONANT"


def test_precomposed_cedilla_is_valid():
    from ipa import IPA_CHAR

    assert IPA_CHAR.is_valid_char("ç") is True


def test_base_plus_diacritic_segment_category():
    """β̞ (beta + combining lowered) falls back to base character category."""
    result = IPAString("β̞a")
    types = result.segment_type
    assert types[0] == "CONSONANT"
    assert types[1] == "VOWEL"


def test_base_plus_diacritic_total_length():
    """β̞ should count as 1 segment with weight 1."""
    result = IPAString("β̞a")
    assert result.total_length() == 2


def test_precomposed_vowel_in_custom_char():
    """Custom char with precomposed á (NFC) matches NFD input."""
    CustomCharacter.add_char("ái", "DIPHTHONG", p_weight=1)
    try:
        result = IPAString("ái")
        assert result.segments == ["\u0061\u0301i"]  # NFD form
        assert result.segment_type == ["DIPHTHONG"]
    finally:
        CustomCharacter.remove_char("\u0061\u0301i")


def test_nfd_normalization_in_maximal_munch():
    """Input with precomposed á matches custom char stored in NFD."""
    import unicodedata

    nfd_seq = unicodedata.normalize("NFD", "áu")
    CustomCharacter.add_char("áu", "DIPHTHONG", p_weight=1)
    try:
        # Feed NFC input — should still match the NFD-stored custom char
        result = IPAString("\u00e1u")  # á in NFC
        assert result.segments == [nfd_seq]
    finally:
        CustomCharacter.remove_char(nfd_seq)


def test_segment_category_base_char_fallback():
    """_segment_category falls back to base char for unknown combined segments."""
    result = IPAString("n\u0325a")  # n + combining ring below + a
    types = result.segment_type
    assert types[0] == "CONSONANT"
    assert types[1] == "VOWEL"
