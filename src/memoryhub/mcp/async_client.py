from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import AsyncIterator, Callable, Optional

from httpx import ASGITransport, AsyncClient, Timeout
from loguru import logger

from memoryhub.api.app import app as fastapi_app


def _build_timeout() -> Timeout:
    """Create a standard timeout config used across all clients."""
    return Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=30.0,
    )


def _asgi_client(timeout: Timeout) -> AsyncClient:
    """Create a local ASGI client."""
    return AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test", timeout=timeout
    )


# Optional factory override for dependency injection
_client_factory: Optional[Callable[[], AbstractAsyncContextManager[AsyncClient]]] = None


def set_client_factory(factory: Callable[[], AbstractAsyncContextManager[AsyncClient]]) -> None:
    """Override the default client factory for testing or alternate transports."""
    global _client_factory
    _client_factory = factory


def is_factory_mode() -> bool:
    """Return True when a client factory override is active."""
    return _client_factory is not None


@asynccontextmanager
async def get_client(
    project_name: Optional[str] = None,
) -> AsyncIterator[AsyncClient]:
    """Get an AsyncClient as a context manager.

    Client selection priority:
    1. Factory injection.
    2. Local ASGI transport.

    MemoryHub supports local ASGI routing only.
    """
    if _client_factory:
        async with _client_factory() as client:
            yield client
        return

    timeout = _build_timeout()

    if project_name is not None:
        logger.debug(f"Project '{project_name}' uses local ASGI routing")
    else:
        logger.debug("Using local ASGI client for MemoryHub API")

    async with _asgi_client(timeout) as client:
        yield client


def create_client() -> AsyncClient:
    """Create an HTTP client for the local ASGI app.

    DEPRECATED: Use get_client() context manager instead for proper resource management.
    """
    logger.info("Creating ASGI client for local MemoryHub API")
    return _asgi_client(_build_timeout())
