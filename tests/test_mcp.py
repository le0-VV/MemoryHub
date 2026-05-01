from __future__ import annotations

from pathlib import Path
from typing import cast

from memoryhub.adapters.mcp.server import PROJECT_LIST_TOOL, handle_request
from memoryhub.framework.layout import RuntimeLayout
from memoryhub.framework.registry import ProjectRegistry


def test_mcp_lists_project_tool(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))

    response = handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        registry,
    )
    result = _response_result(response)
    tools = _expect_list(result["tools"])
    first_tool = _expect_object(tools[0])

    assert first_tool["name"] == PROJECT_LIST_TOOL


def test_mcp_project_list_tool_returns_registered_projects(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    registry.add_project(repo_root, name="demo")

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {"name": PROJECT_LIST_TOOL, "arguments": {}},
        },
        registry,
    )

    result = _response_result(response)
    structured_content = _expect_object(result["structuredContent"])
    projects = _expect_list(structured_content["projects"])
    names = [project["name"] for project in _object_list(projects)]

    assert names == ["main", "demo"]


def _response_result(response: dict[str, object] | None) -> dict[str, object]:
    assert response is not None
    assert "error" not in response
    return _expect_object(response["result"])


def _expect_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _expect_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def _object_list(values: list[object]) -> list[dict[str, object]]:
    return [_expect_object(value) for value in values]
