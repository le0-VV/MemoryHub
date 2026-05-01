"""OpenViking-style project context source layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

from memoryhub.framework.errors import ProjectSourceError
from memoryhub.framework.layout import RuntimeLayout

PROJECT_CONTEXT_RELATIVE_PATH: Final = Path(".agents") / "memoryhub"

SOURCE_DIRECTORIES: Final[tuple[Path, ...]] = (
    Path("agent"),
    Path("agent") / "memories",
    Path("agent") / "memories" / "cases",
    Path("agent") / "memories" / "patterns",
    Path("agent") / "memories" / "skills",
    Path("agent") / "memories" / "tools",
    Path("agent") / "skills",
    Path("resources"),
    Path("user"),
    Path("user") / "memories",
    Path("user") / "memories" / "entities",
    Path("user") / "memories" / "events",
    Path("user") / "memories" / "preferences",
)


@dataclass(frozen=True, slots=True)
class ProjectSourceLayout:
    """Repository-owned or global Markdown context source tree."""

    root: Path

    @classmethod
    def for_repo(cls, repo_root: str | Path) -> Self:
        return cls(Path(repo_root).expanduser() / PROJECT_CONTEXT_RELATIVE_PATH)

    @classmethod
    def for_global(cls, runtime_layout: RuntimeLayout) -> Self:
        return cls(runtime_layout.main_project_path)

    def ensure(self) -> None:
        ensure_source_directory(self.root)
        for relative_path in SOURCE_DIRECTORIES:
            ensure_source_directory(self.root / relative_path)

    def validate(self) -> None:
        validate_source_directory(self.root)
        for relative_path in SOURCE_DIRECTORIES:
            validate_source_directory(self.root / relative_path)


def ensure_source_directory(path: Path) -> None:
    if path.exists() and not path.is_dir():
        raise ProjectSourceError(f"expected context directory but found file: {path}")
    path.mkdir(parents=True, exist_ok=True)


def validate_source_directory(path: Path) -> None:
    if not path.is_dir():
        raise ProjectSourceError(f"missing context directory: {path}")
