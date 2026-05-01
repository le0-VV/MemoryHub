"""SQLite-backed derived index and search."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import cast

from memoryhub.framework.errors import MemoryHubError
from memoryhub.framework.registry import ProjectListItem
from memoryhub.sources.markdown.parser import read_markdown_file
from memoryhub.sources.markdown.sync import iter_markdown_files
from memoryhub.storage.sqlite.connection import connect_database
from memoryhub.storage.sqlite.migrations import migrate_database
from memoryhub.storage.sqlite.models import ReindexReport, SearchResult


class SQLiteIndex:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    @property
    def database_path(self) -> Path:
        return self._database_path

    def migrate(self) -> None:
        with connect_database(self._database_path) as connection:
            migrate_database(connection)

    def rebuild(self, projects: tuple[ProjectListItem, ...]) -> ReindexReport:
        with connect_database(self._database_path) as connection:
            migrate_database(connection)
            self._clear_index(connection)
            document_count = 0
            for project in projects:
                self._insert_project(connection, project)
                document_count += self._index_project(connection, project)
            connection.commit()
            return ReindexReport(
                project_count=len(projects),
                document_count=document_count,
            )

    def search(
        self,
        query: str,
        *,
        project_name: str | None = None,
        limit: int = 10,
    ) -> tuple[SearchResult, ...]:
        if query.strip() == "":
            raise MemoryHubError("search query cannot be empty")
        if limit < 1 or limit > 100:
            raise MemoryHubError("search limit must be between 1 and 100")

        self.migrate()
        sql = [
            "SELECT f.project_name, f.relative_path, f.title, f.kind,",
            "       substr(f.body, 1, 240) AS snippet,",
            "       bm25(source_files_fts) AS rank",
            "FROM source_files_fts",
            "JOIN source_files f ON f.id = source_files_fts.rowid",
            "WHERE source_files_fts MATCH ?",
        ]
        parameters: list[object] = [query]
        if project_name is not None:
            sql.append("AND f.project_name = ?")
            parameters.append(project_name)
        sql.append("ORDER BY rank ASC LIMIT ?")
        parameters.append(limit)

        with connect_database(self._database_path) as connection:
            cursor = connection.execute(" ".join(sql), parameters)
            return tuple(_search_result_from_row(row) for row in cursor.fetchall())

    def _clear_index(self, connection: sqlite3.Connection) -> None:
        connection.execute("DELETE FROM source_files_fts")
        connection.execute("DELETE FROM source_files")
        connection.execute("DELETE FROM projects")

    def _insert_project(
        self,
        connection: sqlite3.Connection,
        project: ProjectListItem,
    ) -> None:
        record = project.record
        connection.execute(
            """
            INSERT INTO projects (name, source_path, registry_path, kind)
            VALUES (?, ?, ?, ?)
            """,
            (
                record.name,
                str(record.source_path),
                str(record.registry_path),
                record.kind.value,
            ),
        )

    def _index_project(
        self,
        connection: sqlite3.Connection,
        project: ProjectListItem,
    ) -> int:
        count = 0
        source_root = project.record.source_path
        for path in iter_markdown_files(source_root):
            document = read_markdown_file(path)
            relative_path = path.relative_to(source_root).as_posix()
            stat = path.stat()
            frontmatter_json = json.dumps(document.frontmatter, sort_keys=True)
            cursor = connection.execute(
                """
                INSERT INTO source_files (
                    project_name,
                    relative_path,
                    absolute_path,
                    title,
                    kind,
                    body,
                    frontmatter_json,
                    mtime_ns,
                    size
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.record.name,
                    relative_path,
                    str(path),
                    document.title,
                    document.kind,
                    document.body,
                    frontmatter_json,
                    stat.st_mtime_ns,
                    stat.st_size,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise MemoryHubError(f"could not index document: {path}")
            connection.execute(
                """
                INSERT INTO source_files_fts (
                    rowid,
                    project_name,
                    relative_path,
                    title,
                    body,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    project.record.name,
                    relative_path,
                    document.title,
                    document.body,
                    ", ".join(document.tags),
                ),
            )
            count += 1
        return count


def _search_result_from_row(row: object) -> SearchResult:
    values = cast(tuple[object, ...], row)
    return SearchResult(
        project_name=_expect_str(values[0], "project_name"),
        relative_path=_expect_str(values[1], "relative_path"),
        title=_expect_str(values[2], "title"),
        kind=_expect_str(values[3], "kind"),
        snippet=_expect_str(values[4], "snippet"),
        rank=_expect_float(values[5], "rank"),
    )


def _expect_str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise MemoryHubError(f"expected string column: {label}")
    return value


def _expect_float(value: object, label: str) -> float:
    if isinstance(value, int | float):
        return float(value)
    raise MemoryHubError(f"expected numeric column: {label}")
