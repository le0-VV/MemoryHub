"""Documented OpenViking-style compatibility contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompatibilityClaim:
    name: str
    supported: bool
    details: str

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "supported": self.supported,
            "details": self.details,
        }


SUPPORTED_CLAIMS: tuple[CompatibilityClaim, ...] = (
    CompatibilityClaim(
        name="repo-local-context-root",
        supported=True,
        details="Project context lives under .agents/memoryhub/ in each repository.",
    ),
    CompatibilityClaim(
        name="central-project-registry",
        supported=True,
        details="The hub references projects under $MEMORYHUB_CONFIG_DIR/projects/.",
    ),
    CompatibilityClaim(
        name="markdown-source-of-truth",
        supported=True,
        details="Markdown files are authoritative; SQLite state is rebuildable.",
    ),
    CompatibilityClaim(
        name="openviking-project-uri",
        supported=True,
        details="MemoryHub supports openviking://project/<project>/<relative.md> URIs.",
    ),
)

UNSUPPORTED_CLAIMS: tuple[CompatibilityClaim, ...] = (
    CompatibilityClaim(
        name="openviking-cli-compatibility",
        supported=False,
        details="MemoryHub does not claim drop-in OpenViking CLI compatibility.",
    ),
    CompatibilityClaim(
        name="openviking-package-compatibility",
        supported=False,
        details="MemoryHub does not expose an OpenViking Python package API.",
    ),
    CompatibilityClaim(
        name="openviking-import-export",
        supported=False,
        details="OpenViking import/export compatibility is not implemented.",
    ),
    CompatibilityClaim(
        name="openviking-server-compatibility",
        supported=False,
        details="Only MemoryHub's local MCP stdio adapter is supported.",
    ),
)


def compatibility_report() -> dict[str, object]:
    return {
        "boundary": "OpenViking implementation layer",
        "supported": [claim.to_json() for claim in SUPPORTED_CLAIMS],
        "unsupported": [claim.to_json() for claim in UNSUPPORTED_CLAIMS],
    }
