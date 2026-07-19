"""Tests for Markdown parsing of API一覧 and 型定義."""

from __future__ import annotations

import pytest

from md_drf_codegen.errors import MissingSectionError
from md_drf_codegen.parser import find_section, find_table, parse_markdown_content

SAMPLE = """# サンプル API

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 説明 |
| --- | --- | --- | --- | --- | --- | --- |
| getItem | 取得 | GET | /api/items/{id} | - | ItemResponse | 1件取得 |
| createItem | 作成 | POST | /api/items | ItemRequest | ItemResponse | 作成 |

## 型定義

| カテゴリー | 型名 | プロパティ | 型 | 任意 | 説明 |
| --- | --- | --- | --- | --- | --- |
| api | ItemRequest | name | string | false | 名前 |
| api | ItemRequest | note | string \\| null | true | 備考 |
| api | ItemResponse | id | string | false | ID |
| view | ItemView | name | string | false | 画面用 |
"""


def test_parse_required_sections() -> None:
    doc = parse_markdown_content(SAMPLE, source_path="sample.md")
    assert doc.title == "サンプル API"
    assert {s.heading for s in doc.sections} >= {"API一覧", "型定義"}


def test_parse_api_table() -> None:
    doc = parse_markdown_content(SAMPLE, source_path="sample.md")
    table = find_table(find_section(doc, "API一覧"), ["API ID", "メソッド", "パス"])
    assert len(table.rows) == 2
    assert table.rows[0]["API ID"] == "getItem"
    assert table.rows[0]["メソッド"] == "GET"
    assert table.rows[1]["パス"] == "/api/items"


def test_parse_type_table_with_escaped_pipe() -> None:
    doc = parse_markdown_content(SAMPLE, source_path="sample.md")
    table = find_table(find_section(doc, "型定義"), ["カテゴリー", "型名", "プロパティ", "型"])
    note_row = next(row for row in table.rows if row["プロパティ"] == "note")
    assert note_row["型"] == "string | null"


def test_missing_section_raises() -> None:
    with pytest.raises(MissingSectionError):
        parse_markdown_content("# Only Title\n\n## その他\n\ntext\n", source_path="bad.md")
