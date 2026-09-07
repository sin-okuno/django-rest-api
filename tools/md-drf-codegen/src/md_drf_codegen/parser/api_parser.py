"""Parse API一覧 table rows."""

from __future__ import annotations

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import normalize_cell
from md_drf_codegen.parser.markdown_parser import API_HEADERS, find_section, find_table
from md_drf_codegen.schema import ApiEndpoint, MarkdownDocument
from md_drf_codegen.schema.api import SUPPORTED_HTTP_METHODS


def parse_api_endpoints(document: MarkdownDocument) -> list[ApiEndpoint]:
    """Extract API endpoints from the API一覧 section."""
    section = find_section(document, "API一覧")
    table = find_table(section, API_HEADERS)
    endpoints: list[ApiEndpoint] = []
    seen_ids: set[str] = set()

    for row in table.rows:
        method_raw = normalize_cell(row.get("メソッド", "")).upper()
        if method_raw not in SUPPORTED_HTTP_METHODS:
            raise SchemaValidationError(
                f'Unsupported API method "{method_raw}".',
                section="API一覧",
                line=table.line,
                fix=f"Use one of {', '.join(sorted(SUPPORTED_HTTP_METHODS))}.",
            )

        api_id = normalize_cell(row.get("API ID", ""))
        if not api_id:
            raise SchemaValidationError(
                "API ID must not be empty.",
                section="API一覧",
                line=table.line,
                fix="Provide a non-empty API ID for every row.",
            )
        if api_id in seen_ids:
            raise SchemaValidationError(
                f'Duplicate API ID "{api_id}".',
                section="API一覧",
                line=table.line,
                fix="Ensure each API ID is unique.",
            )
        seen_ids.add(api_id)

        endpoints.append(
            ApiEndpoint.model_validate(
                {
                    "id": api_id,
                    "name": normalize_cell(row.get("API名", "")),
                    "method": method_raw,
                    "path": normalize_cell(row.get("パス", "")),
                    "requestType": normalize_cell(row.get("リクエスト型", "")),
                    "responseType": normalize_cell(row.get("レスポンス型", "")),
                }
            )
        )
    return endpoints
