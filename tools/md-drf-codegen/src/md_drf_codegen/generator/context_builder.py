"""Context models and builder for DRF serializer generation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec, FieldDefinition, TypeDefinition
from md_drf_codegen.utils.naming import serializer_class_name

PRIMITIVE_FIELD_CLASS: dict[str, str] = {
    "string": "serializers.CharField",
    "integer": "serializers.IntegerField",
    "number": "serializers.FloatField",
    "boolean": "serializers.BooleanField",
    "object": "serializers.JSONField",
}


@dataclass(frozen=True)
class FieldRenderContext:
    name: str
    expression: str
    deferred: bool = False


@dataclass(frozen=True)
class SerializerRenderContext:
    type_name: str
    class_name: str
    fields: tuple[FieldRenderContext, ...]
    deferred_fields: tuple[FieldRenderContext, ...] = ()


@dataclass(frozen=True)
class SerializersModuleContext:
    source: str = ""
    serializers: tuple[SerializerRenderContext, ...] = field(default_factory=tuple)


def build_serializers_context(spec: ApiSpec) -> SerializersModuleContext:
    ordered = _order_types(spec.types)
    emitted: set[str] = set()
    serializers: list[SerializerRenderContext] = []

    for type_name in ordered:
        type_def = spec.types[type_name]
        ser = _build_serializer_context(type_name, type_def, emitted=emitted, known=spec.types)
        serializers.append(ser)
        emitted.add(type_name)

    return SerializersModuleContext(serializers=tuple(serializers))


def _build_serializer_context(
    type_name: str,
    type_def: TypeDefinition,
    *,
    emitted: set[str],
    known: dict[str, TypeDefinition],
) -> SerializerRenderContext:
    body_fields: list[FieldRenderContext] = []
    deferred_fields: list[FieldRenderContext] = []

    for field_name, field_def in type_def.fields.items():
        field_ctx = _build_field_context(
            field_name,
            field_def,
            owner=type_name,
            emitted=emitted,
            known=known,
        )
        if field_ctx.deferred:
            deferred_fields.append(field_ctx)
        else:
            body_fields.append(field_ctx)

    return SerializerRenderContext(
        type_name=type_name,
        class_name=serializer_class_name(type_name),
        fields=tuple(body_fields),
        deferred_fields=tuple(deferred_fields),
    )


def _build_field_context(
    name: str,
    field_def: FieldDefinition,
    *,
    owner: str,
    emitted: set[str],
    known: dict[str, TypeDefinition],
) -> FieldRenderContext:
    required = field_def.required
    allow_null = field_def.nullable
    base = strip_array_suffix(field_def.type)
    many = is_array_type(field_def.type)

    if is_primitive_type(base):
        expression = _primitive_expression(
            base,
            many=many,
            required=required,
            allow_null=allow_null,
        )
        return FieldRenderContext(name=name, expression=expression, deferred=False)

    if base == owner or base not in emitted:
        expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
        return FieldRenderContext(name=name, expression=expression, deferred=True)

    expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
    return FieldRenderContext(name=name, expression=expression, deferred=False)


def _kwargs(required: bool, allow_null: bool) -> str:
    return f"required={_bool(required)}, allow_null={_bool(allow_null)}"


def _bool(value: bool) -> str:
    return "True" if value else "False"


def _primitive_expression(
    base: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
) -> str:
    if base not in PRIMITIVE_FIELD_CLASS:
        raise SchemaValidationError(
            f'Unsupported primitive type "{base}".',
            section="types",
            fix="Use string, integer, number, boolean, or object.",
        )

    field_cls = PRIMITIVE_FIELD_CLASS[base]
    if many:
        child_expr = f"{field_cls}({_kwargs(True, False)})"
        return f"serializers.ListField(child={child_expr}, {_kwargs(required, allow_null)})"
    return f"{field_cls}({_kwargs(required, allow_null)})"


def _nested_expression(
    type_name: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
) -> str:
    cls = serializer_class_name(type_name)
    if many:
        return f"{cls}(many=True, {_kwargs(required, allow_null)})"
    return f"{cls}({_kwargs(required, allow_null)})"


def _order_types(types: dict[str, TypeDefinition]) -> list[str]:
    dependents: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {name: 0 for name in types}

    for type_name, type_def in types.items():
        for dep in _dependencies(type_name, type_def, known=types):
            if type_name not in dependents[dep]:
                dependents[dep].add(type_name)
                indegree[type_name] += 1

    queue: deque[str] = deque(sorted(name for name, deg in indegree.items() if deg == 0))
    ordered: list[str] = []

    while queue:
        name = queue.popleft()
        ordered.append(name)
        for nxt in sorted(dependents[name]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    remaining = [name for name in types if name not in set(ordered)]
    ordered.extend(remaining)
    return ordered


def _dependencies(
    type_name: str,
    type_def: TypeDefinition,
    *,
    known: dict[str, TypeDefinition],
) -> set[str]:
    deps: set[str] = set()
    for field_def in type_def.fields.values():
        base = strip_array_suffix(field_def.type)
        if is_primitive_type(base):
            continue
        if base == type_name:
            continue
        if base in known:
            deps.add(base)
    return deps
