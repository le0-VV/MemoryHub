"""Helpers for serving MCP UI HTML resources."""

from __future__ import annotations

from pathlib import Path

from memoryhub.env_compat import UI_VARIANT_ENV_VARS, get_env_value

DEFAULT_VARIANT = "vanilla"
SUPPORTED_VARIANTS = {"vanilla", "tool-ui", "mcp-ui"}


def get_ui_variant() -> str:
    """Return the active UI variant from environment settings."""
    value = (get_env_value(UI_VARIANT_ENV_VARS, DEFAULT_VARIANT) or DEFAULT_VARIANT).strip().lower()
    return value if value in SUPPORTED_VARIANTS else DEFAULT_VARIANT


def load_html(filename: str) -> str:
    """Load a UI HTML template from disk."""
    path = Path(__file__).parent / "html" / filename
    return path.read_text(encoding="utf-8")


def load_variant_html(base_name: str) -> str:
    """Load a UI template for the current variant."""
    variant = get_ui_variant()
    return load_html(f"{base_name}-{variant}.html")
