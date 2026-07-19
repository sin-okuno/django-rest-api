"""Context builder for handlers.py (business-logic handler classes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_drf_codegen.generator.naming import camel_to_snake, handler_class_name, path_param_names
from md_drf_codegen.generator.sample_data import build_sample_object
from md_drf_codegen.models import ApiEndpoint, ApiSpec, HttpMethod


@dataclass(frozen=True)
class HandlerStubContext:
    api_id: str
    class_name: str
    description: str
    has_validated_data: bool
    path_params: tuple[str, ...]
    is_get: bool
    demo_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class HandlersModuleContext:
    title: str
    source: str
    handlers: tuple[HandlerStubContext, ...] = field(default_factory=tuple)


def build_handlers_context(spec: ApiSpec) -> HandlersModuleContext:
    types_by_name = {type_def.name: type_def for type_def in spec.types}
    return HandlersModuleContext(
        title=spec.title,
        source=spec.source,
        handlers=tuple(_build_stub(endpoint, types_by_name) for endpoint in spec.apis),
    )


# Backward-compatible aliases used by older imports during transition.
HandlerRegistryContext = HandlersModuleContext
build_handler_registry_context = build_handlers_context


def _build_stub(
    endpoint: ApiEndpoint,
    types_by_name: dict[str, Any],
) -> HandlerStubContext:
    is_get = endpoint.method == HttpMethod.GET
    demo_payload: dict[str, Any] | None = None
    if is_get:
        demo_payload = _demo_payload_for_response(endpoint.response_type, types_by_name)

    return HandlerStubContext(
        api_id=endpoint.id,
        class_name=handler_class_name(endpoint.id),
        description=endpoint.description or endpoint.name,
        has_validated_data=endpoint.request_type is not None,
        path_params=tuple(camel_to_snake(name) for name in path_param_names(endpoint.path)),
        is_get=is_get,
        demo_payload=demo_payload,
    )


def _demo_payload_for_response(
    response_type: str | None,
    types_by_name: dict[str, Any],
) -> dict[str, Any]:
    if response_type is None:
        return {"ok": True, "demo": True}
    type_def = types_by_name.get(response_type)
    if type_def is None:
        return {"ok": True, "demo": True, "type": response_type}
    payload = build_sample_object(type_def, types_by_name=types_by_name)
    # Mark as demo so callers can tell temporary data from production.
    return payload
