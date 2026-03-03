"""Focused tests for supported MEMORYHUB_* configuration aliases."""

from pathlib import Path

from memoryhub.config import BasicMemoryConfig


def test_basic_memory_config_reads_memoryhub_project_root_env(monkeypatch, tmp_path):
    """Supported MEMORYHUB_PROJECT_ROOT should populate the project_root setting."""
    project_root = tmp_path / "projects"
    project_root.mkdir()
    monkeypatch.setenv("MEMORYHUB_PROJECT_ROOT", str(project_root))
    monkeypatch.delenv("BASIC_MEMORY_PROJECT_ROOT", raising=False)

    config = BasicMemoryConfig(projects={"main": {"path": str(tmp_path / "main")}})

    assert config.project_root == str(project_root)


def test_basic_memory_config_reads_memoryhub_semantic_env(monkeypatch, tmp_path):
    """Supported semantic-search env aliases should override defaults."""
    monkeypatch.setenv("MEMORYHUB_SEMANTIC_SEARCH_ENABLED", "true")
    monkeypatch.setenv("MEMORYHUB_SEMANTIC_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED", raising=False)
    monkeypatch.delenv("BASIC_MEMORY_SEMANTIC_EMBEDDING_PROVIDER", raising=False)

    config = BasicMemoryConfig(projects={"main": {"path": str(tmp_path / "main")}})

    assert config.semantic_search_enabled is True
    assert config.semantic_embedding_provider == "openai"
