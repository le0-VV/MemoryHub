"""Runtime layout primitives."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

from memoryhub.framework.errors import RuntimeLayoutError

ENV_CONFIG_DIR: Final = "MEMORYHUB_CONFIG_DIR"
DEFAULT_RUNTIME_DIRNAME: Final = ".memoryhub"


@dataclass(frozen=True, slots=True)
class RuntimeLayout:
    """Resolved paths owned by one MemoryHub runtime root."""

    root: Path
    bin_dir: Path
    cache_dir: Path
    pip_cache_dir: Path
    uv_cache_dir: Path
    xdg_cache_dir: Path
    config_path: Path
    database_path: Path
    log_path: Path
    models_dir: Path
    fastembed_models_dir: Path
    projects_dir: Path
    main_project_path: Path
    runtime_dir: Path
    venv_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Self:
        values = os.environ if env is None else env
        configured_root = values.get(ENV_CONFIG_DIR)
        if configured_root is None or configured_root.strip() == "":
            return cls.from_root(Path.home() / DEFAULT_RUNTIME_DIRNAME)
        return cls.from_root(configured_root)

    @classmethod
    def from_root(cls, root: str | Path) -> Self:
        if isinstance(root, str) and root.strip() == "":
            raise RuntimeLayoutError("runtime root cannot be empty")
        runtime_root = Path(root).expanduser()

        return cls(
            root=runtime_root,
            bin_dir=runtime_root / "bin",
            cache_dir=runtime_root / "cache",
            pip_cache_dir=runtime_root / "cache" / "pip",
            uv_cache_dir=runtime_root / "cache" / "uv",
            xdg_cache_dir=runtime_root / "cache" / "xdg",
            config_path=runtime_root / "config.json",
            database_path=runtime_root / "memory.db",
            log_path=runtime_root / "memoryhub.log",
            models_dir=runtime_root / "models",
            fastembed_models_dir=runtime_root / "models" / "fastembed",
            projects_dir=runtime_root / "projects",
            main_project_path=runtime_root / "projects" / "main",
            runtime_dir=runtime_root / "runtime",
            venv_dir=runtime_root / "venv",
        )

    def ensure(self) -> None:
        for directory in self.required_directories:
            ensure_directory(directory)

    @property
    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.root,
            self.bin_dir,
            self.cache_dir,
            self.pip_cache_dir,
            self.uv_cache_dir,
            self.xdg_cache_dir,
            self.models_dir,
            self.fastembed_models_dir,
            self.projects_dir,
            self.runtime_dir,
            self.venv_dir,
        )


def ensure_directory(path: Path) -> None:
    if path.exists() and not path.is_dir():
        raise RuntimeLayoutError(f"expected directory but found file: {path}")
    path.mkdir(parents=True, exist_ok=True)
