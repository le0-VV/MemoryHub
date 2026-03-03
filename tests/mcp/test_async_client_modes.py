from contextlib import asynccontextmanager

import httpx
import pytest

from memoryhub.mcp import async_client as async_client_module
from memoryhub.mcp.async_client import (
    get_client,
    set_client_factory,
)


@pytest.fixture(autouse=True)
def _reset_async_client_state(monkeypatch):
    async_client_module._client_factory = None
    yield
    async_client_module._client_factory = None


@pytest.mark.asyncio
async def test_get_client_uses_injected_factory():
    seen = {"used": False}

    @asynccontextmanager
    async def factory():
        seen["used"] = True
        async with httpx.AsyncClient(base_url="https://example.test") as client:
            yield client

    set_client_factory(factory)
    async with get_client() as client:
        assert str(client.base_url) == "https://example.test"
    assert seen["used"] is True


@pytest.mark.asyncio
async def test_get_client_default_uses_local_asgi_transport():
    async with get_client() as client:
        assert isinstance(client._transport, httpx.ASGITransport)  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_get_client_with_project_name_uses_local_asgi_transport():
    async with get_client(project_name="research") as client:
        assert isinstance(client._transport, httpx.ASGITransport)  # pyright: ignore[reportPrivateUsage]
