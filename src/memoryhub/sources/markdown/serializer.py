"""Markdown serializer for MemoryHub source documents."""

from __future__ import annotations

from pathlib import Path

from memoryhub.sources.markdown.schema import MarkdownDocument


def serialize_markdown(document: MarkdownDocument) -> str:
    lines = [("---")]
    for key, value in document.frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(document.body.rstrip("\n"))
    return "\n".join(lines).rstrip() + "\n"


def write_markdown_file(path: Path, document: MarkdownDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_markdown(document), encoding="utf-8")


def new_markdown_document(
    *,
    path: Path | None,
    title: str,
    body: str,
    kind: str = "memory",
    tags: tuple[str, ...] = (),
) -> MarkdownDocument:
    frontmatter = {
        "title": title,
        "kind": kind,
    }
    if tags:
        frontmatter["tags"] = ", ".join(tags)
    return MarkdownDocument(
        path=path,
        title=title,
        kind=kind,
        body=body,
        frontmatter=frontmatter,
    )
