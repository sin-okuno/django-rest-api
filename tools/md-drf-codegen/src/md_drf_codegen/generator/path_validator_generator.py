"""Context builder for generated path-parameter validators."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from md_drf_codegen.schema import ApiSpec, PathParameterDefinition
from md_drf_codegen.utils.naming import camel_to_snake, path_validators_module_name


@dataclass(frozen=True)
class PathValidatorContext:
    function_name: str
    snake_name: str
    camel_name: str
    body_lines: tuple[str, ...]
    pattern_const: str | None = None
    pattern_regex: str | None = None


@dataclass(frozen=True)
class PathValidatorsModuleContext:
    validators: tuple[PathValidatorContext, ...] = field(default_factory=tuple)
    needs_re: bool = False
    module_name: str = "path_validators"


def build_path_validators_context(
    spec: ApiSpec,
    *,
    module_prefix: str,
) -> PathValidatorsModuleContext:
    validators: list[PathValidatorContext] = []
    needs_re = False

    for camel_name in sorted(spec.path_parameters):
        param_def = spec.path_parameters[camel_name]
        snake_name = camel_to_snake(camel_name)
        function_name = f"validate_{snake_name}"
        body_lines, pattern_const, pattern_regex, uses_re = _build_validator_body(
            snake_name,
            param_def,
        )
        needs_re = needs_re or uses_re
        validators.append(
            PathValidatorContext(
                function_name=function_name,
                snake_name=snake_name,
                camel_name=camel_name,
                body_lines=tuple(body_lines),
                pattern_const=pattern_const,
                pattern_regex=pattern_regex,
            )
        )

    return PathValidatorsModuleContext(
        validators=tuple(validators),
        needs_re=needs_re,
        module_name=path_validators_module_name(module_prefix),
    )


def build_valid_path_param_value(param_def: PathParameterDefinition) -> str:
    """Build a deterministic path segment value that satisfies constraints."""
    value = "a1b2c3"
    constraints = param_def.constraints
    if constraints is None or constraints.is_empty():
        return value

    resolved = constraints.resolved_pattern()
    if resolved is not None:
        regex = resolved[0]
        if not re.fullmatch(regex, value):
            value = "a1"

    if constraints.max_length is not None:
        value = value[: constraints.max_length]

    if constraints.min_length is not None and len(value) < constraints.min_length:
        value = value.ljust(constraints.min_length, "a")

    if resolved is not None and not re.fullmatch(resolved[0], value):
        value = "a" * max(constraints.min_length or 1, 1)
        if constraints.max_length is not None:
            value = value[: constraints.max_length]

    return value


def build_invalid_path_param_value(param_def: PathParameterDefinition) -> str:
    """Build a path segment value that should fail format validation."""
    constraints = param_def.constraints
    if constraints is None or constraints.is_empty():
        return "invalid value!"

    if constraints.max_length is not None:
        return "a" * (constraints.max_length + 1)

    resolved = constraints.resolved_pattern()
    if resolved is not None:
        return "!!!invalid!!!"

    if constraints.min_length is not None and constraints.min_length > 1:
        return "a"

    return "invalid value!"


def _build_validator_body(
    snake_name: str,
    param_def: PathParameterDefinition,
) -> tuple[list[str], str | None, str | None, bool]:
    lines: list[str] = ["    errors: list[str] = []"]
    pattern_const: str | None = None
    pattern_regex: str | None = None
    uses_re = False
    constraints = param_def.constraints
    custom_messages = param_def.error_messages or {}

    if constraints is None or constraints.is_empty():
        lines.append("    return value")
        return lines, pattern_const, pattern_regex, uses_re

    if constraints.min_length is not None:
        min_message = custom_messages.get(
            "min_length",
            f"{constraints.min_length}文字以上で入力してください。",
        )
        lines.append(
            f"    if len(value) < {constraints.min_length}:\n"
            f"        errors.append({min_message!r})"
        )

    if constraints.max_length is not None:
        max_message = custom_messages.get(
            "max_length",
            f"{constraints.max_length}文字以内で入力してください。",
        )
        lines.append(
            f"    if len(value) > {constraints.max_length}:\n"
            f"        errors.append({max_message!r})"
        )

    resolved = constraints.resolved_pattern()
    if resolved is not None:
        uses_re = True
        pattern_const = f"_{snake_name.upper()}_PATTERN"
        pattern_regex = resolved[0]
        message = custom_messages.get("pattern", resolved[1])
        lines.append(
            f"    if not {pattern_const}.fullmatch(value):\n"
            f'        errors.append({message!r})'
        )

    lines.append("    if errors:")
    lines.append(f'        raise ValidationError({{"{snake_name}": errors}})')
    lines.append("    return value")
    return lines, pattern_const, pattern_regex, uses_re


def path_param_has_validation(param_def: PathParameterDefinition) -> bool:
    constraints = param_def.constraints
    return constraints is not None and not constraints.is_empty()
