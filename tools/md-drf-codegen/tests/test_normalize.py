"""Tests for nullable type normalization."""

from __future__ import annotations

import pytest

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import normalize_cell, normalize_nullable_type


def test_normalize_cell_collapses_whitespace() -> None:
    assert normalize_cell("  a\u3000b  ") == "a b"


def test_normalize_nullable_union() -> None:
    result = normalize_nullable_type("string | null")
    assert result.type == "string"
    assert result.nullable is True


def test_normalize_null_first_union() -> None:
    result = normalize_nullable_type("null | ProductDetail")
    assert result.type == "ProductDetail"
    assert result.nullable is True


def test_normalize_non_nullable() -> None:
    result = normalize_nullable_type("ProductTreeNodeDto[]")
    assert result.type == "ProductTreeNodeDto[]"
    assert result.nullable is False


def test_normalize_rejects_multi_member_union() -> None:
    with pytest.raises(SchemaValidationError, match="Unsupported union"):
        normalize_nullable_type("string | number")


def test_normalize_rejects_empty() -> None:
    with pytest.raises(SchemaValidationError, match="empty"):
        normalize_nullable_type("   ")
