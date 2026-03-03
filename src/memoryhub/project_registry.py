"""Configured project registry for canonical lookup and cwd matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from memoryhub.config import ConfigManager, ProjectConfig
from memoryhub.utils import generate_permalink


@dataclass(frozen=True)
class ProjectRegistryEntry:
    """Canonical configured project entry."""

    name: str
    permalink: str
    path: Path

    def to_project_config(self) -> ProjectConfig:
        """Return the legacy config wrapper used by existing callers."""
        return ProjectConfig(name=self.name, home=self.path)


class ProjectRegistry:
    """Registry backed by config for canonical project lookup and cwd matching."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self._entries: Optional[tuple[ProjectRegistryEntry, ...]] = None

    @classmethod
    def from_config(cls, config_manager: Optional[ConfigManager] = None) -> "ProjectRegistry":
        """Create a registry backed by the current config."""
        return cls(config_manager=config_manager)

    def invalidate(self) -> None:
        """Drop cached registry state so the next access reloads config."""
        self._entries = None

    @property
    def entries(self) -> tuple[ProjectRegistryEntry, ...]:
        """Configured projects with canonical names, permalinks, and resolved paths."""
        if self._entries is None:
            config = self.config_manager.config
            self._entries = tuple(
                ProjectRegistryEntry(
                    name=name,
                    permalink=generate_permalink(name),
                    path=Path(entry.path).expanduser().resolve(strict=False),
                )
                for name, entry in config.projects.items()
            )
        return self._entries

    @property
    def default_project(self) -> Optional[str]:
        """Configured default project name."""
        return self.config_manager.default_project

    @property
    def project_paths(self) -> dict[str, str]:
        """Configured project-name to path mapping for compatibility callers."""
        return {entry.name: str(entry.path) for entry in self.entries}

    def lookup(self, identifier: str) -> Optional[ProjectRegistryEntry]:
        """Resolve a project by name or permalink, failing fast on ambiguity."""
        permalink = generate_permalink(identifier)
        matches = [entry for entry in self.entries if entry.permalink == permalink]

        if not matches:
            return None
        if len(matches) > 1:
            projects = ", ".join(sorted(entry.name for entry in matches))
            raise ValueError(
                f"Ambiguous project identifier '{identifier}' matches multiple configured projects: {projects}"
            )
        return matches[0]

    def match_cwd(self, cwd: Optional[str]) -> Optional[ProjectRegistryEntry]:
        """Resolve the configured project containing the provided cwd."""
        if not cwd:
            return None

        cwd_path = Path(cwd).expanduser().resolve(strict=False)
        matches: list[ProjectRegistryEntry] = []
        for entry in self.entries:
            try:
                cwd_path.relative_to(entry.path)
            except ValueError:
                continue
            matches.append(entry)

        if not matches:
            return None

        matches.sort(key=lambda entry: len(entry.path.parts), reverse=True)
        best_match = matches[0]
        ambiguous_matches = [
            entry
            for entry in matches[1:]
            if len(entry.path.parts) == len(best_match.path.parts) and entry.path == best_match.path
        ]
        if ambiguous_matches:
            projects = ", ".join(
                sorted(entry.name for entry in (best_match, *ambiguous_matches))
            )
            raise ValueError(
                f"Ambiguous cwd project match for '{cwd_path}'; multiple configured projects share the same root: {projects}"
            )

        return best_match
