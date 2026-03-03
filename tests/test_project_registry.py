"""Tests for the configured project registry layer."""

from pathlib import Path

import pytest

from memoryhub.config import ProjectEntry
from memoryhub.project_registry import ProjectRegistry
from memoryhub.project_selection import ProjectSelector


def test_registry_lookup_returns_canonical_entry(config_manager, config_home):
    """Lookup should resolve a permalink back to the configured project name."""
    config = config_manager.load_config()
    project_root = config_home / "My Research"
    project_root.mkdir(parents=True, exist_ok=True)
    config.projects["My Research"] = ProjectEntry(path=str(project_root))
    config_manager.save_config(config)

    entry = ProjectRegistry.from_config(config_manager).lookup("my-research")

    assert entry is not None
    assert entry.name == "My Research"
    assert entry.path == Path(project_root).resolve()


def test_registry_lookup_rejects_duplicate_project_slugs(config_manager, config_home):
    """Duplicate permalinks should fail fast instead of picking an arbitrary project."""
    config = config_manager.load_config()
    first_root = config_home / "My Project"
    second_root = config_home / "my-project"
    first_root.mkdir(parents=True, exist_ok=True)
    second_root.mkdir(parents=True, exist_ok=True)
    config.projects["My Project"] = ProjectEntry(path=str(first_root))
    config.projects["my-project"] = ProjectEntry(path=str(second_root))
    config_manager.save_config(config)

    registry = ProjectRegistry.from_config(config_manager)

    with pytest.raises(ValueError, match="Ambiguous project identifier 'my-project'"):
        registry.lookup("my-project")


def test_registry_match_cwd_prefers_deepest_project_root(config_manager, config_home):
    """Cwd resolution should pick the most specific matching project root."""
    config = config_manager.load_config()
    parent_root = config_home / "parent"
    child_root = parent_root / "child"
    nested_dir = child_root / "notes"
    nested_dir.mkdir(parents=True, exist_ok=True)
    config.projects["parent"] = ProjectEntry(path=str(parent_root))
    config.projects["child"] = ProjectEntry(path=str(child_root))
    config_manager.save_config(config)

    entry = ProjectRegistry.from_config(config_manager).match_cwd(str(nested_dir))

    assert entry is not None
    assert entry.name == "child"


def test_selector_resolve_rejects_ambiguous_cwd_matches(config_manager, config_home):
    """Selector should fail fast when multiple configured projects share one root."""
    config = config_manager.load_config()
    shared_root = config_home / "shared"
    nested_dir = shared_root / "notes"
    nested_dir.mkdir(parents=True, exist_ok=True)
    config.projects["alpha"] = ProjectEntry(path=str(shared_root))
    config.projects["beta"] = ProjectEntry(path=str(shared_root))
    config.default_project = None
    config_manager.save_config(config)

    selector = ProjectSelector.from_config(config_manager, cwd=str(nested_dir))

    with pytest.raises(ValueError, match="Ambiguous cwd project match"):
        selector.resolve()
