"""Runtime mode resolution for MemoryHub.

This module centralizes runtime mode detection for the active local-only fork.
Composition roots read ConfigManager and use this module to resolve whether the
process is running in normal local mode or in the test environment.
"""

from enum import Enum, auto


class RuntimeMode(Enum):
    """Supported runtime modes for MemoryHub."""

    LOCAL = auto()  # Local standalone mode (default)
    TEST = auto()  # Test environment

    @property
    def is_local(self) -> bool:
        return self == RuntimeMode.LOCAL

    @property
    def is_test(self) -> bool:
        return self == RuntimeMode.TEST


def resolve_runtime_mode(
    is_test_env: bool,
) -> RuntimeMode:
    """Resolve the runtime mode from configuration flags.

    This is the single source of truth for mode resolution.
    Composition roots call this with config values they've read.

    Args:
        is_test_env: Whether running in test environment

    Returns:
        The resolved RuntimeMode
    """
    # Trigger: test environment is detected
    # Why: tests need special handling (no file sync, isolated DB)
    # Outcome: returns TEST mode instead of the normal local runtime
    if is_test_env:
        return RuntimeMode.TEST

    return RuntimeMode.LOCAL
