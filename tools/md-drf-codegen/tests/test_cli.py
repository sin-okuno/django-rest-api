"""CLI integration tests."""

from __future__ import annotations

import ast
from pathlib import Path

from typer.testing import CliRunner

from md_drf_codegen.cli import app

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "product.md"
runner = CliRunner()


def test_extract_command(tmp_path: Path) -> None:
    output = tmp_path / "product-api.yaml"
    result = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "getProduct" in text
    assert "ProductListRequest" in text
    assert "ProductDetailQuery" in text
    assert "types:" in text


def test_validate_command(tmp_path: Path) -> None:
    output = tmp_path / "product-api.yaml"
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
                "apis:",
                "  - id: badId",
                "    name: x",
                "    method: GET",
                "    path: /x",
                "    requestType: Missing",
                "    responseType: null",
                "types: {}",
            ]
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", str(bad)])
    assert result.exit_code == 1


def test_generate_serializer_target(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-api.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    assert extract.exit_code == 0, extract.output

    out_dir = tmp_path / "product"
    result = runner.invoke(
        app,
        ["generate", str(yaml_out), "-o", str(out_dir), "--target", "serializer"],
    )
    assert result.exit_code == 0, result.output
    ser_file = out_dir / "product_serializers.py"
    assert ser_file.exists()
    ast.parse(ser_file.read_text(encoding="utf-8"))


def test_generate_all_target(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-api.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    assert extract.exit_code == 0, extract.output

    out_dir = tmp_path / "product"
    result = runner.invoke(
        app,
        ["generate", str(yaml_out), "-o", str(out_dir), "--target", "all"],
    )
    assert result.exit_code == 0, result.output

    for name in (
        "product_serializers.py",
        "product_handlers.py",
        "product_views.py",
        "product_path_validators.py",
        "urls.py",
        "openapi.yaml",
        "test_serializers.py",
        "test_urls.py",
        "test_views.py",
    ):
        path = out_dir / name
        assert path.exists(), name
        if name.endswith(".py"):
            ast.parse(path.read_text(encoding="utf-8"))

    openapi = (out_dir / "openapi.yaml").read_text(encoding="utf-8")
    assert "openapi: 3.0.3" in openapi

    views = (out_dir / "product_views.py").read_text(encoding="utf-8")
    assert "handle_update_product" in views
    assert "ProductDetailResponseSerializer" in views
    assert "response_serializer" in views
    assert "def put(" in views
    handlers = (out_dir / "product_handlers.py").read_text(encoding="utf-8")
    assert "def handle_update_product(" in handlers


def test_generate_refuses_overwrite_without_force(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-api.yaml"
    runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    out_dir = tmp_path / "product"
    gen_args = ["generate", str(yaml_out), "-o", str(out_dir), "--target", "serializer"]
    first = runner.invoke(app, gen_args)
    assert first.exit_code == 0
    second = runner.invoke(app, gen_args)
    assert second.exit_code == 1
    assert "FILE_EXISTS_ERROR" in second.output


def test_generate_force_overwrites(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-api.yaml"
    runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    out_dir = tmp_path / "product"
    runner.invoke(app, ["generate", str(yaml_out), "-o", str(out_dir), "--target", "serializer"])
    result = runner.invoke(
        app,
        ["generate", str(yaml_out), "-o", str(out_dir), "--target", "serializer", "--force"],
    )
    assert result.exit_code == 0, result.output


def test_build_command(tmp_path: Path, monkeypatch) -> None:
    from md_drf_codegen.commands import build as build_mod
    from md_drf_codegen.commands import extract as extract_mod
    from md_drf_codegen.commands import generate as generate_mod

    monkeypatch.setattr(extract_mod, "DEFAULT_GENERATED_SPECS_DIR", tmp_path / "generated-specs")
    monkeypatch.setattr(generate_mod, "DEFAULT_GENERATED_DIR", tmp_path / "generated")
    monkeypatch.setattr(build_mod, "DEFAULT_GENERATED_SPECS_DIR", tmp_path / "generated-specs")
    monkeypatch.setattr(build_mod, "DEFAULT_GENERATED_DIR", tmp_path / "generated")

    result = runner.invoke(app, ["build", str(FIXTURE), "--target", "all"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "generated-specs" / "product-api.yaml").exists()
    assert (tmp_path / "generated" / "product" / "product_views.py").exists()


def test_generate_openapi_target(tmp_path: Path) -> None:
    yaml_out = tmp_path / "product-api.yaml"
    extract = runner.invoke(app, ["extract", str(FIXTURE), "-o", str(yaml_out)])
    assert extract.exit_code == 0, extract.output

    openapi_out = tmp_path / "product-api.openapi.yaml"
    result = runner.invoke(
        app,
        ["generate", str(yaml_out), "-o", str(openapi_out), "--target", "openapi"],
    )
    assert result.exit_code == 0, result.output
    assert openapi_out.exists()
    text = openapi_out.read_text(encoding="utf-8")
    assert "openapi: 3.0.3" in text
    assert "operationId: listProducts" in text


def test_build_openapi_target(tmp_path: Path, monkeypatch) -> None:
    from md_drf_codegen.commands import build as build_mod
    from md_drf_codegen.commands import extract as extract_mod

    monkeypatch.setattr(extract_mod, "DEFAULT_GENERATED_SPECS_DIR", tmp_path / "generated-specs")
    monkeypatch.setattr(build_mod, "DEFAULT_GENERATED_SPECS_DIR", tmp_path / "generated-specs")

    result = runner.invoke(app, ["build", str(FIXTURE), "--target", "openapi"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "generated-specs" / "product-api.openapi.yaml").exists()
