"""build command: extract → validate → generate."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.commands.extract import DEFAULT_GENERATED_SPECS_DIR, run_extract
from md_drf_codegen.commands.generate import DEFAULT_GENERATED_DIR, run_generate
from md_drf_codegen.commands.validate import run_validate


def run_build(
    input_path: Path,
    output: Path | None = None,
    *,
    target: str = "all",
    force: bool = False,
    check: bool = False,
) -> list[Path]:
    input_abs = input_path.resolve()

    if target == "yaml":
        yaml_output = output or (DEFAULT_GENERATED_SPECS_DIR / f"{input_abs.stem}-api.yaml")
        return [run_extract(input_abs, yaml_output)]

    yaml_path = DEFAULT_GENERATED_SPECS_DIR / f"{input_abs.stem}-api.yaml"
    run_extract(input_abs, yaml_path)
    run_validate(yaml_path)

    if target == "serializer":
        gen_output = output or (DEFAULT_GENERATED_DIR / input_abs.stem)
        return run_generate(yaml_path, gen_output, target="serializer", force=force, check=check)

    gen_output = output or (DEFAULT_GENERATED_DIR / input_abs.stem)
    return run_generate(yaml_path, gen_output, target="all", force=force, check=check)
