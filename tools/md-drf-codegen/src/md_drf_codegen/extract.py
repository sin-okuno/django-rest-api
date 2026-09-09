"""Extract API endpoints and type definitions from Markdown."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.parser import (
    parse_api_endpoints,
    parse_constants,
    parse_markdown_file,
    parse_path_parameters,
    parse_type_definitions,
)
from md_drf_codegen.schema import ApiSpec


def extract_from_markdown(path: str | Path, *, source_label: str | None = None) -> ApiSpec:
    document = parse_markdown_file(path)
    return extract_from_document(document, source_label=source_label)


def extract_from_document(
    document,
    *,
    source_label: str | None = None,
) -> ApiSpec:
    return ApiSpec(
        version=1,
        apis=parse_api_endpoints(document),
        types=parse_type_definitions(document),
        path_parameters=parse_path_parameters(document),
        constants=parse_constants(document),
    )
