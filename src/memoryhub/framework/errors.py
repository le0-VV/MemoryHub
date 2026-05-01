"""Framework error types."""


class MemoryHubError(Exception):
    """Base class for expected MemoryHub failures."""


class RuntimeLayoutError(MemoryHubError):
    """Raised when the runtime root or one of its paths is invalid."""


class ProjectSourceError(MemoryHubError):
    """Raised when a project context source tree is invalid."""


class RegistryError(MemoryHubError):
    """Raised when the project registry cannot be read or written."""


class ProjectValidationError(RegistryError):
    """Raised when project input is invalid."""


class ProjectConflictError(RegistryError):
    """Raised when a project conflicts with existing registry state."""


class ProjectNotFoundError(RegistryError):
    """Raised when a project does not exist."""
