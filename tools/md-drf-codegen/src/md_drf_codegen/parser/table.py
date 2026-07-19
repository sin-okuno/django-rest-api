"""Markdown table utilities."""

from __future__ import annotations

import re

from md_drf_codegen.errors import MarkdownParseError
from md_drf_codegen.models import MarkdownTable
from md_drf_codegen.normalize import normalize_cell

_TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_SEPARATOR_CELL = re.compile(r"^:?-+:?$")


def _split_row(line: str) -> list[str]:
    match = _TABLE_ROW.match(line)
    if not match:
        return []
    inner = match.group(1)
    # Cells may contain escaped pipes \|
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in inner:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append(normalize_cell("".join(current)))
            current = []
            continue
        current.append(char)
    cells.append(normalize_cell("".join(current)))
    return cells


def _is_separator(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(_SEPARATOR_CELL.match(cell.replace(" ", "")) for cell in cells if cell is not None)


def parse_tables_from_block(block: str, *, start_line: int) -> list[MarkdownTable]:
    """Parse consecutive GFM tables from a section body."""
    lines = block.split("\n")
    tables: list[MarkdownTable] = []
    index = 0
    while index < len(lines):
        header_cells = _split_row(lines[index])
        if not header_cells:
            index += 1
            continue
        if index + 1 >= len(lines):
            break
        separator_cells = _split_row(lines[index + 1])
        if not _is_separator(separator_cells):
            index += 1
            continue

        header_line = start_line + index
        headers = [normalize_cell(cell) for cell in header_cells]
        if not any(headers):
            raise MarkdownParseError(
                "MARKDOWN_PARSE_ERROR",
                "Table has no header row.",
                line=header_line,
            )

        rows: list[dict[str, str]] = []
        row_index = index + 2
        while row_index < len(lines):
            row_cells = _split_row(lines[row_index])
            if not row_cells:
                break
            if _is_separator(row_cells):
                break
            # Pad / trim to header width
            while len(row_cells) < len(headers):
                row_cells.append("")
            row_cells = row_cells[: len(headers)]
            row = {headers[i]: row_cells[i] for i in range(len(headers))}
            rows.append(row)
            row_index += 1

        tables.append(MarkdownTable(headers=headers, rows=rows, line=header_line))
        index = row_index

    return tables


def extract_paragraphs(block: str) -> list[str]:
    """Return non-table paragraph lines from a section body."""
    paragraphs: list[str] = []
    for line in block.split("\n"):
        if _TABLE_ROW.match(line):
            continue
        text = normalize_cell(line)
        if text:
            paragraphs.append(text)
    return paragraphs
