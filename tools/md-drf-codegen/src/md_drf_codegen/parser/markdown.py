"""Markdown document parser focused on API一覧 and 型定義."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import MissingColumnError, MissingSectionError
from md_drf_codegen.models import MarkdownDocument, MarkdownSection, MarkdownTable
from md_drf_codegen.parser.sections import parse_sections

REQUIRED_SECTIONS: tuple[str, ...] = ("API一覧", "型定義")

API_HEADERS: tuple[str, ...] = (
    "API ID",
    "API名",
    "メソッド",
    "パス",
    "リクエスト型",
    "レスポンス型",
)

TYPE_HEADERS: tuple[str, ...] = (
    "カテゴリー",
    "型名",
    "プロパティ",
    "型",
)


def parse_markdown_file(path: str | Path) -> MarkdownDocument:
    source = Path(path)
    content = source.read_text(encoding="utf-8")
    return parse_markdown_content(content, source_path=str(source))


def parse_markdown_content(content: str, *, source_path: str) -> MarkdownDocument:
    title, sections = parse_sections(content)
    _assert_required_sections(sections, source_path)
    return MarkdownDocument(source_path=source_path, title=title, sections=sections)


def find_section(document: MarkdownDocument, heading: str) -> MarkdownSection:
    for section in document.sections:
        if section.heading == heading:
            return section
    raise MissingSectionError([heading], source_path=document.source_path)


def find_table(
    section: MarkdownSection,
    required_headers: tuple[str, ...] | list[str],
) -> MarkdownTable:
    required = list(required_headers)
    for table in section.tables:
        if all(header in table.headers for header in required):
            return table
    found = [", ".join(table.headers) for table in section.tables]
    raise MissingColumnError(
        section.heading,
        required,
        found=found,
        line=section.line,
    )


def _assert_required_sections(sections: list[MarkdownSection], source_path: str) -> None:
    present = {section.heading for section in sections}
    missing = [heading for heading in REQUIRED_SECTIONS if heading not in present]
    if missing:
        raise MissingSectionError(missing, source_path=source_path)
