"""Validate ApiSpec documents (schema + reference integrity)."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import SchemaValidationError, TypeReferenceError
from md_drf_codegen.normalize import is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec
from md_drf_codegen.schema.api import SUPPORTED_HTTP_METHODS
from md_drf_codegen.yaml_io import load_api_spec_yaml

KNOWN_FIELD_TYPES: frozenset[str] = frozenset(
    {
        "string",
        "integer",
        "number",
        "boolean",
        "object",
    }
)


def validate_api_spec(spec: ApiSpec) -> list[str]:
    """Validate an in-memory ApiSpec.

    Returns a list of warning messages. Raises on hard errors.
    """
    warnings: list[str] = []
    _assert_unique_api_ids(spec)
    _assert_supported_methods(spec)
    _assert_unique_type_names(spec)
    _assert_known_field_types(spec)
    _assert_api_type_references(spec)
    _assert_property_type_references(spec)
    _assert_non_empty_types(spec, warnings)
    return warnings


def validate_yaml_file(path: str | Path) -> tuple[ApiSpec, list[str]]:
    spec = load_api_spec_yaml(path)
    warnings = validate_api_spec(spec)
    return spec, warnings


def _assert_unique_api_ids(spec: ApiSpec) -> None:
    seen: set[str] = set()
    for api in spec.apis:
        if not api.id:
            raise SchemaValidationError(
                "API ID must not be empty.",
                section="apis",
                fix="Provide a non-empty id for every API.",
            )
        if api.id in seen:
            raise SchemaValidationError(
                f'Duplicate API ID "{api.id}".',
                section="apis",
                fix="Ensure each apis[].id is unique.",
            )
        seen.add(api.id)


def _assert_supported_methods(spec: ApiSpec) -> None:
    for api in spec.apis:
        if api.method.value not in SUPPORTED_HTTP_METHODS:
            raise SchemaValidationError(
                f'Unsupported HTTP method "{api.method.value}" on API "{api.id}".',
                section="apis",
                fix=f"Use one of: {', '.join(sorted(SUPPORTED_HTTP_METHODS))}.",
            )


def _assert_unique_type_names(spec: ApiSpec) -> None:
    seen: set[str] = set()
    for type_name in spec.types:
        if type_name in seen:
            raise SchemaValidationError(
                f'Duplicate type name "{type_name}".',
                section="types",
                fix="Ensure each types key is unique.",
            )
        seen.add(type_name)
        fields = spec.types[type_name].fields
        field_seen: set[str] = set()
        for field_name in fields:
            if field_name in field_seen:
                raise SchemaValidationError(
                    f'Duplicate field "{field_name}" on type "{type_name}".',
                    section="types",
                    fix="Ensure field names are unique within each type.",
                )
            field_seen.add(field_name)


def _assert_known_field_types(spec: ApiSpec) -> None:
    for type_name, type_def in spec.types.items():
        for field_name, field_def in type_def.fields.items():
            base = strip_array_suffix(field_def.type)
            if is_primitive_type(base):
                if base not in KNOWN_FIELD_TYPES:
                    raise SchemaValidationError(
                        f'Unknown field type "{field_def.type}" on {type_name}.{field_name}.',
                        section="types",
                        fix=f"Use one of: {', '.join(sorted(KNOWN_FIELD_TYPES))}, "
                        "a custom type, or an array (e.g. string[]).",
                    )
                continue
            if base not in spec.types:
                raise SchemaValidationError(
                    f'Unknown field type "{field_def.type}" on {type_name}.{field_name}.',
                    section="types",
                    fix="Define the custom type or use a supported primitive.",
                )


def _assert_api_type_references(spec: ApiSpec) -> None:
    defined = set(spec.types)
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
    defined = set(spec.types)
    for type_name, type_def in spec.types.items():
        for field_name, field_def in type_def.fields.items():
            base = strip_array_suffix(field_def.type)
            if is_primitive_type(base):
                continue
            if base not in defined:
                raise TypeReferenceError(
                    base,
                    context=f"types.{type_name}.{field_name}",
                )


def _assert_non_empty_types(spec: ApiSpec, warnings: list[str]) -> None:
    for type_name, type_def in spec.types.items():
        if not type_def.fields:
            warnings.append(f'Type "{type_name}" has no fields.')
