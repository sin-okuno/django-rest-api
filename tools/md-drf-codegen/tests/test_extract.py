"""Tests for API extraction (api-category only)."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.extract import extract_from_document, extract_from_markdown
from md_drf_codegen.parser import parse_markdown_content

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "specs" / "product-structure.md"

SAMPLE = """# Demo

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 説明 |
| --- | --- | --- | --- | --- | --- | --- |
| load | 読込 | GET | /api/x | Req | Res | desc |

## 型定義

| カテゴリー | 型名 | プロパティ | 型 | 任意 | 説明 |
| --- | --- | --- | --- | --- | --- |
| api | Req | q | string | false | q |
| api | Req | optionalNote | string \\| null | true | note |
| api | Res | value | number | false | v |
| view | ViewModel | q | string | false | ignored |
| action | Payload | q | string | false | ignored |
"""


def test_extract_apis_and_api_types_only() -> None:
    doc = parse_markdown_content(SAMPLE, source_path="demo.md")
    spec = extract_from_document(doc, source_label="demo.md")
    assert len(spec.apis) == 1
    assert spec.apis[0].id == "load"
    assert spec.apis[0].request_type == "Req"
    assert spec.apis[0].response_type == "Res"
    type_names = {t.name for t in spec.types}
    assert type_names == {"Req", "Res"}
    assert all(t.category == "api" for t in spec.types)


def test_nullable_normalized_on_extract() -> None:
    doc = parse_markdown_content(SAMPLE, source_path="demo.md")
    spec = extract_from_document(doc)
    req = next(t for t in spec.types if t.name == "Req")
    note = next(p for p in req.properties if p.name == "optionalNote")
    assert note.type == "string"
    assert note.nullable is True
    assert note.optional is True


def test_extract_product_fixture() -> None:
    spec = extract_from_markdown(FIXTURE)
    assert len(spec.apis) == 3
    assert {t.name for t in spec.types} == {
        "ProductStructureApiRequest",
        "ProductTreeResponseDto",
        "ProductTreeNodeDto",
        "ProductDetailApiResponse",
        "ProductUpdateApiRequest",
    }
    request = next(t for t in spec.types if t.name == "ProductStructureApiRequest")
    category = next(p for p in request.properties if p.name == "categoryId")
    assert category.nullable is True
    assert category.type == "string"
    detail = next(t for t in spec.types if t.name == "ProductDetailApiResponse")
    by_name = {p.name: p for p in detail.properties}
    assert by_name["price"].type == "number"
    assert by_name["price"].max_digits == 12
    assert by_name["price"].decimal_places == 2
    assert by_name["revision"].type == "number"
    assert by_name["revision"].max_digits == 10
    assert by_name["revision"].decimal_places == 0
    assert by_name["description"].nullable is True
    assert by_name["description"].type == "string"
    assert by_name["description"].max_length == 500
    assert by_name["productName"].max_length == 100


def test_extract_digit_columns_from_markdown() -> None:
    sample = """# Demo

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 説明 |
| --- | --- | --- | --- | --- | --- | --- |
| load | 読込 | GET | /api/x | Req | Res | desc |

## 型定義

| カテゴリー | 型名 | プロパティ | 型 | 任意 | 最大桁数 | 小数桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| api | Req | q | string | false | 20 | - | q |
| api | Res | amount | number | false | 12 | 2 | money |
| api | Res | count | integer | false | 5 | - | count |
"""
    doc = parse_markdown_content(sample, source_path="digits.md")
    spec = extract_from_document(doc, source_label="digits.md")
    req = next(t for t in spec.types if t.name == "Req")
    assert req.properties[0].max_length == 20
    res = next(t for t in spec.types if t.name == "Res")
    by_name = {p.name: p for p in res.properties}
    assert by_name["amount"].max_digits == 12
    assert by_name["amount"].decimal_places == 2
    assert by_name["count"].max_digits == 5

