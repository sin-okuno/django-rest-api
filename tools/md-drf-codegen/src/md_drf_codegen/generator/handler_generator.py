"""Context builder for generated handler functions (demo responses)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_drf_codegen.normalize import is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiEndpoint, ApiSpec, FieldDefinition, TypeDefinition
from md_drf_codegen.utils.naming import (
    camel_to_snake,
    handler_function_name,
    handlers_module_name,
    path_param_names,
)

_SAMPLE_VALUES: dict[str, Any] = {
    "string": "sample",
    "integer": 1,
    "number": 1.0,
    "boolean": True,
    "date": "2024-01-15",
    "datetime": "2024-01-15T12:00:00Z",
    "object": {},
}


@dataclass(frozen=True)
class DemoFieldContext:
    name: str
    value_expr: str


@dataclass(frozen=True)
class HandlerRenderContext:
    api_id: str
    function_name: str
    has_validated_data: bool
    path_params: tuple[str, ...]
    demo_fields: tuple[DemoFieldContext, ...]


@dataclass(frozen=True)
class HandlersModuleContext:
    handlers: tuple[HandlerRenderContext, ...] = field(default_factory=tuple)


def build_handlers_context(spec: ApiSpec) -> HandlersModuleContext:
    handlers = tuple(_build_handler(endpoint, spec) for endpoint in spec.apis)
    return HandlersModuleContext(handlers=handlers)


def handlers_module_for_prefix(prefix: str) -> str:
    return handlers_module_name(prefix)


def _build_handler(endpoint: ApiEndpoint, spec: ApiSpec) -> HandlerRenderContext:
    path_params = tuple(camel_to_snake(name) for name in path_param_names(endpoint.path))
    path_camel_to_snake = {
        name: camel_to_snake(name) for name in path_param_names(endpoint.path)
    }
    demo_fields = _demo_fields_for_response(
        endpoint.response_type,
        spec.types,
        path_camel_to_snake,
    )
    return HandlerRenderContext(
        api_id=endpoint.id,
        function_name=handler_function_name(endpoint.id),
        has_validated_data=endpoint.request_type is not None,
        path_params=path_params,
        demo_fields=demo_fields,
    )


def _demo_fields_for_response(
    response_type: str | None,
    types: dict[str, TypeDefinition],
    path_camel_to_snake: dict[str, str],
) -> tuple[DemoFieldContext, ...]:
    if response_type is None:
        return (
            DemoFieldContext(name="ok", value_expr="True"),
            DemoFieldContext(name="demo", value_expr="True"),
        )
    type_def = types.get(response_type)
    if type_def is None:
        return (
            DemoFieldContext(name="ok", value_expr="True"),
            DemoFieldContext(name="demo", value_expr="True"),
            DemoFieldContext(name="type", value_expr=repr(response_type)),
        )

    fields: list[DemoFieldContext] = []
    for field_name, field_def in type_def.fields.items():
        if field_name in path_camel_to_snake:
            fields.append(
                DemoFieldContext(
                    name=field_name,
                    value_expr=path_camel_to_snake[field_name],
                )
            )
            continue
        if not field_def.required and not field_def.nullable:
            continue
        sample = _sample_value(field_def, types)
        fields.append(DemoFieldContext(name=field_name, value_expr=repr(sample)))
    if not fields:
        fields.append(DemoFieldContext(name="demo", value_expr="True"))
    return tuple(fields)


def _sample_value(field_def: FieldDefinition, known: dict[str, TypeDefinition]) -> Any:
    base = strip_array_suffix(field_def.type)
    if field_def.constraints and field_def.constraints.enum:
        first = field_def.constraints.enum[0].value
        if field_def.type.endswith("[]"):
            return [first]
        return first
    if field_def.type.endswith("[]"):
        return [_sample_scalar(base, known)]
    return _sample_scalar(base, known)


def _sample_scalar(base: str, known: dict[str, TypeDefinition]) -> Any:
    if is_primitive_type(base):
        return _SAMPLE_VALUES.get(base, "sample")
    if base in known:
        return {
            name: _sample_value(field_def, known)
            for name, field_def in known[base].fields.items()
            if field_def.required or field_def.nullable
        }
    return {}
