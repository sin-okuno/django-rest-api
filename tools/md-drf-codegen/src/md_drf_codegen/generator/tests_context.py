"""Context builder for generated pytest modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_drf_codegen.generator.context import serializer_class_name
from md_drf_codegen.generator.naming import (
    artifact_module_names,
    django_route,
    module_prefix_from_source,
)
from md_drf_codegen.generator.sample_data import (
    build_sample_object,
    first_nested_field,
    first_nullable_field,
    first_required_field,
)
from md_drf_codegen.generator.urls_context import build_urls_context
from md_drf_codegen.generator.views_context import build_views_context
from md_drf_codegen.models import ApiSpec, ApiTypeDefinition


@dataclass(frozen=True)
class SerializerValidTest:
    type_name: str
    serializer_class: str
    function_name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerMissingRequiredTest:
    type_name: str
    serializer_class: str
    function_name: str
    omitted_field: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerNullableTest:
    type_name: str
    serializer_class: str
    function_name: str
    nullable_field: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class SerializerNestedTest:
    type_name: str
    serializer_class: str
    function_name: str
    nested_field: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class UrlResolveTest:
    function_name: str
    resolve_path: str
    view_class: str
    url_name: str


@dataclass(frozen=True)
class GetHandlerTest:
    function_name: str
    view_class: str
    api_id: str
    handler_class: str
    request_serializer: str | None
    response_serializer: str | None
    uses_query_params: bool
    path_kwargs: dict[str, str]
    query_or_body: dict[str, Any]
    response_payload: dict[str, Any]


@dataclass(frozen=True)
class PutValidationTest:
    function_name: str
    view_class: str
    api_id: str
    handler_class: str
    request_serializer: str
    path_kwargs: dict[str, str]
    invalid_payload: dict[str, Any]
    omitted_field: str


@dataclass(frozen=True)
class ResponseSerializerTest:
    function_name: str
    view_class: str
    api_id: str
    handler_class: str
    request_serializer: str | None
    response_serializer: str
    uses_query_params: bool
    path_kwargs: dict[str, str]
    query_or_body: dict[str, Any]
    response_payload: dict[str, Any]


@dataclass(frozen=True)
class BadRequestTest:
    function_name: str
    view_class: str
    api_id: str
    handler_class: str
    http_method: str
    request_serializer: str
    uses_query_params: bool
    path_kwargs: dict[str, str]
    invalid_payload: dict[str, Any]


@dataclass(frozen=True)
class UnregisteredHandlerTest:
    function_name: str
    view_class: str
    api_id: str
    handler_class: str
    http_method: str
    path_kwargs: dict[str, str]
    query_or_body: dict[str, Any]
    uses_query_params: bool
    has_request_serializer: bool


@dataclass(frozen=True)
class TestsModuleContext:
    title: str
    source: str
    package_name: str = "generated"
    serializers_module: str = "serializers"
    views_module: str = "views"
    handlers_module: str = "handlers"
    serializer_valid: tuple[SerializerValidTest, ...] = field(default_factory=tuple)
    serializer_missing: tuple[SerializerMissingRequiredTest, ...] = field(default_factory=tuple)
    serializer_nullable: tuple[SerializerNullableTest, ...] = field(default_factory=tuple)
    serializer_nested: tuple[SerializerNestedTest, ...] = field(default_factory=tuple)
    url_resolve: tuple[UrlResolveTest, ...] = field(default_factory=tuple)
    get_handler: tuple[GetHandlerTest, ...] = field(default_factory=tuple)
    put_validation: tuple[PutValidationTest, ...] = field(default_factory=tuple)
    response_serializer: tuple[ResponseSerializerTest, ...] = field(default_factory=tuple)
    bad_request: tuple[BadRequestTest, ...] = field(default_factory=tuple)
    unregistered: tuple[UnregisteredHandlerTest, ...] = field(default_factory=tuple)
    serializer_imports: tuple[str, ...] = field(default_factory=tuple)
    view_imports: tuple[str, ...] = field(default_factory=tuple)
    handler_imports: tuple[str, ...] = field(default_factory=tuple)


def build_tests_context(spec: ApiSpec, *, package_name: str = "generated") -> TestsModuleContext:
    prefix = module_prefix_from_source(spec.source, fallback=package_name)
    serializers_module, views_module, handlers_module = artifact_module_names(prefix)

    types_by_name = {type_def.name: type_def for type_def in spec.types}
    views = build_views_context(spec, module_prefix=prefix)
    urls = build_urls_context(spec, module_prefix=prefix)

    serializer_valid = _build_serializer_valid(spec.types, types_by_name)
    serializer_missing = _build_serializer_missing(spec.types, types_by_name)
    serializer_nullable = _build_serializer_nullable(spec.types, types_by_name)
    serializer_nested = _build_serializer_nested(spec.types, types_by_name)
    url_resolve = _build_url_resolve(urls.patterns)
    get_handler = _build_get_handler(views.views, types_by_name)
    put_validation = _build_put_validation(views.views, types_by_name)
    response_serializer = _build_response_serializer(views.views, types_by_name)
    bad_request = _build_bad_request(views.views, types_by_name)
    unregistered = _build_unregistered(views.views, types_by_name)

    serializer_imports = sorted(
        {
            *(item.serializer_class for item in serializer_valid),
            *(item.serializer_class for item in serializer_missing),
            *(item.serializer_class for item in serializer_nullable),
            *(item.serializer_class for item in serializer_nested),
        }
    )
    view_imports = sorted({view.class_name for view in views.views})
    handler_imports = sorted(views.handler_imports)

    return TestsModuleContext(
        title=spec.title,
        source=spec.source,
        package_name=package_name,
        serializers_module=serializers_module,
        views_module=views_module,
        handlers_module=handlers_module,
        serializer_valid=tuple(serializer_valid),
        serializer_missing=tuple(serializer_missing),
        serializer_nullable=tuple(serializer_nullable),
        serializer_nested=tuple(serializer_nested),
        url_resolve=tuple(url_resolve),
        get_handler=tuple(get_handler),
        put_validation=tuple(put_validation),
        response_serializer=tuple(response_serializer),
        bad_request=tuple(bad_request),
        unregistered=tuple(unregistered),
        serializer_imports=tuple(serializer_imports),
        view_imports=tuple(view_imports),
        handler_imports=tuple(handler_imports),
    )


def _build_serializer_valid(
    types: list[ApiTypeDefinition],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[SerializerValidTest]:
    result: list[SerializerValidTest] = []
    for type_def in types:
        if not type_def.properties:
            continue
        payload = build_sample_object(type_def, types_by_name=types_by_name)
        result.append(
            SerializerValidTest(
                type_name=type_def.name,
                serializer_class=serializer_class_name(type_def.name),
                function_name=f"test_{_snake(type_def.name)}_serializer_valid",
                payload=payload,
            )
        )
    return result


def _build_serializer_missing(
    types: list[ApiTypeDefinition],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[SerializerMissingRequiredTest]:
    result: list[SerializerMissingRequiredTest] = []
    for type_def in types:
        required = first_required_field(type_def)
        if required is None:
            continue
        payload = build_sample_object(
            type_def,
            types_by_name=types_by_name,
            omit_field=required.name,
        )
        result.append(
            SerializerMissingRequiredTest(
                type_name=type_def.name,
                serializer_class=serializer_class_name(type_def.name),
                function_name=f"test_{_snake(type_def.name)}_serializer_missing_required",
                omitted_field=required.name,
                payload=payload,
            )
        )
    return result


def _build_serializer_nullable(
    types: list[ApiTypeDefinition],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[SerializerNullableTest]:
    result: list[SerializerNullableTest] = []
    for type_def in types:
        nullable = first_nullable_field(type_def)
        if nullable is None:
            continue
        payload = build_sample_object(
            type_def,
            types_by_name=types_by_name,
            null_field=nullable.name,
        )
        result.append(
            SerializerNullableTest(
                type_name=type_def.name,
                serializer_class=serializer_class_name(type_def.name),
                function_name=f"test_{_snake(type_def.name)}_serializer_nullable",
                nullable_field=nullable.name,
                payload=payload,
            )
        )
    return result


def _build_serializer_nested(
    types: list[ApiTypeDefinition],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[SerializerNestedTest]:
    result: list[SerializerNestedTest] = []
    for type_def in types:
        nested = first_nested_field(type_def, types_by_name=types_by_name)
        if nested is None:
            continue
        payload = build_sample_object(type_def, types_by_name=types_by_name)
        result.append(
            SerializerNestedTest(
                type_name=type_def.name,
                serializer_class=serializer_class_name(type_def.name),
                function_name=f"test_{_snake(type_def.name)}_serializer_nested",
                nested_field=nested.name,
                payload=payload,
            )
        )
    return result


def _build_url_resolve(patterns: tuple[Any, ...]) -> list[UrlResolveTest]:
    result: list[UrlResolveTest] = []
    for pattern in patterns:
        resolve_path = _example_resolve_path(pattern.path)
        result.append(
            UrlResolveTest(
                function_name=f"test_resolve_{_snake(pattern.name.replace('-', '_'))}",
                resolve_path=resolve_path,
                view_class=pattern.view_class,
                url_name=pattern.name,
            )
        )
    return result


def _build_get_handler(
    views: tuple[Any, ...], types_by_name: dict[str, ApiTypeDefinition]
) -> list[GetHandlerTest]:
    result: list[GetHandlerTest] = []
    for view in views:
        for method in view.methods:
            if method.http_method != "get":
                continue
            path_kwargs = {
                param.snake_name: f"sample-{param.snake_name}" for param in method.path_params
            }
            query = _request_payload(method.request_serializer, types_by_name)
            response_payload = _response_payload(method.response_serializer, types_by_name)
            result.append(
                GetHandlerTest(
                    function_name=(
                        f"test_{_snake(view.class_name)}_get_handler_{_snake(method.api_id)}"
                    ),
                    view_class=view.class_name,
                    api_id=method.api_id,
                    handler_class=method.handler_class,
                    request_serializer=method.request_serializer,
                    response_serializer=method.response_serializer,
                    uses_query_params=method.uses_query_params,
                    path_kwargs=path_kwargs,
                    query_or_body=query,
                    response_payload=response_payload,
                )
            )
    return result


def _build_put_validation(
    views: tuple[Any, ...],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[PutValidationTest]:
    result: list[PutValidationTest] = []
    for view in views:
        for method in view.methods:
            if method.http_method != "put" or not method.request_serializer:
                continue
            type_name = method.request_serializer.removesuffix("Serializer")
            type_def = types_by_name[type_name]
            required = first_required_field(type_def)
            if required is None:
                continue
            invalid_payload = build_sample_object(
                type_def,
                types_by_name=types_by_name,
                omit_field=required.name,
            )
            path_kwargs = {
                param.snake_name: f"sample-{param.snake_name}" for param in method.path_params
            }
            result.append(
                PutValidationTest(
                    function_name=(
                        f"test_{_snake(view.class_name)}_put_validation_{_snake(method.api_id)}"
                    ),
                    view_class=view.class_name,
                    api_id=method.api_id,
                    handler_class=method.handler_class,
                    request_serializer=method.request_serializer,
                    path_kwargs=path_kwargs,
                    invalid_payload=invalid_payload,
                    omitted_field=required.name,
                )
            )
    return result


def _build_response_serializer(
    views: tuple[Any, ...],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[ResponseSerializerTest]:
    result: list[ResponseSerializerTest] = []
    for view in views:
        for method in view.methods:
            if method.http_method != "get" or not method.response_serializer:
                continue
            path_kwargs = {
                param.snake_name: f"sample-{param.snake_name}" for param in method.path_params
            }
            result.append(
                ResponseSerializerTest(
                    function_name=(
                        f"test_{_snake(view.class_name)}_response_serializer_"
                        f"{_snake(method.api_id)}"
                    ),
                    view_class=view.class_name,
                    api_id=method.api_id,
                    handler_class=method.handler_class,
                    request_serializer=method.request_serializer,
                    response_serializer=method.response_serializer,
                    uses_query_params=method.uses_query_params,
                    path_kwargs=path_kwargs,
                    query_or_body=_request_payload(method.request_serializer, types_by_name),
                    response_payload=_response_payload(method.response_serializer, types_by_name),
                )
            )
    return result


def _build_bad_request(
    views: tuple[Any, ...],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[BadRequestTest]:
    result: list[BadRequestTest] = []
    for view in views:
        for method in view.methods:
            if not method.request_serializer:
                continue
            type_name = method.request_serializer.removesuffix("Serializer")
            type_def = types_by_name[type_name]
            required = first_required_field(type_def)
            if required is None:
                continue
            invalid_payload = build_sample_object(
                type_def,
                types_by_name=types_by_name,
                omit_field=required.name,
            )
            path_kwargs = {
                param.snake_name: f"sample-{param.snake_name}" for param in method.path_params
            }
            result.append(
                BadRequestTest(
                    function_name=(
                        f"test_{_snake(view.class_name)}_{method.http_method}_400_"
                        f"{_snake(method.api_id)}"
                    ),
                    view_class=view.class_name,
                    api_id=method.api_id,
                    handler_class=method.handler_class,
                    http_method=method.http_method,
                    request_serializer=method.request_serializer,
                    uses_query_params=method.uses_query_params,
                    path_kwargs=path_kwargs,
                    invalid_payload=invalid_payload,
                )
            )
    return result


def _build_unregistered(
    views: tuple[Any, ...],
    types_by_name: dict[str, ApiTypeDefinition],
) -> list[UnregisteredHandlerTest]:
    """Pick a non-GET handler that still raises NotImplementedError."""
    # Prefer mutating methods; GET handlers return demo data and do not raise.
    preferred = ("put", "post", "patch", "delete")
    candidates: list[Any] = []
    for view in views:
        for method in view.methods:
            candidates.append((view, method))

    ordered = sorted(
        candidates,
        key=lambda item: (
            preferred.index(item[1].http_method) if item[1].http_method in preferred else 99
        ),
    )
    for view, method in ordered:
        if method.http_method == "get":
            continue
        path_kwargs = {
            param.snake_name: f"sample-{param.snake_name}" for param in method.path_params
        }
        return [
            UnregisteredHandlerTest(
                function_name=(
                    f"test_{_snake(view.class_name)}_unimplemented_handler_{_snake(method.api_id)}"
                ),
                view_class=view.class_name,
                api_id=method.api_id,
                handler_class=method.handler_class,
                http_method=method.http_method,
                path_kwargs=path_kwargs,
                query_or_body=_request_payload(method.request_serializer, types_by_name),
                uses_query_params=method.uses_query_params,
                has_request_serializer=method.request_serializer is not None,
            )
        ]
    return []


def _request_payload(
    request_serializer: str | None,
    types_by_name: dict[str, ApiTypeDefinition],
) -> dict[str, Any]:
    if not request_serializer:
        return {}
    type_name = request_serializer.removesuffix("Serializer")
    return build_sample_object(types_by_name[type_name], types_by_name=types_by_name)


def _response_payload(
    response_serializer: str | None,
    types_by_name: dict[str, ApiTypeDefinition],
) -> dict[str, Any]:
    if not response_serializer:
        return {"ok": True}
    type_name = response_serializer.removesuffix("Serializer")
    return build_sample_object(types_by_name[type_name], types_by_name=types_by_name)


def _example_resolve_path(spec_path: str) -> str:
    """Build a concrete path for resolve(), converting params to sample values."""
    route = django_route(spec_path)
    # Replace <str:name> with sample-name
    import re

    def replacer(match: re.Match[str]) -> str:
        return f"sample-{match.group(1)}"

    concrete = re.sub(r"<str:([a-z0-9_]+)>", replacer, route)
    return "/" + concrete.lstrip("/")


def _snake(name: str) -> str:
    from md_drf_codegen.generator.naming import camel_to_snake

    return camel_to_snake(name)
