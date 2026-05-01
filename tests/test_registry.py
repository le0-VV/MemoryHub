from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from memoryhub.framework.errors import ProjectConflictError, ProjectNotFoundError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.registry import MAIN_PROJECT_NAME, ProjectRegistry


def test_registry_initializes_main_project(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)

    state = registry.ensure_initialized()
    projects = registry.list_projects()

    assert layout.config_path.is_file()
    assert layout.main_project_path.is_dir()
    assert state.default_project == MAIN_PROJECT_NAME
    assert len(projects) == 1
    assert projects[0].record.name == MAIN_PROJECT_NAME
    assert projects[0].is_default is True


def test_registry_adds_project_source_and_symlink(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    record = registry.add_project(repo_root, name="demo")

    assert record.name == "demo"
    assert record.source_path.is_dir()
    assert record.registry_path.is_symlink()
    assert record.registry_path.resolve(strict=True) == record.source_path.resolve(
        strict=True
    )

    config = _read_config(layout.config_path)
    projects = _expect_object(config["projects"])
    demo = _expect_object(projects["demo"])
    assert demo["kind"] == "repository"
    assert demo["source_path"] == str(record.source_path)


def test_registry_rejects_duplicate_project_name(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    registry.add_project(repo_root, name="demo")

    with pytest.raises(ProjectConflictError):
        registry.add_project(repo_root, name="demo")


def test_registry_rejects_registry_path_conflict(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    registry = ProjectRegistry(layout)
    registry.ensure_initialized()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (layout.projects_dir / "demo").mkdir()

    with pytest.raises(ProjectConflictError):
        registry.add_project(repo_root, name="demo")


def test_registry_resolves_project_by_cwd(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    nested = repo_root / "nested"
    nested.mkdir(parents=True)
    registry.add_project(repo_root, name="demo")

    record = registry.resolve_by_cwd(nested)

    assert record.name == "demo"


def test_registry_removes_project_and_resets_default(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    registry.add_project(repo_root, name="demo", make_default=True)

    removed = registry.remove_project("demo")

    assert removed.name == "demo"
    assert not removed.registry_path.exists()
    assert registry.get_default().name == MAIN_PROJECT_NAME
    with pytest.raises(ProjectNotFoundError):
        registry.remove_project("demo")


def _read_config(path: Path) -> dict[str, object]:
    raw_config = json.loads(path.read_text(encoding="utf-8"))
    return _expect_object(raw_config)


def _expect_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)
