"""OpenViking-style resource descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from memoryhub.framework.registry import validate_project_name
from memoryhub.openviking.uris import build_openviking_uri
from memoryhub.sources.markdown.schema import MarkdownDocument
from memoryhub.sources.markdown.sync import safe_relative_markdown_path


@dataclass(frozen=True, slots=True)
class OpenVikingResource:
    uri: str
    project_name: str
    relative_path: str
    title: str
    kind: str
    tags: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "uri": self.uri,
            "project_name": self.project_name,
            "relative_path": self.relative_path,
            "title": self.title,
            "kind": self.kind,
            "tags": list(self.tags),
        }


def resource_from_document(
    *,
    project_name: str,
    relative_path: str | Path,
    document: MarkdownDocument,
) -> OpenVikingResource:
    project = validate_project_name(project_name)
    path = safe_relative_markdown_path(relative_path)
    path_text = path.as_posix()
    return OpenVikingResource(
        uri=build_openviking_uri(project, path),
        project_name=project,
        relative_path=path_text,
        title=document.title,
        kind=document.kind,
        tags=document.tags,
    )
