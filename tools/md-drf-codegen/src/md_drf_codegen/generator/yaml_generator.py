"""YAML generation from ApiSpec."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.schema import ApiSpec
from md_drf_codegen.validator import validate_api_spec
from md_drf_codegen.yaml_io import write_api_spec_yaml


def generate_yaml_file(spec: ApiSpec, output_path: str | Path) -> Path:
    validate_api_spec(spec)
    return write_api_spec_yaml(spec, output_path)
