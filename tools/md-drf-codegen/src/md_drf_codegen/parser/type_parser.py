"""Parse 型定義 table rows."""

from __future__ import annotations

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import (
    is_primitive_type,
    normalize_cell,
    normalize_nullable_type,
    strip_array_suffix,
)
from md_drf_codegen.parser.constraint_parser import parse_constraints_cell
from md_drf_codegen.parser.error_messages_parser import (
    SERIALIZER_ERROR_MESSAGE_KEYS,
    parse_error_messages_cell,
)
from md_drf_codegen.parser.markdown_parser import (
    LEGACY_TYPE_HEADERS,
    find_section,
    find_type_table,
)
from md_drf_codegen.schema import FieldDefinition, MarkdownDocument, TypeDefinition
from md_drf_codegen.schema.constraints import FieldConstraints


def _to_bool(raw: str) -> bool:
    cell = normalize_cell(raw).lower()
    if cell in {"true", "1", "yes"}:
        return True
    if cell in {"false", "0", "no"}:
        return False
    raise SchemaValidationError(
        f'Invalid boolean value "{raw}".',
        section="型定義",
        fix='Use "true" or "false".',
    )


def _parse_optional_int(raw: str) -> int | None:
    cell = normalize_cell(raw)
    if cell in {"", "-", "なし", "null"}:
        return None
    return int(cell)


def _constraints_from_legacy_digits(
    base_type: str,
    *,
    max_digits_cell: str,
    decimal_places_cell: str,
    type_name: str,
    prop_name: str,
    line: int | None,
) -> FieldConstraints | None:
    """Map legacy 最大桁数 / 小数桁 columns to FieldConstraints."""
    max_digits_value = _parse_optional_int(max_digits_cell)
    decimal_places = _parse_optional_int(decimal_places_cell)
    if max_digits_value is None and decimal_places is None:
        return None

    primitive = strip_array_suffix(base_type)
    constraints = FieldConstraints()

    if max_digits_value is not None:
        if primitive == "string":
            constraints.max_length = max_digits_value
        elif primitive in {"integer", "number", "decimal"}:
            if decimal_places and decimal_places > 0:
                constraints.max = float(10**max_digits_value - 10**-decimal_places)
            else:
                constraints.max = float(10**max_digits_value - 1)
        elif not is_primitive_type(primitive):
            pass
        else:
            raise SchemaValidationError(
                f"最大桁数 is not applicable to type '{primitive}' on {type_name}.{prop_name}.",
                section="型定義",
                line=line,
                fix="Use 最大桁数 for string, integer, or number fields.",
            )

    return constraints if not constraints.is_empty() else None


def parse_type_definitions(document: MarkdownDocument) -> dict[str, TypeDefinition]:
    """Extract type definitions from the 型定義 section."""
    section = find_section(document, "型定義")
    table, headers = find_type_table(section)
    legacy = headers == LEGACY_TYPE_HEADERS
    buckets: dict[str, dict[str, FieldDefinition]] = {}

    for row in table.rows:
        if legacy:
            category = normalize_cell(row.get("カテゴリー", "")).lower()
            if category != "api":
                continue

        type_name = normalize_cell(row.get("型名", ""))
        if not type_name:
            raise SchemaValidationError(
                "Type name is empty.",
                section="型定義",
                line=table.line,
                fix="Fill 型名 for every type row.",
            )

        prop_name = normalize_cell(row.get("プロパティ", ""))
        if not prop_name:
            raise SchemaValidationError(
                f'Property name is empty on type "{type_name}".',
                section="型定義",
                line=table.line,
                fix="Fill プロパティ for every type row.",
            )

        normalized = normalize_nullable_type(
            row.get("型", ""),
            section="型定義",
            line=table.line,
        )

        if legacy:
            optional = _to_bool(row.get("任意", "false"))
            required = not optional
            nullable = normalized.nullable
            constraints = parse_constraints_cell(
                row.get("制約", ""),
                type_name=type_name,
                field_name=prop_name,
                field_type=normalized.type,
                line=table.line,
            )
            if constraints is None:
                constraints = _constraints_from_legacy_digits(
                    normalized.type,
                    max_digits_cell=row.get("最大桁数", ""),
                    decimal_places_cell=row.get("小数桁", ""),
                    type_name=type_name,
                    prop_name=prop_name,
                    line=table.line,
                )
        else:
            nullable_cell = normalize_cell(row.get("Nullable", ""))
            nullable = _to_bool(nullable_cell) if nullable_cell else normalized.nullable
            required = _to_bool(row.get("必須", "true"))
            constraints = parse_constraints_cell(
                row.get("制約", ""),
                type_name=type_name,
                field_name=prop_name,
                field_type=normalized.type,
                line=table.line,
            )

        field_def = FieldDefinition(
            type=normalized.type,
            required=required,
            nullable=nullable,
            constraints=constraints,
            error_messages=parse_error_messages_cell(
                row.get("エラーメッセージ", ""),
                allowed_keys=SERIALIZER_ERROR_MESSAGE_KEYS,
                section="型定義",
                line=table.line,
            )
            if not legacy
            else None,
        )

        type_fields = buckets.setdefault(type_name, {})
        if prop_name in type_fields:
            raise SchemaValidationError(
                f'Duplicate property "{prop_name}" on type "{type_name}".',
                section="型定義",
                line=table.line,
                fix="Ensure property names are unique within each type.",
            )
        type_fields[prop_name] = field_def

    return {name: TypeDefinition(fields=fields) for name, fields in buckets.items()}
