"""Legacy CLI routing helpers for local-only command execution."""

import os
from contextlib import contextmanager
from typing import Generator


@contextmanager
def force_routing(local: bool = False) -> Generator[None, None, None]:
    """Context manager to temporarily force local routing.

    This helper is a transition shim. The supported product surface is already
    local-only, but some CLI commands still use the historical explicit-routing
    environment flags while the entrypoint layer is being simplified.

    Args:
        local: If True, force local ASGI transport

    Usage:
        with force_routing(local=True):
            # All API calls will use local ASGI transport
            await some_api_call()
    """
    original_force_local = os.environ.get("BASIC_MEMORY_FORCE_LOCAL")
    original_explicit = os.environ.get("BASIC_MEMORY_EXPLICIT_ROUTING")

    try:
        if local:
            os.environ["BASIC_MEMORY_FORCE_LOCAL"] = "true"
            os.environ["BASIC_MEMORY_EXPLICIT_ROUTING"] = "true"
        yield
    finally:
        if original_force_local is None:
            os.environ.pop("BASIC_MEMORY_FORCE_LOCAL", None)
        else:
            os.environ["BASIC_MEMORY_FORCE_LOCAL"] = original_force_local

        if original_explicit is None:
            os.environ.pop("BASIC_MEMORY_EXPLICIT_ROUTING", None)
        else:
            os.environ["BASIC_MEMORY_EXPLICIT_ROUTING"] = original_explicit


def validate_routing_flags(local: bool, cloud: bool = False) -> None:
    """Validate routing flags for the local-only CLI surface.

    Args:
        local: Value of --local flag
        cloud: Unused compatibility parameter retained for old call sites

    Raises:
        ValueError: Reserved for future validation failures
    """
    del local
