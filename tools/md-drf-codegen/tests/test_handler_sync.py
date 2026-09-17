"""Tests for appending missing handler functions."""

from __future__ import annotations

from md_drf_codegen.utils.handler_sync import merge_missing_handler_functions


def test_merge_appends_only_missing_functions() -> None:
    existing = (
        "from typing import Any\n\n"
        "def handle_a(*, request: object) -> dict[str, Any]:\n"
        "    return {'a': 1}\n"
    )
    generated = (
        "from typing import Any\n\n"
        "def handle_a(*, request: object) -> dict[str, Any]:\n"
        "    return {}\n\n\n"
        "def handle_b(*, request: object) -> dict[str, Any]:\n"
        "    return {'b': 2}\n"
    )
    merged = merge_missing_handler_functions(existing, generated)
    assert "return {'a': 1}" in merged
    assert "def handle_b(" in merged
    assert "return {'b': 2}" in merged
    assert merged.count("def handle_a(") == 1


def test_merge_noop_when_all_present() -> None:
    existing = "def handle_a():\n    return 1\n"
    generated = "def handle_a():\n    return 0\n"
    assert merge_missing_handler_functions(existing, generated) == existing
