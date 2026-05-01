from __future__ import annotations

from pathlib import Path

from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.library import MemoryHubLibrary
from memoryhub.framework.registry import ProjectRegistry
from memoryhub.sources.markdown.serializer import (
    new_markdown_document,
    write_markdown_file,
)
from memoryhub.storage.sqlite.search import SQLiteIndex


def test_sqlite_rebuild_indexes_markdown_documents(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    record = registry.add_project(repo_root, name="demo")
    document_path = record.source_path / "agent" / "memories" / "patterns" / "cache.md"
    write_markdown_file(
        document_path,
        new_markdown_document(
            path=document_path,
            title="Cache Pattern",
            body="Prefer explicit local caches for repeated context lookups.",
            kind="pattern",
            tags=("cache", "context"),
        ),
    )
    index = SQLiteIndex(layout.database_path)

    report = index.rebuild(registry.list_projects())
    results = index.search("cache")

    assert report.project_count == 2
    assert report.document_count == 1
    assert len(results) == 1
    assert results[0].project_name == "demo"
    assert results[0].relative_path == "agent/memories/patterns/cache.md"


def test_sqlite_rebuild_recreates_deleted_database(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    library = MemoryHubLibrary(registry)
    registry.add_project(repo_root, name="demo")
    library.write_document(
        "demo",
        "user/memories/preferences/local.md",
        title="Local Preference",
        body="Keep generated state under the MemoryHub runtime root.",
        tags=("runtime",),
    )
    first_report = library.reindex()
    layout.database_path.unlink()

    second_report = library.reindex()
    results = library.search("runtime")

    assert first_report.document_count == 1
    assert second_report.document_count == 1
    assert results[0].title == "Local Preference"
