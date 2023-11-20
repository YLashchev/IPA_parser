from .dict_loader import DictionaryLoader
from .debug import ValidationError



class IPA_CHAR:
    _data = DictionaryLoader.get_data()

    ranking_dictionary = {
        'AFFRICATE': 1, 'DIPHTONG': 1, 'CONSONANT': 1,
        'VOWEL': 1, 'DIACRITIC': 0, 'SUPRASEGMENTAL': 0, 'TONE-ACCENT': 0, 'PAUSE': 0
    }

    @classmethod
    def _char_data(cls, char):
        char = char.strip()
        if not char:
            raise ValidationError("EMPTY_INPUT_CHARACTER")

        # Handle multi-codepoint characters
        char_codes = [format(ord(c), '04x') for c in char]
        char_code = ''.join(char_codes)

        for category, symbols in cls._data.items():
            for name, value in symbols.items():
                if value["code"] == char_code:
                    return category, name, value["code"]

        raise ValidationError("SYMBOL_NOT_FOUND", char=char)


    @classmethod
    def rank(cls, char):
        category, _, _ = cls._char_data(char)
        return cls.ranking_dictionary.get(category)

    @classmethod
    def name(cls, char):
        _, name, _ = cls._char_data(char)
        return name

    @classmethod
    def category(cls, char):
        category, _, _ = cls._char_data(char)
        return category

    @classmethod
    def code(cls, char):
        _, _, code = cls._char_data(char)
        return code

    @classmethod
    def is_valid_char(cls, char):
        try:
            cls._char_data(char)
            return True
        except ValidationError:
            return False

class CustomCharacter:
    _custom_chars = {}

    @classmethod
    def add_char(cls, char_sequence, category, rank=1):
        cls._custom_chars[char_sequence] = {'category': category, 'rank': rank}

    @classmethod
    def remove_char(cls, char_sequence):
        if char_sequence in cls._custom_chars:
            del cls._custom_chars[char_sequence]

    @classmethod
    def get_char(cls, char_sequence):
        return cls._custom_chars.get(char_sequence)

    @classmethod
    def clear_all_chars(cls):
        cls._custom_chars.clear()

    @classmethod
    def is_valid_char(cls, char):
        return char in cls._custom_chars
    
