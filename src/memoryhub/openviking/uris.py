"""OpenViking-style URI helpers supported by MemoryHub."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

from memoryhub.framework.errors import ProjectSourceError
from memoryhub.framework.registry import validate_project_name
from memoryhub.sources.markdown.sync import safe_relative_markdown_path

URI_SCHEME = "openviking"
URI_AUTHORITY = "project"


@dataclass(frozen=True, slots=True)
class OpenVikingURI:
    project_name: str
    relative_path: Path

    def __str__(self) -> str:
        return build_openviking_uri(self.project_name, self.relative_path)

    def to_json(self) -> dict[str, object]:
        return {
            "uri": str(self),
            "project_name": self.project_name,
            "relative_path": self.relative_path.as_posix(),
        }


def build_openviking_uri(project_name: str, relative_path: str | Path) -> str:
    project = validate_project_name(project_name)
    path = safe_relative_markdown_path(relative_path)
    encoded_parts = "/".join(quote(part) for part in path.parts)
    return f"{URI_SCHEME}://{URI_AUTHORITY}/{project}/{encoded_parts}"


def parse_openviking_uri(uri: str) -> OpenVikingURI:
    parsed = urlparse(uri)
    if parsed.scheme != URI_SCHEME:
        raise ProjectSourceError(f"unsupported URI scheme: {parsed.scheme}")
    if parsed.netloc != URI_AUTHORITY:
        raise ProjectSourceError(f"unsupported URI authority: {parsed.netloc}")
    parts = tuple(part for part in parsed.path.split("/") if part != "")
    if len(parts) < 2:
        raise ProjectSourceError(f"invalid OpenViking URI: {uri}")
    project = validate_project_name(unquote(parts[0]))
    decoded_parts = tuple(unquote(part) for part in parts[1:])
    relative_path = safe_relative_markdown_path(Path(*decoded_parts))
    return OpenVikingURI(project_name=project, relative_path=relative_path)
