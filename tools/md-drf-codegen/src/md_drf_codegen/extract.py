"""Extract API endpoints and api-category types from Markdown."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.models import (
    ApiEndpoint,
    ApiSpec,
    ApiTypeDefinition,
    HttpMethod,
    MarkdownDocument,
    TypeProperty,
)
from md_drf_codegen.normalize import normalize_cell, normalize_nullable_type, strip_array_suffix
from md_drf_codegen.parser import (
    API_HEADERS,
    TYPE_HEADERS,
    find_section,
    find_table,
    parse_markdown_file,
)

API_METHODS = {method.value for method in HttpMethod}


def extract_from_markdown(path: str | Path, *, source_label: str | None = None) -> ApiSpec:
    document = parse_markdown_file(path)
    return extract_from_document(document, source_label=source_label)


def extract_from_document(
    document: MarkdownDocument,
    *,
    source_label: str | None = None,
) -> ApiSpec:
    apis = _extract_apis(document)
    types = _extract_api_types(document)
    return ApiSpec(
        version=1,
        title=document.title,
        source=source_label or document.source_path,
        apis=apis,
        types=types,
    )


def _extract_apis(document: MarkdownDocument) -> list[ApiEndpoint]:
    section = find_section(document, "API一覧")
    table = find_table(section, API_HEADERS)
    endpoints: list[ApiEndpoint] = []
    seen_ids: set[str] = set()

    for row in table.rows:
        method_raw = normalize_cell(row.get("メソッド", "")).upper()
        if method_raw not in API_METHODS:
            raise SchemaValidationError(
                f'Invalid API method "{method_raw}".',
                section="API一覧",
                line=table.line,
                fix=f"Use one of {', '.join(sorted(API_METHODS))}.",
            )

        api_id = normalize_cell(row.get("API ID", ""))
        if api_id in seen_ids:
            raise SchemaValidationError(
                f'Duplicate API ID "{api_id}".',
                section="API一覧",
                fix="Ensure each API ID is unique.",
            )
        seen_ids.add(api_id)

        endpoints.append(
            ApiEndpoint.model_validate(
                {
                    "id": api_id,
                    "name": normalize_cell(row.get("API名", "")),
                    "method": method_raw,
                    "path": normalize_cell(row.get("パス", "")),
                    "requestType": normalize_cell(row.get("リクエスト型", "")),
                    "responseType": normalize_cell(row.get("レスポンス型", "")),
                    "description": normalize_cell(row.get("説明", "")),
                }
            )
        )
    return endpoints


def _to_bool(raw: str) -> bool:
    return normalize_cell(raw).lower() == "true"


def _parse_optional_int(
    raw: str,
    *,
    column: str,
    type_name: str,
    prop_name: str,
    line: int,
) -> int | None:
    cell = normalize_cell(raw)
    if cell in {"", "-", "なし", "null"}:
        return None
    try:
        value = int(cell)
    except ValueError as exc:
        raise SchemaValidationError(
            f'Invalid {column} "{cell}" on {type_name}.{prop_name}.',
            section="型定義",
            line=line,
            fix=f"Set {column} to a positive integer or leave empty.",
        ) from exc
    if value < 0:
        raise SchemaValidationError(
            f"{column} must be >= 0 on {type_name}.{prop_name}.",
            section="型定義",
            line=line,
            fix=f"Set {column} to a non-negative integer.",
        )
    return value


def _digit_constraints_for_type(
    base_type: str,
    *,
    max_digits_cell: str,
    decimal_places_cell: str,
    type_name: str,
    prop_name: str,
    line: int,
) -> dict[str, int | None]:
    """Map Markdown 最大桁数 / 小数桁 to TypeProperty digit fields by base type."""
    max_digits_value = _parse_optional_int(
        max_digits_cell,
        column="最大桁数",
        type_name=type_name,
        prop_name=prop_name,
        line=line,
    )
    decimal_places = _parse_optional_int(
        decimal_places_cell,
        column="小数桁",
        type_name=type_name,
        prop_name=prop_name,
        line=line,
    )

    # Array suffix already stripped in normalize; base_type may still be "Foo[]" —
    # callers pass normalized.type (no nullable). Strip array for constraint mapping.
    primitive = strip_array_suffix(base_type)
    max_length: int | None = None
    max_digits: int | None = None

    if max_digits_value is not None:
        if max_digits_value < 1:
            raise SchemaValidationError(
                f'最大桁数 must be >= 1 on {type_name}.{prop_name}.',
                section="型定義",
                line=line,
                fix="Set 最大桁数 to a positive integer or leave empty.",
            )
        if primitive == "string":
            max_length = max_digits_value
        elif primitive in {"integer", "number", "decimal"}:
            max_digits = max_digits_value
        else:
            raise SchemaValidationError(
                f'最大桁数 is not applicable to type "{primitive}" on {type_name}.{prop_name}.',
                section="型定義",
                line=line,
                fix="Use 最大桁数 only for string, integer, number, or decimal.",
            )

    if decimal_places is not None and primitive not in {"number", "decimal"}:
        raise SchemaValidationError(
            f'小数桁 is not applicable to type "{primitive}" on {type_name}.{prop_name}.',
            section="型定義",
            line=line,
            fix="Use 小数桁 only for number or decimal.",
        )

    if decimal_places is not None and max_digits is not None and decimal_places > max_digits:
        raise SchemaValidationError(
            f"小数桁 ({decimal_places}) cannot exceed 最大桁数 ({max_digits}) "
            f"on {type_name}.{prop_name}.",
            section="型定義",
            line=line,
            fix="Ensure 小数桁 <= 最大桁数.",
        )

    return {
        "maxLength": max_length,
        "maxDigits": max_digits,
        "decimalPlaces": decimal_places,
    }


def _extract_api_types(document: MarkdownDocument) -> list[ApiTypeDefinition]:
    """Parse 型定義 and keep only category == api."""
    section = find_section(document, "型定義")
    table = find_table(section, TYPE_HEADERS)
    buckets: dict[str, ApiTypeDefinition] = {}

    for row in table.rows:
        category = normalize_cell(row.get("カテゴリー", "")).lower()
        if category != "api":
            # view / action / others are intentionally ignored for DRF codegen.
            continue

        type_name = normalize_cell(row.get("型名", ""))
        if not type_name:
            raise SchemaValidationError(
                "Type name is empty for an api-category row.",
                section="型定義",
                line=table.line,
                fix="Fill 型名 for every api-category row.",
            )

        normalized = normalize_nullable_type(
            row.get("型", ""),
            section="型定義",
            line=table.line,
        )
        prop_name = normalize_cell(row.get("プロパティ", ""))
        digits = _digit_constraints_for_type(
            normalized.type,
            max_digits_cell=row.get("最大桁数", ""),
            decimal_places_cell=row.get("小数桁", ""),
            type_name=type_name,
            prop_name=prop_name or "<empty>",
            line=table.line,
        )
        property_def = TypeProperty.model_validate(
            {
                "name": prop_name,
                "type": normalized.type,
                "nullable": normalized.nullable,
                "optional": _to_bool(row.get("任意", "false")),
                "description": normalize_cell(row.get("説明", "")),
                **digits,
            }
        )
        if not property_def.name:
            raise SchemaValidationError(
                f'Property name is empty on type "{type_name}".',
                section="型定義",
                line=table.line,
                fix="Fill プロパティ for every type row.",
            )

        existing = buckets.get(type_name)
        if existing is None:
            buckets[type_name] = ApiTypeDefinition(
                name=type_name,
                category="api",
                properties=[property_def],
            )
        else:
            existing.properties.append(property_def)

    return list(buckets.values())
