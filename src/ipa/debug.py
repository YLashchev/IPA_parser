"""Custom exception types for the ipa-parser library.

This module defines ``ValidationError``, the single exception class used
throughout the library to signal all input-validation and data-loading
failures.  Each error carries a machine-readable ``error_type`` string and
formats a human-readable, bordered message automatically.
"""


class ValidationError(Exception):
    """Custom exception for IPA parsing and data-loading validation failures.

    Wraps a short machine-readable ``error_type`` code and any number of
    context keyword arguments.  On construction the human-readable message is
    built by ``_get_error_message`` and forwarded to the base ``Exception``
    class so that ``str(exc)`` and ``repr(exc)`` produce a formatted
    diagnostic message.

    Supported ``error_type`` codes and their required keyword arguments:

    +--------------------------+-------------------------------------------+
    | error_type               | Required kwargs                           |
    +==========================+===========================================+
    | ``FILE_NOT_FOUND``       | ``file_path`` (str)                       |
    +--------------------------+-------------------------------------------+
    | ``INVALID_JSON``         | ``file_path`` (str)                       |
    +--------------------------+-------------------------------------------+
    | ``INVALID_SCHEMA``       | ``file_path`` (str)                       |
    +--------------------------+-------------------------------------------+
    | ``EMPTY_INPUT_CHARACTER``| (none)                                    |
    +--------------------------+-------------------------------------------+
    | ``SYMBOL_NOT_FOUND``     | ``char`` (str)                            |
    +--------------------------+-------------------------------------------+
    | ``INVALID_SEGMENT``      | ``segment`` (str), ``string`` (str)       |
    +--------------------------+-------------------------------------------+
    | ``STRING OR LIST MISMATCH`` | (none)                                 |
    +--------------------------+-------------------------------------------+

    Attributes:
        error_type (str): Machine-readable error code.
        kwargs (dict): Context values used when formatting the error message.

    Example:
        >>> raise ValidationError("SYMBOL_NOT_FOUND", char="Q")
        ValidationError [SYMBOL_NOT_FOUND]: Symbol not found:
            'Q'
    """

    def __init__(self, error_type, **kwargs):
        """Initialize a ValidationError with a type code and context values.

        Args:
            error_type (str): A machine-readable code identifying the kind of
                error (e.g. ``'SYMBOL_NOT_FOUND'``, ``'FILE_NOT_FOUND'``).
            **kwargs: Arbitrary keyword arguments providing context for the
                error message.  The required keys depend on ``error_type``
                (see class docstring for details).
        """
        self.error_type = error_type
        self.kwargs = kwargs
        super().__init__(self._get_error_message())

    def _get_error_message(self) -> str:
        """Build and return the formatted error message string.

        Constructs a bordered, human-readable block of text from the
        ``error_type`` code and any context values stored in ``self.kwargs``.
        Unknown error type codes produce a generic fallback message.

        Returns:
            str: A multi-line string beginning and ending with a row of dashes,
                containing a centred ``ERROR OCCURRED`` header, the
                type-specific detail text, and a centred
                ``END OF ERROR MESSAGE`` footer.
        """
        # Error messages
        error_messages = {
            "FILE_NOT_FOUND": lambda: f"File not found:\n    {self.kwargs['file_path']}",
            "INVALID_JSON": lambda: f"Invalid JSON format in file:\n    {self.kwargs['file_path']}",
            "INVALID_SCHEMA": lambda: f"Invalid IPA schema in file:\n    {self.kwargs['file_path']}",
            "EMPTY_INPUT_CHARACTER": lambda: "Input character is empty or consists only of whitespace.",
            "STRING OR LIST MISMATCH": lambda: "The lists or strings are not the same length.",
            "SYMBOL_NOT_FOUND": lambda: f"Symbol not found:\n    '{self.kwargs['char']}'",
            "INVALID_SEGMENT": lambda: f"Invalid segment(s) in string:\n    Segments: {self.kwargs['segment']}\n    Full string: {self.kwargs['string']}"
        }

        message_func = error_messages.get(self.error_type, lambda: "An unknown error occurred.")
        message = message_func()

        return f"ValidationError [{self.error_type}]: {message}"
