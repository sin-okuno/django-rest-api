"""View and URL generator tests."""

from __future__ import annotations

import ast

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.generator import GenerateTarget, generate_code_files
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
        path_parameters={
            "productId": PathParameterDefinition(
                type="string",
                constraints=FieldConstraints(max_length=50),
            ),
        },
    )


def test_views_and_urls_generate() -> None:
    files = generate_code_files(_product_spec(), target=GenerateTarget.ALL, package_name="product")
    views = files["product_views.py"]
    handlers = files["product_handlers.py"]
    urls = files["urls.py"]
    path_validators = files["product_path_validators.py"]
    assert "handle_get_product" in views
    assert "handle_update_product" in views
    assert "ProductDetailResponseSerializer" in views
    assert "response_serializer" in views
    assert "return Response(response_serializer.data)" in views
    assert "NotImplementedError" not in views
    assert "def handle_get_product(" in handlers
    assert "def handle_update_product(" in handlers
    assert "product_id" in views
    assert "validate_product_id" in views
    assert "ValidationError" in path_validators
    assert "get-product" in urls or "list-products" not in urls
    assert "<str:product_id>" in urls
    ast.parse(views)
    ast.parse(handlers)
    ast.parse(urls)


def test_put_api_includes_path_parameter() -> None:
    files = generate_code_files(_product_spec(), target=GenerateTarget.ALL, package_name="product")
    views = files["product_views.py"]
    assert "def put(" in views
    assert "product_id: str" in views
    assert "request.data" in views
    assert "request.query_params" not in views.split("def put(")[1].split("def ")[0]


def test_get_with_path_and_query_parameters() -> None:
    spec = ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="getProduct",
                name="詳細",
                method=HttpMethod.GET,
                path="/api/products/{productId}",
                requestType="ProductDetailQuery",
                responseType="ProductDetailResponse",
            ),
        ],
        types={
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
        },
        path_parameters={
            "productId": PathParameterDefinition(
                type="string",
                constraints=FieldConstraints(max_length=50),
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.ALL, package_name="product")
    views = files["product_views.py"]
    get_block = views.split("def get(")[1].split("def ")[0]
    assert "product_id: str" in get_block
    assert "validate_product_id" in get_block
    assert "request.query_params" in get_block
    assert "ProductDetailQuerySerializer" in get_block
    assert "request.data" not in get_block


def test_get_with_query_parameters_only() -> None:
    spec = ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="listProducts",
                name="一覧",
                method=HttpMethod.GET,
                path="/api/products",
                requestType="ProductListRequest",
                responseType="ProductListResponse",
            ),
        ],
        types={
            "ProductListRequest": TypeDefinition(
                fields={
                    "keyword": FieldDefinition(type="string", required=False, nullable=False),
                    "page": FieldDefinition(type="integer", required=False, nullable=False),
                }
            ),
            "ProductListResponse": TypeDefinition(
                fields={
                    "items": FieldDefinition(
                        type="string[]", required=True, nullable=False
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.ALL, package_name="product")
    views = files["product_views.py"]
    assert "request.query_params" in views
    assert "ProductListRequestSerializer" in views


def test_product_markdown_extracts_query_types() -> None:
    from pathlib import Path

    product_md = Path(__file__).resolve().parents[1] / "examples" / "product.md"
    spec = extract_from_markdown(product_md)
    list_api = next(api for api in spec.apis if api.id == "listProducts")
    get_api = next(api for api in spec.apis if api.id == "getProduct")
    put_api = next(api for api in spec.apis if api.id == "updateProduct")

    assert list_api.request_type == "ProductListRequest"
    assert get_api.request_type == "ProductDetailQuery"
    assert put_api.request_type == "ProductUpdateRequest"
    assert "ProductListRequest" in spec.types
    assert "ProductDetailQuery" in spec.types

    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="product")
    serializers = "\n".join(files.values())
    assert "ProductListRequestSerializer" in serializers
    assert "ProductDetailQuerySerializer" in serializers
