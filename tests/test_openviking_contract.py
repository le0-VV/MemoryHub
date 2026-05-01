from __future__ import annotations

from pathlib import Path

import pytest

from memoryhub.framework.errors import ProjectSourceError
from memoryhub.openviking.compatibility import (
    SUPPORTED_CLAIMS,
    UNSUPPORTED_CLAIMS,
    compatibility_report,
)
from memoryhub.openviking.layout import is_supported_context_path
from memoryhub.openviking.resources import resource_from_document
from memoryhub.openviking.uris import build_openviking_uri, parse_openviking_uri
from memoryhub.sources.markdown.serializer import new_markdown_document


def test_openviking_uri_round_trip() -> None:
    uri = build_openviking_uri("demo", "agent/memories/patterns/cache.md")
    parsed = parse_openviking_uri(uri)

    assert uri == "openviking://project/demo/agent/memories/patterns/cache.md"
    assert parsed.project_name == "demo"
    assert parsed.relative_path == Path("agent/memories/patterns/cache.md")
    assert str(parsed) == uri


def test_openviking_uri_rejects_unsupported_forms() -> None:
    with pytest.raises(ProjectSourceError):
        parse_openviking_uri("https://project/demo/note.md")

    with pytest.raises(ProjectSourceError):
        parse_openviking_uri("openviking://workspace/demo/note.md")

    with pytest.raises(ProjectSourceError):
        build_openviking_uri("demo", "../escape.md")

    with pytest.raises(ProjectSourceError):
        parse_openviking_uri("openviking://project/demo/note.txt")


def test_openviking_resource_descriptor_from_markdown_document() -> None:
    document = new_markdown_document(
        path=None,
        title="Cache Pattern",
        body="Use cache context.",
        kind="pattern",
        tags=("cache",),
    )

    resource = resource_from_document(
        project_name="demo",
        relative_path="agent/memories/patterns/cache.md",
        document=document,
    )

    assert resource.uri == "openviking://project/demo/agent/memories/patterns/cache.md"
    assert resource.project_name == "demo"
    assert resource.relative_path == "agent/memories/patterns/cache.md"
    assert resource.title == "Cache Pattern"
    assert resource.kind == "pattern"
    assert resource.tags == ("cache",)


def test_supported_openviking_context_paths_are_explicit() -> None:
    assert is_supported_context_path(Path("agent/memories/patterns/cache.md"))
    assert is_supported_context_path(Path("user/memories/preferences/local.md"))
    assert not is_supported_context_path(Path("random/cache.md"))


def test_compatibility_report_does_not_claim_full_openviking() -> None:
    report = compatibility_report()
    supported_names = {claim.name for claim in SUPPORTED_CLAIMS}
    unsupported_names = {claim.name for claim in UNSUPPORTED_CLAIMS}

    assert report["boundary"] == "OpenViking implementation layer"
    assert "openviking-project-uri" in supported_names
    assert "openviking-cli-compatibility" in unsupported_names
    assert all(claim.supported for claim in SUPPORTED_CLAIMS)
    assert not any(claim.supported for claim in UNSUPPORTED_CLAIMS)
