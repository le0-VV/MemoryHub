"""Runtime install primitives."""

from __future__ import annotations

import json
import shlex
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from memoryhub.framework.errors import RuntimeLayoutError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.registry import ProjectRegistry

INSTALL_SCHEMA_VERSION = 1
InstallMode = Literal["install", "force", "repair", "update"]
LauncherAction = Literal["created", "unchanged", "repaired", "replaced", "updated"]


@dataclass(frozen=True, slots=True)
class InstallReport:
    runtime_root: Path
    config_path: Path
    bin_path: Path
    metadata_path: Path
    python_executable: Path
    import_root: Path
    launcher_created: bool
    launcher_action: LauncherAction

    def to_json(self) -> dict[str, object]:
        return {
            "runtime_root": str(self.runtime_root),
            "config_path": str(self.config_path),
            "bin_path": str(self.bin_path),
            "metadata_path": str(self.metadata_path),
            "python_executable": str(self.python_executable),
            "import_root": str(self.import_root),
            "launcher_created": self.launcher_created,
            "launcher_action": self.launcher_action,
        }


def install_runtime(
    layout: RuntimeLayout,
    *,
    python_executable: Path | None = None,
    force: bool = False,
    repair: bool = False,
    update: bool = False,
) -> InstallReport:
    mode = _install_mode(force=force, repair=repair, update=update)
    executable = _resolve_python_executable(python_executable)
    import_root = _resolve_import_root()
    ProjectRegistry(layout).ensure_initialized()
    metadata_path = layout.runtime_dir / "install.json"
    bin_path = layout.bin_dir / "memoryhub"
    launcher_action = _write_launcher(
        bin_path,
        executable,
        import_root,
        mode=mode,
    )
    _write_install_metadata(layout, metadata_path, bin_path, executable, import_root)
    return InstallReport(
        runtime_root=layout.root,
        config_path=layout.config_path,
        bin_path=bin_path,
        metadata_path=metadata_path,
        python_executable=executable,
        import_root=import_root,
        launcher_created=launcher_action != "unchanged",
        launcher_action=launcher_action,
    )


def _install_mode(*, force: bool, repair: bool, update: bool) -> InstallMode:
    selected_modes = sum(1 for value in (force, repair, update) if value)
    if selected_modes > 1:
        raise RuntimeLayoutError("choose only one of force, repair, or update")
    if force:
        return "force"
    if repair:
        return "repair"
    if update:
        return "update"
    return "install"


def _resolve_python_executable(python_executable: Path | None) -> Path:
    executable = Path(
        sys.executable if python_executable is None else python_executable
    )
    if not executable.is_file():
        raise RuntimeLayoutError(f"python executable does not exist: {executable}")
    return executable.resolve(strict=True)


def _resolve_import_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_launcher(
    bin_path: Path,
    python_executable: Path,
    import_root: Path,
    *,
    mode: InstallMode,
) -> LauncherAction:
    expected = _launcher_text(python_executable, import_root)
    if bin_path.exists():
        if not bin_path.is_file():
            raise RuntimeLayoutError(f"launcher path is not a file: {bin_path}")
        existing = bin_path.read_text(encoding="utf-8")
        if existing == expected:
            return _ensure_launcher_mode(bin_path)
        if mode == "install":
            raise RuntimeLayoutError(f"launcher already exists: {bin_path}")
        _write_launcher_file(bin_path, expected)
        return _replacement_action(mode)

    _write_launcher_file(bin_path, expected)
    return "created"


def _write_launcher_file(bin_path: Path, text: str) -> None:
    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.write_text(text, encoding="utf-8")
    _ensure_launcher_mode(bin_path)


def _ensure_launcher_mode(bin_path: Path) -> LauncherAction:
    current_mode = bin_path.stat().st_mode
    executable_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    if executable_mode == current_mode:
        return "unchanged"
    bin_path.chmod(executable_mode)
    return "repaired"


def _replacement_action(mode: InstallMode) -> LauncherAction:
    if mode == "repair":
        return "repaired"
    if mode == "update":
        return "updated"
    return "replaced"


def _launcher_text(python_executable: Path, import_root: Path) -> str:
    quoted_python = shlex.quote(str(python_executable))
    quoted_import_root = shlex.quote(str(import_root))
    return "\n".join(
        [
            "#!/bin/sh",
            f"export PYTHONPATH={quoted_import_root}${{PYTHONPATH:+:$PYTHONPATH}}",
            f'exec {quoted_python} -m memoryhub.adapters.cli "$@"',
            "",
        ]
    )


def _write_install_metadata(
    layout: RuntimeLayout,
    metadata_path: Path,
    bin_path: Path,
    python_executable: Path,
    import_root: Path,
) -> None:
    payload = {
        "version": INSTALL_SCHEMA_VERSION,
        "runtime_root": str(layout.root),
        "config_path": str(layout.config_path),
        "bin_path": str(bin_path),
        "python_executable": str(python_executable),
        "import_root": str(import_root),
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
