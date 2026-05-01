"""Framework service for source documents and derived index state."""

from __future__ import annotations

from memoryhub.framework.context import ContextBundle, ContextDocument
from memoryhub.framework.registry import ProjectRecord, ProjectRegistry
from memoryhub.sources.markdown.parser import read_markdown_file
from memoryhub.sources.markdown.schema import MarkdownDocument
from memoryhub.sources.markdown.serializer import (
    new_markdown_document,
    write_markdown_file,
)
from memoryhub.sources.markdown.sync import resolve_document_path
from memoryhub.storage.sqlite.models import ReindexReport, SearchFilters, SearchResult
from memoryhub.storage.sqlite.search import SQLiteIndex


class MemoryHubLibrary:
    def __init__(self, registry: ProjectRegistry) -> None:
        self._registry = registry
        self._index = SQLiteIndex(registry.layout.database_path)

    def reindex(self) -> ReindexReport:
        return self._index.rebuild(self._registry.list_projects())

    def search(
        self,
        query: str,
        *,
        project_name: str | None = None,
        kind: str | None = None,
        tag: str | None = None,
        path_prefix: str | None = None,
        limit: int = 10,
    ) -> tuple[SearchResult, ...]:
        return self._index.search(
            query,
            filters=SearchFilters(
                project_name=project_name,
                kind=kind,
                tag=tag,
                path_prefix=path_prefix,
                limit=limit,
            ),
        )

    def build_context(
        self,
        query: str,
        *,
        project_name: str | None = None,
        kind: str | None = None,
        tag: str | None = None,
        path_prefix: str | None = None,
        limit: int = 5,
    ) -> ContextBundle:
        results = self.search(
            query,
            project_name=project_name,
            kind=kind,
            tag=tag,
            path_prefix=path_prefix,
            limit=limit,
        )
        documents: list[ContextDocument] = []
        for result in results:
            document = self.read_document(result.project_name, result.relative_path)
            documents.append(
                ContextDocument(
                    project_name=result.project_name,
                    relative_path=result.relative_path,
                    title=document.title,
                    kind=document.kind,
                    body=document.body,
                    tags=document.tags,
                )
            )
        return ContextBundle(query=query, documents=tuple(documents))

    def read_document(self, project_name: str, relative_path: str) -> MarkdownDocument:
        record = self._registry.get_project(project_name)
        document_path = resolve_document_path(record.source_path, relative_path)
        return read_markdown_file(document_path)

    def write_document(
        self,
        project_name: str,
        relative_path: str,
        *,
        title: str,
        body: str,
        kind: str = "memory",
        tags: tuple[str, ...] = (),
    ) -> MarkdownDocument:
        record = self._registry.get_project(project_name)
        document_path = resolve_document_path(record.source_path, relative_path)
        document = new_markdown_document(
            path=document_path,
            title=title,
            body=body,
            kind=kind,
            tags=tags,
        )
        write_markdown_file(document_path, document)
        return document

    def project(self, name: str) -> ProjectRecord:
        return self._registry.get_project(name)
