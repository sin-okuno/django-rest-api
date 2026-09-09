"""Parse optional エラーメッセージ table cells."""

from __future__ import annotations

import re

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import normalize_cell

_TOKEN_SPLIT = re.compile(r"[;,、]")


SERIALIZER_ERROR_MESSAGE_KEYS: frozenset[str] = frozenset(
    {
        "required",
        "blank",
        "null",
        "invalid",
        "invalid_choice",
        "max_length",
        "min_length",
        "max_value",
        "min_value",
        "pattern",
    }
)

PATH_ERROR_MESSAGE_KEYS: frozenset[str] = frozenset(
    {
        "max_length",
        "min_length",
        "pattern",
    }
)


def parse_error_messages_cell(
    raw: str,
    *,
    allowed_keys: frozenset[str],
    section: str,
    line: int | None = None,
) -> dict[str, str] | None:
    """Parse ``key:メッセージ`` pairs from an optional table cell."""
    cell = normalize_cell(raw)
    if cell in {"", "-", "なし", "null", "制約なし"}:
        return None

    messages: dict[str, str] = {}
    for token in _TOKEN_SPLIT.split(cell):
        part = token.strip()
        if not part:
            continue
        if ":" not in part:
            raise SchemaValidationError(
                f'Invalid error message entry "{part}".',
                section=section,
                line=line,
                fix='Use "key:メッセージ" format (e.g. required:必須です).',
            )
        key, message = part.split(":", 1)
        key = key.strip()
        message = message.strip()
        if not key or not message:
            raise SchemaValidationError(
                f'Invalid error message entry "{part}".',
                section=section,
                line=line,
                fix="Both key and message must be non-empty.",
            )
        if key not in allowed_keys:
            allowed = ", ".join(sorted(allowed_keys))
            raise SchemaValidationError(
                f'Unsupported error message key "{key}".',
                section=section,
                line=line,
                fix=f"Use one of: {allowed}.",
            )
        if key in messages:
            raise SchemaValidationError(
                f'Duplicate error message key "{key}".',
                section=section,
                line=line,
                fix="Define each key once per row.",
            )
        messages[key] = message

    return messages or None
