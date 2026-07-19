"""Context builder for Django URLConf entries."""

from __future__ import annotations

from dataclasses import dataclass, field

from md_drf_codegen.generator.naming import (
    artifact_module_names,
    django_route,
    is_dynamic_path,
    module_prefix_from_source,
    url_name,
    view_class_name,
)
from md_drf_codegen.models import ApiSpec


@dataclass(frozen=True)
class UrlPatternContext:
    django_route: str
    view_class: str
    name: str
    is_dynamic: bool
    path: str


@dataclass(frozen=True)
class UrlsModuleContext:
    title: str
    source: str
    patterns: tuple[UrlPatternContext, ...] = field(default_factory=tuple)
    views_module: str = "views"


def build_urls_context(
    spec: ApiSpec,
    *,
    module_prefix: str | None = None,
) -> UrlsModuleContext:
    """Build URL patterns: one entry per unique path, fixed routes first."""
    prefix = module_prefix or module_prefix_from_source(spec.source)
    _serializers_module, views_module, _handlers_module = artifact_module_names(prefix)

    seen: set[str] = set()
    patterns: list[UrlPatternContext] = []

    for api in spec.apis:
        if api.path in seen:
            continue
        seen.add(api.path)
        patterns.append(
            UrlPatternContext(
                django_route=django_route(api.path),
                view_class=view_class_name(api.path),
                name=url_name(api.path),
                is_dynamic=is_dynamic_path(api.path),
                path=api.path,
            )
        )

    patterns.sort(key=lambda item: (item.is_dynamic, item.django_route))
    return UrlsModuleContext(
        title=spec.title,
        source=spec.source,
        patterns=tuple(patterns),
        views_module=views_module,
    )
