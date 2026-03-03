"""MCP server command with streamable HTTP transport."""

import os
from typing import Any, Optional

import typer
from loguru import logger

from memoryhub.cli.app import app
from memoryhub.config import init_mcp_logging
from memoryhub.project_selection import ProjectSelector
from memoryhub.project_resolver import PROJECT_CONSTRAINT_ENV_VARS


class _DeferredMcpServer:
    def run(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        from memoryhub.mcp.server import mcp as live_mcp_server

        live_mcp_server.run(*args, **kwargs)


# Keep module-level attribute for tests/monkeypatching while deferring heavy import.
mcp_server = _DeferredMcpServer()


@app.command()
def mcp(
    transport: str = typer.Option("stdio", help="Transport type: stdio, streamable-http, or sse"),
    host: str = typer.Option(
        "0.0.0.0", help="Host for HTTP transports (use 0.0.0.0 to allow external connections)"
    ),
    port: int = typer.Option(8000, help="Port for HTTP transports"),
    path: str = typer.Option("/mcp", help="Path prefix for streamable-http transport"),
    project: Optional[str] = typer.Option(None, help="Restrict MCP server to single project"),
):  # pragma: no cover
    """Run the MCP server with configurable transport options.

    This command starts an MCP server using one of three transport options:

    - stdio: Standard I/O (good for local usage)
    - streamable-http: Recommended for web deployments
    - sse: Server-Sent Events (for compatibility with existing clients)

    Initialization, file sync, and cleanup are handled by the MCP server's lifespan.
    """
    # Import mcp tools/prompts to register them with the server
    import memoryhub.mcp.tools  # noqa: F401  # pragma: no cover
    import memoryhub.mcp.prompts  # noqa: F401  # pragma: no cover
    import memoryhub.mcp.resources  # noqa: F401  # pragma: no cover

    # Initialize logging for MCP (file only, stdout breaks protocol)
    init_mcp_logging()

    # Validate and set project constraint if specified
    if project:
        selector = ProjectSelector.from_config()
        try:
            project_name = selector.require_configured_project(
                project,
                error_message=f"No project found named: {project}",
            ).project
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        # Export both names during the transition to keep older entry points working.
        for env_var in PROJECT_CONSTRAINT_ENV_VARS:
            os.environ[env_var] = project_name
        logger.info(f"MCP server constrained to project: {project_name}")

    # Run the MCP server (blocks)
    # Lifespan handles: initialization, migrations, file sync, cleanup
    logger.info(f"Starting MCP server with {transport.upper()} transport")

    if transport == "stdio":
        mcp_server.run(
            transport=transport,
        )
    elif transport == "streamable-http" or transport == "sse":
        mcp_server.run(
            transport=transport,
            host=host,
            port=port,
            path=path,
            log_level="INFO",
        )
