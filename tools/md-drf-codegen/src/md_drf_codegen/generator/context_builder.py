"""Context models and builder for DRF serializer generation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from md_drf_codegen.errors import SchemaValidationError
from md_drf_codegen.normalize import is_array_type, is_primitive_type, strip_array_suffix
from md_drf_codegen.schema import ApiSpec, FieldDefinition, TypeDefinition
from md_drf_codegen.schema.constraints import EnumMember, FieldConstraints
from md_drf_codegen.utils.naming import (
    enum_class_name_from_field,
    enum_member_name,
    serializer_class_name,
)

PRIMITIVE_FIELD_CLASS: dict[str, str] = {
    "string": "serializers.CharField",
    "integer": "serializers.IntegerField",
    "number": "serializers.FloatField",
    "boolean": "serializers.BooleanField",
    "date": "serializers.DateField",
    "datetime": "serializers.DateTimeField",
    "object": "serializers.JSONField",
}

EnumFingerprint = tuple[tuple[str | int | float, str | None], ...]


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
class EnumMemberRenderContext:
    name: str
    value_repr: str
    label_repr: str


@dataclass(frozen=True)
class EnumDefinitionContext:
    class_name: str
    base_class: str
    members: tuple[EnumMemberRenderContext, ...]


@dataclass(frozen=True)
class EnumImportContext:
    module: str
    class_name: str


@dataclass(frozen=True)
class SerializersModuleContext:
    source: str = ""
    serializers: tuple[SerializerRenderContext, ...] = field(default_factory=tuple)
    enum_definitions: tuple[EnumDefinitionContext, ...] = field(default_factory=tuple)
    enum_imports: tuple[EnumImportContext, ...] = field(default_factory=tuple)
    needs_regex_validator: bool = False
    needs_enum: bool = False


def build_serializers_context(spec: ApiSpec) -> SerializersModuleContext:
    enum_definitions, enum_imports, enum_class_by_field = _collect_enum_definitions(spec)
    ordered = _order_types(spec.types)
    emitted: set[str] = set()
    serializers: list[SerializerRenderContext] = []
    needs_regex = False

    for type_name in ordered:
        type_def = spec.types[type_name]
        ser, uses_regex = _build_serializer_context(
            type_name,
            type_def,
            emitted=emitted,
            known=spec.types,
            enum_class_by_field=enum_class_by_field,
        )
        serializers.append(ser)
        emitted.add(type_name)
        needs_regex = needs_regex or uses_regex

    return SerializersModuleContext(
        serializers=tuple(serializers),
        enum_definitions=enum_definitions,
        enum_imports=enum_imports,
        needs_regex_validator=needs_regex,
        needs_enum=bool(enum_definitions),
    )


def _collect_enum_definitions(
    spec: ApiSpec,
) -> tuple[
    tuple[EnumDefinitionContext, ...],
    tuple[EnumImportContext, ...],
    dict[tuple[str, str], str],
]:
    """Resolve enum class names for each field.

    - If ``ref:ClassName`` or field-derived name matches ``定数定義一覧``,
      import the existing class and do not generate a local Enum class.
    - Otherwise generate a local ``enum.Enum`` class.
    """
    constants_by_class = {item.class_name: item for item in spec.constants}
    groups: dict[EnumFingerprint, dict[str, object]] = {}
    field_infos: list[tuple[str, str, EnumFingerprint | None, str, str]] = []

    for type_name, type_def in spec.types.items():
        for field_name, field_def in type_def.fields.items():
            constraints = field_def.constraints
            if constraints is None:
                continue
            has_enum = bool(constraints.enum)
            has_ref = bool(constraints.enum_ref)
            if not has_enum and not has_ref:
                continue

            base = strip_array_suffix(field_def.type)
            preferred_name = constraints.enum_ref or enum_class_name_from_field(field_name)
            fingerprint: EnumFingerprint | None = None
            if constraints.enum:
                fingerprint = tuple((m.value, m.label) for m in constraints.enum)
                group = groups.setdefault(
                    fingerprint,
                    {
                        "members": constraints.enum,
                        "base": base,
                        "field_names": [],
                        "preferred_names": [],
                    },
                )
                field_names = group["field_names"]
                preferred_names = group["preferred_names"]
                assert isinstance(field_names, list)
                assert isinstance(preferred_names, list)
                field_names.append(field_name)
                preferred_names.append(preferred_name)

            field_infos.append((type_name, field_name, fingerprint, base, preferred_name))

    used_class_names: set[str] = set()
    fingerprint_to_class: dict[EnumFingerprint, str] = {}
    local_definitions: list[EnumDefinitionContext] = []
    imports_by_class: dict[str, EnumImportContext] = {}
    enum_class_by_field: dict[tuple[str, str], str] = {}

    # First pass: resolve external refs for fields with enum values (shared groups).
    for fingerprint, group in sorted(
        ((fp, g) for fp, g in groups.items()),
        key=lambda item: item[0],
    ):
        members = group["members"]
        assert isinstance(members, list)
        base = str(group["base"])
        preferred_names = group["preferred_names"]
        assert isinstance(preferred_names, list)
        preferred = sorted(set(preferred_names))[0]

        external = constants_by_class.get(preferred)
        if external is not None:
            fingerprint_to_class[fingerprint] = external.class_name
            imports_by_class[external.class_name] = EnumImportContext(
                module=external.import_module(),
                class_name=external.class_name,
            )
            continue

        class_name = _unique_enum_class_name(preferred, used_class_names)
        used_class_names.add(class_name)
        fingerprint_to_class[fingerprint] = class_name
        local_definitions.append(
            _build_enum_definition(class_name, base, members)  # type: ignore[arg-type]
        )

    for type_name, field_name, fingerprint, _base, preferred_name in field_infos:
        if fingerprint is not None:
            enum_class_by_field[(type_name, field_name)] = fingerprint_to_class[fingerprint]
            continue

        # ref-only field (values documented elsewhere / OpenAPI may omit enum list)
        external = constants_by_class.get(preferred_name)
        if external is None:
            raise SchemaValidationError(
                f'Enum ref "{preferred_name}" on {type_name}.{field_name} '
                "is not listed in 定数定義一覧.",
                section="定数定義一覧",
                fix="Add the class to ## 定数定義一覧 or provide enum:value:label members.",
            )
        enum_class_by_field[(type_name, field_name)] = external.class_name
        imports_by_class[external.class_name] = EnumImportContext(
            module=external.import_module(),
            class_name=external.class_name,
        )

    imports = tuple(sorted(imports_by_class.values(), key=lambda item: item.class_name))
    return tuple(local_definitions), imports, enum_class_by_field


def _unique_enum_class_name(field_or_class_name: str, used: set[str]) -> str:
    base = (
        field_or_class_name
        if field_or_class_name[:1].isupper()
        else enum_class_name_from_field(field_or_class_name)
    ) or "Enum"
    if base not in used:
        return base
    index = 2
    while f"{base}{index}" in used:
        index += 1
    return f"{base}{index}"


def _build_enum_definition(
    class_name: str,
    base_type: str,
    members: list[EnumMember],
) -> EnumDefinitionContext:
    del base_type  # Values may be int or str; both use stdlib Enum.
    rendered: list[EnumMemberRenderContext] = []
    used_names: set[str] = set()
    for member in members:
        name = enum_member_name(member.value, member.label)
        if name in used_names:
            suffix = 2
            while f"{name}_{suffix}" in used_names:
                suffix += 1
            name = f"{name}_{suffix}"
        used_names.add(name)
        rendered.append(
            EnumMemberRenderContext(
                name=name,
                value_repr=repr(member.value),
                label_repr=repr(member.label if member.label is not None else str(member.value)),
            )
        )
    return EnumDefinitionContext(
        class_name=class_name,
        base_class="Enum",
        members=tuple(rendered),
    )


def _build_serializer_context(
    type_name: str,
    type_def: TypeDefinition,
    *,
    emitted: set[str],
    known: dict[str, TypeDefinition],
    enum_class_by_field: dict[tuple[str, str], str],
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
            enum_class_name=enum_class_by_field.get((type_name, field_name)),
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
    enum_class_name: str | None,
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
            error_messages=field_def.error_messages,
            enum_class_name=enum_class_name,
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


def _error_messages_part(error_messages: dict[str, str] | None) -> list[str]:
    if not error_messages:
        return []
    items = ", ".join(f"{repr(key)}: {repr(value)}" for key, value in error_messages.items())
    return [f"error_messages={{{items}}}"]


def _constraint_parts(
    base: str,
    constraints: FieldConstraints | None,
    *,
    error_messages: dict[str, str] | None = None,
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
            regex, default_message = resolved
            message = (error_messages or {}).get("pattern", default_message)
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
    error_messages: dict[str, str] | None = None,
    enum_class_name: str | None = None,
) -> tuple[str, bool]:
    if base not in PRIMITIVE_FIELD_CLASS:
        raise SchemaValidationError(
            f'Unsupported primitive type "{base}".',
            section="types",
            fix="Use string, integer, number, boolean, date, datetime, or object.",
        )

    filtered_messages = _serializer_error_messages_for_field(error_messages)

    if constraints is not None and (constraints.enum or constraints.enum_ref):
        if not enum_class_name:
            raise SchemaValidationError(
                "Enum field is missing a generated choices class name.",
                section="types",
                fix="Ensure enum constraints are collected before serializer generation.",
            )
        return _choice_expression(
            enum_class_name,
            many=many,
            required=required,
            allow_null=allow_null,
            error_messages=filtered_messages,
        ), False

    field_cls = PRIMITIVE_FIELD_CLASS[base]
    constraint_parts, uses_regex = _constraint_parts(
        base,
        constraints,
        error_messages=filtered_messages,
    )
    base_kwargs = (
        _kwargs_parts(required, allow_null)
        + constraint_parts
        + _error_messages_part(filtered_messages)
    )
    kwargs = ", ".join(base_kwargs)

    if many:
        child_kwargs = ", ".join(
            _kwargs_parts(True, False)
            + constraint_parts
            + _error_messages_part(filtered_messages)
        )
        child_expr = f"{field_cls}({child_kwargs})"
        list_kwargs = ", ".join(_kwargs_parts(required, allow_null))
        return f"serializers.ListField(child={child_expr}, {list_kwargs})", uses_regex

    return f"{field_cls}({kwargs})", uses_regex


def _choice_expression(
    enum_class_name: str,
    *,
    many: bool,
    required: bool,
    allow_null: bool,
    error_messages: dict[str, str] | None,
) -> str:
    choice_messages = None
    if error_messages:
        choice_messages = dict(error_messages)
        if "invalid" in choice_messages and "invalid_choice" not in choice_messages:
            choice_messages["invalid_choice"] = choice_messages.pop("invalid")

    # Compatible with stdlib Enum (and Django Choices, which subclass Enum).
    choices_expr = f"[(m.value, m.name) for m in {enum_class_name}]"
    parts = [f"choices={choices_expr}"] + _kwargs_parts(required, allow_null)
    parts.extend(_error_messages_part(choice_messages))
    kwargs = ", ".join(parts)
    field_expr = f"serializers.ChoiceField({kwargs})"
    if many:
        list_kwargs = ", ".join(_kwargs_parts(required, allow_null))
        return f"serializers.ListField(child={field_expr}, {list_kwargs})"
    return field_expr


def _serializer_error_messages_for_field(
    error_messages: dict[str, str] | None,
) -> dict[str, str] | None:
    if not error_messages:
        return None
    filtered = {key: value for key, value in error_messages.items() if key != "pattern"}
    return filtered or None


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
