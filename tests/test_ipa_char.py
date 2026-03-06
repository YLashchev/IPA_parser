import pytest

from ipa import IPA_CHAR, CustomCharacter, ValidationError


def test_category_consonant():
    assert IPA_CHAR.category("p") == "CONSONANT"


def test_category_vowel():
    assert IPA_CHAR.category("a") == "VOWEL"


def test_category_diacritic():
    assert IPA_CHAR.category("ʰ") == "DIACRITIC"


def test_category_suprasegmental():
    assert IPA_CHAR.category("ˈ") == "SUPRASEGMENTAL"


def test_name_returns_string():
    name = IPA_CHAR.name("p")
    assert isinstance(name, str)
    assert name


def test_p_weight_consonant_is_1():
    assert IPA_CHAR.p_weight("p") == 1


def test_p_weight_diacritic_is_0():
    assert IPA_CHAR.p_weight("ʰ") == 0


def test_is_valid_char_true():
    assert IPA_CHAR.is_valid_char("p") is True


def test_is_valid_char_false():
    assert IPA_CHAR.is_valid_char("@") is False


def test_empty_char_raises():
    with pytest.raises(ValidationError):
        IPA_CHAR.name("  ")


def test_unknown_symbol_raises():
    with pytest.raises(ValidationError):
        IPA_CHAR.name("@")


def test_add_and_get_custom_char():
    CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
    custom = CustomCharacter.get_char("t͡s")
    assert custom == {"category": "CONSONANT", "p_weight": 1}


def test_is_valid_after_add():
    CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
    assert CustomCharacter.is_valid_char("t͡s") is True


def test_remove_char():
    CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
    CustomCharacter.remove_char("t͡s")
    assert CustomCharacter.is_valid_char("t͡s") is False


def test_clear_all():
    CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
    CustomCharacter.add_char("oʊ", "DIPHTHONG", p_weight=1)
    CustomCharacter.clear_all_chars()
    assert CustomCharacter.is_valid_char("t͡s") is False
    assert CustomCharacter.is_valid_char("oʊ") is False


def test_get_nonexistent_returns_none():
    assert CustomCharacter.get_char("xyz") is None


# Tests for convenience helpers (Task 8)


def test_register_common_affricates_count():
    """After calling register_common_affricates(), verify all COMMON_AFFRICATES keys are registered."""
    from ipa import COMMON_AFFRICATES

    CustomCharacter.register_common_affricates()
    for affricate in COMMON_AFFRICATES:
        assert CustomCharacter.is_valid_char(affricate) is True


def test_register_common_affricates_category():
    """After registration, each affricate entry has category 'AFFRICATE'."""
    from ipa import COMMON_AFFRICATES

    CustomCharacter.register_common_affricates()
    for affricate in COMMON_AFFRICATES:
        char_data = CustomCharacter.get_char(affricate)
        assert char_data is not None
        assert char_data["category"] == "AFFRICATE"


def test_register_common_diphthongs_count():
    """After calling register_common_diphthongs(), verify all COMMON_DIPHTHONGS keys are registered."""
    from ipa import COMMON_DIPHTHONGS

    CustomCharacter.register_common_diphthongs()
    for diphthong in COMMON_DIPHTHONGS:
        assert CustomCharacter.is_valid_char(diphthong) is True


def test_register_common_diphthongs_category():
    """After registration, each diphthong entry has category 'DIPHTHONG'."""
    from ipa import COMMON_DIPHTHONGS

    CustomCharacter.register_common_diphthongs()
    for diphthong in COMMON_DIPHTHONGS:
        char_data = CustomCharacter.get_char(diphthong)
        assert char_data is not None
        assert char_data["category"] == "DIPHTHONG"


def test_register_common_affricates_custom_p_weight():
    """register_common_affricates(p_weight=2) assigns p_weight 2 to all affricates."""
    from ipa import COMMON_AFFRICATES

    CustomCharacter.register_common_affricates(p_weight=2)
    for affricate in COMMON_AFFRICATES:
        char_data = CustomCharacter.get_char(affricate)
        assert char_data is not None
        assert char_data["p_weight"] == 2


def test_add_char_invalid_category_raises():
    """add_char with invalid category raises ValueError."""
    with pytest.raises(ValueError):
        CustomCharacter.add_char("x", "NOT_REAL")


def test_add_char_valid_categories_accepted():
    """add_char accepts all valid categories from VALID_CATEGORIES."""
    for category in CustomCharacter.VALID_CATEGORIES:
        # Use a unique char for each category to avoid conflicts
        test_char = f"test_{category}"
        CustomCharacter.add_char(test_char, category)
        assert CustomCharacter.is_valid_char(test_char) is True


def test_register_then_parse_affricate():
    """After registering affricates, IPAString segment_type includes AFFRICATE."""
    from ipa import IPAString

    CustomCharacter.register_common_affricates()
    result = IPAString("t͡sa")
    assert result.segment_type == ["AFFRICATE", "VOWEL"]


def test_register_then_parse_diphthong():
    """After registering diphthongs, IPAString segment_type includes DIPHTHONG."""
    from ipa import IPAString

    CustomCharacter.register_common_diphthongs()
    result = IPAString("pa͡ɪ")
    assert result.segment_type == ["CONSONANT", "DIPHTHONG"]


def test_common_affricates_importable():
    """COMMON_AFFRICATES can be imported from ipa."""
    from ipa import COMMON_AFFRICATES

    assert isinstance(COMMON_AFFRICATES, dict)
    assert len(COMMON_AFFRICATES) == 8


def test_common_diphthongs_importable():
    """COMMON_DIPHTHONGS can be imported from ipa."""
    from ipa import COMMON_DIPHTHONGS

    assert isinstance(COMMON_DIPHTHONGS, dict)
    assert len(COMMON_DIPHTHONGS) == 5
