"""CLI first-run messaging for the local MemoryHub fork."""

import os
import sys

from rich.console import Console

from memoryhub.config import ConfigManager


def _promos_disabled_by_env() -> bool:
    """Check environment-level kill switch for promo output."""
    value = os.getenv("BASIC_MEMORY_NO_PROMOS", "").strip().lower()
    return value in {"1", "true", "yes"}


def _is_interactive_session() -> bool:
    """Return whether stdin/stdout are interactive terminals."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except ValueError:
        # Trigger: stdin/stdout already closed (e.g., MCP stdio transport shutdown)
        # Why: isatty() raises ValueError on closed file descriptors
        # Outcome: treat as non-interactive, suppressing promo output
        return False


def maybe_show_init_line(
    invoked_subcommand: str | None,
    *,
    config_manager: ConfigManager | None = None,
    is_interactive: bool | None = None,
    console: Console | None = None,
) -> None:
    """Show a one-time init confirmation line before command output."""
    manager = config_manager or ConfigManager()
    config = manager.load_config()

    interactive = _is_interactive_session() if is_interactive is None else is_interactive

    # Suppress in non-interactive or root-help contexts, and only show once.
    if _promos_disabled_by_env() or not interactive:
        return

    if invoked_subcommand in {None, "mcp"}:
        return

    if config.init_message_shown:
        return

    out = console or Console()
    out.print("MemoryHub initialized ✓")

    config.init_message_shown = True
    manager.save_config(config)
