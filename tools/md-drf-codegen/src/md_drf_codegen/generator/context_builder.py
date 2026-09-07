"""Context models and builder for DRF serializer generation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec, FieldDefinition, TypeDefinition
from md_drf_codegen.schema.constraints import FieldConstraints
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
    needs_regex_validator: bool = False


def build_serializers_context(spec: ApiSpec) -> SerializersModuleContext:
    ordered = _order_types(spec.types)
    emitted: set[str] = set()
    serializers: list[SerializerRenderContext] = []
    needs_regex = False

    for type_name in ordered:
        type_def = spec.types[type_name]
        ser, uses_regex = _build_serializer_context(
            type_name, type_def, emitted=emitted, known=spec.types
        )
        serializers.append(ser)
        emitted.add(type_name)
        needs_regex = needs_regex or uses_regex

    return SerializersModuleContext(
        serializers=tuple(serializers),
        needs_regex_validator=needs_regex,
    )


def _build_serializer_context(
    type_name: str,
    type_def: TypeDefinition,
    *,
    emitted: set[str],
    known: dict[str, TypeDefinition],
) -> tuple[SerializerRenderContext, bool]:
    body_fields: list[FieldRenderContext] = []
    deferred_fields: list[FieldRenderContext] = []
    needs_regex = False

    for field_name, field_def in type_def.fields.items():
        field_ctx, uses_regex = _build_field_context(
            field_name,
            field_def,
            owner=type_name,
            emitted=emitted,
            known=known,
        )
        needs_regex = needs_regex or uses_regex
        if field_ctx.deferred:
            deferred_fields.append(field_ctx)
        else:
            body_fields.append(field_ctx)

    return (
        SerializerRenderContext(
            type_name=type_name,
            class_name=serializer_class_name(type_name),
            fields=tuple(body_fields),
            deferred_fields=tuple(deferred_fields),
        ),
        needs_regex,
    )


def _build_field_context(
    name: str,
    field_def: FieldDefinition,
    *,
    owner: str,
    emitted: set[str],
    known: dict[str, TypeDefinition],
) -> tuple[FieldRenderContext, bool]:
    required = field_def.required
    allow_null = field_def.nullable
    base = strip_array_suffix(field_def.type)
    many = is_array_type(field_def.type)
    uses_regex = False

    if is_primitive_type(base):
        expression, uses_regex = _primitive_expression(
            base,
            many=many,
            required=required,
            allow_null=allow_null,
            constraints=field_def.constraints,
        )
        return FieldRenderContext(name=name, expression=expression, deferred=False), uses_regex

    if base == owner or base not in emitted:
        expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
        return FieldRenderContext(name=name, expression=expression, deferred=True), False

    expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
    return FieldRenderContext(name=name, expression=expression, deferred=False), False


def _kwargs_parts(required: bool, allow_null: bool) -> list[str]:
    return [f"required={_bool(required)}", f"allow_null={_bool(allow_null)}"]


def _bool(value: bool) -> str:
    return "True" if value else "False"


def _constraint_parts(
    base: str,
    constraints: FieldConstraints | None,
) -> tuple[list[str], bool]:
    if constraints is None or constraints.is_empty():
        return [], False

    parts: list[str] = []
    uses_regex = False

    if base in {"integer", "number", "decimal"}:
        if constraints.min is not None:
            parts.append(f"min_value={_format_number(constraints.min)}")
        if constraints.max is not None:
            parts.append(f"max_value={_format_number(constraints.max)}")
    elif base == "string":
        if constraints.min_length is not None:
            parts.append(f"min_length={constraints.min_length}")
        if constraints.max_length is not None:
            parts.append(f"max_length={constraints.max_length}")
        resolved = constraints.resolved_pattern()
        if resolved is not None:
            regex, message = resolved
            escaped_regex = repr(regex)
            escaped_message = repr(message)
            parts.append(
                "validators=[RegexValidator("
                f"regex={escaped_regex}, message={escaped_message}"
                ")]"
            )
            uses_regex = True

    return parts, uses_regex


def _format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _primitive_expression(
    base: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
    constraints: FieldConstraints | None,
) -> tuple[str, bool]:
    if base not in PRIMITIVE_FIELD_CLASS:
        raise SchemaValidationError(
            f'Unsupported primitive type "{base}".',
            section="types",
            fix="Use string, integer, number, boolean, or object.",
        )

    field_cls = PRIMITIVE_FIELD_CLASS[base]
    constraint_parts, uses_regex = _constraint_parts(base, constraints)
    base_kwargs = _kwargs_parts(required, allow_null) + constraint_parts
    kwargs = ", ".join(base_kwargs)

    if many:
        child_kwargs = ", ".join(_kwargs_parts(True, False) + constraint_parts)
        child_expr = f"{field_cls}({child_kwargs})"
        list_kwargs = ", ".join(_kwargs_parts(required, allow_null))
        return f"serializers.ListField(child={child_expr}, {list_kwargs})", uses_regex

    return f"{field_cls}({kwargs})", uses_regex


def _nested_expression(
    type_name: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
) -> str:
    cls = serializer_class_name(type_name)
    kwargs = ", ".join(_kwargs_parts(required, allow_null))
    if many:
        return f"{cls}(many=True, {kwargs})"
    return f"{cls}({kwargs})"


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
