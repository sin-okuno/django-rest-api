"""Orchestrate YAML → DRF code generation."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.generator.context import build_serializers_context
from md_drf_codegen.generator.handlers_context import build_handlers_context
from md_drf_codegen.generator.naming import (
    artifact_module_names,
    module_prefix_from_source,
)
from md_drf_codegen.generator.renderer import (
    render_conftest,
    render_handlers,
    render_package_init,
    render_serializers,
    render_tests,
    render_urls,
    render_views,
)
from md_drf_codegen.generator.tests_context import build_tests_context
from md_drf_codegen.generator.urls_context import build_urls_context
from md_drf_codegen.generator.views_context import build_views_context
from md_drf_codegen.models import ApiSpec
from md_drf_codegen.validate import validate_api_spec
from md_drf_codegen.yaml_io import load_api_spec_yaml

# Unprefixed legacy filenames removed after generating prefixed modules.
_LEGACY_ARTIFACT_FILES: tuple[str, ...] = (
    "serializers.py",
    "views.py",
    "handlers.py",
)


def generate_serializers_code(spec: ApiSpec) -> str:
    """Validate spec, build context, and render serializers.py source."""
    validate_api_spec(spec)
    context = build_serializers_context(spec)
    return render_serializers(context)


def generate_views_code(spec: ApiSpec) -> str:
    validate_api_spec(spec)
    return render_views(build_views_context(spec))


def generate_urls_code(spec: ApiSpec) -> str:
    validate_api_spec(spec)
    return render_urls(build_urls_context(spec))


def generate_handlers_code(spec: ApiSpec) -> str:
    validate_api_spec(spec)
    return render_handlers(build_handlers_context(spec))


def generate_tests_code(spec: ApiSpec, *, package_name: str = "generated") -> str:
    validate_api_spec(spec)
    return render_tests(build_tests_context(spec, package_name=package_name))


def generate_all_code(spec: ApiSpec, *, package_name: str = "generated") -> dict[str, str]:
    """Return mapping of filename → generated source for all artifacts."""
    validate_api_spec(spec)
    prefix = module_prefix_from_source(spec.source, fallback=package_name)
    serializers_module, views_module, handlers_module = artifact_module_names(prefix)

    tests_ctx = build_tests_context(spec, package_name=package_name)
    views_ctx = build_views_context(spec, module_prefix=prefix)
    urls_ctx = build_urls_context(spec, module_prefix=prefix)
    return {
        "__init__.py": render_package_init(tests_ctx),
        f"{serializers_module}.py": render_serializers(build_serializers_context(spec)),
        f"{views_module}.py": render_views(views_ctx),
        "urls.py": render_urls(urls_ctx),
        f"{handlers_module}.py": render_handlers(build_handlers_context(spec)),
        "conftest.py": render_conftest(tests_ctx),
        "test_generated_api.py": render_tests(tests_ctx),
    }


def generate_serializers_from_yaml(yaml_path: str | Path) -> str:
    spec = load_api_spec_yaml(yaml_path)
    return generate_serializers_code(spec)


def generate_all_from_yaml(
    yaml_path: str | Path,
    *,
    package_name: str = "generated",
) -> dict[str, str]:
    spec = load_api_spec_yaml(yaml_path)
    return generate_all_code(spec, package_name=package_name)


def write_serializers_file(code: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8", newline="\n")
    return path.resolve()


def write_generated_files(files: dict[str, str], output_dir: str | Path) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, code in files.items():
        path = directory / name
        path.write_text(code, encoding="utf-8", newline="\n")
        written.append(path.resolve())

    # Drop unprefixed legacy modules so re-generation does not leave stale files.
    for legacy in _LEGACY_ARTIFACT_FILES:
        legacy_path = directory / legacy
        if legacy_path.exists() and legacy not in files:
            legacy_path.unlink()

    return written
