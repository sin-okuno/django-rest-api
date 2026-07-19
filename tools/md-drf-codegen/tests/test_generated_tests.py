"""Tests for generated pytest module creation."""

from __future__ import annotations

import ast
from pathlib import Path

from md_drf_codegen.generator import generate_all_from_yaml, generate_tests_code
from md_drf_codegen.generator.tests_context import build_tests_context
from md_drf_codegen.yaml_io import load_api_spec_yaml


def test_tests_context_covers_required_categories(product_structure_yaml: Path) -> None:
    spec = load_api_spec_yaml(product_structure_yaml)
    context = build_tests_context(spec)
    assert context.serializer_valid
    assert context.serializer_missing
    assert context.serializer_nullable
    assert context.serializer_nested
    assert context.url_resolve
    assert context.get_handler
    assert context.put_validation
    assert context.response_serializer
    assert context.bad_request
    assert context.unregistered
    # No empty suites
    assert all(item.function_name.startswith("test_") for item in context.serializer_valid)


def test_generated_tests_ast_parseable(product_structure_yaml: Path) -> None:
    code = generate_tests_code(load_api_spec_yaml(product_structure_yaml))
    tree = ast.parse(code)
    functions = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    assert functions
    assert "pass" not in code
    assert "NotImplementedError" in code


def test_generate_all_includes_test_artifacts(product_structure_yaml: Path) -> None:
    files = generate_all_from_yaml(product_structure_yaml)
    assert "test_generated_api.py" in files
    assert "conftest.py" in files
    assert "__init__.py" in files
    for name in ("test_generated_api.py", "conftest.py", "__init__.py"):
        ast.parse(files[name])
