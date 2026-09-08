"""Safe file writing with --force and --check support."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.errors import CodegenError
from md_drf_codegen.utils.python_validator import validate_python_syntax


class FileExistsError(CodegenError):
    """Raised when a generated file already exists and --force was not set."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            "FILE_EXISTS_ERROR",
            f"File already exists: {path}",
            fix="Use --force to overwrite.",
        )
        self.path = path


def write_generated_files(
    files: dict[str, str],
    output_dir: str | Path,
    *,
    force: bool = False,
    check: bool = False,
) -> list[Path]:
    """Write or check generated files.

    When *check* is True, compare content without writing and raise on mismatch.
    When a file exists and *force* is False, raise FileExistsError.
    """
    directory = Path(output_dir)
    if check:
        return _check_files(files, directory)

    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, code in files.items():
        path = directory / name
        if path.exists() and not force:
            raise FileExistsError(path.resolve())
        if name.endswith(".py"):
            validate_python_syntax(code, source_name=name)
        path.write_text(code, encoding="utf-8", newline="\n")
        written.append(path.resolve())
    return written


def check_generated_files(files: dict[str, str], output_dir: str | Path) -> list[Path]:
    """Compare generated content with existing files; raise on any difference."""
    return _check_files(files, Path(output_dir))


def _check_files(files: dict[str, str], directory: Path) -> list[Path]:
    mismatches: list[str] = []
    checked: list[Path] = []

    for name, expected in files.items():
        path = directory / name
        checked.append(path.resolve())
        if not path.exists():
            mismatches.append(f"missing: {path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            mismatches.append(f"differs: {path}")

    if mismatches:
        details = "\n".join(mismatches)
        raise CodegenError(
            "CHECK_FAILED",
            f"Generated output does not match existing files:\n{details}",
            fix="Run generate without --check to update files, or use --force.",
        )
    return checked
