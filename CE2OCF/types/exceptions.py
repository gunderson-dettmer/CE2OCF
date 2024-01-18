class VariableNotFoundError(Exception):
    """
    Special exception to throw where we can't find a variable name in CE Jsons
    """

    pass


class OCFValidationError(ValueError):
    def __init__(self, message: str, validation_error: str):
        self.validation_error = validation_error
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"OCF Validation Error: {self.validation_error}"
