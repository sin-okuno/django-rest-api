"""Typed errors raised by the parser and validators."""

from __future__ import annotations


class CodegenError(Exception):
    """Base error with a machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        section: str | None = None,
        line: int | None = None,
        fix: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.section = section
        self.line = line
        self.fix = fix
        super().__init__(self.format())

    def format(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.section:
            parts.append(f"section={self.section}")
        if self.line is not None:
            parts.append(f"line={self.line}")
        if self.fix:
            parts.append(f"fix: {self.fix}")
        return " | ".join(parts)


class MarkdownParseError(CodegenError):
    pass


class MissingSectionError(CodegenError):
    def __init__(self, missing: list[str], *, source_path: str) -> None:
        joined = ", ".join(missing)
        super().__init__(
            "MISSING_SECTION_ERROR",
            f"Required section(s) missing: {joined}",
            section=missing[0] if missing else None,
            fix=f"Add the following level-2 heading(s) to {source_path}: "
            + ", ".join(f"## {h}" for h in missing),
        )


class MissingColumnError(CodegenError):
    def __init__(
        self,
        section: str,
        required_headers: list[str],
        *,
        found: list[str] | None = None,
        line: int | None = None,
    ) -> None:
        found_text = ", ".join(found) if found else "(none)"
        super().__init__(
            "MISSING_COLUMN_ERROR",
            f'Section "{section}" is missing a table with columns: ' + ", ".join(required_headers),
            section=section,
            line=line,
            fix=(
                f"Add a table containing columns [{', '.join(required_headers)}]. "
                f"Found headers: {found_text}"
            ),
        )


class SchemaValidationError(CodegenError):
    def __init__(
        self,
        message: str,
        *,
        section: str | None = None,
        line: int | None = None,
        fix: str | None = None,
    ) -> None:
        super().__init__(
            "SCHEMA_VALIDATION_ERROR",
            message,
            section=section,
            line=line,
            fix=fix,
        )


class TypeReferenceError(CodegenError):
    def __init__(self, type_name: str, *, context: str) -> None:
        super().__init__(
            "TYPE_REFERENCE_ERROR",
            f'Type "{type_name}" is referenced but not defined in api types',
            fix=f'Add an api-category type named "{type_name}" to 型定義 ({context}).',
        )
