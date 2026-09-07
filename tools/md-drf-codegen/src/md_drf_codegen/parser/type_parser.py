"""Parse 型定義 table rows."""

from __future__ import annotations

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import normalize_cell, normalize_nullable_type
from md_drf_codegen.parser.markdown_parser import TYPE_HEADERS, find_section, find_table
from md_drf_codegen.schema import FieldDefinition, MarkdownDocument, TypeDefinition


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


def parse_type_definitions(document: MarkdownDocument) -> dict[str, TypeDefinition]:
    """Extract type definitions from the 型定義 section."""
    section = find_section(document, "型定義")
    table = find_table(section, TYPE_HEADERS)
    buckets: dict[str, dict[str, FieldDefinition]] = {}

    for row in table.rows:
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
        nullable_cell = normalize_cell(row.get("Nullable", ""))
        nullable = _to_bool(nullable_cell) if nullable_cell else normalized.nullable
        required = _to_bool(row.get("必須", "true"))

        field_def = FieldDefinition(
            type=normalized.type,
            required=required,
            nullable=nullable,
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
