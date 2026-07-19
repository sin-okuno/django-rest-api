"""Validate ApiSpec documents (schema + reference integrity)."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import SchemaValidationError, TypeReferenceError
from md_drf_codegen.models import ApiSpec
from md_drf_codegen.normalize import is_primitive_type, strip_array_suffix
from md_drf_codegen.yaml_io import load_api_spec_yaml


def validate_api_spec(spec: ApiSpec) -> list[str]:
    """Validate an in-memory ApiSpec.

    Returns a list of warning messages. Raises on hard errors.
    """
    warnings: list[str] = []
    _assert_unique_api_ids(spec)
    _assert_unique_type_names(spec)
    _assert_api_type_references(spec)
    _assert_property_type_references(spec)
    _assert_non_empty_properties(spec, warnings)
    return warnings


def validate_yaml_file(path: str | Path) -> tuple[ApiSpec, list[str]]:
    spec = load_api_spec_yaml(path)
    warnings = validate_api_spec(spec)
    return spec, warnings


def _assert_unique_api_ids(spec: ApiSpec) -> None:
    seen: set[str] = set()
    for api in spec.apis:
        if api.id in seen:
            raise SchemaValidationError(
                f'Duplicate API ID "{api.id}".',
                section="apis",
                fix="Ensure each apis[].id is unique.",
            )
        seen.add(api.id)


def _assert_unique_type_names(spec: ApiSpec) -> None:
    seen: set[str] = set()
    for type_def in spec.types:
        if type_def.name in seen:
            raise SchemaValidationError(
                f'Duplicate type name "{type_def.name}".',
                section="types",
                fix="Ensure each types[].name is unique.",
            )
        seen.add(type_def.name)


def _defined_type_names(spec: ApiSpec) -> set[str]:
    return {type_def.name for type_def in spec.types}


def _assert_api_type_references(spec: ApiSpec) -> None:
    defined = _defined_type_names(spec)
    for api in spec.apis:
        for field_name, type_name in (
            ("requestType", api.request_type),
            ("responseType", api.response_type),
        ):
            if type_name is None:
                continue
            base = strip_array_suffix(type_name)
            if is_primitive_type(base):
                continue
            if base not in defined:
                raise TypeReferenceError(base, context=f"apis[].{field_name} ({api.id})")


def _assert_property_type_references(spec: ApiSpec) -> None:
    defined = _defined_type_names(spec)
    for type_def in spec.types:
        for prop in type_def.properties:
            base = strip_array_suffix(prop.type)
            if is_primitive_type(base):
                continue
            if base not in defined:
                raise TypeReferenceError(
                    base,
                    context=f"types.{type_def.name}.{prop.name}",
                )


def _assert_non_empty_properties(spec: ApiSpec, warnings: list[str]) -> None:
    for type_def in spec.types:
        if not type_def.properties:
            warnings.append(f'Type "{type_def.name}" has no properties.')
