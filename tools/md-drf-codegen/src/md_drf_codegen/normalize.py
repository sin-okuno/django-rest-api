"""Nullable / union type normalization."""

from __future__ import annotations

import re

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.models import NormalizedType

_FULL_WIDTH_SPACE = re.compile(r"\u3000")
_WHITESPACE = re.compile(r"\s+")


def normalize_cell(raw: str) -> str:
    """Collapse full/half-width whitespace and trim."""
    return _WHITESPACE.sub(" ", _FULL_WIDTH_SPACE.sub(" ", raw)).strip()


def normalize_nullable_type(
    raw: str,
    *,
    section: str | None = None,
    line: int | None = None,
) -> NormalizedType:
    """Normalize a type cell such as ``string | null`` into base type + nullable flag.

    Rules:
    - ``string | null`` / ``null | string`` -> type=string, nullable=True
    - ``ProductDetail[]`` -> type=ProductDetail[], nullable=False
    - Escaped pipes (``\\|``) are treated as literal ``|`` inside a single type token
      and are not used as union separators.
    - Multiple non-null members (``A | B``) are rejected.
    """
    text = normalize_cell(raw)
    if not text:
        raise SchemaValidationError(
            "Type cell is empty.",
            section=section,
            line=line,
            fix="Provide a type such as string, number, or TypeName | null.",
        )

    # Temporarily protect escaped pipes so split works on real unions only.
    placeholder = "\0PIPE\0"
    protected = text.replace("\\|", placeholder)
    parts = [normalize_cell(part.replace(placeholder, "|")) for part in protected.split("|")]
    parts = [part for part in parts if part]

    if not parts:
        raise SchemaValidationError(
            f'Invalid type expression "{raw}".',
            section=section,
            line=line,
            fix="Use a non-empty type expression.",
        )

    null_parts = [part for part in parts if part.lower() == "null"]
    non_null = [part for part in parts if part.lower() != "null"]

    if len(non_null) != 1:
        raise SchemaValidationError(
            f'Unsupported union type "{raw}". Only "<Type> | null" is allowed.',
            section=section,
            line=line,
            fix='Write a single base type, optionally followed by " | null".',
        )

    return NormalizedType(type=non_null[0], nullable=len(null_parts) > 0)


def strip_array_suffix(type_name: str) -> str:
    """Return the element type name if ``type_name`` ends with ``[]``."""
    if type_name.endswith("[]"):
        return type_name[:-2]
    return type_name


PRIMITIVE_TYPES: frozenset[str] = frozenset(
    {
        "string",
        "number",
        "integer",
        "decimal",
        "boolean",
        "any",
        "object",
        "null",
    }
)


def is_primitive_type(type_name: str) -> bool:
    return strip_array_suffix(type_name) in PRIMITIVE_TYPES


def is_array_type(type_name: str) -> bool:
    return type_name.endswith("[]")
