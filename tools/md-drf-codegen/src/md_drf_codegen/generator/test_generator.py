"""Context builder for generated pytest modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_drf_codegen.generator.context_builder import build_serializers_context
from md_drf_codegen.generator.url_generator import build_urls_context
from md_drf_codegen.generator.view_generator import build_views_context
from md_drf_codegen.normalize import is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec, FieldDefinition, TypeDefinition
from md_drf_codegen.utils.naming import (
    artifact_module_names,
    camel_to_snake,
)

_SAMPLE_VALUES: dict[str, Any] = {
    "string": "sample",
    "integer": 1,
    "number": 1.0,
    "boolean": True,
    "object": {},
}


@dataclass(frozen=True)
class SerializerValidTest:
    serializer_class: str
    function_name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerMissingTest:
    serializer_class: str
    function_name: str
    omitted_field: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerInvalidTypeTest:
    serializer_class: str
    function_name: str
    field_name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerNullableTest:
    serializer_class: str
    function_name: str
    nullable_field: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class UrlResolveTest:
    function_name: str
    resolve_path: str
    view_class: str


@dataclass(frozen=True)
class ViewMethodTest:
    function_name: str
    view_class: str
    http_method: str
    path: str
    path_kwargs: dict[str, str]
    request_data: dict[str, Any] | None
    uses_query_params: bool
    expects_not_implemented: bool


@dataclass(frozen=True)
class ViewBadRequestTest:
    function_name: str
    view_class: str
    http_method: str
    path: str
    path_kwargs: dict[str, str]
    invalid_payload: dict[str, Any]
    uses_query_params: bool


@dataclass(frozen=True)
class TestsModuleContext:
    package_name: str = "generated"
    serializers_module: str = "serializers"
    views_module: str = "views"
    serializer_valid: tuple[SerializerValidTest, ...] = field(default_factory=tuple)
    serializer_missing: tuple[SerializerMissingTest, ...] = field(default_factory=tuple)
    serializer_invalid_type: tuple[SerializerInvalidTypeTest, ...] = field(default_factory=tuple)
    serializer_nullable: tuple[SerializerNullableTest, ...] = field(default_factory=tuple)
    url_resolve: tuple[UrlResolveTest, ...] = field(default_factory=tuple)
    view_method: tuple[ViewMethodTest, ...] = field(default_factory=tuple)
    view_bad_request: tuple[ViewBadRequestTest, ...] = field(default_factory=tuple)
    serializer_imports: tuple[str, ...] = field(default_factory=tuple)
    view_imports: tuple[str, ...] = field(default_factory=tuple)


def build_tests_context(spec: ApiSpec, *, package_name: str = "generated") -> TestsModuleContext:
    serializers_module, views_module = artifact_module_names(package_name)
    ser_ctx = build_serializers_context(spec)
    views_ctx = build_views_context(spec, module_prefix=package_name)
    urls_ctx = build_urls_context(spec, module_prefix=package_name)

    serializer_valid: list[SerializerValidTest] = []
    serializer_missing: list[SerializerMissingTest] = []
    serializer_invalid_type: list[SerializerInvalidTypeTest] = []
    serializer_nullable: list[SerializerNullableTest] = []

    for ser in ser_ctx.serializers:
        type_def = spec.types[ser.type_name]
        payload = _build_valid_payload(ser.type_name, type_def, spec.types)
        serializer_valid.append(
            SerializerValidTest(
                serializer_class=ser.class_name,
                function_name=f"test_{_snake(ser.class_name)}_valid",
                payload=payload,
            )
        )
        for field_name, field_def in type_def.fields.items():
            if field_def.required:
                missing_payload = dict(payload)
                missing_payload.pop(field_name, None)
                serializer_missing.append(
                    SerializerMissingTest(
                        serializer_class=ser.class_name,
                        function_name=f"test_{_snake(ser.class_name)}_missing_{_snake(field_name)}",
                        omitted_field=field_name,
                        payload=missing_payload,
                    )
                )
                invalid_payload = dict(payload)
                invalid_payload[field_name] = _invalid_value(field_def)
                serializer_invalid_type.append(
                    SerializerInvalidTypeTest(
                        serializer_class=ser.class_name,
                        function_name=f"test_{_snake(ser.class_name)}_invalid_{_snake(field_name)}",
                        field_name=field_name,
                        payload=invalid_payload,
                    )
                )
            if field_def.nullable:
                nullable_payload = dict(payload)
                nullable_payload[field_name] = None
                serializer_nullable.append(
                    SerializerNullableTest(
                        serializer_class=ser.class_name,
                        function_name=f"test_{_snake(ser.class_name)}_nullable_{_snake(field_name)}",
                        nullable_field=field_name,
                        payload=nullable_payload,
                    )
                )

    url_resolve = [
        UrlResolveTest(
            function_name=f"test_resolve_{pattern.name.replace('-', '_')}",
            resolve_path=f"/{pattern.django_route}",
            view_class=pattern.view_class,
        )
        for pattern in urls_ctx.patterns
    ]

    view_method: list[ViewMethodTest] = []
    view_bad_request: list[ViewBadRequestTest] = []
    for view in views_ctx.views:
        for method in view.methods:
            path_kwargs = {
                param.snake_name: "test-value" for param in method.path_params
            }
            request_data = None
            if method.request_serializer:
                req_type = _find_request_type(spec, method.api_id)
                if req_type:
                    request_data = _build_valid_payload(req_type, spec.types[req_type], spec.types)
            view_method.append(
                ViewMethodTest(
                    function_name=f"test_{_snake(view.class_name)}_{method.http_method}_not_implemented",
                    view_class=view.class_name,
                    http_method=method.http_method,
                    path=view.path,
                    path_kwargs=path_kwargs,
                    request_data=request_data,
                    uses_query_params=bool(method.uses_query_params),
                    expects_not_implemented=True,
                )
            )
            if method.request_serializer and request_data:
                bad = dict(request_data)
                first_key = next(iter(bad))
                bad[first_key] = _invalid_value_for_key(first_key, spec, method.api_id)
                view_bad_request.append(
                    ViewBadRequestTest(
                        function_name=f"test_{_snake(view.class_name)}_{method.http_method}_bad_request",
                        view_class=view.class_name,
                        http_method=method.http_method,
                        path=view.path,
                        path_kwargs=path_kwargs,
                        invalid_payload=bad,
                        uses_query_params=bool(method.uses_query_params),
                    )
                )

    serializer_imports = tuple(sorted({ser.class_name for ser in ser_ctx.serializers}))
    view_imports = tuple(sorted({view.class_name for view in views_ctx.views}))

    return TestsModuleContext(
        package_name=package_name,
        serializers_module=serializers_module,
        views_module=views_module,
        serializer_valid=tuple(serializer_valid),
        serializer_missing=tuple(serializer_missing),
        serializer_invalid_type=tuple(serializer_invalid_type),
        serializer_nullable=tuple(serializer_nullable),
        url_resolve=tuple(url_resolve),
        view_method=tuple(view_method),
        view_bad_request=tuple(view_bad_request),
        serializer_imports=serializer_imports,
        view_imports=view_imports,
    )


def _snake(name: str) -> str:
    return camel_to_snake(name.replace("Serializer", ""))


def _find_request_type(spec: ApiSpec, api_id: str) -> str | None:
    for api in spec.apis:
        if api.id == api_id:
            return api.request_type
    return None


def _build_valid_payload(
    type_name: str,
    type_def: TypeDefinition,
    known: dict[str, TypeDefinition],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field_name, field_def in type_def.fields.items():
        if not field_def.required and not field_def.nullable:
            continue
        payload[field_name] = _sample_value(field_def, known)
    return payload


def _sample_value(field_def: FieldDefinition, known: dict[str, TypeDefinition]) -> Any:
    base = strip_array_suffix(field_def.type)
    if field_def.type.endswith("[]"):
        return [_sample_scalar(base, known)]
    return _sample_scalar(base, known)


def _sample_scalar(base: str, known: dict[str, TypeDefinition]) -> Any:
    if is_primitive_type(base):
        return _SAMPLE_VALUES.get(base, "sample")
    if base in known:
        return _build_valid_payload(base, known[base], known)
    return {}


def _invalid_value(field_def: FieldDefinition) -> Any:
    base = strip_array_suffix(field_def.type)
    if base == "string":
        return 123
    if base in {"integer", "number"}:
        return "not-a-number"
    if base == "boolean":
        return "not-a-bool"
    return None


def _invalid_value_for_key(key: str, spec: ApiSpec, api_id: str) -> Any:
    req_type = _find_request_type(spec, api_id)
    if not req_type or req_type not in spec.types:
        return "invalid"
    field_def = spec.types[req_type].fields.get(key)
    if field_def is None:
        return "invalid"
    return _invalid_value(field_def)
