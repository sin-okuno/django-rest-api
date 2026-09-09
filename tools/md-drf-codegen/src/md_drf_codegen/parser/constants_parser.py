"""Parse ## 定数定義一覧 table rows."""

from __future__ import annotations

from md_drf_codegen.errors import MissingSectionError, SchemaValidationError
from md_drf_codegen.normalize import normalize_cell
from md_drf_codegen.parser.markdown_parser import find_section, find_table
from md_drf_codegen.schema import MarkdownDocument
from md_drf_codegen.schema.constant import ConstantDefinition

CONSTANT_HEADERS: tuple[str, ...] = (
    "ファイルパス",
    "クラス名",
)


def parse_constants(document: MarkdownDocument) -> list[ConstantDefinition]:
    """Extract constant definitions when the section is present."""
    try:
        section = find_section(document, "定数定義一覧")
    except MissingSectionError:
        return []

    table = find_table(section, CONSTANT_HEADERS)
    definitions: list[ConstantDefinition] = []
    seen_classes: set[str] = set()

    for row in table.rows:
        path = normalize_cell(row.get("ファイルパス", ""))
        class_name = normalize_cell(row.get("クラス名", ""))
        remarks = normalize_cell(row.get("備考", ""))

        if not path:
            raise SchemaValidationError(
                "Constant file path is empty.",
                section="定数定義一覧",
                line=table.line,
                fix="Fill ファイルパス (e.g. common/util/Consts.py).",
            )
        if not class_name:
            raise SchemaValidationError(
                "Constant class name is empty.",
                section="定数定義一覧",
                line=table.line,
                fix="Fill クラス名 (e.g. Status).",
            )
        if class_name in seen_classes:
            raise SchemaValidationError(
                f'Duplicate constant class name "{class_name}".',
                section="定数定義一覧",
                line=table.line,
                fix="Define each class name once.",
            )
        seen_classes.add(class_name)
        definitions.append(
            ConstantDefinition(
                path=path,
                className=class_name,
                remarks=remarks or None,
            )
        )

    return definitions
