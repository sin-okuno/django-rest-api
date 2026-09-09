"""Naming helpers for generated views, URLs, and serializers."""

from __future__ import annotations

import re
from pathlib import Path

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_PATH_PARAM = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_MODULE_SAFE = re.compile(r"[^0-9A-Za-z_]+")
_ENUM_MEMBER_SAFE = re.compile(r"[^0-9A-Za-z]+")


def camel_to_snake(name: str) -> str:
    """Convert camelCase / PascalCase to snake_case."""
    text = name.strip()
    if not text:
        return text
    return _CAMEL_BOUNDARY.sub("_", text).replace("-", "_").lower()


def snake_to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def enum_class_name_from_field(field_name: str) -> str:
    """Map ``status`` / ``productStatus`` to ``Status`` / ``ProductStatus``."""
    return snake_to_pascal(camel_to_snake(field_name))


def enum_member_name(value: str | int | float, label: str | None) -> str:
    """Derive a SCREAMING_SNAKE member name from label or value."""
    source = (label or str(value)).strip()
    cleaned = _ENUM_MEMBER_SAFE.sub("_", source).strip("_").upper()
    if cleaned and cleaned[0].isdigit():
        cleaned = f"VALUE_{cleaned}"
    if not cleaned:
        cleaned = f"VALUE_{value}".upper().replace(".", "_").replace("-", "_")
        cleaned = _ENUM_MEMBER_SAFE.sub("_", cleaned).strip("_")
    if not cleaned or not cleaned.replace("_", "").isalnum():
        cleaned = f"VALUE_{value}".upper().replace(".", "_").replace("-", "NEG_")
        cleaned = _ENUM_MEMBER_SAFE.sub("_", cleaned).strip("_") or "VALUE"
    if cleaned[0].isdigit():
        cleaned = f"VALUE_{cleaned}"
    return cleaned


def sanitize_module_name(raw: str, *, fallback: str = "generated") -> str:
    """Normalize a path stem (e.g. ``product-structure``) into a Python module token."""
    name = _MODULE_SAFE.sub("_", raw.strip()).strip("_")
    if not name:
        return fallback
    if name[0].isdigit():
        return f"pkg_{name}"
    return name


def module_prefix_from_source(source: str, *, fallback: str = "generated") -> str:
    """Derive file-prefix from Markdown source path stem."""
    text = (source or "").strip().replace("\\", "/")
    if not text:
        return fallback
    stem = Path(text).stem
    return sanitize_module_name(stem, fallback=fallback)


def artifact_module_names(prefix: str) -> tuple[str, str]:
    """Return ``(serializers_module, views_module)`` for *prefix*."""
    return (
        f"{prefix}_serializers",
        f"{prefix}_views",
    )


def path_validators_module_name(prefix: str) -> str:
    """Return the generated path-validators module name for *prefix*."""
    return f"{prefix}_path_validators"


def serializer_class_name(type_name: str) -> str:
    """Map ``ProductDetailResponse`` to ``ProductDetailResponseSerializer``."""
    return f"{type_name}Serializer"


def api_id_to_url_name(api_id: str) -> str:
    """Map ``getProduct`` to ``get-product``."""
    snake = camel_to_snake(api_id)
    return _NON_ALNUM.sub("-", snake).strip("-")


def view_class_name_from_api_id(api_id: str) -> str:
    """Map ``getProduct`` to ``GetProductAPIView``."""
    return f"{snake_to_pascal(camel_to_snake(api_id))}APIView"


def path_param_names(path: str) -> tuple[str, ...]:
    """Return camelCase path parameter names in appearance order."""
    return tuple(_PATH_PARAM.findall(path))


def resolve_path_template(path: str, *, values: dict[str, str] | None = None) -> str:
    """Replace ``{productId}`` placeholders with concrete values for tests."""
    result = path
    for camel in path_param_names(path):
        snake = camel_to_snake(camel)
        value = (values or {}).get(snake, "test-value")
        result = result.replace(f"{{{camel}}}", value)
    return result


def django_route(path: str) -> str:
    """Convert ``/api/products/{productId}`` to ``api/products/<str:product_id>``."""
    trimmed = path.lstrip("/")

    def replacer(match: re.Match[str]) -> str:
        return f"<str:{camel_to_snake(match.group(1))}>"

    return _PATH_PARAM.sub(replacer, trimmed)


def is_dynamic_path(path: str) -> bool:
    return "{" in path
