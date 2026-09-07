"""Backward-compatible re-exports from schema package."""

from md_drf_codegen.schema import (
    ApiEndpoint,
    ApiSpec,
    FieldDefinition,
    HttpMethod,
    MarkdownDocument,
    MarkdownSection,
    MarkdownTable,
    NormalizedType,
    TypeDefinition,
)

# Legacy aliases used by older modules during migration.
ApiTypeDefinition = TypeDefinition
TypeProperty = FieldDefinition

__all__ = [
    "ApiEndpoint",
    "ApiSpec",
    "ApiTypeDefinition",
    "FieldDefinition",
    "HttpMethod",
    "MarkdownDocument",
    "MarkdownSection",
    "MarkdownTable",
    "NormalizedType",
    "TypeDefinition",
    "TypeProperty",
]
