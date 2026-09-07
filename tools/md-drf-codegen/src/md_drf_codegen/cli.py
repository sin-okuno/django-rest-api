"""CLI commands: extract / validate / generate / build."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from md_drf_codegen.commands.build import run_build
from md_drf_codegen.commands.extract import run_extract
from md_drf_codegen.commands.generate import run_generate
from md_drf_codegen.commands.validate import run_validate
from md_drf_codegen.errors import CodegenError

app = typer.Typer(
    name="md-drf-codegen",
    help="Markdown / YAML から DRF 向けコードを生成するツール。",
    no_args_is_help=True,
    add_completion=False,
)


class TargetOption(StrEnum):
    YAML = "yaml"
    SERIALIZER = "serializer"
    ALL = "all"


InputMarkdown = Annotated[
    Path,
    typer.Argument(exists=True, dir_okay=False, readable=True, help="入力 Markdown"),
]
OutputYaml = Annotated[
    Path | None,
    typer.Option("--output", "-o", help="出力 YAML パス"),
]
InputYaml = Annotated[
    Path,
    typer.Argument(exists=True, dir_okay=False, readable=True, help="入力 YAML"),
]
OutputDir = Annotated[
    Path | None,
    typer.Option("--output", "-o", help="生成物の出力ディレクトリ"),
]
Target = Annotated[
    TargetOption,
    typer.Option("--target", help="生成ターゲット: yaml / serializer / all"),
]
Force = Annotated[
    bool,
    typer.Option("--force", help="既存ファイルを上書きする"),
]
Check = Annotated[
    bool,
    typer.Option("--check", help="差分チェックのみ（CI向け）"),
]


def _handle_error(exc: CodegenError) -> None:
    typer.secho(str(exc), fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1) from exc


@app.command("extract")
def extract_command(input_path: InputMarkdown, output: OutputYaml = None) -> None:
    """Markdown から API一覧 / 型定義を抽出し YAML を書き出す。"""
    try:
        result = run_extract(input_path, output)
    except CodegenError as exc:
        _handle_error(exc)
    typer.secho(f"Wrote {result}", fg=typer.colors.GREEN)


@app.command("validate")
def validate_command(yaml_path: InputYaml) -> None:
    """YAML を Pydantic スキーマと参照整合性で検証する。"""
    try:
        _spec, warnings = run_validate(yaml_path)
    except CodegenError as exc:
        _handle_error(exc)

    for warning in warnings:
        typer.secho(f"WARNING: {warning}", fg=typer.colors.YELLOW, err=True)
    typer.secho(f"OK: {yaml_path}", fg=typer.colors.GREEN)


@app.command("generate")
def generate_command(
    yaml_path: InputYaml,
    output: OutputDir = None,
    target: Target = TargetOption.ALL,
    force: Force = False,
    check: Check = False,
) -> None:
    """YAML から Serializer / View / URL / 基本テストを生成する。"""
    try:
        results = run_generate(
            yaml_path,
            output,
            target=target.value,
            force=force,
            check=check,
        )
    except CodegenError as exc:
        _handle_error(exc)
    if check:
        typer.secho("OK: generated output matches existing files", fg=typer.colors.GREEN)
    else:
        for path in results:
            typer.secho(f"Wrote {path}", fg=typer.colors.GREEN)


@app.command("build")
def build_command(
    input_path: InputMarkdown,
    output: OutputDir = None,
    target: Target = TargetOption.ALL,
    force: Force = False,
    check: Check = False,
) -> None:
    """extract → validate → generate をまとめて実行する。"""
    try:
        results = run_build(
            input_path,
            output,
            target=target.value,
            force=force,
            check=check,
        )
    except CodegenError as exc:
        _handle_error(exc)
    if check:
        typer.secho("OK: generated output matches existing files", fg=typer.colors.GREEN)
    else:
        for path in results:
            typer.secho(f"Wrote {path}", fg=typer.colors.GREEN)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
