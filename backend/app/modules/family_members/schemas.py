from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RelationshipType(StrEnum):
    SELF = "self"
    MOTHER = "mother"
    FATHER = "father"
    CHILD = "child"
    SPOUSE = "spouse"
    OTHER = "other"


def _normalize_name(value: str) -> str:
    return value.strip()


def _validate_date_of_birth(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return value


class FamilyMemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    relationship_type: RelationshipType
    date_of_birth: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("Name cannot be empty")
        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        return _validate_date_of_birth(value)


class FamilyMemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    relationship_type: RelationshipType | None = None
    date_of_birth: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = _normalize_name(value)
        if not normalized:
            raise ValueError("Name cannot be empty")
        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        return _validate_date_of_birth(value)


class FamilyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    relationship_type: RelationshipType
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime


class FamilyMemberListResponse(BaseModel):
    items: list[FamilyMemberResponse]
    total: int
