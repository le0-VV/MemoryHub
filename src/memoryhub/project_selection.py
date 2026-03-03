"""Shared project selection utilities built on top of ProjectResolver."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from memoryhub.config import ConfigManager, ProjectConfig
from memoryhub.project_resolver import ProjectResolver, ResolvedProject


@dataclass(frozen=True)
class ProjectSelection:
    """Resolved project selection with optional config-backed canonical data."""

    resolution: ResolvedProject
    configured_project: Optional[ProjectConfig] = None

    @property
    def project(self) -> Optional[str]:
        """Return the canonical configured project name when available."""
        if self.configured_project is not None:
            return self.configured_project.name
        return self.resolution.project

    @property
    def path(self) -> Optional[Path]:
        """Return the configured project path when the project exists in config."""
        if self.configured_project is None:
            return None
        return self.configured_project.home

    @property
    def is_configured(self) -> bool:
        """Return True when the resolved project exists in config."""
        return self.configured_project is not None


@dataclass
class ProjectSelector:
    """Resolve and canonicalize project identifiers from local config state."""

    config_manager: ConfigManager
    cwd: Optional[str] = None

    @classmethod
    def from_config(
        cls,
        config_manager: Optional[ConfigManager] = None,
        cwd: Optional[str] = None,
    ) -> "ProjectSelector":
        """Create a selector backed by the current config file."""
        return cls(config_manager=config_manager or ConfigManager(), cwd=cwd)

    @property
    def project_paths(self) -> dict[str, str]:
        """Configured project-name to path mapping."""
        return self.config_manager.projects

    @property
    def default_project(self) -> Optional[str]:
        """Configured default project name."""
        return self.config_manager.default_project

    def lookup(self, identifier: str) -> Optional[ProjectConfig]:
        """Return canonical project config for a name or permalink."""
        project_name, path = self.config_manager.get_project(identifier)
        if not project_name or path is None:
            return None
        return ProjectConfig(name=project_name, home=Path(path))

    def resolve(
        self,
        project: Optional[str] = None,
        allow_discovery: bool = False,
        default_project: Optional[str] = None,
    ) -> ProjectSelection:
        """Resolve a project using config, env constraints, cwd, and defaults."""
        resolver = ProjectResolver.from_env(
            default_project=self.default_project if default_project is None else default_project,
            project_paths=self.project_paths,
            cwd=self.cwd,
        )
        resolution = resolver.resolve(project=project, allow_discovery=allow_discovery)
        configured_project = (
            self.lookup(resolution.project) if resolution.project is not None else None
        )
        return ProjectSelection(resolution=resolution, configured_project=configured_project)

    def require_project(
        self,
        project: Optional[str] = None,
        error_message: Optional[str] = None,
        default_project: Optional[str] = None,
    ) -> ProjectSelection:
        """Resolve a project, raising when no selection is possible."""
        selection = self.resolve(project=project, default_project=default_project)
        if selection.project is None:
            raise ValueError(
                error_message
                or "No project specified. Either set 'default_project' in config, or provide a 'project' argument."
            )
        return selection

    def require_configured_project(
        self,
        project: str,
        error_message: Optional[str] = None,
    ) -> ProjectSelection:
        """Require a project identifier that matches configured local project metadata."""
        selection = self.resolve(project=project)
        if not selection.is_configured:
            raise ValueError(error_message or f"No project found named: {project}")
        return selection
