import pytest

from ipa import CustomCharacter


@pytest.fixture(autouse=True)
def clear_custom_chars():
    CustomCharacter.clear_all_chars()
