"""Typed internal API clients for MCP tools.

These clients encapsulate API paths, error handling, and response validation.
MCP tools become thin adapters that call these clients and format results.

Usage:
    from memoryhub.mcp.clients import KnowledgeClient, SearchClient

    async with get_client() as http_client:
        knowledge = KnowledgeClient(http_client, project_id)
        entity = await knowledge.create_entity(entity_data)
"""

from memoryhub.mcp.clients.knowledge import KnowledgeClient
from memoryhub.mcp.clients.search import SearchClient
from memoryhub.mcp.clients.memory import MemoryClient
from memoryhub.mcp.clients.directory import DirectoryClient
from memoryhub.mcp.clients.resource import ResourceClient
from memoryhub.mcp.clients.project import ProjectClient
from memoryhub.mcp.clients.schema import SchemaClient

__all__ = [
    "KnowledgeClient",
    "SearchClient",
    "MemoryClient",
    "DirectoryClient",
    "ResourceClient",
    "ProjectClient",
    "SchemaClient",
]
