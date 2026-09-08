"""Context builder for APIView skeletons (no ORM, no business logic)."""

from __future__ import annotations

from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.schema import ApiEndpoint, ApiSpec, HttpMethod, PathParameterDefinition
from md_drf_codegen.utils.naming import (
    artifact_module_names,
    camel_to_snake,
    path_param_names,
    path_validators_module_name,
    serializer_class_name,
    view_class_name_from_api_id,
)

_QUERY_METHODS = {HttpMethod.GET}


@dataclass(frozen=True)
class PathParamContext:
    camel_name: str
    snake_name: str
    validator_function: str | None = None


@dataclass(frozen=True)
class MethodRenderContext:
    http_method: str
    api_id: str
    request_serializer: str | None
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
    views: tuple[ViewRenderContext, ...] = field(default_factory=tuple)
    serializer_imports: tuple[str, ...] = field(default_factory=tuple)
    serializers_module: str = "serializers"
    path_validators_module: str = "path_validators"
    path_validator_imports: tuple[str, ...] = field(default_factory=tuple)


def build_views_context(
    spec: ApiSpec,
    *,
    module_prefix: str | None = None,
) -> ViewsModuleContext:
    prefix = module_prefix or "generated"
    serializers_module, _views_module = artifact_module_names(prefix)
    path_validators_module = path_validators_module_name(prefix)

    grouped = _group_endpoints_by_path(spec.apis)
    views: list[ViewRenderContext] = []
    serializer_names: set[str] = set()
    validator_names: set[str] = set()

    for path in sorted(grouped.keys(), key=lambda p: ("{" in p, p)):
        endpoints = grouped[path]
        view = _build_view(path, endpoints, spec.path_parameters)
        views.append(view)
        for method in view.methods:
            if method.request_serializer:
                serializer_names.add(method.request_serializer)
            for param in method.path_params:
                if param.validator_function:
                    validator_names.add(param.validator_function)

    return ViewsModuleContext(
        views=tuple(views),
        serializer_imports=tuple(sorted(serializer_names)),
        serializers_module=serializers_module,
        path_validators_module=path_validators_module,
        path_validator_imports=tuple(sorted(validator_names)),
    )


def _group_endpoints_by_path(apis: list[ApiEndpoint]) -> dict[str, list[ApiEndpoint]]:
    grouped: dict[str, list[ApiEndpoint]] = {}
    for api in apis:
        grouped.setdefault(api.path, []).append(api)
    return grouped


def _build_view(
    path: str,
    endpoints: list[ApiEndpoint],
    path_parameters: dict[str, PathParameterDefinition],
) -> ViewRenderContext:
    params = tuple(
        PathParamContext(
            camel_name=name,
            snake_name=camel_to_snake(name),
            validator_function=(
                f"validate_{camel_to_snake(name)}"
                if name in path_parameters
                else None
            ),
        )
        for name in path_param_names(path)
    )
    by_method = {endpoint.method: endpoint for endpoint in endpoints}
    if len(by_method) != len(endpoints):
        raise SchemaValidationError(
            f'Duplicate HTTP method on path "{path}".',
            section="apis",
            fix="Keep at most one endpoint per HTTP method for each path.",
        )

    method_order = [HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT]
    methods: list[MethodRenderContext] = []
    primary_api_id = endpoints[0].id

    for method in method_order:
        endpoint = by_method.get(method)
        if endpoint is None:
            continue
        request_serializer = (
            serializer_class_name(endpoint.request_type) if endpoint.request_type else None
        )
        methods.append(
            MethodRenderContext(
                http_method=endpoint.method.value.lower(),
                api_id=endpoint.id,
                request_serializer=request_serializer,
                uses_query_params=endpoint.method in _QUERY_METHODS and request_serializer,
                path_params=params,
            )
        )

    return ViewRenderContext(
        class_name=view_class_name_from_api_id(primary_api_id),
        path=path,
        methods=tuple(methods),
        path_params=params,
    )
