"""Section splitting for Markdown documents."""

from __future__ import annotations

import re

from md_drf_codegen.models import MarkdownSection
from md_drf_codegen.normalize import normalize_cell
from md_drf_codegen.parser.table import extract_paragraphs, parse_tables_from_block

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_sections(content: str) -> tuple[str, list[MarkdownSection]]:
    """Split Markdown into title (H1) and level-2 sections."""
    normalized = content.replace("\r\n", "\n")
    lines = normalized.split("\n")

    title = "Untitled Specification"
    sections: list[MarkdownSection] = []
    current_heading: str | None = None
    current_level = 2
    current_line = 1
    body_lines: list[str] = []
    body_start_line = 1

    def flush() -> None:
        nonlocal current_heading, body_lines, body_start_line
        if current_heading is None:
            body_lines = []
            return
        body = "\n".join(body_lines)
        sections.append(
            MarkdownSection(
                heading=current_heading,
                level=current_level,
                line=current_line,
                paragraphs=extract_paragraphs(body),
                tables=parse_tables_from_block(body, start_line=body_start_line),
            )
        )
        current_heading = None
        body_lines = []

    for offset, line in enumerate(lines):
        line_no = offset + 1
        match = _HEADING.match(line)
        if match:
            level = len(match.group(1))
            text = normalize_cell(match.group(2))
            if level == 1 and current_heading is None and not sections:
                title = text
                continue
            if level == 2:
                flush()
                current_heading = text
                current_level = 2
                current_line = line_no
                body_start_line = line_no + 1
                continue
            # Deeper headings belong to the current section body as text.
            if current_heading is not None:
                body_lines.append(line)
            continue

        if current_heading is not None:
            body_lines.append(line)

    flush()
    return title, sections
