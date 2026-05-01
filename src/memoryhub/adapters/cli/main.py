"""Command line adapter."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO, cast

from memoryhub.adapters.mcp.server import run_stdio
from memoryhub.framework.backup import create_backup, inspect_backup, restore_backup
from memoryhub.framework.errors import MemoryHubError
from memoryhub.framework.install import InstallReport, install_runtime
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.library import MemoryHubLibrary
from memoryhub.framework.registry import (
    ProjectListItem,
    ProjectRecord,
    ProjectRegistry,
)
from memoryhub.framework.runtime import doctor
from memoryhub.openviking.resources import resource_descriptor, resource_from_document
from memoryhub.sources.markdown.schema import MarkdownDocument
from memoryhub.storage.sqlite.models import SearchResult


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
        if command == "install":
            return _install(args, layout, out)
        if command == "doctor":
            return _doctor(args, registry, out)
        if command == "project":
            return _project(args, registry, cwd, out)
        if command == "reindex":
            return _reindex(args, registry, out)
        if command == "backup":
            return _backup(args, registry, cwd, out)
        if command == "search":
            return _search(args, registry, out)
        if command == "context":
            return _context(args, registry, out)
        if command == "read":
            return _read(args, registry, out)
        if command == "write":
            return _write(args, registry, out)
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

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--repair", action="store_true")
    install_parser.add_argument("--update", action="store_true")
    install_parser.add_argument("--json", action="store_true")

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

    reindex_parser = subparsers.add_parser("reindex")
    reindex_parser.add_argument("--json", action="store_true")

    backup_parser = subparsers.add_parser("backup")
    backup_subparsers = backup_parser.add_subparsers(
        dest="backup_command",
        required=True,
    )

    backup_create_parser = backup_subparsers.add_parser("create")
    backup_create_parser.add_argument("path")
    backup_create_parser.add_argument("--force", action="store_true")
    backup_create_parser.add_argument("--json", action="store_true")

    backup_inspect_parser = backup_subparsers.add_parser("inspect")
    backup_inspect_parser.add_argument("path")
    backup_inspect_parser.add_argument("--json", action="store_true")

    backup_restore_parser = backup_subparsers.add_parser("restore")
    backup_restore_parser.add_argument("path")
    backup_restore_parser.add_argument("--json", action="store_true")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--project")
    search_parser.add_argument("--kind")
    search_parser.add_argument("--tag")
    search_parser.add_argument("--path-prefix")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--json", action="store_true")

    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("query")
    context_parser.add_argument("--project")
    context_parser.add_argument("--kind")
    context_parser.add_argument("--tag")
    context_parser.add_argument("--path-prefix")
    context_parser.add_argument("--limit", type=int, default=5)
    context_parser.add_argument("--json", action="store_true")

    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("project")
    read_parser.add_argument("path")
    read_parser.add_argument("--json", action="store_true")

    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("project")
    write_parser.add_argument("path")
    write_parser.add_argument("--title", required=True)
    write_parser.add_argument("--body", required=True)
    write_parser.add_argument("--kind", default="memory")
    write_parser.add_argument("--tag", action="append", dest="tags")
    write_parser.add_argument("--json", action="store_true")

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


def _install(
    args: argparse.Namespace,
    layout: RuntimeLayout,
    stdout: TextIO,
) -> int:
    report = install_runtime(
        layout,
        force=cast(bool, args.force),
        repair=cast(bool, args.repair),
        update=cast(bool, args.update),
    )
    if cast(bool, args.json):
        _write_json(_install_payload(report), stdout)
    else:
        stdout.write(f"Installed MemoryHub runtime at {report.runtime_root}\n")
        stdout.write(f"Launcher: {report.bin_path}\n")
        stdout.write(f"Launcher action: {report.launcher_action}\n")
    return 0


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


def _reindex(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    report = MemoryHubLibrary(registry).reindex()
    if cast(bool, args.json):
        _write_json({"reindex": report.to_json()}, stdout)
    else:
        stdout.write(
            f"Indexed {report.document_count} documents "
            f"across {report.project_count} projects.\n"
        )
    return 0


def _backup(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    cwd: Path | None,
    stdout: TextIO,
) -> int:
    backup_command = cast(str, args.backup_command)
    archive_path = _resolve_cli_path(cast(str, args.path), cwd)
    if backup_command == "create":
        report = create_backup(
            registry,
            archive_path,
            force=cast(bool, args.force),
        )
        if cast(bool, args.json):
            _write_json({"backup": report.to_json()}, stdout)
        else:
            stdout.write(f"Created MemoryHub backup: {report.archive_path}\n")
        return 0

    if backup_command == "inspect":
        report = inspect_backup(archive_path)
        if cast(bool, args.json):
            _write_json({"backup": report.to_json()}, stdout)
        else:
            stdout.write(f"MemoryHub backup: {report.archive_path}\n")
            stdout.write(f"Projects: {report.manifest.project_count}\n")
            stdout.write(f"Markdown files: {report.manifest.file_count}\n")
        return 0

    if backup_command == "restore":
        report = restore_backup(archive_path, registry.layout)
        if cast(bool, args.json):
            _write_json({"backup": report.to_json()}, stdout)
        else:
            stdout.write(f"Restored MemoryHub runtime: {report.runtime_root}\n")
            stdout.write(f"Projects: {report.project_count}\n")
            stdout.write(f"Markdown files: {report.file_count}\n")
        return 0

    raise MemoryHubError(f"unsupported backup command: {backup_command}")


def _search(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    results = MemoryHubLibrary(registry).search(
        cast(str, args.query),
        project_name=cast(str | None, args.project),
        kind=cast(str | None, args.kind),
        tag=cast(str | None, args.tag),
        path_prefix=cast(str | None, args.path_prefix),
        limit=cast(int, args.limit),
    )
    if cast(bool, args.json):
        _write_json(_search_payload(results), stdout)
        return 0
    for result in results:
        stdout.write(
            f"{result.project_name}:{result.relative_path}\t"
            f"{result.title}\t{result.snippet}\n"
        )
    return 0


def _context(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    bundle = MemoryHubLibrary(registry).build_context(
        cast(str, args.query),
        project_name=cast(str | None, args.project),
        kind=cast(str | None, args.kind),
        tag=cast(str | None, args.tag),
        path_prefix=cast(str | None, args.path_prefix),
        limit=cast(int, args.limit),
    )
    if cast(bool, args.json):
        _write_json({"context": bundle.to_json()}, stdout)
    else:
        stdout.write(bundle.to_markdown())
    return 0


def _read(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    document = MemoryHubLibrary(registry).read_document(
        cast(str, args.project),
        cast(str, args.path),
    )
    if cast(bool, args.json):
        _write_json(
            _document_payload(
                project_name=cast(str, args.project),
                relative_path=cast(str, args.path),
                document=document,
            ),
            stdout,
        )
    else:
        stdout.write(document.body)
    return 0


def _write(
    args: argparse.Namespace,
    registry: ProjectRegistry,
    stdout: TextIO,
) -> int:
    tags = tuple(cast(list[str] | None, args.tags) or [])
    library = MemoryHubLibrary(registry)
    document = library.write_document(
        cast(str, args.project),
        cast(str, args.path),
        title=cast(str, args.title),
        body=cast(str, args.body),
        kind=cast(str, args.kind),
        tags=tags,
    )
    library.reindex()
    return _document_result(
        document,
        cast(bool, args.json),
        stdout,
        project_name=cast(str, args.project),
        relative_path=cast(str, args.path),
    )


def _project_list_payload(projects: tuple[ProjectListItem, ...]) -> dict[str, object]:
    return {"projects": [project.to_json() for project in projects]}


def _search_payload(results: tuple[SearchResult, ...]) -> dict[str, object]:
    return {"results": [_search_result_payload(result) for result in results]}


def _search_result_payload(result: SearchResult) -> dict[str, object]:
    payload = result.to_json()
    resource = resource_descriptor(
        project_name=result.project_name,
        relative_path=result.relative_path,
        title=result.title,
        kind=result.kind,
        tags=result.tags,
    )
    payload["uri"] = resource.uri
    payload["resource"] = resource.to_json()
    return payload


def _document_result(
    document: MarkdownDocument,
    as_json: bool,
    stdout: TextIO,
    *,
    project_name: str,
    relative_path: str,
) -> int:
    if as_json:
        _write_json(
            _document_payload(
                project_name=project_name,
                relative_path=relative_path,
                document=document,
            ),
            stdout,
        )
    else:
        stdout.write(f"{document.title}\n")
    return 0


def _document_payload(
    *,
    project_name: str,
    relative_path: str,
    document: MarkdownDocument,
) -> dict[str, object]:
    resource = resource_from_document(
        project_name=project_name,
        relative_path=relative_path,
        document=document,
    )
    payload = document.to_json()
    payload["uri"] = resource.uri
    payload["resource"] = resource.to_json()
    return {"document": payload, "resource": resource.to_json()}


def _install_payload(report: InstallReport) -> dict[str, object]:
    return {"install": report.to_json()}


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
