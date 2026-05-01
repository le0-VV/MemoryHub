from __future__ import annotations

from pathlib import Path

import pytest

from memoryhub.framework.errors import RuntimeLayoutError
from memoryhub.framework.install import install_runtime
from memoryhub.framework.layout import RuntimeLayout


def test_install_runtime_creates_config_metadata_and_launcher(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)

    report = install_runtime(layout, python_executable=python_executable)

    assert layout.config_path.is_file()
    assert layout.main_project_path.is_dir()
    assert report.metadata_path.is_file()
    assert report.bin_path.is_file()
    assert report.launcher_created is True
    assert report.import_root.name == "src"
    assert "memoryhub.adapters.cli" in report.bin_path.read_text(encoding="utf-8")
    assert "PYTHONPATH" in report.bin_path.read_text(encoding="utf-8")
    assert report.bin_path.stat().st_mode & 0o111


def test_install_runtime_is_idempotent_for_matching_launcher(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)

    first_report = install_runtime(layout, python_executable=python_executable)
    second_report = install_runtime(layout, python_executable=python_executable)

    assert first_report.launcher_created is True
    assert second_report.launcher_created is False


def test_install_runtime_rejects_existing_different_launcher(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)
    layout.ensure()
    layout.bin_dir.mkdir(parents=True, exist_ok=True)
    (layout.bin_dir / "memoryhub").write_text("different\n", encoding="utf-8")

    with pytest.raises(RuntimeLayoutError):
        install_runtime(layout, python_executable=python_executable)


def test_install_runtime_force_replaces_existing_launcher(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)
    layout.ensure()
    launcher = layout.bin_dir / "memoryhub"
    launcher.write_text("different\n", encoding="utf-8")

    report = install_runtime(layout, python_executable=python_executable, force=True)

    assert report.launcher_created is True
    assert "memoryhub.adapters.cli" in launcher.read_text(encoding="utf-8")


def _fake_python(tmp_path: Path) -> Path:
    path = tmp_path / "python"
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    return path
