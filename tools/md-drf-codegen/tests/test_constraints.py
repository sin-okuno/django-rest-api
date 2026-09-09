"""Constraint parser tests."""

from __future__ import annotations

import pytest

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.parser.constraint_parser import parse_constraints_cell
from md_drf_codegen.schema.constraints import StringFormat


def test_parse_numeric_range() -> None:
    c = parse_constraints_cell("1-50", type_name="T", field_name="revision", field_type="integer")
    assert c is not None
    assert c.min == 1
    assert c.max == 50


def test_parse_japanese_range() -> None:
    c = parse_constraints_cell("1〜50", type_name="T", field_name="revision", field_type="integer")
    assert c is not None
    assert c.min == 1
    assert c.max == 50


def test_parse_alphanumeric_format() -> None:
    c = parse_constraints_cell(
        "半角英数字",
        type_name="T",
        field_name="productId",
        field_type="string",
    )
    assert c is not None
    assert c.format == StringFormat.HALFWIDTH_ALPHANUMERIC


def test_parse_combined_string_constraints() -> None:
    c = parse_constraints_cell(
        "半角英数字, 最大20文字",
        type_name="T",
        field_name="productId",
        field_type="string",
    )
    assert c is not None
    assert c.format == StringFormat.HALFWIDTH_ALPHANUMERIC
    assert c.max_length == 20


def test_parse_max_length_japanese() -> None:
    c = parse_constraints_cell(
        "最大50文字",
        type_name="T",
        field_name="productName",
        field_type="string",
    )
    assert c is not None
    assert c.max_length == 50


def test_empty_constraint_returns_none() -> None:
    assert (
        parse_constraints_cell("-", type_name="T", field_name="x", field_type="string") is None
    )


def test_parse_enum_with_labels() -> None:
    c = parse_constraints_cell(
        "enum:1:Low|2:Middle|3:High",
        type_name="T",
        field_name="status",
        field_type="integer",
    )
    assert c is not None
    assert c.enum is not None
    assert [m.value for m in c.enum] == [1, 2, 3]
    assert [m.label for m in c.enum] == ["Low", "Middle", "High"]


def test_parse_enum_japanese_separator() -> None:
    c = parse_constraints_cell(
        "enum:1:Low、2:Middle、3:High",
        type_name="T",
        field_name="status",
        field_type="integer",
    )
    assert c is not None
    assert c.enum is not None
    assert [m.value for m in c.enum] == [1, 2, 3]


def test_parse_string_enum() -> None:
    c = parse_constraints_cell(
        "enum:Low|Middle|High",
        type_name="T",
        field_name="level",
        field_type="string",
    )
    assert c is not None
    assert c.enum is not None
    assert [m.value for m in c.enum] == ["Low", "Middle", "High"]


def test_unknown_token_raises() -> None:
    with pytest.raises(SchemaValidationError):
        parse_constraints_cell(
            "不明な制約",
            type_name="T",
            field_name="x",
            field_type="string",
        )
