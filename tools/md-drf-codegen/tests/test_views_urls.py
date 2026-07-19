"""Tests for APIView and URL generation."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.generator import generate_all_code, generate_all_from_yaml
from md_drf_codegen.generator.urls_context import build_urls_context
from md_drf_codegen.generator.views_context import build_views_context
from md_drf_codegen.yaml_io import parse_api_spec_yaml

MERGED_SPEC = """
version: 1
title: Merge Demo
source: test
apis:
  - id: loadDetail
    name: load
    method: GET
    path: /api/products/{productId}
    requestType: null
    responseType: ProductDetail
    description: get
  - id: updateDetail
    name: update
    method: PUT
    path: /api/products/{productId}
    requestType: ProductUpdate
    responseType: ProductDetail
    description: put
  - id: loadTree
    name: tree
    method: GET
    path: /api/products/tree
    requestType: TreeRequest
    responseType: TreeResponse
    description: tree
types:
  - name: ProductDetail
    category: api
    properties:
      - name: id
        type: string
        nullable: false
        optional: false
        description: id
  - name: ProductUpdate
    category: api
    properties:
      - name: name
        type: string
        nullable: false
        optional: false
        description: name
  - name: TreeRequest
    category: api
    properties:
      - name: keyword
        type: string
        nullable: false
        optional: false
        description: keyword
  - name: TreeResponse
    category: api
    properties:
      - name: nodes
        type: string[]
        nullable: false
        optional: false
        description: nodes
"""


def test_same_path_get_put_merged_into_one_view() -> None:
    spec = parse_api_spec_yaml(MERGED_SPEC)
    context = build_views_context(spec)
    by_path = {view.path: view for view in context.views}
    assert "/api/products/{productId}" in by_path
    detail = by_path["/api/products/{productId}"]
    methods = {method.http_method for method in detail.methods}
    assert methods == {"get", "put"}
    assert detail.class_name == "ApiProductsProductIdView"
    put = next(method for method in detail.methods if method.http_method == "put")
    assert put.request_serializer == "ProductUpdateSerializer"
    assert put.response_serializer == "ProductDetailSerializer"
    assert put.path_params[0].snake_name == "product_id"


def test_fixed_urls_before_dynamic() -> None:
    spec = parse_api_spec_yaml(MERGED_SPEC)
    urls = build_urls_context(spec)
    names = [pattern.name for pattern in urls.patterns]
    assert names == ["api-products-tree", "api-products-product-id"]
    assert urls.patterns[0].is_dynamic is False
    assert urls.patterns[1].is_dynamic is True
    assert urls.patterns[1].django_route == "api/products/<str:product_id>"


def test_generated_views_urls_registry_ast_parseable() -> None:
    files = generate_all_code(parse_api_spec_yaml(MERGED_SPEC))
    for name in (
        "test_serializers.py",
        "test_views.py",
        "urls.py",
        "test_handlers.py",
        "test_generated_api.py",
        "conftest.py",
        "__init__.py",
    ):
        assert name in files
        ast.parse(files[name])

    views = files["test_views.py"]
    assert "class ApiProductsProductIdView" in views
    assert "def get(" in views
    assert "def put(" in views
    assert "LoadDetailHandler()" in views
    assert "handler.handle(" in views
    assert "product_id" in views
    assert "ProductUpdateSerializer(data=request.data)" in views
    assert "TreeRequestSerializer(data=request.query_params)" in views
    assert "get_handler" not in views
    assert "NotImplementedError" not in views
    assert "from .test_handlers import" in views
    assert "from .test_serializers import" in views

    handlers = files["test_handlers.py"]
    assert "class LoadDetailHandler" in handlers
    assert "def handle(" in handlers
    assert "register(" not in handlers
    assert "get_handler" not in handlers
    assert "NotImplementedError" in handlers  # non-GET stubs
    # GET handlers return demo payloads instead of raising.
    assert "sample-productId" in handlers or "sample-" in handlers

    urls = files["urls.py"]
    assert "from . import test_views as views" in urls
    tree_pos = urls.index("api-products-tree")
    detail_pos = urls.index("api-products-product-id")
    assert tree_pos < detail_pos


def test_product_fixture_generate_all_ast_parseable(product_structure_yaml: Path) -> None:
    files = generate_all_from_yaml(product_structure_yaml)
    for code in files.values():
        ast.parse(code)
    assert "product_structure_views.py" in files
    assert "product_structure_serializers.py" in files
    assert "product_structure_handlers.py" in files
    assert "ApiProductsTreeView" in files["product_structure_views.py"]
    assert "ApiProductsProductIdView" in files["product_structure_views.py"]
    assert "from .product_structure_handlers import" in files["product_structure_views.py"]
    assert "from . import product_structure_views as views" in files["urls.py"]


def test_duplicate_method_on_same_path_raises() -> None:
    raw = """
version: 1
title: Dup
source: t
apis:
  - id: a
    name: a
    method: GET
    path: /api/x
    requestType: null
    responseType: null
    description: a
  - id: b
    name: b
    method: GET
    path: /api/x
    requestType: null
    responseType: null
    description: b
types: []
"""
    with pytest.raises(SchemaValidationError, match="Duplicate HTTP method"):
        build_views_context(parse_api_spec_yaml(raw))
