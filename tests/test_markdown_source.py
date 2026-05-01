from __future__ import annotations

from pathlib import Path

import pytest

from memoryhub.framework.errors import ProjectSourceError
from memoryhub.sources.markdown.parser import parse_markdown
from memoryhub.sources.markdown.serializer import serialize_markdown
from memoryhub.sources.markdown.sync import safe_relative_markdown_path


def test_markdown_frontmatter_round_trip_preserves_unknown_fields() -> None:
    document = parse_markdown(
        "\n".join(
            [
                "---",
                "title: Cache Pattern",
                "kind: pattern",
                "tags: cache, performance",
                "unknown: keep-me",
                "---",
                "# Cache Pattern",
                "Use local caches deliberately.",
                "",
            ]
        )
    )

    serialized = serialize_markdown(document)
    reparsed = parse_markdown(serialized)

    assert reparsed.title == "Cache Pattern"
    assert reparsed.kind == "pattern"
    assert reparsed.tags == ("cache", "performance")
    assert reparsed.frontmatter["unknown"] == "keep-me"
    assert "Use local caches deliberately." in reparsed.body


def test_markdown_title_falls_back_to_heading() -> None:
    document = parse_markdown("# Derived Title\nBody\n", path=Path("note.md"))

    assert document.title == "Derived Title"
    assert document.kind == "memory"


def test_safe_relative_markdown_path_rejects_unsafe_paths() -> None:
    with pytest.raises(ProjectSourceError):
        safe_relative_markdown_path("../escape.md")

    with pytest.raises(ProjectSourceError):
        safe_relative_markdown_path("/tmp/escape.md")

    with pytest.raises(ProjectSourceError):
        safe_relative_markdown_path("note.txt")
