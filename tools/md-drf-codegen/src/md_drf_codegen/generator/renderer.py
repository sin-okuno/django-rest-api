"""Jinja2 template rendering for generated DRF code."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from md_drf_codegen.generator.context import SerializersModuleContext
from md_drf_codegen.generator.handlers_context import HandlersModuleContext
from md_drf_codegen.generator.tests_context import TestsModuleContext
from md_drf_codegen.generator.urls_context import UrlsModuleContext
from md_drf_codegen.generator.views_context import ViewsModuleContext


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("md_drf_codegen", "templates"),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["tojson"] = lambda value: json.dumps(value, ensure_ascii=False)
    env.filters["topython"] = repr
    return env


def render_serializers(context: SerializersModuleContext) -> str:
    """Render serializers.py from a prepared context."""
    template = _environment().get_template("serializers.py.j2")
    payload: dict[str, Any] = {
        "title": context.title,
        "source": context.source,
        "serializers": context.serializers,
    }
    return template.render(**payload)


def render_views(context: ViewsModuleContext) -> str:
    template = _environment().get_template("views.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
        views=context.views,
        serializer_imports=context.serializer_imports,
        handler_imports=context.handler_imports,
        serializers_module=context.serializers_module,
        handlers_module=context.handlers_module,
    )


def render_urls(context: UrlsModuleContext) -> str:
    template = _environment().get_template("urls.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
        patterns=context.patterns,
        views_module=context.views_module,
    )


def render_handlers(context: HandlersModuleContext) -> str:
    template = _environment().get_template("handlers.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
        handlers=context.handlers,
    )


# Backward-compatible alias
render_handler_registry = render_handlers


def render_tests(context: TestsModuleContext) -> str:
    template = _environment().get_template("test_generated_api.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
        package_name=context.package_name,
        serializers_module=context.serializers_module,
        views_module=context.views_module,
        handlers_module=context.handlers_module,
        serializer_valid=context.serializer_valid,
        serializer_missing=context.serializer_missing,
        serializer_nullable=context.serializer_nullable,
        serializer_nested=context.serializer_nested,
        url_resolve=context.url_resolve,
        get_handler=context.get_handler,
        put_validation=context.put_validation,
        response_serializer=context.response_serializer,
        bad_request=context.bad_request,
        unregistered=context.unregistered,
        serializer_imports=context.serializer_imports,
        view_imports=context.view_imports,
        handler_imports=context.handler_imports,
    )


def render_conftest(context: TestsModuleContext) -> str:
    template = _environment().get_template("conftest.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
        package_name=context.package_name,
        serializers_module=context.serializers_module,
        views_module=context.views_module,
        handlers_module=context.handlers_module,
    )


def render_package_init(context: TestsModuleContext) -> str:
    template = _environment().get_template("__init__.py.j2")
    return template.render(
        title=context.title,
        source=context.source,
    )


def template_package_available() -> bool:
    """Return True when packaged Jinja2 templates are importable."""
    root = resources.files("md_drf_codegen")
    return (root / "templates" / "serializers.py.j2").is_file()
