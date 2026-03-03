"""Tests for local Alembic migration helpers."""

import runpy
from pathlib import Path

import pytest

from memoryhub.alembic.migrations import create_migration_connectable, get_alembic_config


def test_create_migration_connectable_rejects_non_sqlite_urls():
    """Migration bootstrap should fail fast on unsupported backends."""
    with pytest.raises(ValueError, match="SQLite URLs only"):
        create_migration_connectable("postgresql+asyncpg://user:pass@host/db")


@pytest.mark.asyncio
async def test_create_migration_connectable_accepts_sqlite_aiosqlite_url():
    """Supported migration bootstrap should use the async SQLite engine."""
    engine = create_migration_connectable("sqlite+aiosqlite://")
    try:
        assert engine.dialect.name == "sqlite"
    finally:
        await engine.dispose()


def test_migration_revision_graph_has_no_missing_parents():
    """Every Alembic migration should point at an existing parent revision."""
    versions_dir = Path(get_alembic_config().get_main_option("script_location")) / "versions"
    revision_map: dict[str, str | tuple[str, ...] | None] = {}

    for migration_file in sorted(versions_dir.glob("*.py")):
        if migration_file.name == "__init__.py":
            continue
        migration_globals = runpy.run_path(str(migration_file))
        revision_map[migration_globals["revision"]] = migration_globals["down_revision"]

    known_revisions = set(revision_map)
    missing_parents: list[tuple[str, str]] = []

    for revision, down_revision in revision_map.items():
        if down_revision is None:
            continue
        parents = (down_revision,) if isinstance(down_revision, str) else down_revision
        for parent in parents:
            if parent not in known_revisions:
                missing_parents.append((revision, parent))

    assert missing_parents == []
