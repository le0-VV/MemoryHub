"""Legacy CLI routing helpers for local-only command execution."""

from contextlib import contextmanager
from typing import Generator


@contextmanager
def force_routing(local: bool = False) -> Generator[None, None, None]:
    """Context manager kept for CLI call-site compatibility.

    MemoryHub is local-only, so there is no routing mode to switch anymore.
    This helper remains only to avoid broad call-site churn while the CLI
    entrypoint layer is simplified.

    Args:
        local: Compatibility parameter retained for old call sites

    Usage:
        with force_routing(local=True):
            # All API calls already use local ASGI transport
            await some_api_call()
    """
    del local
    yield


def validate_routing_flags(local: bool, cloud: bool = False) -> None:
    """Validate routing flags for the local-only CLI surface.

    Args:
        local: Value of --local flag
        cloud: Unused compatibility parameter retained for old call sites

    Raises:
        ValueError: Reserved for future validation failures
    """
    del local
    del cloud
