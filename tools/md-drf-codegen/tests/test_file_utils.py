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


def test_check_detects_diff(tmp_path: Path) -> None:
    target = tmp_path / "out.py"
    target.write_text("old\n", encoding="utf-8")
    from md_drf_codegen.errors import CodegenError

    with pytest.raises(CodegenError, match="CHECK_FAILED"):
        write_generated_files({"out.py": "new\n"}, tmp_path, check=True)
