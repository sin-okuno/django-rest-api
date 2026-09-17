"""Append missing handler functions without overwriting customized ones."""

from __future__ import annotations

import ast


def merge_missing_handler_functions(existing: str, generated: str) -> str:
    """Return *existing* with any missing top-level functions from *generated* appended.

    Existing function bodies are never replaced. Only names absent from *existing*
    are appended, using the corresponding source from *generated*.
    """
    existing_tree = ast.parse(existing)
    generated_tree = ast.parse(generated)

    existing_names = {
        node.name
        for node in existing_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing_nodes = [
        node
        for node in generated_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name not in existing_names
    ]
    if not missing_nodes:
        return existing

    generated_lines = generated.splitlines(keepends=True)
    chunks: list[str] = []
    for node in missing_nodes:
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        # Include a leading blank line separator when previous chunk or file
        # does not already end with a blank line.
        chunk = "".join(generated_lines[start:end])
        chunks.append(chunk.rstrip() + "\n")

    base = existing.rstrip() + "\n\n"
    return base + "\n\n".join(chunks)
