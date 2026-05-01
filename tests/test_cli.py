from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import cast

from memoryhub.adapters.cli.main import run


def test_cli_doctor_outputs_json(tmp_path: Path) -> None:
    code, stdout, stderr = _run_cli(["doctor", "--json"], tmp_path / "hub", tmp_path)

    payload = _parse_object(stdout)
    assert code == 0
    assert stderr == ""
    assert payload["ok"] is True
    assert payload["runtime_root"] == str(tmp_path / "hub")


def test_cli_doctor_fails_on_missing_project_registry_symlink(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run_cli(
        ["project", "add", str(repo_root), "--name", "demo", "--json"],
        config_dir,
        tmp_path,
    )
    (config_dir / "projects" / "demo").unlink()

    code, stdout, stderr = _run_cli(["doctor", "--json"], config_dir, tmp_path)
    payload = _parse_object(stdout)
    checks = _object_list(_expect_list(payload["checks"]))
    failing_project_checks = [
        check for check in checks if check["name"] == "project_registry"
    ]

    assert code == 1
    assert stderr == ""
    assert payload["ok"] is False
    assert failing_project_checks[-1]["ok"] is False
    assert failing_project_checks[-1]["message"] == "demo registry symlink is missing"


def test_cli_install_outputs_json_and_creates_launcher(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"

    code, stdout, stderr = _run_cli(["install", "--json"], config_dir, tmp_path)

    payload = _parse_object(stdout)
    install = _expect_object(payload["install"])
    bin_path = Path(_expect_str(install["bin_path"]))

    assert code == 0
    assert stderr == ""
    assert install["runtime_root"] == str(config_dir)
    assert install["launcher_action"] == "created"
    assert bin_path.is_file()
    assert "memoryhub.adapters.cli" in bin_path.read_text(encoding="utf-8")


def test_cli_install_repair_outputs_json_and_repairs_launcher(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    install_code, install_stdout, _ = _run_cli(
        ["install", "--json"],
        config_dir,
        tmp_path,
    )
    install_payload = _parse_object(install_stdout)
    install = _expect_object(install_payload["install"])
    bin_path = Path(_expect_str(install["bin_path"]))
    bin_path.write_text("damaged\n", encoding="utf-8")

    repair_code, repair_stdout, repair_stderr = _run_cli(
        ["install", "--repair", "--json"],
        config_dir,
        tmp_path,
    )
    repair_payload = _parse_object(repair_stdout)
    repair = _expect_object(repair_payload["install"])

    assert install_code == 0
    assert repair_code == 0
    assert repair_stderr == ""
    assert repair["launcher_action"] == "repaired"
    assert "memoryhub.adapters.cli" in bin_path.read_text(encoding="utf-8")


def test_cli_project_add_list_default_and_remove_json(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    add_code, add_stdout, add_stderr = _run_cli(
        ["project", "add", str(repo_root), "--name", "demo", "--json"],
        config_dir,
        tmp_path,
    )
    add_payload = _parse_object(add_stdout)
    add_project = _expect_object(add_payload["project"])

    assert add_code == 0
    assert add_stderr == ""
    assert add_project["name"] == "demo"

    list_code, list_stdout, _ = _run_cli(
        ["project", "list", "--json"],
        config_dir,
        tmp_path,
    )
    list_payload = _parse_object(list_stdout)
    projects = _expect_list(list_payload["projects"])

    assert list_code == 0
    assert [project["name"] for project in _object_list(projects)] == ["main", "demo"]

    default_code, default_stdout, _ = _run_cli(
        ["project", "default", "demo", "--json"],
        config_dir,
        tmp_path,
    )
    default_payload = _parse_object(default_stdout)
    default_project = _expect_object(default_payload["project"])

    assert default_code == 0
    assert default_project["name"] == "demo"

    remove_code, remove_stdout, _ = _run_cli(
        ["project", "remove", "demo", "--json"],
        config_dir,
        tmp_path,
    )
    remove_payload = _parse_object(remove_stdout)
    removed_project = _expect_object(remove_payload["project"])

    assert remove_code == 0
    assert removed_project["name"] == "demo"


def test_cli_write_reindex_search_and_read_json(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run_cli(
        ["project", "add", str(repo_root), "--name", "demo", "--json"],
        config_dir,
        tmp_path,
    )

    write_code, write_stdout, write_stderr = _run_cli(
        [
            "write",
            "demo",
            "agent/memories/patterns/cache.md",
            "--title",
            "Cache Pattern",
            "--body",
            "Use local caches for repeated context lookups.",
            "--kind",
            "pattern",
            "--tag",
            "cache",
            "--json",
        ],
        config_dir,
        tmp_path,
    )
    write_payload = _parse_object(write_stdout)
    written_document = _expect_object(write_payload["document"])

    assert write_code == 0
    assert write_stderr == ""
    assert written_document["title"] == "Cache Pattern"
    assert written_document["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )

    reindex_code, reindex_stdout, _ = _run_cli(
        ["reindex", "--json"],
        config_dir,
        tmp_path,
    )
    reindex_payload = _parse_object(reindex_stdout)
    reindex_report = _expect_object(reindex_payload["reindex"])

    assert reindex_code == 0
    assert reindex_report["document_count"] == 1

    search_code, search_stdout, _ = _run_cli(
        ["search", "cache", "--json"],
        config_dir,
        tmp_path,
    )
    search_payload = _parse_object(search_stdout)
    results = _object_list(_expect_list(search_payload["results"]))

    assert search_code == 0
    assert results[0]["relative_path"] == "agent/memories/patterns/cache.md"
    assert results[0]["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )

    read_code, read_stdout, _ = _run_cli(
        ["read", "demo", "agent/memories/patterns/cache.md", "--json"],
        config_dir,
        tmp_path,
    )
    read_payload = _parse_object(read_stdout)
    read_document = _expect_object(read_payload["document"])

    assert read_code == 0
    assert read_document["body"] == "Use local caches for repeated context lookups."
    assert read_document["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )


def test_cli_search_filters_and_context_json(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run_cli(
        ["project", "add", str(repo_root), "--name", "demo", "--json"],
        config_dir,
        tmp_path,
    )
    _run_cli(
        [
            "write",
            "demo",
            "agent/memories/patterns/cache.md",
            "--title",
            "Cache Pattern",
            "--body",
            "Context lookup should prefer explicit caches.",
            "--kind",
            "pattern",
            "--tag",
            "cache",
            "--json",
        ],
        config_dir,
        tmp_path,
    )
    _run_cli(
        [
            "write",
            "demo",
            "user/memories/preferences/runtime.md",
            "--title",
            "Runtime Preference",
            "--body",
            "Context files should remain in project repositories.",
            "--kind",
            "preference",
            "--tag",
            "runtime",
            "--json",
        ],
        config_dir,
        tmp_path,
    )

    search_code, search_stdout, _ = _run_cli(
        [
            "search",
            "context",
            "--kind",
            "preference",
            "--tag",
            "runtime",
            "--path-prefix",
            "user/",
            "--json",
        ],
        config_dir,
        tmp_path,
    )
    search_payload = _parse_object(search_stdout)
    results = _object_list(_expect_list(search_payload["results"]))

    assert search_code == 0
    assert [result["title"] for result in results] == ["Runtime Preference"]

    context_code, context_stdout, _ = _run_cli(
        ["context", "context", "--tag", "cache", "--json"],
        config_dir,
        tmp_path,
    )
    context_payload = _parse_object(context_stdout)
    context = _expect_object(context_payload["context"])
    documents = _object_list(_expect_list(context["documents"]))

    assert context_code == 0
    assert context["document_count"] == 1
    assert documents[0]["title"] == "Cache Pattern"
    assert documents[0]["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )
    assert "## Cache Pattern" in _expect_str(context["markdown"])
    assert (
        "- uri: openviking://project/demo/agent/memories/patterns/cache.md"
        in _expect_str(context["markdown"])
    )


def test_cli_backup_create_inspect_restore_and_read_json(tmp_path: Path) -> None:
    config_dir = tmp_path / "hub"
    repo_root = tmp_path / "repo"
    archive_path = tmp_path / "memoryhub.zip"
    restored_config_dir = tmp_path / "restored-hub"
    repo_root.mkdir()
    _run_cli(
        ["project", "add", str(repo_root), "--name", "demo", "--default", "--json"],
        config_dir,
        tmp_path,
    )
    _run_cli(
        [
            "write",
            "demo",
            "agent/memories/patterns/cache.md",
            "--title",
            "Cache Pattern",
            "--body",
            "Backups include repo-local Markdown.",
            "--kind",
            "pattern",
            "--tag",
            "cache",
            "--json",
        ],
        config_dir,
        tmp_path,
    )

    create_code, create_stdout, create_stderr = _run_cli(
        ["backup", "create", str(archive_path), "--json"],
        config_dir,
        tmp_path,
    )
    create_payload = _parse_object(create_stdout)
    create_backup_payload = _expect_object(create_payload["backup"])
    create_manifest = _expect_object(create_backup_payload["manifest"])

    assert create_code == 0
    assert create_stderr == ""
    assert create_backup_payload["archive_path"] == str(archive_path)
    assert create_manifest["project_count"] == 2
    assert create_manifest["file_count"] == 1

    inspect_code, inspect_stdout, _ = _run_cli(
        ["backup", "inspect", str(archive_path), "--json"],
        config_dir,
        tmp_path,
    )
    inspect_payload = _parse_object(inspect_stdout)
    inspect_backup_payload = _expect_object(inspect_payload["backup"])
    inspect_manifest = _expect_object(inspect_backup_payload["manifest"])

    assert inspect_code == 0
    assert inspect_manifest["default_project"] == "demo"

    restore_code, restore_stdout, _ = _run_cli(
        ["backup", "restore", str(archive_path), "--json"],
        restored_config_dir,
        tmp_path,
    )
    restore_payload = _parse_object(restore_stdout)
    restore_backup_payload = _expect_object(restore_payload["backup"])

    assert restore_code == 0
    assert restore_backup_payload["runtime_root"] == str(restored_config_dir)
    assert restore_backup_payload["project_count"] == 2
    assert restore_backup_payload["file_count"] == 1

    read_code, read_stdout, _ = _run_cli(
        ["read", "demo", "agent/memories/patterns/cache.md", "--json"],
        restored_config_dir,
        tmp_path,
    )
    read_payload = _parse_object(read_stdout)
    read_document = _expect_object(read_payload["document"])

    assert read_code == 0
    assert read_document["body"] == "Backups include repo-local Markdown."


def _run_cli(
    args: list[str],
    config_dir: Path,
    cwd: Path,
) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    code = run(
        ["--config-dir", str(config_dir), *args],
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def _parse_object(text: str) -> dict[str, object]:
    value = json.loads(text)
    return _expect_object(value)


def _expect_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _expect_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def _expect_str(value: object) -> str:
    assert isinstance(value, str)
    return value


def _object_list(values: list[object]) -> list[dict[str, object]]:
    return [_expect_object(value) for value in values]
