"""Naming utility tests."""

from md_drf_codegen.utils.naming import (
    api_id_to_url_name,
    camel_to_snake,
    django_route,
    serializer_class_name,
)


def test_camel_to_snake() -> None:
    assert camel_to_snake("productId") == "product_id"


def test_django_route() -> None:
    assert django_route("/api/products/{productId}") == "api/products/<str:product_id>"


def test_api_id_to_url_name() -> None:
    assert api_id_to_url_name("getProduct") == "get-product"


def test_serializer_class_name() -> None:
    assert serializer_class_name("ProductDetailResponse") == "ProductDetailResponseSerializer"
