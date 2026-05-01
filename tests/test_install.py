from __future__ import annotations

import json
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
    assert report.launcher_action == "created"
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
    assert first_report.launcher_action == "created"
    assert second_report.launcher_action == "unchanged"


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
    assert report.launcher_action == "replaced"
    assert "memoryhub.adapters.cli" in launcher.read_text(encoding="utf-8")


def test_install_runtime_repair_replaces_damaged_launcher(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)
    layout.ensure()
    launcher = layout.bin_dir / "memoryhub"
    launcher.write_text("damaged\n", encoding="utf-8")

    report = install_runtime(layout, python_executable=python_executable, repair=True)

    assert report.launcher_created is True
    assert report.launcher_action == "repaired"
    assert "memoryhub.adapters.cli" in launcher.read_text(encoding="utf-8")


def test_install_runtime_repair_restores_launcher_execute_mode(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)
    install_runtime(layout, python_executable=python_executable)
    launcher = layout.bin_dir / "memoryhub"
    launcher.chmod(0o644)

    report = install_runtime(layout, python_executable=python_executable, repair=True)

    assert report.launcher_created is True
    assert report.launcher_action == "repaired"
    assert launcher.stat().st_mode & 0o111


def test_install_runtime_update_refreshes_launcher_and_metadata(
    tmp_path: Path,
) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    first_python = _fake_python(tmp_path, "python-one")
    second_python = _fake_python(tmp_path, "python-two")
    install_runtime(layout, python_executable=first_python)

    report = install_runtime(
        layout,
        python_executable=second_python,
        update=True,
    )
    metadata = json.loads(report.metadata_path.read_text(encoding="utf-8"))

    assert report.launcher_created is True
    assert report.launcher_action == "updated"
    assert metadata["python_executable"] == str(second_python.resolve(strict=True))
    assert str(second_python.resolve(strict=True)) in report.bin_path.read_text(
        encoding="utf-8"
    )


def test_install_runtime_rejects_multiple_reconcile_modes(tmp_path: Path) -> None:
    layout = RuntimeLayout.from_root(tmp_path / "hub")
    python_executable = _fake_python(tmp_path)

    with pytest.raises(RuntimeLayoutError):
        install_runtime(
            layout,
            python_executable=python_executable,
            force=True,
            repair=True,
        )


def _fake_python(tmp_path: Path, name: str = "python") -> Path:
    path = tmp_path / name
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    return path
