"""Context assembly models."""

from __future__ import annotations

from dataclasses import dataclass

from memoryhub.openviking.resources import resource_descriptor


@dataclass(frozen=True, slots=True)
class ContextDocument:
    project_name: str
    relative_path: str
    title: str
    kind: str
    body: str
    tags: tuple[str, ...]

    @property
    def uri(self) -> str:
        return resource_descriptor(
            project_name=self.project_name,
            relative_path=self.relative_path,
            title=self.title,
            kind=self.kind,
            tags=self.tags,
        ).uri

    def to_markdown(self) -> str:
        tags = ", ".join(self.tags)
        metadata = [
            f"- project: {self.project_name}",
            f"- path: {self.relative_path}",
            f"- uri: {self.uri}",
            f"- kind: {self.kind}",
        ]
        if tags:
            metadata.append(f"- tags: {tags}")
        return "\n".join(
            [
                f"## {self.title}",
                *metadata,
                "",
                self.body.strip(),
            ]
        ).strip()

    def to_json(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "relative_path": self.relative_path,
            "uri": self.uri,
            "title": self.title,
            "kind": self.kind,
            "body": self.body,
            "tags": list(self.tags),
            "resource": resource_descriptor(
                project_name=self.project_name,
                relative_path=self.relative_path,
                title=self.title,
                kind=self.kind,
                tags=self.tags,
            ).to_json(),
        }


@dataclass(frozen=True, slots=True)
class ContextBundle:
    query: str
    documents: tuple[ContextDocument, ...]

    def to_markdown(self) -> str:
        sections = [f"# MemoryHub Context\n\nQuery: {self.query.strip()}"]
        sections.extend(document.to_markdown() for document in self.documents)
        return "\n\n".join(sections).strip() + "\n"

    def to_json(self) -> dict[str, object]:
        return {
            "query": self.query,
            "document_count": len(self.documents),
            "documents": [document.to_json() for document in self.documents],
            "markdown": self.to_markdown(),
        }
