"""API v2 module for MemoryHub.

Version 2 standardizes the active API surface around stable external IDs and
explicit request models instead of path-only routing.

Key changes from v1:
- project and entity operations prefer external UUIDs in API paths
- request bodies carry file-path details when needed
- lookups are more direct and less dependent on permalink/path resolution
- routers are grouped under the `/v2` prefix
"""

from memoryhub.api.v2.routers import (
    knowledge_router,
    memory_router,
    project_router,
    resource_router,
    search_router,
    directory_router,
    prompt_router,
    importer_router,
)

__all__ = [
    "knowledge_router",
    "memory_router",
    "project_router",
    "resource_router",
    "search_router",
    "directory_router",
    "prompt_router",
    "importer_router",
]
