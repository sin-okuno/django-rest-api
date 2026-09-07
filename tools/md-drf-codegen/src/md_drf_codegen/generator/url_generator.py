"""Context builder for Django URLConf entries."""

from __future__ import annotations

from dataclasses import dataclass, field

from md_drf_codegen.generator.view_generator import build_views_context
from md_drf_codegen.schema import ApiSpec
from md_drf_codegen.utils.naming import (
    api_id_to_url_name,
    artifact_module_names,
    django_route,
    is_dynamic_path,
)


@dataclass(frozen=True)
class UrlPatternContext:
    django_route: str
    view_class: str
    name: str
    is_dynamic: bool
    path: str


@dataclass(frozen=True)
class UrlsModuleContext:
    patterns: tuple[UrlPatternContext, ...] = field(default_factory=tuple)
    views_module: str = "views"


def build_urls_context(
    spec: ApiSpec,
    *,
    module_prefix: str | None = None,
) -> UrlsModuleContext:
    prefix = module_prefix or "generated"
    _serializers_module, views_module = artifact_module_names(prefix)
    views_ctx = build_views_context(spec, module_prefix=prefix)

    seen: set[str] = set()
    patterns: list[UrlPatternContext] = []

    for api in spec.apis:
        if api.path in seen:
            continue
        seen.add(api.path)
        view = next(v for v in views_ctx.views if v.path == api.path)
        patterns.append(
            UrlPatternContext(
                django_route=django_route(api.path),
                view_class=view.class_name,
                name=api_id_to_url_name(api.id),
                is_dynamic=is_dynamic_path(api.path),
                path=api.path,
            )
        )

    patterns.sort(key=lambda item: (item.is_dynamic, item.django_route))
    return UrlsModuleContext(
        patterns=tuple(patterns),
        views_module=views_module,
    )
