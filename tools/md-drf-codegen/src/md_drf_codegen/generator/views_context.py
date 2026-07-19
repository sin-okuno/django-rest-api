"""Context builder for APIView skeletons (no ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.generator.context import serializer_class_name
from md_drf_codegen.generator.naming import (
    artifact_module_names,
    camel_to_snake,
    handler_class_name,
    module_prefix_from_source,
    path_param_names,
    view_class_name,
)
from md_drf_codegen.models import ApiEndpoint, ApiSpec, HttpMethod

_QUERY_METHODS = {HttpMethod.GET, HttpMethod.DELETE}


@dataclass(frozen=True)
class PathParamContext:
    camel_name: str
    snake_name: str


@dataclass(frozen=True)
class MethodRenderContext:
    """One HTTP method handler on an APIView."""

    http_method: str
    api_id: str
    handler_class: str
    description: str
    request_serializer: str | None
    response_serializer: str | None
    uses_query_params: bool
    path_params: tuple[PathParamContext, ...]


@dataclass(frozen=True)
class ViewRenderContext:
    class_name: str
    path: str
    methods: tuple[MethodRenderContext, ...]
    path_params: tuple[PathParamContext, ...]


@dataclass(frozen=True)
class ViewsModuleContext:
    title: str
    source: str
    views: tuple[ViewRenderContext, ...] = field(default_factory=tuple)
    serializer_imports: tuple[str, ...] = field(default_factory=tuple)
    handler_imports: tuple[str, ...] = field(default_factory=tuple)
    serializers_module: str = "serializers"
    handlers_module: str = "handlers"


def build_views_context(
    spec: ApiSpec,
    *,
    module_prefix: str | None = None,
) -> ViewsModuleContext:
    prefix = module_prefix or module_prefix_from_source(spec.source)
    serializers_module, _views_module, handlers_module = artifact_module_names(prefix)

    grouped = _group_endpoints_by_path(spec.apis)
    views: list[ViewRenderContext] = []
    serializer_names: set[str] = set()
    handler_names: set[str] = set()

    # Fixed paths first (same ordering rule as URLConf).
    ordered_paths = sorted(grouped.keys(), key=lambda path: ("{" in path, path))

    for path in ordered_paths:
        endpoints = grouped[path]
        view = _build_view(path, endpoints)
        views.append(view)
        for method in view.methods:
            handler_names.add(method.handler_class)
            if method.request_serializer:
                serializer_names.add(method.request_serializer)
            if method.response_serializer:
                serializer_names.add(method.response_serializer)

    return ViewsModuleContext(
        title=spec.title,
        source=spec.source,
        views=tuple(views),
        serializer_imports=tuple(sorted(serializer_names)),
        handler_imports=tuple(sorted(handler_names)),
        serializers_module=serializers_module,
        handlers_module=handlers_module,
    )


def _group_endpoints_by_path(apis: list[ApiEndpoint]) -> dict[str, list[ApiEndpoint]]:
    """Group by path, preserving first-seen path order."""
    grouped: dict[str, list[ApiEndpoint]] = {}
    for api in apis:
        grouped.setdefault(api.path, []).append(api)
    return grouped


def _build_view(path: str, endpoints: list[ApiEndpoint]) -> ViewRenderContext:
    params = tuple(
        PathParamContext(camel_name=name, snake_name=camel_to_snake(name))
        for name in path_param_names(path)
    )
    seen_methods: set[HttpMethod] = set()
    methods: list[MethodRenderContext] = []

    # Stable order: GET, POST, PUT, PATCH, DELETE
    method_order = [
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.PATCH,
        HttpMethod.DELETE,
    ]
    by_method = {endpoint.method: endpoint for endpoint in endpoints}
    if len(by_method) != len(endpoints):
        duplicates = [ep.method.value for ep in endpoints]
        raise SchemaValidationError(
            f'Duplicate HTTP method on path "{path}": {duplicates}',
            section="apis",
            fix="Keep at most one endpoint per HTTP method for each path.",
        )

    for method in method_order:
        endpoint = by_method.get(method)
        if endpoint is None:
            continue
        if method in seen_methods:
            raise SchemaValidationError(
                f'Duplicate HTTP method {method.value} on path "{path}".',
                section="apis",
            )
        seen_methods.add(method)
        methods.append(_build_method(endpoint, params))

    return ViewRenderContext(
        class_name=view_class_name(path),
        path=path,
        methods=tuple(methods),
        path_params=params,
    )


def _build_method(
    endpoint: ApiEndpoint,
    path_params: tuple[PathParamContext, ...],
) -> MethodRenderContext:
    request_serializer = (
        serializer_class_name(endpoint.request_type) if endpoint.request_type else None
    )
    response_serializer = (
        serializer_class_name(endpoint.response_type) if endpoint.response_type else None
    )
    return MethodRenderContext(
        http_method=endpoint.method.value.lower(),
        api_id=endpoint.id,
        handler_class=handler_class_name(endpoint.id),
        description=endpoint.description or endpoint.name,
        request_serializer=request_serializer,
        response_serializer=response_serializer,
        uses_query_params=endpoint.method in _QUERY_METHODS,
        path_params=path_params,
    )
