"""MemoryHub FastMCP server."""

from contextlib import asynccontextmanager

from fastmcp import FastMCP
from loguru import logger

from basic_memory import db
from basic_memory.mcp.container import McpContainer, set_container
from basic_memory.services.initialization import initialize_app


@asynccontextmanager
async def lifespan(app: FastMCP):
    """Lifecycle manager for the MCP server.

    Handles:
    - Database initialization and migrations
    - File sync via SyncCoordinator
    - Proper cleanup on shutdown
    """
    # --- Composition Root ---
    # Create container and read config (single point of config access)
    container = McpContainer.create()
    set_container(container)

    config = container.config
    logger.info(f"Starting MemoryHub MCP server (mode={container.mode.name})")
    logger.info(
        f"Config: database_backend={config.database_backend.value}, "
        f"semantic_search_enabled={config.semantic_search_enabled}, "
        f"default_project={config.default_project}"
    )
    if config.semantic_search_enabled:
        logger.info(
            f"Semantic search: provider={config.semantic_embedding_provider}, "
            f"model={config.semantic_embedding_model}, "
            f"dimensions={config.semantic_embedding_dimensions or 'auto'}, "
            f"batch_size={config.semantic_embedding_batch_size}"
        )

    # Log configured projects
    for name, entry in config.projects.items():
        default = " (default)" if name == config.default_project else ""
        logger.info(f"Project: {name} -> {entry.path}{default}")

    # Track if we created the engine (vs test fixtures providing it)
    # This prevents disposing an engine provided by test fixtures when
    # multiple Client connections are made in the same test
    engine_was_none = db._engine is None

    # Initialize app (runs migrations, reconciles projects)
    await initialize_app(container.config)

    # Create and start sync coordinator (lifecycle centralized in coordinator)
    sync_coordinator = container.create_sync_coordinator()
    await sync_coordinator.start()

    try:
        yield
    finally:
        # Shutdown - coordinator handles clean task cancellation
        logger.debug("Shutting down MemoryHub MCP server")
        await sync_coordinator.stop()

        # Only shutdown DB if we created it (not if test fixture provided it)
        if engine_was_none:
            await db.shutdown_db()
            logger.debug("Database connections closed")
        else:  # pragma: no cover
            logger.debug("Skipping DB shutdown - engine provided externally")


mcp = FastMCP(
    name="Basic Memory",
    lifespan=lifespan,
)
