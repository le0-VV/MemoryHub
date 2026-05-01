"""JSON-backed project registry."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, cast

from memoryhub.framework.errors import (
    ProjectConflictError,
    ProjectNotFoundError,
    ProjectValidationError,
    RegistryError,
)
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.project_source import ProjectSourceLayout
from memoryhub.framework.runtime import DoctorCheck, ensure_runtime

CONFIG_VERSION: Final = 1
MAIN_PROJECT_NAME: Final = "main"
PROJECT_NAME_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SLUG_REPLACEMENT_PATTERN: Final = re.compile(r"[^a-z0-9._-]+")


class ProjectKind(StrEnum):
    GLOBAL = "global"
    REPOSITORY = "repository"


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    name: str
    source_path: Path
    registry_path: Path
    kind: ProjectKind

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source_path": str(self.source_path),
            "registry_path": str(self.registry_path),
            "kind": self.kind.value,
        }


@dataclass(frozen=True, slots=True)
class ProjectListItem:
    record: ProjectRecord
    is_default: bool

    def to_json(self) -> dict[str, object]:
        payload = self.record.to_json()
        payload["is_default"] = self.is_default
        return payload


@dataclass(slots=True)
class RegistryState:
    default_project: str
    projects: dict[str, ProjectRecord]

    def to_json(self) -> dict[str, object]:
        return {
            "version": CONFIG_VERSION,
            "default_project": self.default_project,
            "projects": {
                name: record.to_json() for name, record in sorted(self.projects.items())
            },
        }


class ProjectRegistry:
    def __init__(self, layout: RuntimeLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> RuntimeLayout:
        return self._layout

    def ensure_initialized(self) -> RegistryState:
        ensure_runtime(self._layout)
        if not self._layout.config_path.exists():
            state = self._initial_state()
            self.save(state)
            return state

        state = self.load()
        main_record = self._main_record()
        if state.projects.get(MAIN_PROJECT_NAME) != main_record:
            state.projects[MAIN_PROJECT_NAME] = main_record
            self.save(state)
        return state

    def load(self) -> RegistryState:
        try:
            raw_data = json.loads(self._layout.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RegistryError(f"invalid registry JSON: {error}") from error
        except OSError as error:
            raise RegistryError(f"could not read registry: {error}") from error

        root = _expect_object(raw_data, "config")
        version = _expect_int(root.get("version"), "version")
        if version != CONFIG_VERSION:
            raise RegistryError(f"unsupported registry version: {version}")

        default_project = validate_project_name(
            _expect_str(root.get("default_project"), "default_project")
        )
        projects_raw = _expect_object(root.get("projects"), "projects")
        projects: dict[str, ProjectRecord] = {}
        for name, value in projects_raw.items():
            project_name = validate_project_name(name)
            record = _project_record_from_json(value, f"projects.{project_name}")
            if record.name != project_name:
                raise RegistryError(
                    f"project key does not match record name: {project_name}"
                )
            projects[project_name] = record

        if MAIN_PROJECT_NAME not in projects:
            raise RegistryError("registry is missing main project")
        if default_project not in projects:
            raise RegistryError(f"default project does not exist: {default_project}")

        return RegistryState(default_project=default_project, projects=projects)

    def save(self, state: RegistryState) -> None:
        self._layout.ensure()
        payload = json.dumps(state.to_json(), indent=2, sort_keys=True)
        temp_path = self._layout.config_path.with_suffix(".json.tmp")
        try:
            temp_path.write_text(f"{payload}\n", encoding="utf-8")
            temp_path.replace(self._layout.config_path)
        except OSError as error:
            raise RegistryError(f"could not write registry: {error}") from error

    def add_project(
        self,
        repo_root: Path,
        *,
        name: str | None = None,
        create_source: bool = True,
        make_default: bool = False,
    ) -> ProjectRecord:
        state = self.ensure_initialized()
        project_name = (
            validate_project_name(name)
            if name is not None
            else slugify_project_name(repo_root.name)
        )
        if project_name == MAIN_PROJECT_NAME:
            raise ProjectValidationError("main is reserved for global context")
        if project_name in state.projects:
            raise ProjectConflictError(f"project already exists: {project_name}")

        repo_path = _existing_directory(repo_root, "repository root")
        source_layout = ProjectSourceLayout.for_repo(repo_path)
        if create_source:
            source_layout.ensure()
        else:
            source_layout.validate()

        source_path = source_layout.root
        registry_path = self._layout.projects_dir / project_name
        self._create_project_link(registry_path, source_path)

        record = ProjectRecord(
            name=project_name,
            source_path=source_path,
            registry_path=registry_path,
            kind=ProjectKind.REPOSITORY,
        )
        state.projects[project_name] = record
        if make_default:
            state.default_project = project_name
        self.save(state)
        return record

    def remove_project(self, name: str) -> ProjectRecord:
        project_name = validate_project_name(name)
        if project_name == MAIN_PROJECT_NAME:
            raise ProjectValidationError("main cannot be removed")

        state = self.ensure_initialized()
        record = state.projects.get(project_name)
        if record is None:
            raise ProjectNotFoundError(f"project does not exist: {project_name}")

        if record.registry_path.is_symlink():
            record.registry_path.unlink()
        elif record.registry_path.exists():
            raise ProjectConflictError(
                f"registry path is not a symlink: {record.registry_path}"
            )

        del state.projects[project_name]
        if state.default_project == project_name:
            state.default_project = MAIN_PROJECT_NAME
        self.save(state)
        return record

    def set_default(self, name: str) -> ProjectRecord:
        project_name = validate_project_name(name)
        state = self.ensure_initialized()
        record = state.projects.get(project_name)
        if record is None:
            raise ProjectNotFoundError(f"project does not exist: {project_name}")
        state.default_project = project_name
        self.save(state)
        return record

    def get_default(self) -> ProjectRecord:
        state = self.ensure_initialized()
        record = state.projects.get(state.default_project)
        if record is None:
            raise RegistryError(f"default project is missing: {state.default_project}")
        return record

    def get_project(self, name: str) -> ProjectRecord:
        project_name = validate_project_name(name)
        state = self.ensure_initialized()
        record = state.projects.get(project_name)
        if record is None:
            raise ProjectNotFoundError(f"project does not exist: {project_name}")
        return record

    def list_projects(self) -> tuple[ProjectListItem, ...]:
        state = self.ensure_initialized()
        ordered_names = sorted(
            name for name in state.projects if name != MAIN_PROJECT_NAME
        )
        names = (MAIN_PROJECT_NAME, *ordered_names)
        return tuple(
            ProjectListItem(
                record=state.projects[name],
                is_default=name == state.default_project,
            )
            for name in names
        )

    def resolve_by_cwd(self, cwd: Path) -> ProjectRecord:
        state = self.ensure_initialized()
        cwd_path = cwd.expanduser().resolve(strict=False)
        matches: list[tuple[int, ProjectRecord]] = []
        for record in state.projects.values():
            if record.kind is not ProjectKind.REPOSITORY:
                continue
            repo_root = _repo_root_for_source(record.source_path)
            if _is_relative_to(cwd_path, repo_root):
                matches.append((len(repo_root.parts), record))

        if matches:
            return max(matches, key=lambda match: match[0])[1]
        return self.get_default()

    def inspect_health(self) -> tuple[DoctorCheck, ...]:
        state = self.ensure_initialized()
        ordered_names = (
            MAIN_PROJECT_NAME,
            *sorted(name for name in state.projects if name != MAIN_PROJECT_NAME),
        )
        checks: list[DoctorCheck] = []
        for name in ordered_names:
            record = state.projects[name]
            checks.append(_project_source_check(record))
            checks.append(_project_registry_check(record))
        return tuple(checks)

    def _initial_state(self) -> RegistryState:
        return RegistryState(
            default_project=MAIN_PROJECT_NAME,
            projects={MAIN_PROJECT_NAME: self._main_record()},
        )

    def _main_record(self) -> ProjectRecord:
        return ProjectRecord(
            name=MAIN_PROJECT_NAME,
            source_path=self._layout.main_project_path,
            registry_path=self._layout.main_project_path,
            kind=ProjectKind.GLOBAL,
        )

    def _create_project_link(self, registry_path: Path, source_path: Path) -> None:
        self._layout.projects_dir.mkdir(parents=True, exist_ok=True)
        if registry_path.is_symlink():
            linked_path = _read_symlink_absolute(registry_path)
            if linked_path.resolve(strict=False) != source_path.resolve(strict=False):
                raise ProjectConflictError(
                    f"registry symlink points elsewhere: {registry_path}"
                )
            return
        if registry_path.exists():
            raise ProjectConflictError(f"registry path already exists: {registry_path}")
        registry_path.symlink_to(source_path, target_is_directory=True)


def validate_project_name(name: str) -> str:
    value = name.strip()
    if value == "":
        raise ProjectValidationError("project name cannot be empty")
    if not PROJECT_NAME_PATTERN.fullmatch(value):
        raise ProjectValidationError(
            "project name must start with a lowercase letter or digit and contain "
            "only lowercase letters, digits, dots, underscores, or hyphens"
        )
    if value in {".", ".."}:
        raise ProjectValidationError("project name cannot be a relative path marker")
    return value


def slugify_project_name(name: str) -> str:
    lowered = name.strip().lower()
    slug = SLUG_REPLACEMENT_PATTERN.sub("-", lowered).strip(".-_")
    return validate_project_name(slug)


def _existing_directory(path: Path, label: str) -> Path:
    candidate = path.expanduser()
    if not candidate.is_dir():
        raise ProjectValidationError(f"{label} must be an existing directory: {path}")
    return candidate.resolve(strict=True)


def _read_symlink_absolute(path: Path) -> Path:
    target = path.readlink()
    if target.is_absolute():
        return target
    return path.parent / target


def _repo_root_for_source(source_path: Path) -> Path:
    return source_path.parent.parent.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _project_source_check(record: ProjectRecord) -> DoctorCheck:
    if record.source_path.is_dir():
        return DoctorCheck(
            name="project_source",
            ok=True,
            path=record.source_path,
            message=f"{record.name} source exists",
        )
    if record.source_path.exists():
        return DoctorCheck(
            name="project_source",
            ok=False,
            path=record.source_path,
            message=f"{record.name} source path is not a directory",
        )
    return DoctorCheck(
        name="project_source",
        ok=False,
        path=record.source_path,
        message=f"{record.name} source is missing",
    )


def _project_registry_check(record: ProjectRecord) -> DoctorCheck:
    if record.kind is ProjectKind.GLOBAL:
        return _global_registry_check(record)
    return _repository_registry_check(record)


def _global_registry_check(record: ProjectRecord) -> DoctorCheck:
    if record.registry_path.is_dir():
        return DoctorCheck(
            name="project_registry",
            ok=True,
            path=record.registry_path,
            message=f"{record.name} registry path exists",
        )
    if record.registry_path.exists():
        return DoctorCheck(
            name="project_registry",
            ok=False,
            path=record.registry_path,
            message=f"{record.name} registry path is not a directory",
        )
    return DoctorCheck(
        name="project_registry",
        ok=False,
        path=record.registry_path,
        message=f"{record.name} registry path is missing",
    )


def _repository_registry_check(record: ProjectRecord) -> DoctorCheck:
    if not record.registry_path.is_symlink():
        if record.registry_path.exists():
            return DoctorCheck(
                name="project_registry",
                ok=False,
                path=record.registry_path,
                message=f"{record.name} registry path is not a symlink",
            )
        return DoctorCheck(
            name="project_registry",
            ok=False,
            path=record.registry_path,
            message=f"{record.name} registry symlink is missing",
        )

    linked_path = _read_symlink_absolute(record.registry_path)
    if linked_path.resolve(strict=False) == record.source_path.resolve(strict=False):
        return DoctorCheck(
            name="project_registry",
            ok=True,
            path=record.registry_path,
            message=f"{record.name} registry symlink points to source",
        )
    return DoctorCheck(
        name="project_registry",
        ok=False,
        path=record.registry_path,
        message=f"{record.name} registry symlink points to {linked_path}",
    )


def _expect_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RegistryError(f"expected object at {label}")
    result: dict[str, object] = {}
    raw_object = cast(dict[object, object], value)
    for key, item in raw_object.items():
        if not isinstance(key, str):
            raise RegistryError(f"expected string key at {label}")
        result[key] = item
    return result


def _expect_str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"expected string at {label}")
    return value


def _expect_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise RegistryError(f"expected integer at {label}")
    return value


def _project_record_from_json(value: object, label: str) -> ProjectRecord:
    raw_record = _expect_object(value, label)
    kind_value = _expect_str(raw_record.get("kind"), f"{label}.kind")
    try:
        kind = ProjectKind(kind_value)
    except ValueError as error:
        raise RegistryError(
            f"unsupported project kind at {label}: {kind_value}"
        ) from error

    return ProjectRecord(
        name=validate_project_name(
            _expect_str(raw_record.get("name"), f"{label}.name")
        ),
        source_path=Path(
            _expect_str(raw_record.get("source_path"), f"{label}.source_path")
        ),
        registry_path=Path(
            _expect_str(raw_record.get("registry_path"), f"{label}.registry_path")
        ),
        kind=kind,
    )
