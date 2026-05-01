from pathlib import Path

import pytest

from memoryhub.framework.errors import ProjectSourceError, RuntimeLayoutError
from memoryhub.framework.layout import ENV_CONFIG_DIR, RuntimeLayout
from memoryhub.framework.project_source import SOURCE_DIRECTORIES, ProjectSourceLayout


def test_runtime_layout_from_env_uses_config_dir(tmp_path: Path) -> None:
    runtime_root = tmp_path / "hub"
    layout = RuntimeLayout.from_env({ENV_CONFIG_DIR: str(runtime_root)})

    assert layout.root == runtime_root
    assert layout.config_path == runtime_root / "config.json"
    assert layout.database_path == runtime_root / "memory.db"
    assert layout.main_project_path == runtime_root / "projects" / "main"

    layout.ensure()

    for directory in layout.required_directories:
        assert directory.is_dir()


def test_runtime_layout_rejects_file_conflict(tmp_path: Path) -> None:
    runtime_root = tmp_path / "hub"
    runtime_root.write_text("not a directory", encoding="utf-8")
    layout = RuntimeLayout.from_root(runtime_root)

    with pytest.raises(RuntimeLayoutError):
        layout.ensure()


def test_runtime_layout_rejects_empty_root() -> None:
    with pytest.raises(RuntimeLayoutError):
        RuntimeLayout.from_root("")


def test_project_source_layout_creates_openviking_style_tree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = ProjectSourceLayout.for_repo(repo_root)

    source.ensure()

    assert source.root == repo_root / ".agents" / "memoryhub"
    for relative_path in SOURCE_DIRECTORIES:
        assert (source.root / relative_path).is_dir()


def test_project_source_layout_rejects_file_conflict(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source_root = repo_root / ".agents" / "memoryhub"
    source_root.parent.mkdir(parents=True)
    source_root.write_text("not a directory", encoding="utf-8")
    source = ProjectSourceLayout.for_repo(repo_root)

    with pytest.raises(ProjectSourceError):
        source.ensure()
