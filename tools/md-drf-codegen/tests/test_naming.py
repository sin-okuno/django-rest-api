"""Tests for naming helpers."""

from __future__ import annotations

from md_drf_codegen.generator.naming import (
    camel_to_snake,
    django_route,
    handler_class_name,
    url_name,
    view_class_name,
)


def test_camel_to_snake() -> None:
    assert camel_to_snake("productId") == "product_id"
    assert camel_to_snake("ProductID") == "product_id"
    assert camel_to_snake("api") == "api"


def test_django_route_converts_path_params() -> None:
    assert django_route("/api/products/{productId}") == "api/products/<str:product_id>"
    assert django_route("/api/products/tree") == "api/products/tree"


def test_view_class_name() -> None:
    assert view_class_name("/api/products/tree") == "ApiProductsTreeView"
    assert view_class_name("/api/products/{productId}") == "ApiProductsProductIdView"


def test_url_name_kebab_case() -> None:
    assert url_name("/api/products/tree") == "api-products-tree"
    assert url_name("/api/products/{productId}") == "api-products-product-id"


def test_handler_class_name() -> None:
    assert handler_class_name("loadDetail") == "LoadDetailHandler"
    assert handler_class_name("loadTree") == "LoadTreeHandler"
    assert handler_class_name("updateDetail") == "UpdateDetailHandler"
