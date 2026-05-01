"""Markdown parser for MemoryHub source documents."""

from __future__ import annotations

from pathlib import Path

from memoryhub.framework.errors import ProjectSourceError
from memoryhub.sources.markdown.schema import MarkdownDocument

FRONTMATTER_BOUNDARY = "---"


def read_markdown_file(path: Path) -> MarkdownDocument:
    return parse_markdown(path.read_text(encoding="utf-8"), path=path)


def parse_markdown(text: str, *, path: Path | None = None) -> MarkdownDocument:
    frontmatter, body = _split_frontmatter(text)
    title = frontmatter.get("title") or _title_from_body(body) or _title_from_path(path)
    kind = frontmatter.get("kind", "memory")
    return MarkdownDocument(
        path=path,
        title=title,
        kind=kind,
        body=body,
        frontmatter=frontmatter,
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0] != FRONTMATTER_BOUNDARY:
        return {}, text

    closing_index = _closing_frontmatter_index(lines)
    frontmatter_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1 :]
    if body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    body = "\n".join(body_lines)
    return _parse_frontmatter_lines(frontmatter_lines), body


def _closing_frontmatter_index(lines: list[str]) -> int:
    for index, line in enumerate(lines[1:], start=1):
        if line == FRONTMATTER_BOUNDARY:
            return index
    raise ProjectSourceError("frontmatter is missing closing boundary")


def _parse_frontmatter_lines(lines: list[str]) -> dict[str, str]:
    frontmatter: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator == "":
            raise ProjectSourceError(f"invalid frontmatter line: {line}")
        normalized_key = key.strip()
        if normalized_key == "":
            raise ProjectSourceError(f"invalid frontmatter key: {line}")
        frontmatter[normalized_key] = value.strip()
    return frontmatter


def _title_from_body(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None


def _title_from_path(path: Path | None) -> str:
    if path is None:
        return "Untitled"
    return path.stem.replace("-", " ").replace("_", " ").strip().title()
