"""File generator safety tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from md_drf_codegen.utils.file_utils import FileExistsError, write_generated_files


def test_refuses_overwrite_without_force(tmp_path: Path) -> None:
    target = tmp_path / "out.py"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_generated_files({"out.py": "new"}, tmp_path, force=False)


def test_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "out.py"
    target.write_text("old", encoding="utf-8")
    write_generated_files({"out.py": "new"}, tmp_path, force=True)
    assert target.read_text(encoding="utf-8") == "new"


def test_preserve_if_exists_skips_even_with_force(tmp_path: Path) -> None:
    handlers = tmp_path / "product_handlers.py"
    handlers.write_text("custom", encoding="utf-8")
    views = tmp_path / "product_views.py"
    views.write_text("old", encoding="utf-8")
    written = write_generated_files(
        {
            "product_handlers.py": "generated-handlers",
            "product_views.py": "generated-views",
        },
        tmp_path,
        force=True,
        preserve_if_exists=frozenset({"product_handlers.py"}),
    )
    assert handlers.read_text(encoding="utf-8") == "custom"
    assert views.read_text(encoding="utf-8") == "generated-views"
    assert handlers.resolve() not in written


def test_force_preserved_overwrites_handlers(tmp_path: Path) -> None:
    handlers = tmp_path / "product_handlers.py"
    handlers.write_text("custom", encoding="utf-8")
    write_generated_files(
        {"product_handlers.py": "generated-handlers"},
        tmp_path,
        force=True,
        preserve_if_exists=frozenset({"product_handlers.py"}),
        force_preserved=True,
    )
    assert handlers.read_text(encoding="utf-8") == "generated-handlers"


def test_preserve_appends_missing_handler_functions(tmp_path: Path) -> None:
    handlers = tmp_path / "product_handlers.py"
    handlers.write_text(
        "from typing import Any\n\n"
        "def handle_list_products(*, request: object) -> dict[str, Any]:\n"
        "    return {'custom': True}\n",
        encoding="utf-8",
    )
    generated = (
        "from typing import Any\n\n"
        "def handle_list_products(*, request: object) -> dict[str, Any]:\n"
        "    return {}\n\n\n"
        "def handle_create_product(*, request: object) -> dict[str, Any]:\n"
        "    return {'ok': True}\n"
    )
    written = write_generated_files(
        {"product_handlers.py": generated},
        tmp_path,
        force=True,
        preserve_if_exists=frozenset({"product_handlers.py"}),
    )
    content = handlers.read_text(encoding="utf-8")
    assert "return {'custom': True}" in content
    assert "def handle_create_product(" in content
    assert "return {'ok': True}" in content
    assert handlers.resolve() in written


def test_check_skips_preserved_existing_files(tmp_path: Path) -> None:
    handlers = tmp_path / "product_handlers.py"
    handlers.write_text("custom", encoding="utf-8")
    views = tmp_path / "product_views.py"
    views.write_text("generated-views\n", encoding="utf-8")
    write_generated_files(
        {
            "product_handlers.py": "would-differ",
            "product_views.py": "generated-views\n",
        },
        tmp_path,
        check=True,
        preserve_if_exists=frozenset({"product_handlers.py"}),
    )


def test_check_detects_diff(tmp_path: Path) -> None:
    target = tmp_path / "out.py"
    target.write_text("old\n", encoding="utf-8")
    from md_drf_codegen.errors import CodegenError

    with pytest.raises(CodegenError, match="CHECK_FAILED"):
        write_generated_files({"out.py": "new\n"}, tmp_path, check=True)
