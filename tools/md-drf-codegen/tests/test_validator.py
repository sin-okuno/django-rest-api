"""Validator tests."""

from __future__ import annotations

import pytest

from md_drf_codegen.errors import SchemaValidationError, TypeReferenceError
from md_drf_codegen.schema import ApiEndpoint, ApiSpec, FieldDefinition, HttpMethod, TypeDefinition
from md_drf_codegen.validator import validate_api_spec


def _minimal_spec() -> ApiSpec:
    return ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="getProduct",
                name="詳細",
                method=HttpMethod.GET,
                path="/api/products/{productId}",
                requestType=None,
                responseType="ProductDetailResponse",
            )
        ],
        types={
            "ProductDetailResponse": TypeDefinition(
                fields={
                    "productId": FieldDefinition(type="string", required=True, nullable=False),
                }
            )
        },
    )


def test_validate_ok() -> None:
    validate_api_spec(_minimal_spec())


def test_duplicate_api_id() -> None:
    spec = _minimal_spec()
    spec.apis.append(spec.apis[0])
    with pytest.raises(SchemaValidationError):
        validate_api_spec(spec)


def test_undefined_response_type() -> None:
    spec = _minimal_spec()
    spec.apis[0].response_type = "MissingType"
    with pytest.raises(TypeReferenceError):
        validate_api_spec(spec)


def test_unknown_field_type() -> None:
    spec = _minimal_spec()
    spec.types["ProductDetailResponse"].fields["productId"] = FieldDefinition(
        type="unknownType",
        required=True,
        nullable=False,
    )
    with pytest.raises(SchemaValidationError):
        validate_api_spec(spec)


def test_numeric_constraint_on_string_rejected() -> None:
    from md_drf_codegen.schema.constraints import FieldConstraints

    spec = _minimal_spec()
    spec.types["ProductDetailResponse"].fields["productId"].constraints = FieldConstraints(
        min=1,
        max=50,
    )
    with pytest.raises(SchemaValidationError):
        validate_api_spec(spec)
