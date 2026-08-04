from app.core.exceptions import ConflictError, NotFoundError


class FamilyMemberNotFoundError(NotFoundError):
    def __init__(self, message: str = "Family member not found") -> None:
        super().__init__(message)


class DuplicateFamilyMemberNameError(ConflictError):
    def __init__(self, message: str = "A family member with this name already exists") -> None:
        super().__init__(message)
