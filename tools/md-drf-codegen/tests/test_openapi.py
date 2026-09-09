"""OpenAPI generator tests."""

from __future__ import annotations

import yaml

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.generator.openapi_generator import build_openapi_document
from md_drf_codegen.openapi_io import dump_openapi_yaml
from md_drf_codegen.schema import (
    ApiEndpoint,
    ApiSpec,
    FieldDefinition,
    HttpMethod,
    PathParameterDefinition,
    TypeDefinition,
)
from md_drf_codegen.schema.constraints import FieldConstraints


def _product_spec() -> ApiSpec:
    return ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="listProducts",
                name="製品一覧取得",
                method=HttpMethod.GET,
                path="/api/products",
                requestType="ProductListRequest",
                responseType="ProductListResponse",
            ),
            ApiEndpoint(
                id="getProduct",
                name="製品詳細取得",
                method=HttpMethod.GET,
                path="/api/products/{productId}",
                requestType="ProductDetailQuery",
                responseType="ProductDetailResponse",
            ),
            ApiEndpoint(
                id="updateProduct",
                name="製品更新",
                method=HttpMethod.PUT,
                path="/api/products/{productId}",
                requestType="ProductUpdateRequest",
                responseType="ProductDetailResponse",
            ),
        ],
        types={
            "ProductListRequest": TypeDefinition(
                fields={
                    "keyword": FieldDefinition(
                        type="string",
                        required=False,
                        nullable=False,
                        constraints=FieldConstraints(max_length=50),
                    ),
                }
            ),
            "ProductListResponse": TypeDefinition(
                fields={
                    "items": FieldDefinition(
                        type="ProductSummary[]", required=True, nullable=False
                    ),
                }
            ),
            "ProductSummary": TypeDefinition(
                fields={
                    "productId": FieldDefinition(type="string", required=True, nullable=False),
                }
            ),
            "ProductDetailQuery": TypeDefinition(
                fields={
                    "includeDeleted": FieldDefinition(
                        type="boolean", required=False, nullable=False
                    ),
                }
            ),
            "ProductDetailResponse": TypeDefinition(
                fields={
                    "productId": FieldDefinition(type="string", required=True, nullable=False),
                }
            ),
            "ProductUpdateRequest": TypeDefinition(
                fields={
                    "productName": FieldDefinition(type="string", required=True, nullable=False),
                }
            ),
        },
        path_parameters={
            "productId": PathParameterDefinition(
                type="string",
                constraints=FieldConstraints(
                    max_length=20,
                    format="halfwidth-alphanumeric",
                ),
            ),
        },
    )


def test_build_openapi_document_structure() -> None:
    doc = build_openapi_document(_product_spec(), title="Product API")
    assert doc["openapi"] == "3.0.3"
    assert doc["info"]["title"] == "Product API"

    list_get = doc["paths"]["/api/products"]["get"]
    assert list_get["operationId"] == "listProducts"
    assert any(p["name"] == "keyword" and p["in"] == "query" for p in list_get["parameters"])

    detail_get = doc["paths"]["/api/products/{productId}"]["get"]
    path_params = [p for p in detail_get["parameters"] if p["in"] == "path"]
    assert path_params[0]["name"] == "productId"
    assert path_params[0]["schema"]["maxLength"] == 20
    assert path_params[0]["schema"]["pattern"] == r"^[A-Za-z0-9]+$"

    update_put = doc["paths"]["/api/products/{productId}"]["put"]
    assert update_put["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "ProductUpdateRequest"
    )

    assert "ProductListResponse" in doc["components"]["schemas"]


def test_dump_openapi_yaml_from_product_markdown() -> None:
    from pathlib import Path

    product_md = Path(__file__).resolve().parents[1] / "examples" / "product.md"
    spec = extract_from_markdown(product_md)
    raw = dump_openapi_yaml(spec, title="Product API")
    assert raw.startswith("# AUTO-GENERATED FILE.")
    body = "\n".join(line for line in raw.splitlines() if not line.startswith("#"))
    doc = yaml.safe_load(body)
    assert doc["openapi"] == "3.0.3"
    assert "/api/products/{productId}" in doc["paths"]
    updated = doc["components"]["schemas"]["ProductDetailResponse"]["properties"][
        "updatedDate"
    ]
    assert updated["type"] == "string"
    assert updated["format"] == "date"
    assert updated["description"] == "最終更新日"


def test_date_and_datetime_openapi_formats() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "Sample": TypeDefinition(
                fields={
                    "updatedDate": FieldDefinition(
                        type="date", required=True, nullable=False
                    ),
                    "updatedAt": FieldDefinition(
                        type="datetime", required=True, nullable=False
                    ),
                }
            ),
        },
    )
    doc = build_openapi_document(spec, title="Sample")
    props = doc["components"]["schemas"]["Sample"]["properties"]
    assert props["updatedDate"] == {"type": "string", "format": "date"}
    assert props["updatedAt"] == {"type": "string", "format": "date-time"}
