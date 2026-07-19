"""validate command implementation."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.models import ApiSpec
from md_drf_codegen.validate import validate_yaml_file


def run_validate(yaml_path: Path) -> tuple[ApiSpec, list[str]]:
    return validate_yaml_file(yaml_path.resolve())
