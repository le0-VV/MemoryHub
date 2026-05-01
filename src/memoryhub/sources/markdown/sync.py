"""Markdown source tree scanning and safe path helpers."""

from __future__ import annotations

from pathlib import Path

from memoryhub.framework.errors import ProjectSourceError


def iter_markdown_files(source_root: Path) -> tuple[Path, ...]:
    if not source_root.is_dir():
        raise ProjectSourceError(f"source root is not a directory: {source_root}")
    return tuple(sorted(path for path in source_root.rglob("*.md") if path.is_file()))


def safe_relative_markdown_path(relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ProjectSourceError(f"document path must be relative: {relative_path}")
    if ".." in path.parts:
        raise ProjectSourceError(f"document path cannot contain '..': {relative_path}")
    if path.suffix != ".md":
        raise ProjectSourceError(f"document path must end with .md: {relative_path}")
    if str(path).strip() == "":
        raise ProjectSourceError("document path cannot be empty")
    return path


def resolve_document_path(source_root: Path, relative_path: str | Path) -> Path:
    safe_path = safe_relative_markdown_path(relative_path)
    return source_root / safe_path
