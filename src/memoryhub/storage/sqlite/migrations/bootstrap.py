"""SQLite migration bootstrap."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def migrate_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
            name TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            registry_path TEXT NOT NULL,
            kind TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_files (
            id INTEGER PRIMARY KEY,
            project_name TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            absolute_path TEXT NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL,
            size INTEGER NOT NULL,
            UNIQUE(project_name, relative_path),
            FOREIGN KEY(project_name) REFERENCES projects(name) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS source_files_fts USING fts5(
            project_name UNINDEXED,
            relative_path UNINDEXED,
            title,
            body,
            tags
        );
        """
    )
    _ensure_column(connection, "source_files", "tags", "TEXT NOT NULL DEFAULT ''")
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    columns = {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )
