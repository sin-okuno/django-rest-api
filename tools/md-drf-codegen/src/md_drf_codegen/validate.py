"""Backward-compatible re-export of validator."""

from md_drf_codegen.validator import validate_api_spec, validate_yaml_file

__all__ = ["validate_api_spec", "validate_yaml_file"]
