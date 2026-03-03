"""Tests for local Alembic migration helpers."""

import pytest

from memoryhub.alembic.migrations import create_migration_connectable


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
