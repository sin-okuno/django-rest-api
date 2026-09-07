"""Python syntax validation for generated code."""

from __future__ import annotations

import ast

from md_drf_codegen.errors import CodegenError


def validate_python_syntax(source: str, *, source_name: str = "<generated>") -> None:
    """Parse *source* with ``ast.parse`` and raise on syntax errors."""
    try:
        ast.parse(source, filename=source_name)
    except SyntaxError as exc:
        raise CodegenError(
            "PYTHON_SYNTAX_ERROR",
            f"Generated Python has a syntax error in {source_name}: {exc}",
            fix="Fix the generator template or context builder.",
        ) from exc
