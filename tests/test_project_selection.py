"""Tests for shared project selection utilities."""

from pathlib import Path

import pytest

from memoryhub.config import ProjectEntry
from memoryhub.project_resolver import ResolutionMode
from memoryhub.project_selection import ProjectSelector


def test_lookup_canonicalizes_permalink_identifier(config_manager, config_home):
    """Configured project lookup should map permalinks back to canonical names."""
    config = config_manager.load_config()
    project_root = config_home / "My Research"
    project_root.mkdir(parents=True, exist_ok=True)
    config.projects["My Research"] = ProjectEntry(path=str(project_root))
    config_manager.save_config(config)

    selection = ProjectSelector.from_config(config_manager).require_configured_project("my-research")

    assert selection.project == "My Research"
    assert selection.path == Path(project_root)


def test_resolve_canonicalizes_env_constraint(config_manager, config_home, monkeypatch):
    """Env-constrained project slugs should resolve to configured canonical names."""
    config = config_manager.load_config()
    project_root = config_home / "My Research"
    project_root.mkdir(parents=True, exist_ok=True)
    config.projects["My Research"] = ProjectEntry(path=str(project_root))
    config.default_project = None
    config_manager.save_config(config)

    monkeypatch.setenv("BASIC_MEMORY_MCP_PROJECT", "my-research")
    selection = ProjectSelector.from_config(config_manager).resolve()

    assert selection.project == "My Research"
    assert selection.is_configured is True
    assert selection.resolution.mode == ResolutionMode.ENV_CONSTRAINT


def test_resolve_uses_cwd_project_before_default(config_manager, config_home, monkeypatch):
    """Selector should reuse cwd inference from ProjectResolver with config-backed names."""
    default_root = config_home / "default-project"
    cwd_root = config_home / "cwd-project"
    nested_dir = cwd_root / "nested" / "worktree"
    default_root.mkdir(parents=True, exist_ok=True)
    nested_dir.mkdir(parents=True, exist_ok=True)

    config = config_manager.load_config()
    config.projects["default-project"] = ProjectEntry(path=str(default_root))
    config.projects["cwd-project"] = ProjectEntry(path=str(cwd_root))
    config.default_project = "default-project"
    config_manager.save_config(config)

    monkeypatch.chdir(nested_dir)
    monkeypatch.delenv("BASIC_MEMORY_MCP_PROJECT", raising=False)

    selection = ProjectSelector.from_config(config_manager).resolve()

    assert selection.project == "cwd-project"
    assert selection.path == Path(cwd_root)
    assert selection.resolution.mode == ResolutionMode.CWD


def test_require_configured_project_rejects_unknown_identifier(config_manager):
    """Explicit configured-project validation should fail fast for unknown names."""
    selector = ProjectSelector.from_config(config_manager)

    with pytest.raises(ValueError, match="No project found named: missing-project"):
        selector.require_configured_project("missing-project")


def test_routing_context_exposes_canonical_constraint(config_manager, config_home, monkeypatch):
    """Routing context should surface the canonical constrained project name."""
    config = config_manager.load_config()
    project_root = config_home / "My Research"
    project_root.mkdir(parents=True, exist_ok=True)
    config.projects["My Research"] = ProjectEntry(path=str(project_root))
    config.default_project = None
    config_manager.save_config(config)

    monkeypatch.setenv("BASIC_MEMORY_MCP_PROJECT", "my-research")
    routing_context = ProjectSelector.from_config(config_manager).routing_context(
        project="ignored-project",
        allow_discovery=True,
    )

    assert routing_context.project == "My Research"
    assert routing_context.constrained_project == "My Research"
    assert routing_context.is_constrained is True
    assert routing_context.requested_project == "ignored-project"


def test_routing_context_prefers_memoryhub_constraint_alias(config_manager, monkeypatch):
    """Routing context should prefer the MemoryHub env alias over the legacy name."""
    monkeypatch.setenv("BASIC_MEMORY_MCP_PROJECT", "legacy-project")
    monkeypatch.setenv("MEMORYHUB_MCP_PROJECT", "memoryhub-project")

    routing_context = ProjectSelector.from_config(config_manager).routing_context(
        allow_discovery=True
    )

    assert routing_context.project == "memoryhub-project"
    assert routing_context.constrained_project == "memoryhub-project"
