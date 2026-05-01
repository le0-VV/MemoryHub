from __future__ import annotations

from pathlib import Path
from typing import cast

from memoryhub.adapters.mcp.server import (
    CONTEXT_TOOL,
    PROJECT_LIST_TOOL,
    READ_TOOL,
    SEARCH_TOOL,
    STATUS_TOOL,
    WRITE_TOOL,
    handle_request,
)
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


def test_mcp_status_write_search_and_read_tools(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    registry.add_project(repo_root, name="demo")

    status_response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": "status",
            "method": "tools/call",
            "params": {"name": STATUS_TOOL, "arguments": {}},
        },
        registry,
    )
    status_result = _response_result(status_response)
    status_content = _expect_object(status_result["structuredContent"])

    assert _expect_object(status_content["status"])["ok"] is True

    write_response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": "write",
            "method": "tools/call",
            "params": {
                "name": WRITE_TOOL,
                "arguments": {
                    "project": "demo",
                    "path": "agent/memories/patterns/cache.md",
                    "title": "Cache Pattern",
                    "body": "Use local caches for repeated context lookups.",
                    "kind": "pattern",
                    "tags": ["cache"],
                },
            },
        },
        registry,
    )
    write_result = _response_result(write_response)
    write_content = _expect_object(write_result["structuredContent"])
    written_document = _expect_object(write_content["document"])

    assert written_document["title"] == "Cache Pattern"
    assert written_document["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )

    search_response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": "search",
            "method": "tools/call",
            "params": {"name": SEARCH_TOOL, "arguments": {"query": "cache"}},
        },
        registry,
    )
    search_result = _response_result(search_response)
    search_content = _expect_object(search_result["structuredContent"])
    results = _object_list(_expect_list(search_content["results"]))

    assert results[0]["project_name"] == "demo"
    assert results[0]["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )

    read_response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": "read",
            "method": "tools/call",
            "params": {
                "name": READ_TOOL,
                "arguments": {
                    "project": "demo",
                    "path": "agent/memories/patterns/cache.md",
                },
            },
        },
        registry,
    )
    read_result = _response_result(read_response)
    read_content = _expect_object(read_result["structuredContent"])
    read_document = _expect_object(read_content["document"])

    assert read_document["body"] == "Use local caches for repeated context lookups."
    assert read_document["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )


def test_mcp_status_fails_on_missing_project_registry_symlink(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    record = registry.add_project(repo_root, name="demo")
    record.registry_path.unlink()

    status_content = _call_tool(registry, STATUS_TOOL, {})
    status = _expect_object(status_content["status"])
    checks = _object_list(_expect_list(status["checks"]))
    project_registry_checks = [
        check for check in checks if check["name"] == "project_registry"
    ]

    assert status["ok"] is False
    assert project_registry_checks[-1]["ok"] is False
    assert project_registry_checks[-1]["message"] == "demo registry symlink is missing"


def test_mcp_search_filters_and_context_tool(tmp_path: Path) -> None:
    registry = ProjectRegistry(RuntimeLayout.from_root(tmp_path / "hub"))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    registry.add_project(repo_root, name="demo")
    _call_tool(
        registry,
        WRITE_TOOL,
        {
            "project": "demo",
            "path": "agent/memories/patterns/cache.md",
            "title": "Cache Pattern",
            "body": "Context lookup should prefer explicit caches.",
            "kind": "pattern",
            "tags": ["cache"],
        },
    )
    _call_tool(
        registry,
        WRITE_TOOL,
        {
            "project": "demo",
            "path": "user/memories/preferences/runtime.md",
            "title": "Runtime Preference",
            "body": "Context files should remain in project repositories.",
            "kind": "preference",
            "tags": ["runtime"],
        },
    )

    search_content = _call_tool(
        registry,
        SEARCH_TOOL,
        {
            "query": "context",
            "kind": "preference",
            "tag": "runtime",
            "path_prefix": "user/",
        },
    )
    results = _object_list(_expect_list(search_content["results"]))

    assert [result["title"] for result in results] == ["Runtime Preference"]

    context_content = _call_tool(
        registry,
        CONTEXT_TOOL,
        {"query": "context", "tag": "cache"},
    )
    context = _expect_object(context_content["context"])
    documents = _object_list(_expect_list(context["documents"]))

    assert context["document_count"] == 1
    assert documents[0]["title"] == "Cache Pattern"
    assert documents[0]["uri"] == (
        "openviking://project/demo/agent/memories/patterns/cache.md"
    )
    assert "## Cache Pattern" in _expect_str(context["markdown"])


def _response_result(response: dict[str, object] | None) -> dict[str, object]:
    assert response is not None
    assert "error" not in response
    return _expect_object(response["result"])


def _call_tool(
    registry: ProjectRegistry,
    name: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": name,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        registry,
    )
    result = _response_result(response)
    return _expect_object(result["structuredContent"])


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
