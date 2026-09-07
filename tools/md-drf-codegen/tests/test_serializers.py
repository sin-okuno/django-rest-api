"""Serializer generator tests."""

from __future__ import annotations

import ast

from md_drf_codegen.generator import GenerateTarget, generate_code_files
from md_drf_codegen.schema import ApiSpec, FieldDefinition, TypeDefinition


def _spec_with_types(types: dict[str, TypeDefinition]) -> ApiSpec:
    return ApiSpec(version=1, apis=[], types=types)


def test_string_field() -> None:
    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={"name": FieldDefinition(type="string", required=True, nullable=False)}
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "CharField" in code
    ast.parse(code)


def test_nullable_field() -> None:
    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "description": FieldDefinition(type="string", required=False, nullable=True)
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "allow_null=True" in code
    assert "required=False" in code


def test_nested_serializer() -> None:
    spec = _spec_with_types(
        {
            "Child": TypeDefinition(
                fields={"id": FieldDefinition(type="string", required=True, nullable=False)}
            ),
            "Parent": TypeDefinition(
                fields={"child": FieldDefinition(type="Child", required=True, nullable=False)}
            ),
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "ChildSerializer" in code
    ast.parse(code)


def test_integer_range_constraint() -> None:
    from md_drf_codegen.schema.constraints import FieldConstraints

    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "revision": FieldDefinition(
                        type="integer",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(min=1, max=50),
                    )
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "min_value=1" in code
    assert "max_value=50" in code
    ast.parse(code)


def test_string_alphanumeric_constraint() -> None:
    from md_drf_codegen.schema.constraints import FieldConstraints, StringFormat

    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "productId": FieldDefinition(
                        type="string",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(
                            format=StringFormat.ALPHANUMERIC,
                            max_length=20,
                        ),
                    )
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "RegexValidator" in code
    assert "max_length=20" in code
    assert r"^[A-Za-z0-9]+$" in code
    ast.parse(code)
