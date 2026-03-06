"""Validation errors used throughout the package."""


class ValidationError(Exception):
    """Validation error with a short machine-readable ``error_type``."""

    def __init__(self, error_type, **kwargs):
        """Store the error code and render the final exception message."""
        self.error_type = error_type
        self.kwargs = kwargs
        super().__init__(self._get_error_message())

    def _get_error_message(self) -> str:
        """Return the formatted message for this validation error."""
        error_messages = {
            "FILE_NOT_FOUND": lambda: f"File not found:\n    {self.kwargs['file_path']}",
            "INVALID_JSON": lambda: f"Invalid JSON format in file:\n    {self.kwargs['file_path']}",
            "INVALID_SCHEMA": lambda: (
                f"Invalid IPA schema in file:\n    {self.kwargs['file_path']}"
            ),
            "EMPTY_INPUT_CHARACTER": lambda: (
                "Input character is empty or consists only of whitespace."
            ),
            "STRING OR LIST MISMATCH": lambda: "The lists or strings are not the same length.",
            "SYMBOL_NOT_FOUND": lambda: f"Symbol not found:\n    '{self.kwargs['char']}'",
            "INVALID_SEGMENT": lambda: (
                f"Invalid segment(s) in string:\n    Segments: {self.kwargs['segment']}\n    Full string: {self.kwargs['string']}"
            ),
            "UNREGISTERED_TIE_BAR": lambda: (
                f'Unregistered tie-bar sequence: \'{self.kwargs["segment"]}\'\n    Register it with: CustomCharacter.add_char("{self.kwargs["segment"]}", "AFFRICATE", p_weight=1)\n    Or add to your language config TOML:\n        [[custom_chars]]\n        sequence = "{self.kwargs["segment"]}"\n        category = "AFFRICATE"\n        weight = 1'
            ),
        }

        message_func = error_messages.get(self.error_type, lambda: "An unknown error occurred.")
        message = message_func()

        return f"ValidationError [{self.error_type}]: {message}"
