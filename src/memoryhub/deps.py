"""Dependency injection functions for memoryhub services.

DEPRECATED: This module is a backwards-compatibility shim.
Import from memoryhub.deps package submodules instead:
- memoryhub.deps.config for configuration
- memoryhub.deps.db for database/session
- memoryhub.deps.projects for project resolution
- memoryhub.deps.repositories for data access
- memoryhub.deps.services for business logic
- memoryhub.deps.importers for import functionality

This file will be removed once all callers are migrated.
"""

# Re-export everything from the deps package for backwards compatibility
from memoryhub.deps import *  # noqa: F401, F403  # pragma: no cover
