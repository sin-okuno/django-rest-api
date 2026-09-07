"""generate command: YAML → DRF artifacts."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.generator import GenerateTarget, generate_from_yaml, write_generation_result
from md_drf_codegen.utils.naming import sanitize_module_name
from md_drf_codegen.yaml_io import dump_api_spec_yaml, load_api_spec_yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_DIR = PACKAGE_ROOT / "generated"


def run_generate(
    yaml_path: Path,
    output: Path | None = None,
    *,
    target: str = "all",
    force: bool = False,
    check: bool = False,
) -> list[Path]:
    input_abs = yaml_path.resolve()
    generate_target = GenerateTarget(target)

    if generate_target == GenerateTarget.YAML:
        spec = load_api_spec_yaml(input_abs)
        yaml_output = output or input_abs
        yaml_text = dump_api_spec_yaml(spec)
        if check:
            from md_drf_codegen.utils.file_utils import _check_files

            _check_files({yaml_output.name: yaml_text}, yaml_output.parent)
            return [yaml_output.resolve()]
        yaml_output.parent.mkdir(parents=True, exist_ok=True)
        yaml_output.write_text(yaml_text, encoding="utf-8")
        return [yaml_output.resolve()]

    output_dir = _resolve_output_dir(output, yaml_stem=input_abs.stem)
    package_name = sanitize_module_name(output_dir.name)
    files = generate_from_yaml(input_abs, target=generate_target, package_name=package_name)
    return write_generation_result(files, output_dir, force=force, check=check)


def _resolve_output_dir(output: Path | None, *, yaml_stem: str) -> Path:
    if output is None:
        return (DEFAULT_GENERATED_DIR / yaml_stem).resolve()
    resolved = output.resolve()
    if resolved.suffix == ".py":
        return resolved.parent
    return resolved
