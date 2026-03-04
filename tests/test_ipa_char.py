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


def test_rank_consonant_is_1():
    assert IPA_CHAR.rank("p") == 1


def test_rank_diacritic_is_0():
    assert IPA_CHAR.rank("ʰ") == 0


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
    CustomCharacter.add_char("t͡s", "CONSONANT", rank=1)
    custom = CustomCharacter.get_char("t͡s")
    assert custom == {"category": "CONSONANT", "rank": 1}


def test_is_valid_after_add():
    CustomCharacter.add_char("t͡s", "CONSONANT", rank=1)
    assert CustomCharacter.is_valid_char("t͡s") is True


def test_remove_char():
    CustomCharacter.add_char("t͡s", "CONSONANT", rank=1)
    CustomCharacter.remove_char("t͡s")
    assert CustomCharacter.is_valid_char("t͡s") is False


def test_clear_all():
    CustomCharacter.add_char("t͡s", "CONSONANT", rank=1)
    CustomCharacter.add_char("oʊ", "DIPHTHONG", rank=1)
    CustomCharacter.clear_all_chars()
    assert CustomCharacter.is_valid_char("t͡s") is False
    assert CustomCharacter.is_valid_char("oʊ") is False


def test_get_nonexistent_returns_none():
    assert CustomCharacter.get_char("xyz") is None
