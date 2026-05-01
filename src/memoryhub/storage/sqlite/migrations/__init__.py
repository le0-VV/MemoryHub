"""SQLite migrations for MemoryHub."""

from memoryhub.storage.sqlite.migrations.bootstrap import (
    SCHEMA_VERSION,
    migrate_database,
)

__all__ = ["SCHEMA_VERSION", "migrate_database"]
