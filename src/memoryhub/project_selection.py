"""Shared project selection utilities built on top of ProjectResolver."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from memoryhub.config import ConfigManager, ProjectConfig
from memoryhub.project_registry import ProjectRegistry
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


@dataclass(frozen=True)
class ProjectRoutingContext:
    """Resolved routing state for a request or long-lived session."""

    selection: ProjectSelection
    requested_project: Optional[str] = None
    constrained_project: Optional[str] = None

    @property
    def project(self) -> Optional[str]:
        """Return the canonical project selected for this context."""
        return self.selection.project

    @property
    def path(self) -> Optional[Path]:
        """Return the selected project path when configured locally."""
        return self.selection.path

    @property
    def is_constrained(self) -> bool:
        """Return True when the session is restricted to one project."""
        return self.constrained_project is not None


@dataclass
class ProjectSelector:
    """Resolve and canonicalize project identifiers from local config state."""

    project_registry: ProjectRegistry
    cwd: Optional[str] = None

    @classmethod
    def from_config(
        cls,
        config_manager: Optional[ConfigManager] = None,
        cwd: Optional[str] = None,
    ) -> "ProjectSelector":
        """Create a selector backed by the current config file."""
        return cls(
            project_registry=ProjectRegistry.from_config(config_manager or ConfigManager()),
            cwd=cwd,
        )

    @property
    def config_manager(self) -> ConfigManager:
        """Expose the backing config manager for compatibility callers."""
        return self.project_registry.config_manager

    @property
    def project_paths(self) -> dict[str, str]:
        """Configured project-name to path mapping."""
        return self.project_registry.project_paths

    @property
    def default_project(self) -> Optional[str]:
        """Configured default project name."""
        return self.project_registry.default_project

    def lookup(self, identifier: str) -> Optional[ProjectConfig]:
        """Return canonical project config for a name or permalink."""
        entry = self.project_registry.lookup(identifier)
        if entry is None:
            return None
        return entry.to_project_config()

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
            project_registry=self.project_registry,
            cwd=self.cwd,
        )
        resolution = resolver.resolve(project=project, allow_discovery=allow_discovery)
        configured_project = (
            self.lookup(resolution.project) if resolution.project is not None else None
        )
        return ProjectSelection(resolution=resolution, configured_project=configured_project)

    def resolve_constraint(self) -> Optional[ProjectSelection]:
        """Resolve only the env-based project constraint, if one is active."""
        resolver = ProjectResolver.from_env(
            default_project=None,
            project_paths=self.project_paths,
            project_registry=self.project_registry,
            cwd=self.cwd,
        )
        if resolver.constrained_project is None:
            return None

        resolution = resolver.resolve(project=None, allow_discovery=True)
        configured_project = self.lookup(resolution.project) if resolution.project else None
        return ProjectSelection(resolution=resolution, configured_project=configured_project)

    def routing_context(
        self,
        project: Optional[str] = None,
        allow_discovery: bool = False,
        default_project: Optional[str] = None,
    ) -> ProjectRoutingContext:
        """Build a routing context with selection and constraint state."""
        selection = self.resolve(
            project=project,
            allow_discovery=allow_discovery,
            default_project=default_project,
        )
        constraint = self.resolve_constraint()
        return ProjectRoutingContext(
            selection=selection,
            requested_project=project,
            constrained_project=constraint.project if constraint is not None else None,
        )

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
