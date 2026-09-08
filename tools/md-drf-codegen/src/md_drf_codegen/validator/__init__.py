"""Validate ApiSpec documents (schema + reference integrity)."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import SchemaValidationError, TypeReferenceError
from md_drf_codegen.normalize import is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec
from md_drf_codegen.schema.api import SUPPORTED_HTTP_METHODS
from md_drf_codegen.schema.constraints import FieldConstraints
from md_drf_codegen.utils.naming import path_param_names
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
    _assert_field_constraints(spec)
    _assert_path_parameters(spec)
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


def _assert_field_constraints(spec: ApiSpec) -> None:
    for type_name, type_def in spec.types.items():
        for field_name, field_def in type_def.fields.items():
            if field_def.constraints is None or field_def.constraints.is_empty():
                continue
            _validate_constraints_for_field(
                field_def.constraints,
                base_type=strip_array_suffix(field_def.type),
                context=f"types.{type_name}.{field_name}",
            )


def _validate_constraints_for_field(
    constraints: FieldConstraints,
    *,
    base_type: str,
    context: str,
) -> None:
    numeric_keys = constraints.min is not None or constraints.max is not None
    string_keys = (
        constraints.min_length is not None
        or constraints.max_length is not None
        or constraints.format is not None
        or constraints.pattern is not None
    )

    if base_type in {"integer", "number", "decimal"}:
        if string_keys:
            raise SchemaValidationError(
                f"String constraints are not allowed on numeric field {context}.",
                section="types",
                fix="Use min/max or a range like 1-50 for numeric fields.",
            )
    elif base_type == "string":
        if numeric_keys:
            raise SchemaValidationError(
                f"Numeric range constraints are not allowed on string field {context}.",
                section="types",
                fix="Use 最大N文字, minLength, maxLength, or 半角英数字 for strings.",
            )
    else:
        raise SchemaValidationError(
            f"Constraints are not supported on type '{base_type}' at {context}.",
            section="types",
            fix="Apply constraints only to string, integer, or number fields.",
        )

    if (
        constraints.min is not None
        and constraints.max is not None
        and constraints.min > constraints.max
    ):
        raise SchemaValidationError(
            f"min ({constraints.min}) cannot exceed max ({constraints.max}) at {context}.",
            section="types",
            fix="Ensure min <= max.",
        )

    if (
        constraints.min_length is not None
        and constraints.max_length is not None
        and constraints.min_length > constraints.max_length
    ):
        raise SchemaValidationError(
            f"minLength ({constraints.min_length}) cannot exceed "
            f"maxLength ({constraints.max_length}) at {context}.",
            section="types",
            fix="Ensure minLength <= maxLength.",
        )


def _assert_path_parameters(spec: ApiSpec) -> None:
    used: set[str] = set()
    for api in spec.apis:
        used.update(path_param_names(api.path))

    for name in sorted(used):
        if name not in spec.path_parameters:
            raise SchemaValidationError(
                f'Path parameter "{name}" is used in apis[].path but missing from pathParameters.',
                section="pathParameters",
                fix='Add a row to the "## パスパラメータ" section in Markdown.',
            )

    for name, param_def in spec.path_parameters.items():
        if param_def.param_type != "string":
            raise SchemaValidationError(
                f'Path parameter "{name}" must use type "string".',
                section="pathParameters",
                fix="URL path segments are validated as strings in generated views.",
            )
        if param_def.constraints is None or param_def.constraints.is_empty():
            continue
        _validate_constraints_for_field(
            param_def.constraints,
            base_type="string",
            context=f"pathParameters.{name}",
        )

    unused = set(spec.path_parameters) - used
    if unused:
        names = ", ".join(sorted(unused))
        raise SchemaValidationError(
            f"Unused path parameter definitions: {names}.",
            section="pathParameters",
            fix="Remove unused rows or reference the parameter in an API path.",
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
