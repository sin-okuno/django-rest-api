"""Constant / enum class references defined outside generated code."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConstantDefinition(BaseModel):
    """One row from the 定数定義一覧 section."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    path: str = Field(min_length=1, description="Source file path, e.g. common/util/Consts.py")
    class_name: str = Field(min_length=1, alias="className", pattern=r"^[A-Z][A-Za-z0-9]*$")
    remarks: str | None = None

    @field_validator("path", "class_name", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("remarks", mode="before")
    @classmethod
    def empty_remarks_to_none(cls, value: object) -> object:
        from md_drf_codegen.normalize import normalize_remarks

        return normalize_remarks(value)

    def import_module(self) -> str:
        """Convert ``common/util/Consts.py`` to ``common.util.Consts``."""
        text = self.path.replace("\\", "/").strip()
        if text.endswith(".py"):
            text = text[:-3]
        text = text.strip("/")
        return text.replace("/", ".")
