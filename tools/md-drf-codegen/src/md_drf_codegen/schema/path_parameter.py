"""Path parameter models for URL segment validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from md_drf_codegen.schema.constraints import FieldConstraints


class PathParameterDefinition(BaseModel):
    """Validation metadata for a ``{name}`` placeholder in API paths."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    param_type: str = Field(min_length=1, alias="type")
    constraints: FieldConstraints | None = None
    error_messages: dict[str, str] | None = Field(default=None, alias="errorMessages")

    @field_validator("param_type", mode="before")
    @classmethod
    def strip_type(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value
