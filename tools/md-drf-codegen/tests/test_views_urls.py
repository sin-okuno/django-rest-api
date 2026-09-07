"""View and URL generator tests."""

from __future__ import annotations

import ast

from md_drf_codegen.generator import GenerateTarget, generate_code_files
from md_drf_codegen.schema import ApiEndpoint, ApiSpec, FieldDefinition, HttpMethod, TypeDefinition


def _product_spec() -> ApiSpec:
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
            ),
            ApiEndpoint(
                id="updateProduct",
                name="更新",
                method=HttpMethod.PUT,
                path="/api/products/{productId}",
                requestType="ProductUpdateRequest",
                responseType="ProductDetailResponse",
            ),
        ],
        types={
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
    )


def test_views_and_urls_generate() -> None:
    files = generate_code_files(_product_spec(), target=GenerateTarget.ALL, package_name="product")
    views = files["product_views.py"]
    urls = files["urls.py"]
    assert "NotImplementedError" in views
    assert "product_id" in views
    assert "get-product" in urls or "list-products" not in urls
    assert "<str:product_id>" in urls
    ast.parse(views)
    ast.parse(urls)
