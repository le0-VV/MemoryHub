"""Backup and restore primitives for MemoryHub runtime state."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, cast

from memoryhub.framework.errors import BackupError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.project_source import ProjectSourceLayout
from memoryhub.framework.registry import (
    MAIN_PROJECT_NAME,
    ProjectKind,
    ProjectRecord,
    ProjectRegistry,
    RegistryState,
    validate_project_name,
)
from memoryhub.framework.runtime import ensure_runtime
from memoryhub.sources.markdown.sync import (
    iter_markdown_files,
    safe_relative_markdown_path,
)

BACKUP_VERSION: Final = 1
MANIFEST_PATH: Final = "manifest.json"
CONFIG_SNAPSHOT_PATH: Final = "config.json"
RESTORED_PROJECTS_DIRNAME: Final = "restored-projects"


@dataclass(frozen=True, slots=True)
class BackupProject:
    name: str
    kind: ProjectKind
    original_source_path: Path
    original_registry_path: Path
    files: tuple[str, ...]

    @property
    def file_count(self) -> int:
        return len(self.files)

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "original_source_path": str(self.original_source_path),
            "original_registry_path": str(self.original_registry_path),
            "file_count": self.file_count,
            "files": list(self.files),
        }


@dataclass(frozen=True, slots=True)
class BackupManifest:
    created_at: str
    runtime_root: Path
    default_project: str
    projects: tuple[BackupProject, ...]

    @property
    def project_count(self) -> int:
        return len(self.projects)

    @property
    def file_count(self) -> int:
        return sum(project.file_count for project in self.projects)

    def to_json(self) -> dict[str, object]:
        return {
            "version": BACKUP_VERSION,
            "created_at": self.created_at,
            "runtime_root": str(self.runtime_root),
            "default_project": self.default_project,
            "project_count": self.project_count,
            "file_count": self.file_count,
            "projects": [project.to_json() for project in self.projects],
        }


@dataclass(frozen=True, slots=True)
class BackupCreateReport:
    archive_path: Path
    manifest: BackupManifest

    def to_json(self) -> dict[str, object]:
        return {
            "archive_path": str(self.archive_path),
            "manifest": self.manifest.to_json(),
        }


@dataclass(frozen=True, slots=True)
class BackupInspectReport:
    archive_path: Path
    manifest: BackupManifest

    def to_json(self) -> dict[str, object]:
        return {
            "archive_path": str(self.archive_path),
            "manifest": self.manifest.to_json(),
        }


@dataclass(frozen=True, slots=True)
class BackupRestoreReport:
    archive_path: Path
    runtime_root: Path
    project_count: int
    file_count: int

    def to_json(self) -> dict[str, object]:
        return {
            "archive_path": str(self.archive_path),
            "runtime_root": str(self.runtime_root),
            "project_count": self.project_count,
            "file_count": self.file_count,
        }


def create_backup(
    registry: ProjectRegistry,
    archive_path: str | Path,
    *,
    force: bool = False,
) -> BackupCreateReport:
    state = registry.ensure_initialized()
    archive = _prepare_archive_path(archive_path, force=force)
    manifest = BackupManifest(
        created_at=_utc_timestamp(),
        runtime_root=registry.layout.root,
        default_project=state.default_project,
        projects=_collect_projects(state),
    )

    mode: Literal["w", "x"] = "w" if force else "x"
    try:
        with zipfile.ZipFile(
            archive, mode, compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr(_zip_info(MANIFEST_PATH), _json_bytes(manifest.to_json()))
            zip_file.write(registry.layout.config_path, CONFIG_SNAPSHOT_PATH)
            for project in manifest.projects:
                for relative_path in project.files:
                    zip_file.write(
                        project.original_source_path / relative_path,
                        _project_archive_path(project.name, relative_path),
                    )
    except (FileExistsError, OSError, zipfile.BadZipFile) as error:
        raise BackupError(f"could not create backup archive: {error}") from error

    return BackupCreateReport(archive_path=archive, manifest=manifest)


def inspect_backup(archive_path: str | Path) -> BackupInspectReport:
    archive = _existing_archive_path(archive_path)
    return BackupInspectReport(
        archive_path=archive,
        manifest=_read_manifest(archive),
    )


def restore_backup(
    archive_path: str | Path,
    target_layout: RuntimeLayout,
) -> BackupRestoreReport:
    archive = _existing_archive_path(archive_path)
    manifest = _read_manifest(archive)
    _validate_restore_target(target_layout.root)
    ensure_runtime(target_layout)

    restored_records: dict[str, ProjectRecord] = {}
    with _open_archive(archive) as zip_file:
        for project in manifest.projects:
            source_root = _restore_source_root(target_layout, project)
            ProjectSourceLayout(source_root).ensure()
            _restore_project_files(zip_file, project, source_root)
            registry_path = _restore_registry_path(target_layout, project, source_root)
            restored_records[project.name] = ProjectRecord(
                name=project.name,
                source_path=source_root,
                registry_path=registry_path,
                kind=project.kind,
            )

    if MAIN_PROJECT_NAME not in restored_records:
        raise BackupError("backup manifest is missing the main project")
    if manifest.default_project not in restored_records:
        raise BackupError(f"default project is missing: {manifest.default_project}")

    ProjectRegistry(target_layout).save(
        RegistryState(
            default_project=manifest.default_project,
            projects=restored_records,
        )
    )
    return BackupRestoreReport(
        archive_path=archive,
        runtime_root=target_layout.root,
        project_count=manifest.project_count,
        file_count=manifest.file_count,
    )


def _collect_projects(state: RegistryState) -> tuple[BackupProject, ...]:
    ordered_names = (
        MAIN_PROJECT_NAME,
        *sorted(name for name in state.projects if name != MAIN_PROJECT_NAME),
    )
    projects: list[BackupProject] = []
    for name in ordered_names:
        record = state.projects[name]
        files = tuple(
            _safe_project_relative_path(path, record.source_path)
            for path in iter_markdown_files(record.source_path)
        )
        projects.append(
            BackupProject(
                name=record.name,
                kind=record.kind,
                original_source_path=record.source_path,
                original_registry_path=record.registry_path,
                files=files,
            )
        )
    return tuple(projects)


def _read_manifest(archive_path: Path) -> BackupManifest:
    try:
        with _open_archive(archive_path) as zip_file:
            raw_manifest = zip_file.read(MANIFEST_PATH)
    except KeyError as error:
        raise BackupError("backup archive is missing manifest.json") from error
    try:
        decoded = json.loads(raw_manifest.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BackupError(f"invalid backup manifest: {error}") from error
    return _manifest_from_json(decoded)


def _manifest_from_json(value: object) -> BackupManifest:
    raw_manifest = _expect_object(value, "manifest")
    version = _expect_int(raw_manifest.get("version"), "manifest.version")
    if version != BACKUP_VERSION:
        raise BackupError(f"unsupported backup version: {version}")
    projects_raw = _expect_list(raw_manifest.get("projects"), "manifest.projects")
    projects = tuple(
        _project_from_json(project, f"manifest.projects[{index}]")
        for index, project in enumerate(projects_raw)
    )
    return BackupManifest(
        created_at=_expect_str(raw_manifest.get("created_at"), "manifest.created_at"),
        runtime_root=Path(
            _expect_str(raw_manifest.get("runtime_root"), "manifest.runtime_root")
        ),
        default_project=validate_project_name(
            _expect_str(raw_manifest.get("default_project"), "manifest.default_project")
        ),
        projects=projects,
    )


def _project_from_json(value: object, label: str) -> BackupProject:
    raw_project = _expect_object(value, label)
    kind_value = _expect_str(raw_project.get("kind"), f"{label}.kind")
    try:
        kind = ProjectKind(kind_value)
    except ValueError as error:
        raise BackupError(
            f"unsupported project kind at {label}: {kind_value}"
        ) from error
    files = tuple(
        _safe_manifest_file_path(file_value, f"{label}.files[{index}]")
        for index, file_value in enumerate(
            _expect_list(raw_project.get("files"), f"{label}.files")
        )
    )
    return BackupProject(
        name=validate_project_name(
            _expect_str(raw_project.get("name"), f"{label}.name")
        ),
        kind=kind,
        original_source_path=Path(
            _expect_str(
                raw_project.get("original_source_path"),
                f"{label}.original_source_path",
            )
        ),
        original_registry_path=Path(
            _expect_str(
                raw_project.get("original_registry_path"),
                f"{label}.original_registry_path",
            )
        ),
        files=files,
    )


def _restore_project_files(
    zip_file: zipfile.ZipFile,
    project: BackupProject,
    source_root: Path,
) -> None:
    for relative_path in project.files:
        target_path = source_root / safe_relative_markdown_path(relative_path)
        archive_member = _project_archive_path(project.name, relative_path)
        try:
            data = zip_file.read(archive_member)
        except KeyError as error:
            raise BackupError(f"backup archive is missing {archive_member}") from error
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)


def _restore_registry_path(
    layout: RuntimeLayout,
    project: BackupProject,
    source_root: Path,
) -> Path:
    if project.name == MAIN_PROJECT_NAME:
        return layout.main_project_path
    registry_path = layout.projects_dir / project.name
    registry_path.symlink_to(source_root, target_is_directory=True)
    return registry_path


def _restore_source_root(layout: RuntimeLayout, project: BackupProject) -> Path:
    if project.name == MAIN_PROJECT_NAME:
        if project.kind is not ProjectKind.GLOBAL:
            raise BackupError("main project must be global")
        return layout.main_project_path
    return layout.runtime_dir / RESTORED_PROJECTS_DIRNAME / project.name


def _prepare_archive_path(path: str | Path, *, force: bool) -> Path:
    archive = Path(path).expanduser()
    if archive.exists() and not force:
        raise BackupError(f"backup archive already exists: {archive}")
    if archive.exists() and archive.is_dir():
        raise BackupError(f"backup archive path is a directory: {archive}")
    archive.parent.mkdir(parents=True, exist_ok=True)
    return archive


def _existing_archive_path(path: str | Path) -> Path:
    archive = Path(path).expanduser()
    if not archive.is_file():
        raise BackupError(f"backup archive does not exist: {archive}")
    return archive


def _validate_restore_target(root: Path) -> None:
    target = root.expanduser()
    if target.exists() and not target.is_dir():
        raise BackupError(f"restore target is not a directory: {target}")
    if target.is_dir() and any(target.iterdir()):
        raise BackupError(f"restore target must be empty: {target}")


def _safe_project_relative_path(path: Path, source_root: Path) -> str:
    relative_path = path.relative_to(source_root)
    return safe_relative_markdown_path(relative_path).as_posix()


def _safe_manifest_file_path(value: object, label: str) -> str:
    return safe_relative_markdown_path(_expect_str(value, label)).as_posix()


def _project_archive_path(project_name: str, relative_path: str) -> str:
    project = validate_project_name(project_name)
    safe_path = safe_relative_markdown_path(relative_path).as_posix()
    return f"projects/{project}/{safe_path}"


def _open_archive(path: Path) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise BackupError(f"could not read backup archive: {error}") from error


def _zip_info(filename: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename)
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def _json_bytes(payload: dict[str, object]) -> bytes:
    return f"{json.dumps(payload, indent=2, sort_keys=True)}\n".encode()


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _expect_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise BackupError(f"expected object at {label}")
    result: dict[str, object] = {}
    raw_object = cast(dict[object, object], value)
    for key, item in raw_object.items():
        if not isinstance(key, str):
            raise BackupError(f"expected string key at {label}")
        result[key] = item
    return result


def _expect_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise BackupError(f"expected list at {label}")
    return cast(list[object], value)


def _expect_str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise BackupError(f"expected string at {label}")
    return value


def _expect_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise BackupError(f"expected integer at {label}")
    return value
