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
    assert "allow_blank=False" in code


def test_allow_blank_field() -> None:
    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "description": FieldDefinition(
                        type="string",
                        required=False,
                        nullable=True,
                        allowBlank=True,
                    )
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "allow_null=True" in code
    assert "allow_blank=True" in code
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
    assert "IntegerField" in code
    assert "min_value=1" in code
    assert "max_value=50" in code
    ast.parse(code)


def test_number_uses_decimal_field() -> None:
    from md_drf_codegen.schema.constraints import FieldConstraints

    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "price": FieldDefinition(
                        type="number",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(min=1, max=999999),
                    )
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert "DecimalField" in code
    assert "FloatField" not in code
    assert "max_digits=20" in code
    assert "decimal_places=6" in code
    assert "min_value=1" in code
    assert "max_value=999999" in code
    ast.parse(code)


def test_response_only_types_are_read_only() -> None:
    from md_drf_codegen.schema import ApiEndpoint, HttpMethod, PathParameterDefinition

    spec = ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="getItem",
                name="詳細",
                method=HttpMethod.GET,
                path="/api/items/{itemId}",
                requestType="ItemQuery",
                responseType="ItemResponse",
            ),
            ApiEndpoint(
                id="updateItem",
                name="更新",
                method=HttpMethod.PUT,
                path="/api/items/{itemId}",
                requestType="ItemUpdateRequest",
                responseType="ItemResponse",
            ),
        ],
        pathParameters={
            "itemId": PathParameterDefinition(type="string"),
        },
        types={
            "ItemQuery": TypeDefinition(
                fields={
                    "includeDeleted": FieldDefinition(
                        type="boolean", required=False, nullable=False
                    )
                }
            ),
            "ItemUpdateRequest": TypeDefinition(
                fields={
                    "price": FieldDefinition(type="number", required=True, nullable=False)
                }
            ),
            "ItemResponse": TypeDefinition(
                fields={
                    "price": FieldDefinition(type="number", required=True, nullable=False),
                    "name": FieldDefinition(type="string", required=True, nullable=False),
                }
            ),
            "Orphan": TypeDefinition(
                fields={"note": FieldDefinition(type="string", required=True, nullable=False)}
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))

    assert "class ItemResponseSerializer" in code
    assert "read_only=True, max_digits=20, decimal_places=6" in code
    assert "allow_blank=False, read_only=True" in code

    assert "class ItemUpdateRequestSerializer" in code
    assert "max_digits=20, decimal_places=6" in code
    update_block = code.split("class ItemUpdateRequestSerializer")[1].split("class ")[0]
    assert "read_only=True" not in update_block

    assert "class ItemQuerySerializer" in code
    query_block = code.split("class ItemQuerySerializer")[1].split("class ")[0]
    assert "read_only=True" not in query_block

    assert "class OrphanSerializer" in code
    orphan_block = code.split("class OrphanSerializer")[1]
    assert "read_only=True" not in orphan_block
    ast.parse(code)


def test_date_and_datetime_fields() -> None:
    spec = _spec_with_types(
        {
            "Sample": TypeDefinition(
                fields={
                    "updatedDate": FieldDefinition(
                        type="date", required=True, nullable=False
                    ),
                    "updatedAt": FieldDefinition(
                        type="datetime", required=False, nullable=True
                    ),
                }
            )
        }
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    code = next(iter(files.values()))
    assert (
        "updatedDate = serializers.DateField(required=True, allow_null=False)" in code
    )
    assert (
        "updatedAt = serializers.DateTimeField(required=False, allow_null=True)" in code
    )
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
