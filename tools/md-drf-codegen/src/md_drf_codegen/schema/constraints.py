"""Field constraint models for input validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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


class FieldConstraints(BaseModel):
    """Validation constraints for a single field."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    min: float | None = Field(default=None, description="Minimum numeric value (inclusive)")
    max: float | None = Field(default=None, description="Maximum numeric value (inclusive)")
    min_length: int | None = Field(default=None, alias="minLength", ge=0)
    max_length: int | None = Field(default=None, alias="maxLength", ge=1)
    format: StringFormat | None = None
    pattern: str | None = Field(default=None, min_length=1)

    def is_empty(self) -> bool:
        return (
            self.min is None
            and self.max is None
            and self.min_length is None
            and self.max_length is None
            and self.format is None
            and self.pattern is None
        )

    def resolved_pattern(self) -> tuple[str, str] | None:
        """Return (regex, message) from format or pattern."""
        if self.pattern is not None:
            return self.pattern, "入力形式が正しくありません。"
        if self.format is not None:
            return FORMAT_PATTERNS[self.format]
        return None
