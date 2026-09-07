"""Root specification and Markdown parse models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from md_drf_codegen.schema.api import ApiEndpoint
from md_drf_codegen.schema.type_definition import TypeDefinition


class ApiSpec(BaseModel):
    """Root document written to / read from YAML."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: Literal[1] = 1
    apis: list[ApiEndpoint] = Field(default_factory=list)
    types: dict[str, TypeDefinition] = Field(default_factory=dict)


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
