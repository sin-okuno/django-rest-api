"""generate command: YAML → serializers / views / urls / handlers."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.generator import generate_all_from_yaml, write_generated_files
from md_drf_codegen.generator.naming import module_prefix_from_source, sanitize_module_name

# commands/generate.py -> md_drf_codegen -> src -> md-drf-codegen
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERATED_DIR = PACKAGE_ROOT / "examples" / "generated"


def run_generate(yaml_path: Path, output: Path | None = None) -> list[Path]:
    """Generate all DRF artifacts into an output directory.

    Default output is ``examples/generated/<yaml-stem>/`` so that
    ``product-structure.yaml`` writes under ``product-structure/``.
    Module file prefixes come from the Markdown source path in the YAML
    (e.g. ``product-structure.md`` → ``product_structure_serializers.py``).
    """
    input_abs = yaml_path.resolve()
    output_dir = _resolve_output_dir(output, yaml_stem=input_abs.stem)
    package_name = package_name_from_dirname(output_dir.name)
    files = generate_all_from_yaml(input_abs, package_name=package_name)
    return write_generated_files(files, output_dir)


def package_name_from_dirname(dirname: str) -> str:
    """Map a folder name (possibly kebab-case) to a valid Python package name."""
    return sanitize_module_name(dirname)


def _resolve_output_dir(output: Path | None, *, yaml_stem: str) -> Path:
    if output is None:
        return (DEFAULT_GENERATED_DIR / yaml_stem).resolve()

    resolved = output.resolve()
    # Backward compatible: if a serializers.py path is given, use its parent.
    if resolved.suffix == ".py":
        return resolved.parent
    return resolved


# Re-exported for tests / callers that derive prefixes from Markdown sources.
__all__ = [
    "DEFAULT_GENERATED_DIR",
    "PACKAGE_ROOT",
    "module_prefix_from_source",
    "package_name_from_dirname",
    "run_generate",
]
