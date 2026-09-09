"""Context models and builder for DRF serializer generation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.models import ApiSpec, ApiTypeDefinition, TypeProperty
from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix

PRIMITIVE_FIELD_CLASS: dict[str, str] = {
    "string": "serializers.CharField",
    "integer": "serializers.IntegerField",
    "number": "serializers.FloatField",
    "decimal": "serializers.DecimalField",
    "boolean": "serializers.BooleanField",
    "date": "serializers.DateField",
    "datetime": "serializers.DateTimeField",
}


@dataclass(frozen=True)
class FieldRenderContext:
    """One serializer field ready for the Jinja2 template."""

    name: str
    description: str
    expression: str
    deferred: bool = False


@dataclass(frozen=True)
class SerializerRenderContext:
    """One Serializer class ready for the Jinja2 template."""

    type_name: str
    class_name: str
    fields: tuple[FieldRenderContext, ...]
    deferred_fields: tuple[FieldRenderContext, ...] = ()


@dataclass(frozen=True)
class SerializersModuleContext:
    """Root context passed to the serializers Jinja2 template."""

    title: str
    source: str
    serializers: tuple[SerializerRenderContext, ...] = field(default_factory=tuple)


def serializer_class_name(type_name: str) -> str:
    return f"{type_name}Serializer"


def build_serializers_context(spec: ApiSpec) -> SerializersModuleContext:
    """Build a template-ready context from an ApiSpec (no rendering)."""
    ordered = _order_types(spec.types)
    emitted: set[str] = set()
    serializers: list[SerializerRenderContext] = []

    for type_def in ordered:
        ser = _build_serializer_context(type_def, emitted=emitted)
        serializers.append(ser)
        emitted.add(type_def.name)

    return SerializersModuleContext(
        title=spec.title,
        source=spec.source,
        serializers=tuple(serializers),
    )


def _build_serializer_context(
    type_def: ApiTypeDefinition,
    *,
    emitted: set[str],
) -> SerializerRenderContext:
    body_fields: list[FieldRenderContext] = []
    deferred_fields: list[FieldRenderContext] = []

    for prop in type_def.properties:
        field_ctx = _build_field_context(prop, owner=type_def.name, emitted=emitted)
        if field_ctx.deferred:
            deferred_fields.append(field_ctx)
        else:
            body_fields.append(field_ctx)

    return SerializerRenderContext(
        type_name=type_def.name,
        class_name=serializer_class_name(type_def.name),
        fields=tuple(body_fields),
        deferred_fields=tuple(deferred_fields),
    )


def _build_field_context(
    prop: TypeProperty,
    *,
    owner: str,
    emitted: set[str],
) -> FieldRenderContext:
    required = not prop.optional
    allow_null = prop.nullable
    base = strip_array_suffix(prop.type)
    many = is_array_type(prop.type)

    if is_primitive_type(base):
        expression = _primitive_expression(
            base,
            many=many,
            required=required,
            allow_null=allow_null,
            prop=prop,
        )
        return FieldRenderContext(
            name=prop.name,
            description=prop.description,
            expression=expression,
            deferred=False,
        )

    # Custom / nested type
    if base == owner or base not in emitted:
        # Recursive or forward reference: patch after class body.
        expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
        return FieldRenderContext(
            name=prop.name,
            description=prop.description,
            expression=expression,
            deferred=True,
        )

    expression = _nested_expression(base, many=many, required=required, allow_null=allow_null)
    return FieldRenderContext(
        name=prop.name,
        description=prop.description,
        expression=expression,
        deferred=False,
    )


def _kwargs(required: bool, allow_null: bool, *, extra: dict[str, str] | None = None) -> str:
    parts = [
        f"required={_bool(required)}",
        f"allow_null={_bool(allow_null)}",
    ]
    if extra:
        for key, value in extra.items():
            parts.append(f"{key}={value}")
    return ", ".join(parts)


def _bool(value: bool) -> str:
    return "True" if value else "False"


def _primitive_expression(
    base: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
    prop: TypeProperty,
) -> str:
    if base not in PRIMITIVE_FIELD_CLASS:
        raise SchemaValidationError(
            f'Unsupported primitive type "{base}".',
            section="types",
            fix="Use string, integer, number, decimal, boolean, date, or datetime.",
        )

    field_cls, extra = _resolve_primitive_field(base, prop=prop, allow_null=allow_null)
    if many:
        child_extra = _resolve_primitive_field(base, prop=prop, allow_null=False)[1]
        # child field itself is always required as list element
        child_cls = field_cls
        child_expr = f"{child_cls}({_kwargs(True, False, extra=child_extra)})"
        return f"serializers.ListField(child={child_expr}, {_kwargs(required, allow_null)})"

    return f"{field_cls}({_kwargs(required, allow_null, extra=extra)})"


def _resolve_primitive_field(
    base: str,
    *,
    prop: TypeProperty,
    allow_null: bool,
) -> tuple[str, dict[str, str] | None]:
    """Return (field class expression, extra kwargs) with digit constraints applied."""
    field_cls = PRIMITIVE_FIELD_CLASS[base]
    extra: dict[str, str] = {}

    if base == "string":
        if allow_null:
            extra["allow_blank"] = "True"
        if prop.max_length is not None:
            extra["max_length"] = str(prop.max_length)
        if prop.max_digits is not None or prop.decimal_places is not None:
            raise SchemaValidationError(
                f'Digit constraints maxDigits/decimalPlaces are invalid for string "{prop.name}".',
                section="types",
                fix="Use maxLength for string fields.",
            )
        return field_cls, extra or None

    if base == "integer":
        if prop.max_length is not None:
            raise SchemaValidationError(
                f'maxLength is invalid for integer "{prop.name}".',
                section="types",
                fix="Use maxDigits for integer fields.",
            )
        if prop.decimal_places is not None:
            raise SchemaValidationError(
                f'decimalPlaces is invalid for integer "{prop.name}".',
                section="types",
                fix="Remove decimalPlaces from integer fields.",
            )
        if prop.max_digits is not None:
            # N桁の整数として扱える上限（例: 3 → 999）
            extra["max_value"] = str(10**prop.max_digits - 1)
        return field_cls, extra or None

    if base == "boolean":
        has_digits = (
            prop.max_length is not None
            or prop.max_digits is not None
            or prop.decimal_places is not None
        )
        if has_digits:
            raise SchemaValidationError(
                f'Digit constraints are invalid for boolean "{prop.name}".',
                section="types",
                fix="Remove maxLength/maxDigits/decimalPlaces from boolean fields.",
            )
        return field_cls, None

    if base in {"number", "decimal"}:
        if prop.max_length is not None:
            raise SchemaValidationError(
                f'maxLength is invalid for {base} "{prop.name}".',
                section="types",
                fix="Use maxDigits / decimalPlaces for numeric fields.",
            )
        # number with digit constraints → DecimalField for precise digit validation
        use_decimal = (
            base == "decimal"
            or prop.max_digits is not None
            or prop.decimal_places is not None
        )
        if use_decimal:
            field_cls = PRIMITIVE_FIELD_CLASS["decimal"]
            max_digits = prop.max_digits if prop.max_digits is not None else 20
            if prop.decimal_places is not None:
                decimal_places = prop.decimal_places
            elif base == "number":
                decimal_places = 0
            else:
                decimal_places = 8
            if decimal_places > max_digits:
                raise SchemaValidationError(
                    f'decimalPlaces ({decimal_places}) cannot exceed maxDigits ({max_digits}) '
                    f'on "{prop.name}".',
                    section="types",
                    fix="Ensure decimalPlaces <= maxDigits.",
                )
            extra["max_digits"] = str(max_digits)
            extra["decimal_places"] = str(decimal_places)
            return field_cls, extra
        return field_cls, None

    return field_cls, extra or None


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


def _order_types(types: list[ApiTypeDefinition]) -> list[ApiTypeDefinition]:
    """Topological order: dependencies first. Cycles keep a stable residual order."""
    by_name = {type_def.name: type_def for type_def in types}
    dependents: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {type_def.name: 0 for type_def in types}

    for type_def in types:
        for dep in _dependencies(type_def, known=by_name):
            # Edge: dep -> type_def (dep must come first)
            if type_def.name not in dependents[dep]:
                dependents[dep].add(type_def.name)
                indegree[type_def.name] += 1

    queue: deque[str] = deque(sorted(name for name, deg in indegree.items() if deg == 0))
    ordered_names: list[str] = []

    while queue:
        name = queue.popleft()
        ordered_names.append(name)
        for nxt in sorted(dependents[name]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    # Remaining nodes are in cycles; append in original relative order.
    remaining = [type_def.name for type_def in types if type_def.name not in set(ordered_names)]
    ordered_names.extend(remaining)
    return [by_name[name] for name in ordered_names]


def _dependencies(type_def: ApiTypeDefinition, *, known: dict[str, ApiTypeDefinition]) -> set[str]:
    deps: set[str] = set()
    for prop in type_def.properties:
        base = strip_array_suffix(prop.type)
        if is_primitive_type(base):
            continue
        if base == type_def.name:
            continue  # self-recursion handled via deferred fields
        if base in known:
            deps.add(base)
    return deps
