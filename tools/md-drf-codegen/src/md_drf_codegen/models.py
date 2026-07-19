"""Pydantic models for the API intermediate representation (YAML)."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class TypeProperty(BaseModel):
    """A single property on an API DTO type."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    type: str = Field(min_length=1, description="Base type after nullable normalization")
    nullable: bool = False
    optional: bool = False
    description: str = ""
    max_length: int | None = Field(
        default=None,
        ge=1,
        alias="maxLength",
        description="string の最大文字数（Markdown 列: 最大桁数）",
    )
    max_digits: int | None = Field(
        default=None,
        ge=1,
        alias="maxDigits",
        description="数値の最大桁数（Markdown 列: 最大桁数）",
    )
    decimal_places: int | None = Field(
        default=None,
        ge=0,
        alias="decimalPlaces",
        description="小数桁数（Markdown 列: 小数桁）",
    )

    @field_validator("name", "type", "description", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ApiTypeDefinition(BaseModel):
    """API-category type (DTO) definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, pattern=r"^[A-Z][A-Za-z0-9]*$")
    category: Literal["api"] = "api"
    properties: list[TypeProperty] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ApiEndpoint(BaseModel):
    """One row from the API一覧 section."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, pattern=r"^[a-z][a-zA-Z0-9]*$")
    name: str = Field(min_length=1)
    method: HttpMethod
    path: str = Field(min_length=1, pattern=r"^/")
    request_type: str | None = Field(default=None, alias="requestType")
    response_type: str | None = Field(default=None, alias="responseType")
    description: str = ""

    @field_validator("id", "name", "path", "description", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("request_type", "response_type", mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if normalized in {"", "-", "なし", "null"}:
                return None
            return normalized
        return value


class ApiSpec(BaseModel):
    """Root document written to / read from YAML."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: Literal[1] = 1
    title: str = Field(min_length=1)
    source: str = Field(default="", description="Relative path to the source Markdown")
    apis: list[ApiEndpoint] = Field(default_factory=list)
    types: list[ApiTypeDefinition] = Field(default_factory=list)


# --- Intermediate Markdown parse models (not serialized to YAML) ---


class MarkdownTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headers: list[str]
    rows: list[dict[str, str]]
    line: int


class MarkdownSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    level: int
    line: int
    paragraphs: list[str] = Field(default_factory=list)
    tables: list[MarkdownTable] = Field(default_factory=list)


class MarkdownDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_path: str
    title: str
    sections: list[MarkdownSection] = Field(default_factory=list)


class NormalizedType(BaseModel):
    """Result of nullable-type normalization."""

    model_config = ConfigDict(extra="forbid")

    type: str
    nullable: bool
