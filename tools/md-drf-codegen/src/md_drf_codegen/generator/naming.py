"""Naming helpers for generated views and URLs."""

from __future__ import annotations

import re
from pathlib import Path

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_PATH_PARAM = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_MODULE_SAFE = re.compile(r"[^0-9A-Za-z_]+")


def camel_to_snake(name: str) -> str:
    """Convert camelCase / PascalCase to snake_case."""
    text = name.strip()
    if not text:
        return text
    return _CAMEL_BOUNDARY.sub("_", text).replace("-", "_").lower()


def snake_to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def sanitize_module_name(raw: str, *, fallback: str = "generated") -> str:
    """Normalize a path stem (e.g. ``product-structure``) into a Python module token."""
    name = _MODULE_SAFE.sub("_", raw.strip()).strip("_")
    if not name:
        return fallback
    if name[0].isdigit():
        return f"pkg_{name}"
    return name


def module_prefix_from_source(source: str, *, fallback: str = "generated") -> str:
    """Derive file-prefix from Markdown source path stem.

    ``examples/specs/product-structure.md`` → ``product_structure``
    """
    text = (source or "").strip().replace("\\", "/")
    if not text:
        return fallback
    stem = Path(text).stem
    return sanitize_module_name(stem, fallback=fallback)


def artifact_module_names(prefix: str) -> tuple[str, str, str]:
    """Return ``(serializers_module, views_module, handlers_module)`` for *prefix*."""
    return (
        f"{prefix}_serializers",
        f"{prefix}_views",
        f"{prefix}_handlers",
    )


def path_param_names(path: str) -> tuple[str, ...]:
    """Return camelCase path parameter names in appearance order."""
    return tuple(_PATH_PARAM.findall(path))


def path_params_snake(path: str) -> tuple[str, ...]:
    return tuple(camel_to_snake(name) for name in path_param_names(path))


def is_dynamic_path(path: str) -> bool:
    return "{" in path


def django_route(path: str) -> str:
    """Convert `/api/products/{productId}` to `api/products/<str:product_id>`."""
    trimmed = path.lstrip("/")

    def replacer(match: re.Match[str]) -> str:
        return f"<str:{camel_to_snake(match.group(1))}>"

    return _PATH_PARAM.sub(replacer, trimmed)


def view_class_name(path: str) -> str:
    """Derive an APIView class name from a URL path."""
    parts: list[str] = []
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        param_match = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", segment)
        if param_match:
            parts.append(snake_to_pascal(camel_to_snake(param_match.group(1))))
        else:
            parts.append(snake_to_pascal(camel_to_snake(segment)))
    if not parts:
        return "RootView"
    return "".join(parts) + "View"


def url_name(path: str) -> str:
    """Build a kebab-case Django URL name from a path."""
    parts: list[str] = []
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        param_match = re.fullmatch(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", segment)
        if param_match:
            snake = camel_to_snake(param_match.group(1))
            parts.append(snake.replace("_", "-"))
        else:
            snake = camel_to_snake(segment)
            parts.append(_NON_ALNUM.sub("-", snake).strip("-"))
    return "-".join(part for part in parts if part)


def handler_class_name(api_id: str) -> str:
    """Convert API ID ``loadDetail`` to class name ``LoadDetailHandler``."""
    return f"{snake_to_pascal(camel_to_snake(api_id))}Handler"
