"""Runtime doctor primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.project_source import ProjectSourceLayout


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    ok: bool
    path: Path
    message: str

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ok": self.ok,
            "path": str(self.path),
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class DoctorReport:
    runtime_root: Path
    ok: bool
    checks: tuple[DoctorCheck, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "runtime_root": str(self.runtime_root),
            "ok": self.ok,
            "checks": [check.to_json() for check in self.checks],
        }


def ensure_runtime(layout: RuntimeLayout) -> None:
    layout.ensure()
    ProjectSourceLayout.for_global(layout).ensure()


def inspect_runtime(layout: RuntimeLayout) -> DoctorReport:
    checks = tuple(_directory_check(path) for path in _doctor_directories(layout))
    return DoctorReport(
        runtime_root=layout.root,
        ok=all(check.ok for check in checks),
        checks=checks,
    )


def doctor(layout: RuntimeLayout) -> DoctorReport:
    ensure_runtime(layout)
    return inspect_runtime(layout)


def _doctor_directories(layout: RuntimeLayout) -> tuple[Path, ...]:
    return (*layout.required_directories, layout.main_project_path)


def _directory_check(path: Path) -> DoctorCheck:
    if path.is_dir():
        return DoctorCheck(
            name="directory",
            ok=True,
            path=path,
            message="exists",
        )
    if path.exists():
        return DoctorCheck(
            name="directory",
            ok=False,
            path=path,
            message="path exists but is not a directory",
        )
    return DoctorCheck(
        name="directory",
        ok=False,
        path=path,
        message="missing",
    )
