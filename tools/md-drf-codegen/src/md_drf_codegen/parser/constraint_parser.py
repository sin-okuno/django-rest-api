"""Parse 制約 column values from Markdown type definitions."""

from __future__ import annotations

import re

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import normalize_cell
from md_drf_codegen.schema.constraints import FORMAT_ALIASES, FieldConstraints

_TOKEN_SPLIT = re.compile(r"[,;、]")
_RANGE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*[-〜~]\s*(-?\d+(?:\.\d+)?)$")
_MIN_ONLY = re.compile(r"^(?:>=|≧)\s*(-?\d+(?:\.\d+)?)$|^(?P<jp>\d+(?:\.\d+)?)以上$")
_MAX_ONLY = re.compile(r"^(?:<=|≦)\s*(-?\d+(?:\.\d+)?)$|^(?P<jp>\d+(?:\.\d+)?)以下$")
_MIN_LENGTH = re.compile(r"^(?:minLength|最小)\s*[:：]?\s*(\d+)\s*(?:文字)?$|^(?P<jp>\d+)文字以上$")
_MAX_LENGTH = re.compile(
    r"^(?:maxLength|最大)\s*[:：]?\s*(\d+)\s*(?:文字)?$|^(?P<jp>\d+)文字(?:以内|まで)?$"
)
_PATTERN = re.compile(r"^pattern\s*[:：]\s*(.+)$", re.IGNORECASE)
_MIN_KW = re.compile(r"^min\s*[:：]\s*(-?\d+(?:\.\d+)?)$", re.IGNORECASE)
_MAX_KW = re.compile(r"^max\s*[:：]\s*(-?\d+(?:\.\d+)?)$", re.IGNORECASE)


def parse_constraints_cell(
    raw: str,
    *,
    type_name: str,
    field_name: str,
    field_type: str,
    line: int | None = None,
) -> FieldConstraints | None:
    """Parse a 制約 cell into FieldConstraints.

    Supported tokens (comma/semicolon separated):
    - ``1-50`` / ``1〜50`` — numeric range
    - ``min:1`` / ``max:50`` — numeric bounds
    - ``1以上`` / ``50以下`` — numeric bounds (Japanese)
    - ``最大50文字`` / ``maxLength:50`` — string max length
    - ``最小1文字`` / ``minLength:1`` — string min length
    - ``半角英数字`` / ``alphanumeric`` — string format
    - ``pattern:^[A-Z]+$`` — custom regex
    """
    text = normalize_cell(raw)
    if not text or text in {"-", "なし", "null", "制約なし"}:
        return None

    constraints = FieldConstraints()
    tokens = [normalize_cell(part) for part in _TOKEN_SPLIT.split(text) if normalize_cell(part)]

    for token in tokens:
        _apply_token(
            constraints,
            token,
            type_name=type_name,
            field_name=field_name,
            field_type=field_type,
            line=line,
        )

    if constraints.is_empty():
        raise SchemaValidationError(
            f'Could not parse constraints "{text}" on {type_name}.{field_name}.',
            section="型定義",
            line=line,
            fix="Use e.g. 1-50, 半角英数字, 最大50文字, pattern:^[A-Z]+$.",
        )
    return constraints


def _apply_token(
    constraints: FieldConstraints,
    token: str,
    *,
    type_name: str,
    field_name: str,
    field_type: str,
    line: int | None,
) -> None:
    ctx = f"{type_name}.{field_name}"

    alias = FORMAT_ALIASES.get(token.casefold()) or FORMAT_ALIASES.get(token)
    if alias is not None:
        constraints.format = alias
        return

    pattern_match = _PATTERN.match(token)
    if pattern_match:
        constraints.pattern = pattern_match.group(1).strip()
        return

    range_match = _RANGE.match(token)
    if range_match:
        constraints.min = _parse_number(range_match.group(1), ctx=ctx, line=line)
        constraints.max = _parse_number(range_match.group(2), ctx=ctx, line=line)
        return

    min_kw = _MIN_KW.match(token)
    if min_kw:
        constraints.min = _parse_number(min_kw.group(1), ctx=ctx, line=line)
        return

    max_kw = _MAX_KW.match(token)
    if max_kw:
        constraints.max = _parse_number(max_kw.group(1), ctx=ctx, line=line)
        return

    min_only = _MIN_ONLY.match(token)
    if min_only:
        value = min_only.group(1) or min_only.group("jp")
        constraints.min = _parse_number(value, ctx=ctx, line=line)
        return

    max_only = _MAX_ONLY.match(token)
    if max_only:
        value = max_only.group(1) or max_only.group("jp")
        constraints.max = _parse_number(value, ctx=ctx, line=line)
        return

    min_len = _MIN_LENGTH.match(token)
    if min_len:
        value = min_len.group(1) or min_len.group("jp")
        constraints.min_length = _parse_int(value, ctx=ctx, line=line)
        return

    max_len = _MAX_LENGTH.match(token)
    if max_len:
        value = max_len.group(1) or max_len.group("jp")
        constraints.max_length = _parse_int(value, ctx=ctx, line=line)
        return

    raise SchemaValidationError(
        f'Unknown constraint token "{token}" on {ctx}.',
        section="型定義",
        line=line,
        fix="Use 1-50, 半角英数字, 最大50文字, min:1, max:50, pattern:...",
    )


def _parse_number(raw: str, *, ctx: str, line: int | None) -> float:
    try:
        return float(raw) if "." in raw else int(raw)
    except ValueError as exc:
        raise SchemaValidationError(
            f'Invalid numeric constraint "{raw}" on {ctx}.',
            section="型定義",
            line=line,
            fix="Use a numeric value such as 1 or 50.",
        ) from exc


def _parse_int(raw: str, *, ctx: str, line: int | None) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise SchemaValidationError(
            f'Invalid length constraint "{raw}" on {ctx}.',
            section="型定義",
            line=line,
            fix="Use a positive integer for length constraints.",
        ) from exc
