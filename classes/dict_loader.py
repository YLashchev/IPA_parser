import json
import os
from .debug import ValidationError

class DictionaryLoader:
    _data = None

    @classmethod
    def load_data(cls, relative_path='data/IPA_Table.json'):
        if cls._data is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, relative_path)
            try:
                with open(file_path, 'r') as f:
                    cls._data = json.load(f)
            except FileNotFoundError:
                raise ValidationError("FILE_NOT_FOUND", file_path=file_path)
            except json.JSONDecodeError:
                raise ValidationError("INVALID_JSON", file_path=file_path)

    @classmethod
    def get_data(cls):
        if cls._data is None:
            cls.load_data()
        return cls._data