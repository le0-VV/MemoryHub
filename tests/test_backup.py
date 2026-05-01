from __future__ import annotations

from pathlib import Path

import pytest

from memoryhub.framework.backup import create_backup, inspect_backup, restore_backup
from memoryhub.framework.errors import BackupError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.library import MemoryHubLibrary
from memoryhub.framework.registry import ProjectRegistry
from memoryhub.sources.markdown.serializer import (
    new_markdown_document,
    write_markdown_file,
)


def test_backup_create_inspect_and_restore_remaps_project_sources(
    tmp_path: Path,
) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    registry.ensure_initialized()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    registry.add_project(repo_root, name="demo", make_default=True)
    write_markdown_file(
        layout.main_project_path / "agent/memories/cases/global.md",
        new_markdown_document(
            path=None,
            title="Global Memory",
            body="Global context survives backup.",
            kind="case",
        ),
    )
    write_markdown_file(
        repo_root / ".agents/memoryhub/agent/memories/patterns/cache.md",
        new_markdown_document(
            path=None,
            title="Cache Pattern",
            body="Repository context survives backup.",
            kind="pattern",
            tags=("cache",),
        ),
    )

    archive_path = tmp_path / "memoryhub.zip"
    create_report = create_backup(registry, archive_path)
    inspect_report = inspect_backup(archive_path)
    restored_layout = RuntimeLayout.from_root(tmp_path / "restored-hub")

    restore_report = restore_backup(archive_path, restored_layout)
    restored_registry = ProjectRegistry(restored_layout)
    restored_demo = restored_registry.get_project("demo")
    reindex_report = MemoryHubLibrary(restored_registry).reindex()

    assert create_report.archive_path == archive_path
    assert inspect_report.manifest.project_count == 2
    assert inspect_report.manifest.file_count == 2
    assert restore_report.project_count == 2
    assert restore_report.file_count == 2
    assert restored_registry.get_default().name == "demo"
    assert restored_demo.registry_path.is_symlink()
    assert restored_demo.source_path == (
        restored_layout.runtime_dir / "restored-projects" / "demo"
    )
    assert (
        restored_layout.main_project_path / "agent/memories/cases/global.md"
    ).is_file()
    assert "Repository context survives backup." in (
        restored_demo.source_path / "agent/memories/patterns/cache.md"
    ).read_text(encoding="utf-8")
    assert reindex_report.document_count == 2


def test_restore_rejects_non_empty_target_runtime(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    registry.ensure_initialized()
    archive_path = tmp_path / "memoryhub.zip"
    create_backup(registry, archive_path)
    target_root = tmp_path / "target"
    target_root.mkdir()
    (target_root / "keep.txt").write_text("do not clobber\n", encoding="utf-8")

    with pytest.raises(BackupError):
        restore_backup(archive_path, RuntimeLayout.from_root(target_root))
