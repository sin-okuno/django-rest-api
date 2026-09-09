"""Convert ApiSpec to OpenAPI 3.0 documents."""

from __future__ import annotations

from typing import Any

from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiEndpoint, ApiSpec, FieldDefinition, HttpMethod, TypeDefinition
from md_drf_codegen.schema.constraints import FieldConstraints
from md_drf_codegen.utils.naming import path_param_names

_OPENAPI_VERSION = "3.0.3"
_QUERY_METHODS = {HttpMethod.GET}
_PRIMITIVE_OPENAPI_SCHEMA: dict[str, dict[str, str]] = {
    "string": {"type": "string"},
    "integer": {"type": "integer"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
    "date": {"type": "string", "format": "date"},
    "datetime": {"type": "string", "format": "date-time"},
    "object": {"type": "object"},
}


def build_openapi_document(
    spec: ApiSpec,
    *,
    title: str = "API",
    api_version: str = "1.0.0",
) -> dict[str, Any]:
    """Build an OpenAPI 3.0 mapping from *spec*."""
    paths: dict[str, dict[str, Any]] = {}
    for endpoint in spec.apis:
        path_item = paths.setdefault(endpoint.path, {})
        path_item[endpoint.method.value.lower()] = _build_operation(endpoint, spec)

    return {
        "openapi": _OPENAPI_VERSION,
        "info": {
            "title": title,
            "version": api_version,
        },
        "paths": paths,
        "components": {
            "schemas": _build_component_schemas(spec),
        },
    }


def _build_operation(endpoint: ApiEndpoint, spec: ApiSpec) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "operationId": endpoint.id,
        "summary": endpoint.name,
        "responses": _build_responses(endpoint, spec),
    }
    if endpoint.remarks:
        operation["description"] = endpoint.remarks

    parameters: list[dict[str, Any]] = []
    for camel_name in path_param_names(endpoint.path):
        param_def = spec.path_parameters.get(camel_name)
        parameter: dict[str, Any] = {
            "name": camel_name,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }
        if param_def is not None:
            parameter["schema"] = _path_parameter_schema(param_def)
            if param_def.remarks:
                parameter["description"] = param_def.remarks
        parameters.append(parameter)

    if endpoint.request_type and endpoint.request_type in spec.types:
        request_type = spec.types[endpoint.request_type]
        if endpoint.method in _QUERY_METHODS:
            parameters.extend(_query_parameters(endpoint.request_type, request_type, spec))
        else:
            operation["requestBody"] = _request_body(endpoint.request_type)

    if parameters:
        operation["parameters"] = parameters

    return operation


def _build_responses(endpoint: ApiEndpoint, spec: ApiSpec) -> dict[str, Any]:
    if endpoint.response_type is None:
        return {"200": {"description": "OK"}}

    return {
        "200": {
            "description": "OK",
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{endpoint.response_type}"},
                },
            },
        },
    }


def _request_body(type_name: str) -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": f"#/components/schemas/{type_name}"},
            },
        },
    }


def _query_parameters(
    type_name: str,
    type_def: TypeDefinition,
    spec: ApiSpec,
) -> list[dict[str, Any]]:
    del type_name
    parameters: list[dict[str, Any]] = []
    for field_name, field_def in type_def.fields.items():
        parameter: dict[str, Any] = {
            "name": field_name,
            "in": "query",
            "required": field_def.required,
            "schema": _field_schema(field_def, spec),
        }
        if field_def.remarks:
            parameter["description"] = field_def.remarks
        parameters.append(parameter)
    return parameters


def _path_parameter_schema(param_def: object) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    constraints = getattr(param_def, "constraints", None)
    if constraints is not None:
        schema.update(_constraint_properties(constraints, base_type="string"))
    return schema


def _build_component_schemas(spec: ApiSpec) -> dict[str, Any]:
    return {
        type_name: _object_schema(type_def, spec)
        for type_name, type_def in spec.types.items()
    }


def _object_schema(type_def: TypeDefinition, spec: ApiSpec) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for field_name, field_def in type_def.fields.items():
        properties[field_name] = _field_schema(field_def, spec)
        if field_def.required:
            required.append(field_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _field_schema(field_def: FieldDefinition, spec: ApiSpec) -> dict[str, Any]:
    schema = _type_expression_schema(field_def.type, spec)
    schema.update(
        _constraint_properties(
            field_def.constraints,
            base_type=strip_array_suffix(field_def.type),
        )
    )
    if field_def.nullable:
        schema["nullable"] = True
    if field_def.remarks:
        existing = schema.get("description")
        if isinstance(existing, str) and existing:
            schema["description"] = f"{field_def.remarks} ({existing})"
        else:
            schema["description"] = field_def.remarks
    return schema


def _type_expression_schema(type_expr: str, spec: ApiSpec) -> dict[str, Any]:
    if is_array_type(type_expr):
        base = strip_array_suffix(type_expr)
        return {
            "type": "array",
            "items": _type_expression_schema(base, spec),
        }

    base = strip_array_suffix(type_expr)
    if is_primitive_type(base):
        schema = _PRIMITIVE_OPENAPI_SCHEMA.get(base)
        if schema is not None:
            return dict(schema)
        return {"type": "string"}

    if base in spec.types:
        return {"$ref": f"#/components/schemas/{base}"}

    return {"type": "object"}


def _constraint_properties(
    constraints: FieldConstraints | None,
    *,
    base_type: str,
) -> dict[str, Any]:
    if constraints is None or constraints.is_empty():
        return {}

    props: dict[str, Any] = {}

    if constraints.enum:
        props["enum"] = [member.value for member in constraints.enum]
        labels = [member.label for member in constraints.enum if member.label]
        if labels:
            labeled = ", ".join(
                f"{member.value}={member.label}"
                if member.label
                else str(member.value)
                for member in constraints.enum
            )
            props["description"] = labeled
        return props

    if base_type in {"integer", "number", "decimal"}:
        if constraints.min is not None:
            props["minimum"] = _numeric_value(constraints.min)
        if constraints.max is not None:
            props["maximum"] = _numeric_value(constraints.max)
    elif base_type == "string":
        if constraints.min_length is not None:
            props["minLength"] = constraints.min_length
        if constraints.max_length is not None:
            props["maxLength"] = constraints.max_length
        resolved = constraints.resolved_pattern()
        if resolved is not None:
            props["pattern"] = resolved[0]

    return props


def _numeric_value(value: float) -> int | float:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value
