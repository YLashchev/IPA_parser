import pytest

from ipa import ValidationError, IPAString, CustomCharacter


def test_unregistered_tiebar_error_message_format():
    """Test that UNREGISTERED_TIE_BAR error includes segment and registration hints."""
    segment = "t͡s"
    error = ValidationError("UNREGISTERED_TIE_BAR", segment=segment)
    message = str(error)

    # Verify error type appears in message
    assert "UNREGISTERED_TIE_BAR" in message

    # Verify segment appears in message
    assert segment in message

    # Verify registration hints are present
    assert "CustomCharacter.add_char" in message
    assert "AFFRICATE" in message
    assert "TOML" in message or "config" in message


def test_unregistered_tiebar_error_type_distinct():
    """Test that error type is stored correctly and message is distinct."""
    segment = "t͡s"
    error = ValidationError("UNREGISTERED_TIE_BAR", segment=segment)

    # Verify error_type attribute
    assert error.error_type == "UNREGISTERED_TIE_BAR"

    # Verify it's not confused with other error types
    assert "SYMBOL_NOT_FOUND" not in str(error)


# === IPAString Validation Tests (TDD RED Phase) ===


def test_unregistered_tiebar_raises_early():
    """Test that IPAString("t͡s") raises UNREGISTERED_TIE_BAR during __init__."""
    with pytest.raises(ValidationError) as exc:
        IPAString("t͡s")
    assert exc.value.error_type == "UNREGISTERED_TIE_BAR"


def test_unregistered_tiebar_error_message_contains_hint():
    """Test that error message contains registration hint and the sequence."""
    with pytest.raises(ValidationError) as exc:
        IPAString("t͡s")

    message = str(exc.value)
    assert "CustomCharacter.add_char" in message
    assert "t͡s" in message


def test_registered_tiebar_no_error():
    """Test that after registration, IPAString constructs without error."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", 1)
    # Should not raise
    result = IPAString("t͡s")
    assert result.segments == ["t͡s"]


def test_registered_tiebar_segment_type():
    """Test that segment_type works after registration."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", 1)
    result = IPAString("t͡s")
    assert result.segment_type == ["AFFRICATE"]


def test_registered_tiebar_segment_count():
    """Test that segment_count works after registration."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", 1)
    result = IPAString("at͡s")
    assert result.segment_count == {"V": 1, "C": 1}  # 't͡s' counted as one consonant


def test_multiple_affricates():
    """Test string with multiple registered affricates."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", 1)
    CustomCharacter.add_char("d͡ʒ", "AFFRICATE", 1)
    result = IPAString("t͡sad͡ʒa")
    assert result.segments == ["t͡s", "a", "d͡ʒ", "a"]
    assert result.segment_count == {"V": 2, "C": 2}


def test_all_common_affricates_fail_without_registration():
    """Test that common affricates all raise UNREGISTERED_TIE_BAR."""
    common_affricates = ["t͡s", "d͡z", "t͡ʃ", "d͡ʒ"]

    for affricate in common_affricates:
        with pytest.raises(ValidationError) as exc:
            IPAString(affricate)
        assert exc.value.error_type == "UNREGISTERED_TIE_BAR"
        assert affricate in str(exc.value)


def test_diphthong_tiebar_raises():
    """Test that diphthongs with tie-bar also raise UNREGISTERED_TIE_BAR."""
    with pytest.raises(ValidationError) as exc:
        IPAString("a͡ɪ")
    assert exc.value.error_type == "UNREGISTERED_TIE_BAR"


def test_lower_tiebar_raises():
    """Test that lower tie-bar (U+035C) also raises UNREGISTERED_TIE_BAR."""
    lower_tiebar_sequence = "t" + "\u035c" + "s"
    with pytest.raises(ValidationError) as exc:
        IPAString(lower_tiebar_sequence)
    assert exc.value.error_type == "UNREGISTERED_TIE_BAR"


def test_tiebar_with_trailing_diacritic():
    """Test that tie-bar with trailing diacritic raises UNREGISTERED_TIE_BAR."""
    with pytest.raises(ValidationError) as exc:
        IPAString("t͡sʰ")
    assert exc.value.error_type == "UNREGISTERED_TIE_BAR"


def test_non_tiebar_sequences_unaffected():
    """Test that normal IPA strings without tie-bars work as before."""
    result = IPAString("pasta")
    assert result.segments == ["p", "a", "s", "t", "a"]
    assert result.segment_count == {"V": 2, "C": 3}


# === Downstream Operation Tests (char_only, coda, total_length) ===


def test_char_only_retains_registered_tiebar():
    """Test that char_only preserves registered tie-bar affricates while removing stress."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
    result = IPAString("ˈt͡sa")
    cleaned = result.char_only()
    assert cleaned == "t͡sa"  # Stress removed, affricate kept


def test_char_only_tiebar_with_diacritics():
    """Test that char_only removes diacritics but preserves registered tie-bar affricates."""
    CustomCharacter.add_char("t͡ʃ", "AFFRICATE", p_weight=1)
    result = IPAString("t͡ʃʰa")
    cleaned = result.char_only()
    assert cleaned == "t͡ʃa"  # Aspiration removed, affricate kept


def test_coda_registered_affricate():
    """Test that coda counts registered tie-bar affricates as single consonants."""
    CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
    result = IPAString("pat͡s")
    assert result.coda == 1


def test_coda_registered_diphthong_ends_vowel():
    """Test that coda returns 0 when word ends with registered tie-bar diphthong."""
    CustomCharacter.add_char("a͡ɪ", "DIPHTHONG", p_weight=1)
    result = IPAString("pa͡ɪ")
    assert result.coda == 0


def test_total_length_with_registered_tiebar():
    CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
    result = IPAString("t͡sa")
    assert result.total_length() == 2  # t͡s (weight=1) + a (weight=1)


def test_total_length_tiebar_p_weight_zero():
    CustomCharacter.add_char("‿", "PAUSE", p_weight=0)
    result = IPAString("pa‿ba")
    assert result.total_length() == 4  # p + a + b + a, pause (weight=0) excluded
