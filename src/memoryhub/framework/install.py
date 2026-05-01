"""Runtime install primitives."""

from __future__ import annotations

import json
import shlex
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from memoryhub.framework.errors import RuntimeLayoutError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.registry import ProjectRegistry

INSTALL_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class InstallReport:
    runtime_root: Path
    config_path: Path
    bin_path: Path
    metadata_path: Path
    python_executable: Path
    import_root: Path
    launcher_created: bool

    def to_json(self) -> dict[str, object]:
        return {
            "runtime_root": str(self.runtime_root),
            "config_path": str(self.config_path),
            "bin_path": str(self.bin_path),
            "metadata_path": str(self.metadata_path),
            "python_executable": str(self.python_executable),
            "import_root": str(self.import_root),
            "launcher_created": self.launcher_created,
        }


def install_runtime(
    layout: RuntimeLayout,
    *,
    python_executable: Path | None = None,
    force: bool = False,
) -> InstallReport:
    executable = _resolve_python_executable(python_executable)
    import_root = _resolve_import_root()
    ProjectRegistry(layout).ensure_initialized()
    metadata_path = layout.runtime_dir / "install.json"
    bin_path = layout.bin_dir / "memoryhub"
    launcher_created = _write_launcher(
        bin_path,
        executable,
        import_root,
        force=force,
    )
    _write_install_metadata(layout, metadata_path, bin_path, executable, import_root)
    return InstallReport(
        runtime_root=layout.root,
        config_path=layout.config_path,
        bin_path=bin_path,
        metadata_path=metadata_path,
        python_executable=executable,
        import_root=import_root,
        launcher_created=launcher_created,
    )


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
    force: bool,
) -> bool:
    if bin_path.exists() and not force:
        existing = bin_path.read_text(encoding="utf-8")
        expected = _launcher_text(python_executable, import_root)
        if existing == expected:
            return False
        raise RuntimeLayoutError(f"launcher already exists: {bin_path}")

    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.write_text(
        _launcher_text(python_executable, import_root),
        encoding="utf-8",
    )
    current_mode = bin_path.stat().st_mode
    bin_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return True


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
