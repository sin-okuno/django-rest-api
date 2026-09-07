"""extract command implementation."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.generator.yaml_generator import generate_yaml_file

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_SPECS_DIR = PACKAGE_ROOT / "generated-specs"


def run_extract(input_path: Path, output: Path | None = None) -> Path:
    input_abs = input_path.resolve()
    spec = extract_from_markdown(input_abs)
    output_abs = (output or DEFAULT_GENERATED_SPECS_DIR / f"{input_abs.stem}-api.yaml").resolve()
    return generate_yaml_file(spec, output_abs)
