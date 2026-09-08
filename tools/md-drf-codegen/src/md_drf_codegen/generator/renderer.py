"""Jinja2 template rendering for generated DRF code."""

from __future__ import annotations

import json
from importlib import resources

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from md_drf_codegen.generator.context_builder import SerializersModuleContext
from md_drf_codegen.generator.path_validator_generator import PathValidatorsModuleContext
from md_drf_codegen.generator.test_generator import TestsModuleContext
from md_drf_codegen.generator.url_generator import UrlsModuleContext
from md_drf_codegen.generator.view_generator import ViewsModuleContext


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
    template = _environment().get_template("serializers.py.j2")
    return template.render(
        serializers=context.serializers,
        needs_regex_validator=context.needs_regex_validator,
    )


def render_path_validators(context: PathValidatorsModuleContext) -> str:
    template = _environment().get_template("path_validators.py.j2")
    return template.render(
        validators=context.validators,
        needs_re=context.needs_re,
    )


def render_views(context: ViewsModuleContext) -> str:
    template = _environment().get_template("views.py.j2")
    return template.render(
        views=context.views,
        serializer_imports=context.serializer_imports,
        serializers_module=context.serializers_module,
        path_validator_imports=context.path_validator_imports,
        path_validators_module=context.path_validators_module,
    )


def render_urls(context: UrlsModuleContext) -> str:
    template = _environment().get_template("urls.py.j2")
    return template.render(
        patterns=context.patterns,
        views_module=context.views_module,
    )


def render_test_serializers(context: TestsModuleContext) -> str:
    template = _environment().get_template("test_serializers.py.j2")
    return template.render(
        package_name=context.package_name,
        serializers_module=context.serializers_module,
        serializer_imports=context.serializer_imports,
        serializer_valid=context.serializer_valid,
        serializer_missing=context.serializer_missing,
        serializer_invalid_type=context.serializer_invalid_type,
        serializer_nullable=context.serializer_nullable,
    )


def render_test_urls(context: TestsModuleContext) -> str:
    template = _environment().get_template("test_urls.py.j2")
    return template.render(url_resolve=context.url_resolve)


def render_test_views(context: TestsModuleContext) -> str:
    template = _environment().get_template("test_views.py.j2")
    return template.render(
        package_name=context.package_name,
        views_module=context.views_module,
        view_imports=context.view_imports,
        view_method=context.view_method,
        view_bad_request=context.view_bad_request,
        view_path_invalid=context.view_path_invalid,
    )


def render_conftest(context: TestsModuleContext) -> str:
    template = _environment().get_template("conftest.py.j2")
    return template.render(package_name=context.package_name)


def render_package_init() -> str:
    template = _environment().get_template("__init__.py.j2")
    return template.render()


def template_package_available() -> bool:
    root = resources.files("md_drf_codegen")
    return (root / "templates" / "serializers.py.j2").is_file()
