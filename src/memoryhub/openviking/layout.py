"""OpenViking-style layout declarations supported by MemoryHub."""

from __future__ import annotations

from pathlib import Path
from typing import Final

CONTEXT_ROOT: Final = Path(".agents") / "memoryhub"

AGENT_MEMORY_DIRS: Final[tuple[Path, ...]] = (
    Path("agent") / "memories" / "cases",
    Path("agent") / "memories" / "patterns",
    Path("agent") / "memories" / "skills",
    Path("agent") / "memories" / "tools",
)

USER_MEMORY_DIRS: Final[tuple[Path, ...]] = (
    Path("user") / "memories" / "entities",
    Path("user") / "memories" / "events",
    Path("user") / "memories" / "preferences",
)

RESOURCE_DIRS: Final[tuple[Path, ...]] = (Path("resources"),)

SUPPORTED_CONTEXT_DIRS: Final[tuple[Path, ...]] = (
    *AGENT_MEMORY_DIRS,
    Path("agent") / "skills",
    *RESOURCE_DIRS,
    *USER_MEMORY_DIRS,
)


def is_supported_context_path(relative_path: Path) -> bool:
    return any(
        _is_relative_to(relative_path, directory)
        for directory in SUPPORTED_CONTEXT_DIRS
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
