"""Tests for local project context utilities."""

from __future__ import annotations

import pytest


class _ContextState:
    """Minimal FastMCP context-state stub for unit tests."""

    def __init__(self):
        self._state: dict[str, object] = {}

    async def get_state(self, key: str):
        return self._state.get(key)

    async def set_state(self, key: str, value: object, **kwargs) -> None:
        self._state[key] = value


@pytest.mark.asyncio
async def test_returns_none_when_no_default_and_no_project(config_manager, monkeypatch):
    from memoryhub.mcp.project_context import resolve_project_parameter

    cfg = config_manager.load_config()
    cfg.default_project = None
    config_manager.save_config(cfg)

    monkeypatch.delenv("BASIC_MEMORY_MCP_PROJECT", raising=False)
    assert await resolve_project_parameter(project=None, allow_discovery=False) is None


@pytest.mark.asyncio
async def test_allows_discovery_when_enabled(config_manager):
    from memoryhub.mcp.project_context import resolve_project_parameter

    cfg = config_manager.load_config()
    cfg.default_project = None
    config_manager.save_config(cfg)

    assert await resolve_project_parameter(project=None, allow_discovery=True) is None


@pytest.mark.asyncio
async def test_returns_project_when_specified():
    from memoryhub.mcp.project_context import resolve_project_parameter

    assert await resolve_project_parameter(project="my-project") == "my-project"


@pytest.mark.asyncio
async def test_canonicalizes_configured_project_permalink(config_manager, config_home):
    from memoryhub.config import ProjectEntry
    from memoryhub.mcp.project_context import resolve_project_parameter

    cfg = config_manager.load_config()
    (config_home / "My Research").mkdir(parents=True, exist_ok=True)
    cfg.projects["My Research"] = ProjectEntry(path=str(config_home / "My Research"))
    cfg.default_project = None
    config_manager.save_config(cfg)

    assert await resolve_project_parameter(project="my-research") == "My Research"


@pytest.mark.asyncio
async def test_uses_env_var_priority(monkeypatch):
    from memoryhub.mcp.project_context import resolve_project_parameter

    monkeypatch.setenv("BASIC_MEMORY_MCP_PROJECT", "env-project")
    assert await resolve_project_parameter(project="explicit-project") == "env-project"


@pytest.mark.asyncio
async def test_uses_default_project(config_manager, config_home, monkeypatch):
    from memoryhub.mcp.project_context import resolve_project_parameter
    from memoryhub.config import ProjectEntry

    cfg = config_manager.load_config()
    (config_home / "default-project").mkdir(parents=True, exist_ok=True)
    cfg.projects["default-project"] = ProjectEntry(path=str(config_home / "default-project"))
    cfg.default_project = "default-project"
    config_manager.save_config(cfg)

    monkeypatch.delenv("BASIC_MEMORY_MCP_PROJECT", raising=False)
    assert await resolve_project_parameter(project=None) == "default-project"


@pytest.mark.asyncio
async def test_uses_cwd_project_when_default_missing(config_manager, config_home, monkeypatch):
    from memoryhub.mcp.project_context import resolve_project_parameter
    from memoryhub.config import ProjectEntry

    project_root = config_home / "cwd-project"
    nested_dir = project_root / "nested" / "worktree"
    nested_dir.mkdir(parents=True, exist_ok=True)

    cfg = config_manager.load_config()
    cfg.default_project = None
    cfg.projects["cwd-project"] = ProjectEntry(path=str(project_root))
    config_manager.save_config(cfg)

    monkeypatch.chdir(nested_dir)
    monkeypatch.delenv("BASIC_MEMORY_MCP_PROJECT", raising=False)

    assert await resolve_project_parameter(project=None) == "cwd-project"


class TestDetectProjectFromUrlPrefix:
    def test_detects_project_from_memory_url(self, config_manager):
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        result = detect_project_from_url_prefix("memory://test-project/some-note", config)
        assert result == "test-project"

    def test_detects_project_from_plain_path(self, config_manager):
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        result = detect_project_from_url_prefix("test-project/some-note", config)
        assert result == "test-project"

    def test_returns_none_for_unknown_prefix(self, config_manager):
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        result = detect_project_from_url_prefix("memory://unknown-project/note", config)
        assert result is None

    def test_returns_none_for_no_slash(self, config_manager):
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        result = detect_project_from_url_prefix("memory://single-segment", config)
        assert result is None

    def test_returns_none_for_wildcard_prefix(self, config_manager):
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        result = detect_project_from_url_prefix("memory://*/notes", config)
        assert result is None

    def test_matches_case_insensitive_via_permalink(self, config_manager):
        from memoryhub.config import ProjectEntry
        from memoryhub.mcp.project_context import detect_project_from_url_prefix

        config = config_manager.load_config()
        (config_manager.config_dir.parent / "My Research").mkdir(parents=True, exist_ok=True)
        config.projects["My Research"] = ProjectEntry(
            path=str(config_manager.config_dir.parent / "My Research")
        )
        config_manager.save_config(config)

        result = detect_project_from_url_prefix("memory://my-research/notes", config)
        assert result == "My Research"
