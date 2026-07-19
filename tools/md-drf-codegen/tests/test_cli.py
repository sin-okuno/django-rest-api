"""CLI integration tests for extract / validate / generate."""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from md_drf_codegen.cli import app

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "specs" / "product-structure.md"
runner = CliRunner()


def test_extract_command(tmp_path: Path) -> None:
    output = tmp_path / "product-structure.yaml"
    result = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert "Wrote" in result.output


def test_validate_command(tmp_path: Path) -> None:
    output = tmp_path / "product-structure.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(output)])
    assert extract.exit_code == 0, extract.output
    result = runner.invoke(app, ["validate", str(output)])
    assert result.exit_code == 0, result.output
    assert "OK:" in result.output


def test_validate_fails_on_bad_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "\n".join(
            [
                "version: 1",
                "title: t",
                "apis:",
                "  - id: badId",
                "    name: x",
                "    method: GET",
                "    path: /x",
                "    requestType: Missing",
                "    responseType: null",
                "    description: ''",
                "types: []",
            ]
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", str(bad)])
    assert result.exit_code == 1


def test_generate_command(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-structure.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    assert extract.exit_code == 0, extract.output

    out_dir = tmp_path / "generated"
    result = runner.invoke(app, ["generate", str(yaml_out), "-o", str(out_dir)])
    assert result.exit_code == 0, result.output
    assert "Wrote" in result.output

    expected = (
        "__init__.py",
        "product_structure_serializers.py",
        "product_structure_views.py",
        "urls.py",
        "product_structure_handlers.py",
        "conftest.py",
        "test_generated_api.py",
    )
    for name in expected:
        path = out_dir / name
        assert path.exists(), name
        ast.parse(path.read_text(encoding="utf-8"))

    views = (out_dir / "product_structure_views.py").read_text(encoding="utf-8")
    assert "class ApiProductsProductIdView" in views
    assert "def get(" in views
    assert "def put(" in views
    assert "product_id" in views
    assert "from .product_structure_handlers import" in views

    tests = (out_dir / "test_generated_api.py").read_text(encoding="utf-8")
    assert "def test_" in tests
    assert "pass" not in tests
    assert "product_structure_serializers" in tests


def test_generate_default_output_uses_yaml_stem(tmp_path: Path, monkeypatch) -> None:
    """-o 省略時は examples/generated/<yaml-stem>/ に出力する。"""
    from md_drf_codegen.commands import generate as generate_mod

    monkeypatch.setattr(generate_mod, "DEFAULT_GENERATED_DIR", tmp_path / "generated")

    yaml_out = tmp_path / "product-structure.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    assert extract.exit_code == 0, extract.output

    result = runner.invoke(app, ["generate", str(yaml_out)])
    assert result.exit_code == 0, result.output

    out_dir = tmp_path / "generated" / "product-structure"
    assert (out_dir / "product_structure_serializers.py").exists()
    assert (out_dir / "product_structure_views.py").exists()
    assert (out_dir / "product_structure_handlers.py").exists()
    conftest = (out_dir / "conftest.py").read_text(encoding="utf-8")
    assert '_PACKAGE_NAME = "product_structure"' in conftest
    tests = (out_dir / "test_generated_api.py").read_text(encoding="utf-8")
    assert "from product_structure.product_structure_serializers import" in tests
