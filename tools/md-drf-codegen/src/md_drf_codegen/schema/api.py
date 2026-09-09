"""API endpoint models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_HTTP_METHODS: frozenset[str] = frozenset({"GET", "POST", "PUT"})


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"


class ApiEndpoint(BaseModel):
    """One row from the API一覧 section."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str = Field(min_length=1, pattern=r"^[a-z][a-zA-Z0-9]*$")
    name: str = Field(min_length=1)
    method: HttpMethod
    path: str = Field(min_length=1, pattern=r"^/")
    request_type: str | None = Field(default=None, alias="requestType")
    response_type: str | None = Field(default=None, alias="responseType")
    remarks: str | None = None

    @field_validator("id", "name", "path", mode="before")
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

    @field_validator("remarks", mode="before")
    @classmethod
    def empty_remarks_to_none(cls, value: object) -> object:
        from md_drf_codegen.normalize import normalize_remarks

        return normalize_remarks(value)
