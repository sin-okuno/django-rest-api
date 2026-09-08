"""Parse ## パスパラメータ table rows."""

from __future__ import annotations

from md_drf_codegen.errors import MissingSectionError, SchemaValidationError
from md_drf_codegen.normalize import normalize_cell
from md_drf_codegen.parser.constraint_parser import parse_constraints_cell
from md_drf_codegen.parser.error_messages_parser import (
    PATH_ERROR_MESSAGE_KEYS,
    parse_error_messages_cell,
)
from md_drf_codegen.parser.markdown_parser import find_section, find_table
from md_drf_codegen.schema import MarkdownDocument, PathParameterDefinition

PATH_PARAM_HEADERS: tuple[str, ...] = (
    "パラメータ名",
    "型",
)


def parse_path_parameters(document: MarkdownDocument) -> dict[str, PathParameterDefinition]:
    """Extract path parameter definitions when the section is present."""
    try:
        section = find_section(document, "パスパラメータ")
    except MissingSectionError:
        return {}

    table = find_table(section, PATH_PARAM_HEADERS)
    definitions: dict[str, PathParameterDefinition] = {}

    for row in table.rows:
        name = normalize_cell(row.get("パラメータ名", ""))
        if not name:
            raise SchemaValidationError(
                "Path parameter name is empty.",
                section="パスパラメータ",
                line=table.line,
                fix="Fill パラメータ名 for every row.",
            )

        param_type = normalize_cell(row.get("型", ""))
        if not param_type:
            raise SchemaValidationError(
                f'Type is empty for path parameter "{name}".',
                section="パスパラメータ",
                line=table.line,
                fix='Use "string" for URL path segments.',
            )

        constraints = parse_constraints_cell(
            row.get("制約", ""),
            type_name=f"path:{name}",
            field_name=name,
            field_type=param_type,
            line=table.line,
        )

        if name in definitions:
            raise SchemaValidationError(
                f'Duplicate path parameter "{name}".',
                section="パスパラメータ",
                line=table.line,
                fix="Define each path parameter once.",
            )

        definitions[name] = PathParameterDefinition(
            type=param_type,
            constraints=constraints,
            error_messages=parse_error_messages_cell(
                row.get("エラーメッセージ", ""),
                allowed_keys=PATH_ERROR_MESSAGE_KEYS,
                section="パスパラメータ",
                line=table.line,
            ),
        )

    return definitions
