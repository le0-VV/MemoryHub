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


def _object_list(values: list[object]) -> list[dict[str, object]]:
    return [_expect_object(value) for value in values]
