"""Deterministic sample payload generation from API type definitions."""

from __future__ import annotations

from typing import Any

from md_drf_codegen.models import ApiTypeDefinition, TypeProperty
from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix

MAX_NESTING_DEPTH = 2


def build_sample_value(
    type_expr: str,
    *,
    field_name: str,
    types_by_name: dict[str, ApiTypeDefinition],
    depth: int = 0,
    force_null: bool = False,
    prop: TypeProperty | None = None,
) -> Any:
    """Build a deterministic sample value for a type expression."""
    if force_null:
        return None

    base = strip_array_suffix(type_expr)
    if is_array_type(type_expr):
        element = build_sample_value(
            base,
            field_name=field_name,
            types_by_name=types_by_name,
            depth=depth,
            prop=None,
        )
        return [element]

    if is_primitive_type(base):
        return _primitive_sample(base, field_name=field_name, prop=prop)

    type_def = types_by_name.get(base)
    if type_def is None:
        return {f"unknown_{field_name}": f"sample-{field_name}"}

    if depth >= MAX_NESTING_DEPTH:
        # Break recursion with an empty-ish object of required primitives only.
        return _shallow_object(type_def, types_by_name=types_by_name, depth=depth)

    return build_sample_object(type_def, types_by_name=types_by_name, depth=depth)


def build_sample_object(
    type_def: ApiTypeDefinition,
    *,
    types_by_name: dict[str, ApiTypeDefinition],
    depth: int = 0,
    null_field: str | None = None,
    omit_field: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic object for ``type_def``."""
    payload: dict[str, Any] = {}
    for prop in type_def.properties:
        if omit_field is not None and prop.name == omit_field:
            continue
        payload[prop.name] = build_sample_value(
            prop.type,
            field_name=prop.name,
            types_by_name=types_by_name,
            depth=depth + 1,
            force_null=(null_field == prop.name),
            prop=prop,
        )
    return payload


def first_required_field(type_def: ApiTypeDefinition) -> TypeProperty | None:
    for prop in type_def.properties:
        if not prop.optional:
            return prop
    return None


def first_nullable_field(type_def: ApiTypeDefinition) -> TypeProperty | None:
    for prop in type_def.properties:
        if prop.nullable:
            return prop
    return None


def first_nested_field(
    type_def: ApiTypeDefinition,
    *,
    types_by_name: dict[str, ApiTypeDefinition],
) -> TypeProperty | None:
    for prop in type_def.properties:
        base = strip_array_suffix(prop.type)
        if not is_primitive_type(base) and base in types_by_name:
            return prop
    return None


def _primitive_sample(
    base: str,
    *,
    field_name: str,
    prop: TypeProperty | None = None,
) -> Any:
    if base == "string":
        text = f"sample-{field_name}"
        if prop is not None and prop.max_length is not None:
            return text[: prop.max_length]
        return text
    if base == "integer":
        value = 1
        if prop is not None and prop.max_digits is not None:
            return min(value, 10**prop.max_digits - 1)
        return value
    if base == "number":
        if prop is not None and (prop.max_digits is not None or prop.decimal_places is not None):
            places = prop.decimal_places if prop.decimal_places is not None else 0
            if places == 0:
                return "1"
            return "1." + ("2" * places)
        return 1.25
    if base == "decimal":
        places = 2
        if prop is not None and prop.decimal_places is not None:
            places = prop.decimal_places
        if places == 0:
            return "10"
        return "10." + ("5" * places)
    if base == "boolean":
        return True
    if base in {"any", "object"}:
        return {f"sample_{field_name}": True}
    return f"sample-{field_name}"


def _shallow_object(
    type_def: ApiTypeDefinition,
    *,
    types_by_name: dict[str, ApiTypeDefinition],
    depth: int,
) -> dict[str, Any]:
    """Object used at max depth: arrays become empty, nested objects become {}."""
    payload: dict[str, Any] = {}
    for prop in type_def.properties:
        base = strip_array_suffix(prop.type)
        if is_array_type(prop.type):
            payload[prop.name] = []
        elif is_primitive_type(base):
            if prop.nullable:
                payload[prop.name] = None
            else:
                payload[prop.name] = _primitive_sample(base, field_name=prop.name, prop=prop)
        else:
            # Nested custom type at max depth: empty dict or one-level primitives.
            nested = types_by_name.get(base)
            if nested is None or depth >= MAX_NESTING_DEPTH:
                payload[prop.name] = {}
            else:
                payload[prop.name] = _shallow_object(
                    nested,
                    types_by_name=types_by_name,
                    depth=depth + 1,
                )
    return payload
