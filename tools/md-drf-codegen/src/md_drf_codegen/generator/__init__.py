"""Orchestrate YAML → DRF code generation."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from md_drf_codegen.generator.context_builder import build_serializers_context
from md_drf_codegen.generator.path_validator_generator import build_path_validators_context
from md_drf_codegen.generator.renderer import (
    render_conftest,
    render_package_init,
    render_path_validators,
    render_serializers,
    render_test_serializers,
    render_test_urls,
    render_test_views,
    render_urls,
    render_views,
)
from md_drf_codegen.generator.test_generator import build_tests_context
from md_drf_codegen.generator.url_generator import build_urls_context
from md_drf_codegen.generator.view_generator import build_views_context
from md_drf_codegen.openapi_io import dump_openapi_yaml
from md_drf_codegen.schema import ApiSpec
from md_drf_codegen.utils.file_utils import write_generated_files
from md_drf_codegen.utils.naming import (
    artifact_module_names,
    path_validators_module_name,
    sanitize_module_name,
)
from md_drf_codegen.validator import validate_api_spec
from md_drf_codegen.yaml_io import dump_api_spec_yaml, load_api_spec_yaml


class GenerateTarget(StrEnum):
    YAML = "yaml"
    OPENAPI = "openapi"
    SERIALIZER = "serializer"
    ALL = "all"


def generate_openapi_content(spec: ApiSpec, *, title: str | None = None) -> str:
    return dump_openapi_yaml(spec, title=title)


def generate_yaml_content(spec: ApiSpec) -> str:
    validate_api_spec(spec)
    return dump_api_spec_yaml(spec)


def generate_code_files(
    spec: ApiSpec,
    *,
    target: GenerateTarget,
    package_name: str = "generated",
) -> dict[str, str]:
    validate_api_spec(spec)
    prefix = sanitize_module_name(package_name)
    serializers_module, views_module = artifact_module_names(prefix)

    files: dict[str, str] = {}
    if target in {GenerateTarget.SERIALIZER, GenerateTarget.ALL}:
        files[f"{serializers_module}.py"] = render_serializers(build_serializers_context(spec))

    if target in {GenerateTarget.OPENAPI, GenerateTarget.ALL}:
        files["openapi.yaml"] = generate_openapi_content(spec)

    if target == GenerateTarget.ALL:
        views_ctx = build_views_context(spec, module_prefix=prefix)
        urls_ctx = build_urls_context(spec, module_prefix=prefix)
        tests_ctx = build_tests_context(spec, package_name=prefix)
        path_ctx = build_path_validators_context(spec, module_prefix=prefix)

        files[f"{views_module}.py"] = render_views(views_ctx)
        if path_ctx.validators:
            files[f"{path_validators_module_name(prefix)}.py"] = render_path_validators(path_ctx)
        files["urls.py"] = render_urls(urls_ctx)
        files["__init__.py"] = render_package_init()
        files["conftest.py"] = render_conftest(tests_ctx)
        files["test_serializers.py"] = render_test_serializers(tests_ctx)
        files["test_urls.py"] = render_test_urls(tests_ctx)
        files["test_views.py"] = render_test_views(tests_ctx)

    return files


def generate_from_yaml(
    yaml_path: str | Path,
    *,
    target: GenerateTarget,
    package_name: str | None = None,
) -> dict[str, str]:
    spec = load_api_spec_yaml(yaml_path)
    pkg = package_name or sanitize_module_name(Path(yaml_path).stem)
    if target == GenerateTarget.YAML:
        return {"output.yaml": generate_yaml_content(spec)}
    if target == GenerateTarget.OPENAPI:
        return {"openapi.yaml": generate_openapi_content(spec)}
    return generate_code_files(spec, target=target, package_name=pkg)


def write_generation_result(
    files: dict[str, str],
    output_dir: str | Path,
    *,
    force: bool = False,
    check: bool = False,
) -> list[Path]:
    return write_generated_files(files, output_dir, force=force, check=check)
