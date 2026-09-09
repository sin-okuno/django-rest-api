"""Parser tests."""

from __future__ import annotations

import pytest

from md_drf_codegen.errors import MissingSectionError, SchemaValidationError
from md_drf_codegen.parser import (
    parse_api_endpoints,
    parse_markdown_content,
    parse_path_parameters,
    parse_type_definitions,
)


def test_parse_api_list() -> None:
    content = """# Sample

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| getProduct | 詳細 | GET | /api/products/{productId} | - | ProductDetailResponse | 単一取得 |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable | 備考 |
| --- | --- | --- | --- | --- | --- |
| ProductDetailResponse | productId | string | true | false | 製品 ID |
"""
    doc = parse_markdown_content(content, source_path="sample.md")
    apis = parse_api_endpoints(doc)
    assert len(apis) == 1
    assert apis[0].id == "getProduct"
    assert apis[0].request_type is None
    assert apis[0].remarks == "単一取得"
    types = parse_type_definitions(doc)
    assert types["ProductDetailResponse"].fields["productId"].remarks == "製品 ID"


def test_missing_api_section_raises() -> None:
    content = "# T\n\n## 型定義\n\n| 型名 | プロパティ | 型 | 必須 | Nullable |\n"
    with pytest.raises(MissingSectionError):
        parse_markdown_content(content, source_path="x.md")


def test_dash_becomes_null() -> None:
    content = """# T

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| listProducts | 一覧 | GET | /api/products | - | ProductList |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable |
| --- | --- | --- | --- | --- |
| ProductList | items | string[] | true | false |
"""
    doc = parse_markdown_content(content, source_path="x.md")
    apis = parse_api_endpoints(doc)
    assert apis[0].request_type is None


def test_unsupported_method_raises() -> None:
    content = """# T

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| deleteProduct | 削除 | DELETE | /api/products/1 | - | null |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable |
| --- | --- | --- | --- | --- |
"""
    doc = parse_markdown_content(content, source_path="x.md")
    with pytest.raises(SchemaValidationError):
        parse_api_endpoints(doc)


def test_parse_legacy_type_definitions() -> None:
    content = """# T

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| loadDetail | 詳細 | GET | /api/products/{productId} | - | ProductDetailApiResponse |

## 型定義

| カテゴリー | 型名 | プロパティ | 型 | 任意 | 最大桁数 | 小数桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| api | ProductDetailApiResponse | productId | string | false | 50 | - | ID |
| view | ProductDetail | productId | string | false | 50 | - | ignored |
"""
    doc = parse_markdown_content(content, source_path="legacy.md")
    types = parse_type_definitions(doc)
    assert "ProductDetailApiResponse" in types
    assert "ProductDetail" not in types
    field = types["ProductDetailApiResponse"].fields["productId"]
    assert field.required is True
    assert field.constraints is not None
    assert field.constraints.max_length == 50


def test_parse_type_definitions() -> None:
    content = """# T

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| getProduct | 詳細 | GET | /api/x | - | ProductDetailResponse |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable |
| --- | --- | --- | --- | --- |
| ProductDetailResponse | productId | string | true | false |
| ProductDetailResponse | description | string | false | true |
"""
    doc = parse_markdown_content(content, source_path="x.md")
    types = parse_type_definitions(doc)
    assert "ProductDetailResponse" in types
    assert types["ProductDetailResponse"].fields["description"].nullable is True
    assert types["ProductDetailResponse"].fields["description"].required is False


def test_parse_path_parameters() -> None:
    content = """# T

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| getProduct | 詳細 | GET | /api/products/{productId} | - | ProductDetailResponse |

## パスパラメータ

| パラメータ名 | 型 | 制約 | 備考 |
| --- | --- | --- | --- |
| productId | string | 半角英数字, 最大20文字 | URL 上の製品 ID |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable |
| --- | --- | --- | --- | --- |
| ProductDetailResponse | productId | string | true | false |
"""
    doc = parse_markdown_content(content, source_path="x.md")
    path_params = parse_path_parameters(doc)
    assert "productId" in path_params
    assert path_params["productId"].param_type == "string"
    assert path_params["productId"].constraints is not None
    assert path_params["productId"].constraints.max_length == 20
    assert path_params["productId"].remarks == "URL 上の製品 ID"
