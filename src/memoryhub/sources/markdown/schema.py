"""Markdown source schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    path: Path | None
    title: str
    kind: str
    body: str
    frontmatter: dict[str, str]

    @property
    def tags(self) -> tuple[str, ...]:
        raw_tags = self.frontmatter.get("tags")
        if raw_tags is None or raw_tags.strip() == "":
            return ()
        return tuple(tag.strip() for tag in raw_tags.split(",") if tag.strip() != "")

    def to_json(self) -> dict[str, object]:
        return {
            "path": None if self.path is None else str(self.path),
            "title": self.title,
            "kind": self.kind,
            "body": self.body,
            "frontmatter": dict(self.frontmatter),
            "tags": list(self.tags),
        }
