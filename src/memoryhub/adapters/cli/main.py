"""Command line adapter."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO, cast

from memoryhub.adapters.mcp.server import run_stdio
from memoryhub.framework.errors import MemoryHubError
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.registry import ProjectListItem, ProjectRecord, ProjectRegistry
from memoryhub.framework.runtime import doctor


def main() -> int:
    return run()


def run(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = sys.stdout if stdout is None else stdout
    err = sys.stderr if stderr is None else stderr
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return _system_exit_code(error)

    layout = _layout_from_args(args, env)
    registry = ProjectRegistry(layout)

    try:
        command = cast(str, args.command)
        if command == "doctor":
            return _doctor(args, registry, out)
        if command == "project":
            return _project(args, registry, cwd, out)
        if command == "mcp":
            run_stdio(registry=registry)
            return 0
    except MemoryHubError as error:
        err.write(f"memoryhub: {error}\n")
        return 1

    err.write("memoryhub: unsupported command\n")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memoryhub")
    parser.add_argument(
        "--config-dir",
        help="override MEMORYHUB_CONFIG_DIR for this command",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--json", action="store_true")

    project_parser = subparsers.add_parser("project")
    project_subparsers = project_parser.add_subparsers(
        dest="project_command",
        required=True,
    )

    add_parser = project_subparsers.add_parser("add")
    add_parser.add_argument("path", nargs="?", default=".")
    add_parser.add_argument("--name")
    add_parser.add_argument("--default", action="store_true", dest="make_default")
    add_parser.add_argument("--json", action="store_true")

    list_parser = project_subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true")

    remove_parser = project_subparsers.add_parser("remove")
    remove_parser.add_argument("name")
    remove_parser.add_argument("--json", action="store_true")

    default_parser = project_subparsers.add_parser("default")
    default_parser.add_argument("name", nargs="?")
    default_parser.add_argument("--json", action="store_true")

    subparsers.add_parser("mcp")
    return parser


def _layout_from_args(
    args: argparse.Namespace,
    env: Mapping[str, str] | None,
) -> RuntimeLayout:
    config_dir = cast(str | None, args.config_dir)
    if config_dir is not None:
        return RuntimeLayout.from_root(config_dir)
    return RuntimeLayout.from_env(env)


def _doctor(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    registry.ensure_initialized()
    report = doctor(registry.layout)
    if cast(bool, args.json):
        _write_json(report.to_json(), stdout)
        return 0

    status = "ok" if report.ok else "failed"
    stdout.write(f"MemoryHub runtime: {status}\n")
    stdout.write(f"Runtime root: {report.runtime_root}\n")
    for check in report.checks:
        marker = "ok" if check.ok else "fail"
        stdout.write(f"- {marker}: {check.path} ({check.message})\n")
    return 0 if report.ok else 1


def _project(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    cwd: Path | None,
    stdout: TextIO,
) -> int:
    project_command = cast(str, args.project_command)
    if project_command == "add":
        repo_path = _resolve_cli_path(cast(str, args.path), cwd)
        record = registry.add_project(
            repo_path,
            name=cast(str | None, args.name),
            make_default=cast(bool, args.make_default),
        )
        return _project_result(record, cast(bool, args.json), stdout)

    if project_command == "list":
        projects = registry.list_projects()
        if cast(bool, args.json):
            _write_json(_project_list_payload(projects), stdout)
            return 0
        for item in projects:
            marker = "*" if item.is_default else " "
            stdout.write(f"{marker} {item.record.name}\t{item.record.source_path}\n")
        return 0

    if project_command == "remove":
        record = registry.remove_project(cast(str, args.name))
        return _project_result(record, cast(bool, args.json), stdout)

    if project_command == "default":
        name = cast(str | None, args.name)
        record = registry.get_default() if name is None else registry.set_default(name)
        return _project_result(record, cast(bool, args.json), stdout)

    raise MemoryHubError(f"unsupported project command: {project_command}")


def _project_result(record: ProjectRecord, as_json: bool, stdout: TextIO) -> int:
    if as_json:
        _write_json({"project": record.to_json()}, stdout)
    else:
        stdout.write(f"{record.name}\t{record.source_path}\n")
    return 0


def _project_list_payload(projects: tuple[ProjectListItem, ...]) -> dict[str, object]:
    return {"projects": [project.to_json() for project in projects]}


def _resolve_cli_path(value: str, cwd: Path | None) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    base = Path.cwd() if cwd is None else cwd
    return base / path


def _write_json(payload: dict[str, object], stdout: TextIO) -> None:
    json.dump(payload, stdout, indent=2, sort_keys=True)
    stdout.write("\n")


def _system_exit_code(error: SystemExit) -> int:
    code = error.code
    if isinstance(code, int):
        return code
    return 1
