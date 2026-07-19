"""extract command implementation."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.validate import validate_api_spec
from md_drf_codegen.yaml_io import write_api_spec_yaml

# commands/extract.py -> md_drf_codegen -> src -> md-drf-codegen
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_DIR = PACKAGE_ROOT / "examples" / "generated"


def run_extract(input_path: Path, output: Path | None = None) -> Path:
    input_abs = input_path.resolve()
    source_label = _relative_label(input_abs)
    spec = extract_from_markdown(input_abs, source_label=source_label)
    validate_api_spec(spec)

    output_abs = (output or DEFAULT_GENERATED_DIR / f"{input_abs.stem}.yaml").resolve()
    return write_api_spec_yaml(spec, output_abs)


def _relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
