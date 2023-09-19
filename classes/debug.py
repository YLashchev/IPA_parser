class ValidationError(Exception):
    def __init__(self, error_type, **kwargs):
        self.error_type = error_type
        self.kwargs = kwargs
        super().__init__(self._get_error_message())

    def _get_error_message(self):
        horizontal_bar = "-" * 50
        header = "ERROR OCCURRED"
        footer = "END OF ERROR MESSAGE"
        
        # Error messages
        error_messages = {
            "FILE_NOT_FOUND": lambda: f"File not found:\n    {self.kwargs['file_path']}",
            "INVALID_JSON": lambda: f"Invalid JSON format in file:\n    {self.kwargs['file_path']}",
            "EMPTY_INPUT_CHARACTER": lambda: "Input character is empty or consists only of whitespace.",
            "SYMBOL_NOT_FOUND": lambda: f"Symbol not found:\n    '{self.kwargs['char']}'",
            "INVALID_SEGMENT": lambda: f"Invalid segment(s) in string:\n    Segments: {self.kwargs['segment']}\n    Full string: {self.kwargs['string']}"
        }

        # Select the appropriate error message based on error_type
        message_func = error_messages.get(self.error_type, lambda: "An unknown error occurred.")
        message = message_func()

        # Construct the complete pretty error message
        pretty_message = f"\n{horizontal_bar}\n{header:^50}\n{horizontal_bar}\n{message}\n{horizontal_bar}\n{footer:^50}\n{horizontal_bar}\n"

        return pretty_message