"""Type definition models for request/response DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from md_drf_codegen.schema.constraints import FieldConstraints


class FieldDefinition(BaseModel):
    """A single field on a DTO type."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: str = Field(min_length=1)
    required: bool = True
    nullable: bool = False
    constraints: FieldConstraints | None = None

    @field_validator("type", mode="before")
    @classmethod
    def strip_type(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TypeDefinition(BaseModel):
    """Named type with a map of field definitions."""

    model_config = ConfigDict(extra="forbid")

    fields: dict[str, FieldDefinition] = Field(default_factory=dict)

    @field_validator("fields", mode="before")
    @classmethod
    def strip_field_names(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        return {str(key).strip(): item for key, item in value.items()}
