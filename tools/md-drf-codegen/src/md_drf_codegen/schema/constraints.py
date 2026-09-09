"""Field constraint models for input validation."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StringFormat(StrEnum):
    """Predefined string formats mapped to regex patterns."""

    ALPHANUMERIC = "alphanumeric"
    HALFWIDTH_ALPHANUMERIC = "halfwidth-alphanumeric"


FORMAT_PATTERNS: dict[StringFormat, tuple[str, str]] = {
    StringFormat.ALPHANUMERIC: (
        r"^[A-Za-z0-9]+$",
        "半角英数字のみ入力できます。",
    ),
    StringFormat.HALFWIDTH_ALPHANUMERIC: (
        r"^[A-Za-z0-9]+$",
        "半角英数字のみ入力できます。",
    ),
}

FORMAT_ALIASES: dict[str, StringFormat] = {
    "alphanumeric": StringFormat.ALPHANUMERIC,
    "ascii-alphanumeric": StringFormat.ALPHANUMERIC,
    "半角英数字": StringFormat.HALFWIDTH_ALPHANUMERIC,
    "halfwidth-alphanumeric": StringFormat.HALFWIDTH_ALPHANUMERIC,
}


class EnumMember(BaseModel):
    """One allowed value in an enum constraint."""

    model_config = ConfigDict(extra="forbid")

    value: str | int | float
    label: str | None = None


class FieldConstraints(BaseModel):
    """Validation constraints for a single field."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    min: float | None = Field(default=None, description="Minimum numeric value (inclusive)")
    max: float | None = Field(default=None, description="Maximum numeric value (inclusive)")
    min_length: int | None = Field(default=None, alias="minLength", ge=0)
    max_length: int | None = Field(default=None, alias="maxLength", ge=1)
    format: StringFormat | None = None
    pattern: str | None = Field(default=None, min_length=1)
    enum: list[EnumMember] | None = None
    enum_ref: str | None = Field(default=None, alias="enumRef")

    @field_validator("enum", mode="before")
    @classmethod
    def normalize_enum(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, list):
            return value
        members: list[Any] = []
        for item in value:
            if isinstance(item, (str, int, float)):
                members.append({"value": item})
            else:
                members.append(item)
        return members

    @field_validator("enum_ref", mode="before")
    @classmethod
    def strip_enum_ref(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        return value

    def is_empty(self) -> bool:
        return (
            self.min is None
            and self.max is None
            and self.min_length is None
            and self.max_length is None
            and self.format is None
            and self.pattern is None
            and not self.enum
            and self.enum_ref is None
        )

    def resolved_pattern(self) -> tuple[str, str] | None:
        """Return (regex, message) from format or pattern."""
        if self.pattern is not None:
            return self.pattern, "入力形式が正しくありません。"
        if self.format is not None:
            return FORMAT_PATTERNS[self.format]
        return None

    def enum_values(self) -> list[str | int | float]:
        if not self.enum:
            return []
        return [member.value for member in self.enum]
