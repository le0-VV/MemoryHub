"""SQLite storage data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchFilters:
    project_name: str | None = None
    kind: str | None = None
    tag: str | None = None
    path_prefix: str | None = None
    limit: int = 10

    def to_json(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "kind": self.kind,
            "tag": self.tag,
            "path_prefix": self.path_prefix,
            "limit": self.limit,
        }


@dataclass(frozen=True, slots=True)
class ReindexReport:
    project_count: int
    document_count: int

    def to_json(self) -> dict[str, object]:
        return {
            "project_count": self.project_count,
            "document_count": self.document_count,
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    project_name: str
    relative_path: str
    title: str
    kind: str
    snippet: str
    rank: float
    tags: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "relative_path": self.relative_path,
            "title": self.title,
            "kind": self.kind,
            "snippet": self.snippet,
            "rank": self.rank,
            "tags": list(self.tags),
        }
