"""Project context utilities for the MemoryHub MCP server.

Provides project lookup utilities for MCP tools.
Handles project validation and context management in one place.

Note: This module uses ProjectSelector for unified project resolution.
The resolve_project_parameter function is a thin wrapper for backwards
compatibility with existing MCP tools.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, List, Tuple

from httpx import AsyncClient
from httpx._types import (
    HeaderTypes,
)
from loguru import logger
from fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from memoryhub.config import BasicMemoryConfig, ConfigManager
from memoryhub.project_selection import ProjectSelector
from memoryhub.schemas.project_info import ProjectItem, ProjectList
from memoryhub.schemas.v2 import ProjectResolveResponse
from memoryhub.schemas.memory import memory_url_path
from memoryhub.utils import generate_permalink, normalize_project_reference


async def resolve_project_parameter(
    project: Optional[str] = None,
    allow_discovery: bool = False,
    default_project: Optional[str] = None,
) -> Optional[str]:
    """Resolve project parameter using unified local selection rules.

    This is a thin wrapper around ProjectSelector for backwards compatibility.
    New code should consider using ProjectSelector directly for more detailed
    resolution information.

    Resolution order:
    1. ENV_CONSTRAINT: MEMORYHUB_MCP_PROJECT env var (or BASIC_MEMORY_MCP_PROJECT during compatibility)
    2. EXPLICIT: project parameter passed directly
    3. CWD: configured project containing the active working directory
    4. DEFAULT: default_project from config (if set)
    5. Fallback: discovery (if allowed) → NONE

    Args:
        project: Optional explicit project parameter
        allow_discovery: If True, allows returning None for discovery mode
            (used by tools like recent_activity that can operate across all projects)
        default_project: Optional explicit default project. If not provided, reads from ConfigManager.

    Returns:
        Resolved project name or None if no resolution possible
    """
    selector = ProjectSelector.from_config()
    selection = selector.resolve(
        project=project,
        allow_discovery=allow_discovery,
        default_project=default_project,
    )
    return selection.project


async def get_project_names(client: AsyncClient, headers: HeaderTypes | None = None) -> List[str]:
    # Deferred import to avoid circular dependency with tools
    from memoryhub.mcp.tools.utils import call_get

    response = await call_get(client, "/v2/projects/", headers=headers)
    project_list = ProjectList.model_validate(response.json())
    return [project.name for project in project_list.projects]


async def get_active_project(
    client: AsyncClient,
    project: Optional[str] = None,
    context: Optional[Context] = None,
    headers: HeaderTypes | None = None,
) -> ProjectItem:
    """Get and validate project, setting it in context if available.

    Args:
        client: HTTP client for API calls
        project: Optional project name (resolved using hierarchy)
        context: Optional FastMCP context to cache the result

    Returns:
        The validated project item

    Raises:
        ValueError: If no project can be resolved
        HTTPError: If project doesn't exist or is inaccessible
    """
    # Deferred import to avoid circular dependency with tools
    from memoryhub.mcp.tools.utils import call_post

    resolved_project = await resolve_project_parameter(project)
    if not resolved_project:
        project_names = await get_project_names(client, headers)
        raise ValueError(
            "No project specified. "
            "Either set 'default_project' in config, or use 'project' argument.\n"
            f"Available projects: {project_names}"
        )

    project = resolved_project

    # Check if already cached in context
    if context:
        cached_raw = await context.get_state("active_project")
        if isinstance(cached_raw, dict):
            cached_project = ProjectItem.model_validate(cached_raw)
            if cached_project.name == project:
                logger.debug(f"Using cached project from context: {project}")
                return cached_project

    # Validate project exists by calling API
    logger.debug(f"Validating project: {project}")
    response = await call_post(
        client,
        "/v2/projects/resolve",
        json={"identifier": project},
        headers=headers,
    )
    resolved = ProjectResolveResponse.model_validate(response.json())
    active_project = ProjectItem(
        id=resolved.project_id,
        external_id=resolved.external_id,
        name=resolved.name,
        path=resolved.path,
        is_default=resolved.is_default,
    )

    # Cache in context if available
    if context:
        await context.set_state("active_project", active_project.model_dump())
        logger.debug(f"Cached project in context: {project}")

    logger.debug(f"Validated project: {active_project.name}")
    return active_project


def _split_project_prefix(path: str) -> tuple[Optional[str], str]:
    """Split a possible project prefix from a memory URL path."""
    if "/" not in path:
        return None, path

    project_prefix, remainder = path.split("/", 1)
    if not project_prefix or not remainder:
        return None, path

    if "*" in project_prefix:
        return None, path

    return project_prefix, remainder


async def resolve_project_and_path(
    client: AsyncClient,
    identifier: str,
    project: Optional[str] = None,
    context: Optional[Context] = None,
    headers: HeaderTypes | None = None,
) -> tuple[ProjectItem, str, bool]:
    """Resolve project and normalized path for memory:// identifiers.

    Returns:
        Tuple of (active_project, normalized_path, is_memory_url)
    """
    is_memory_url = identifier.strip().startswith("memory://")
    if not is_memory_url:
        active_project = await get_active_project(client, project, context, headers)
        return active_project, identifier, False

    normalized_path = normalize_project_reference(memory_url_path(identifier))
    project_prefix, remainder = _split_project_prefix(normalized_path)
    include_project = ConfigManager().config.permalinks_include_project

    # Trigger: memory URL begins with a potential project segment
    # Why: allow project-scoped memory URLs without requiring a separate project parameter
    # Outcome: attempt to resolve the prefix as a project and route to it
    if project_prefix:
        try:
            from memoryhub.mcp.tools.utils import call_post

            response = await call_post(
                client,
                "/v2/projects/resolve",
                json={"identifier": project_prefix},
                headers=headers,
            )
            resolved = ProjectResolveResponse.model_validate(response.json())
        except ToolError as exc:
            if "project not found" not in str(exc).lower():
                raise
        else:
            resolved_project = await resolve_project_parameter(project_prefix)
            if resolved_project and generate_permalink(resolved_project) != generate_permalink(
                project_prefix
            ):
                raise ValueError(
                    f"Project is constrained to '{resolved_project}', cannot use '{project_prefix}'."
                )

            active_project = ProjectItem(
                id=resolved.project_id,
                external_id=resolved.external_id,
                name=resolved.name,
                path=resolved.path,
                is_default=resolved.is_default,
            )
            if context:
                await context.set_state("active_project", active_project.model_dump())

            resolved_path = f"{resolved.permalink}/{remainder}" if include_project else remainder
            return active_project, resolved_path, True

    # Trigger: no resolvable project prefix in the memory URL
    # Why: preserve existing memory URL behavior within the active project
    # Outcome: use the active project and normalize the path for lookup
    active_project = await get_active_project(client, project, context, headers)
    resolved_path = normalized_path
    if include_project:
        # Trigger: project-prefixed permalinks are enabled and the path lacks a prefix
        # Why: ensure memory URL lookups align with canonical permalinks
        # Outcome: prefix the path with the active project's permalink
        project_prefix = active_project.permalink
        if resolved_path != project_prefix and not resolved_path.startswith(f"{project_prefix}/"):
            resolved_path = f"{project_prefix}/{resolved_path}"
    return active_project, resolved_path, True


def add_project_metadata(result: str, project_name: str) -> str:
    """Add project context as metadata footer for assistant session tracking.

    Provides clear project context to help the assistant remember which
    project is being used throughout the conversation session.

    Args:
        result: The tool result string
        project_name: The project name that was used

    Returns:
        Result with project session tracking metadata
    """
    return f"{result}\n\n[Session: Using project '{project_name}']"


def detect_project_from_url_prefix(identifier: str, config: BasicMemoryConfig) -> Optional[str]:
    """Check if a memory URL's first path segment matches a known project in config.

    This enables automatic project routing from memory URLs like
    ``memory://specs/in-progress`` without requiring the caller to pass
    an explicit ``project`` parameter.

    Uses local config only — no network calls.

    Args:
        identifier: Raw identifier string (may or may not start with ``memory://``).
        config: Current BasicMemoryConfig with project entries.

    Returns:
        Matching project name from config, or None if no match.
    """
    path = memory_url_path(identifier) if identifier.strip().startswith("memory://") else identifier
    normalized = normalize_project_reference(path)
    prefix, _ = _split_project_prefix(normalized)
    if prefix is None:
        return None

    prefix_permalink = generate_permalink(prefix)
    for project_name in config.projects:
        if generate_permalink(project_name) == prefix_permalink:
            return project_name
    return None


@asynccontextmanager
async def get_project_client(
    project: Optional[str] = None,
    context: Optional[Context] = None,
) -> AsyncIterator[Tuple[AsyncClient, ProjectItem]]:
    """Resolve a project, create a local client, and validate the project."""
    from memoryhub.mcp.async_client import get_client

    resolved_project = await resolve_project_parameter(project)
    if not resolved_project:
        async with get_client() as client:
            project_names = await get_project_names(client)
            raise ValueError(
                "No project specified. "
                "Either set 'default_project' in config, or use 'project' argument.\n"
                f"Available projects: {project_names}"
            )

    async with get_client(project_name=resolved_project) as client:
        active_project = await get_active_project(client, resolved_project, context)
        yield client, active_project
