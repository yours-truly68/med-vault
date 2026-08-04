from app.core.exceptions import NotFoundError, ValidationError


class InvalidFileTypeError(ValidationError):
    def __init__(self, message: str = "Unsupported file type") -> None:
        super().__init__(message)


class FileTooLargeError(ValidationError):
    def __init__(self, message: str = "File exceeds maximum upload size") -> None:
        super().__init__(message)


class DocumentNotFoundError(NotFoundError):
    def __init__(self, message: str = "Document not found") -> None:
        super().__init__(message)
