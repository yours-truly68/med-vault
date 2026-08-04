class AppException(Exception):
    """Base application exception with HTTP mapping."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "internal_error",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404, code="not_found")


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, status_code=401, code="unauthorized")


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403, code="forbidden")


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, status_code=409, code="conflict")


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status_code=422, code="validation_error")
