"""Tests for YAML I/O and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from md_drf_codegen.errors import SchemaValidationError, TypeReferenceError
from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.validate import validate_api_spec, validate_yaml_file
from md_drf_codegen.yaml_io import (
    dump_api_spec_yaml,
    load_api_spec_yaml,
    parse_api_spec_yaml,
    write_api_spec_yaml,
)

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "specs" / "product-structure.md"


def test_roundtrip_yaml(tmp_path: Path) -> None:
    spec = extract_from_markdown(FIXTURE)
    out = tmp_path / "out.yaml"
    write_api_spec_yaml(spec, out)
    loaded = load_api_spec_yaml(out)
    assert loaded.title == spec.title
    assert len(loaded.apis) == len(spec.apis)
    assert len(loaded.types) == len(spec.types)
    category = next(
        p
        for t in loaded.types
        if t.name == "ProductStructureApiRequest"
        for p in t.properties
        if p.name == "categoryId"
    )
    assert category.nullable is True


def test_validate_ok() -> None:
    spec = extract_from_markdown(FIXTURE)
    warnings = validate_api_spec(spec)
    assert warnings == []


def test_validate_missing_type_reference() -> None:
    raw = dump_api_spec_yaml(extract_from_markdown(FIXTURE))
    # Break a response type reference
    broken = raw.replace("ProductDetailApiResponse", "MissingDto", 1)
    with pytest.raises(TypeReferenceError):
        validate_api_spec(parse_api_spec_yaml(broken))


def test_validate_invalid_yaml_schema() -> None:
    invalid = "version: 1\ntitle: x\napis: []\ntypes: [{name: bad-name, properties: []}]\n"
    with pytest.raises(SchemaValidationError):
        parse_api_spec_yaml(invalid)


def test_validate_file(tmp_path: Path) -> None:
    spec = extract_from_markdown(FIXTURE)
    path = write_api_spec_yaml(spec, tmp_path / "ok.yaml")
    loaded, warnings = validate_yaml_file(path)
    assert loaded.version == 1
    assert warnings == []
