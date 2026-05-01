"""Minimal stdio MCP adapter."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import TextIO, cast

from memoryhub import __version__
from memoryhub.framework.errors import MemoryHubError
from memoryhub.framework.library import MemoryHubLibrary
from memoryhub.framework.registry import ProjectRegistry
from memoryhub.framework.runtime import doctor

PROTOCOL_VERSION = "2025-06-18"
PROJECT_LIST_TOOL = "project_list"
STATUS_TOOL = "status"
SEARCH_TOOL = "search"
CONTEXT_TOOL = "context"
READ_TOOL = "read"
WRITE_TOOL = "write"


def run_stdio(
    *,
    registry: ProjectRegistry,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> None:
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    for line in input_stream:
        if line.strip() == "":
            continue
        response = handle_json_line(line, registry)
        if response is None:
            continue
        json.dump(response, output_stream, sort_keys=True)
        output_stream.write("\n")
        output_stream.flush()


def handle_json_line(line: str, registry: ProjectRegistry) -> dict[str, object] | None:
    try:
        raw_message = json.loads(line)
    except json.JSONDecodeError as error:
        return _error_response(None, -32700, f"parse error: {error.msg}")
    if not isinstance(raw_message, dict):
        return _error_response(None, -32600, "request must be a JSON object")
    return handle_request(
        _string_key_mapping(cast(dict[object, object], raw_message)),
        registry,
    )


def handle_request(
    message: Mapping[str, object],
    registry: ProjectRegistry,
) -> dict[str, object] | None:
    request_id = _json_rpc_id(message.get("id"))
    method_value = message.get("method")
    if not isinstance(method_value, str):
        return _error_response(request_id, -32600, "request method must be a string")

    try:
        if method_value == "notifications/initialized":
            return None
        if method_value == "initialize":
            return _success_response(request_id, _initialize_result())
        if method_value == "tools/list":
            return _success_response(request_id, _tools_list_result())
        if method_value == "tools/call":
            return _success_response(
                request_id,
                _tools_call_result(message.get("params"), registry),
            )
    except MemoryHubError as error:
        return _error_response(request_id, -32000, str(error))

    return _error_response(request_id, -32601, f"unknown method: {method_value}")


def _initialize_result() -> dict[str, object]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "memoryhub", "version": __version__},
    }


def _tools_list_result() -> dict[str, object]:
    return {
        "tools": [
            {
                "name": PROJECT_LIST_TOOL,
                "description": "List registered MemoryHub projects.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": STATUS_TOOL,
                "description": "Return MemoryHub runtime status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": SEARCH_TOOL,
                "description": "Search indexed MemoryHub Markdown context.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "project": {"type": "string"},
                        "kind": {"type": "string"},
                        "tag": {"type": "string"},
                        "path_prefix": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
            {
                "name": CONTEXT_TOOL,
                "description": "Build prompt-ready context from indexed documents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "project": {"type": "string"},
                        "kind": {"type": "string"},
                        "tag": {"type": "string"},
                        "path_prefix": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
            {
                "name": READ_TOOL,
                "description": "Read a Markdown context document.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "required": ["project", "path"],
                    "additionalProperties": False,
                },
            },
            {
                "name": WRITE_TOOL,
                "description": "Write a Markdown context document.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string"},
                        "path": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "kind": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["project", "path", "title", "body"],
                    "additionalProperties": False,
                },
            },
        ]
    }


def _tools_call_result(params: object, registry: ProjectRegistry) -> dict[str, object]:
    params_object = _expect_object(params, "params")
    tool_name = params_object.get("name")
    arguments = _expect_object(params_object.get("arguments", {}), "params.arguments")
    library = MemoryHubLibrary(registry)

    if tool_name == PROJECT_LIST_TOOL:
        return _tool_result(
            {"projects": [project.to_json() for project in registry.list_projects()]}
        )
    if tool_name == STATUS_TOOL:
        registry.ensure_initialized()
        return _tool_result({"status": doctor(registry.layout).to_json()})
    if tool_name == SEARCH_TOOL:
        query = _expect_string(arguments.get("query"), "arguments.query")
        project = _optional_string(arguments.get("project"), "arguments.project")
        kind = _optional_string(arguments.get("kind"), "arguments.kind")
        tag = _optional_string(arguments.get("tag"), "arguments.tag")
        path_prefix = _optional_string(
            arguments.get("path_prefix"),
            "arguments.path_prefix",
        )
        limit = _optional_int(arguments.get("limit"), "arguments.limit") or 10
        return _tool_result(
            {
                "results": [
                    result.to_json()
                    for result in library.search(
                        query,
                        project_name=project,
                        kind=kind,
                        tag=tag,
                        path_prefix=path_prefix,
                        limit=limit,
                    )
                ]
            }
        )
    if tool_name == CONTEXT_TOOL:
        query = _expect_string(arguments.get("query"), "arguments.query")
        project = _optional_string(arguments.get("project"), "arguments.project")
        kind = _optional_string(arguments.get("kind"), "arguments.kind")
        tag = _optional_string(arguments.get("tag"), "arguments.tag")
        path_prefix = _optional_string(
            arguments.get("path_prefix"),
            "arguments.path_prefix",
        )
        limit = _optional_int(arguments.get("limit"), "arguments.limit") or 5
        return _tool_result(
            {
                "context": library.build_context(
                    query,
                    project_name=project,
                    kind=kind,
                    tag=tag,
                    path_prefix=path_prefix,
                    limit=limit,
                ).to_json()
            }
        )
    if tool_name == READ_TOOL:
        document = library.read_document(
            _expect_string(arguments.get("project"), "arguments.project"),
            _expect_string(arguments.get("path"), "arguments.path"),
        )
        return _tool_result({"document": document.to_json()})
    if tool_name == WRITE_TOOL:
        document = library.write_document(
            _expect_string(arguments.get("project"), "arguments.project"),
            _expect_string(arguments.get("path"), "arguments.path"),
            title=_expect_string(arguments.get("title"), "arguments.title"),
            body=_expect_string(arguments.get("body"), "arguments.body"),
            kind=_optional_string(arguments.get("kind"), "arguments.kind") or "memory",
            tags=_optional_string_list(arguments.get("tags"), "arguments.tags"),
        )
        library.reindex()
        return _tool_result({"document": document.to_json()})

    raise MemoryHubError(f"unsupported tool: {tool_name}")


def _tool_result(structured_content: dict[str, object]) -> dict[str, object]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(structured_content, sort_keys=True),
            }
        ],
        "structuredContent": structured_content,
        "isError": False,
    }


def _success_response(
    request_id: str | int | None,
    result: dict[str, object],
) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error_response(
    request_id: str | int | None,
    code: int,
    message: str,
) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _json_rpc_id(value: object) -> str | int | None:
    if isinstance(value, str):
        return value
    if type(value) is int:
        return value
    return None


def _string_key_mapping(value: Mapping[object, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            continue
        result[key] = item
    return result


def _expect_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MemoryHubError(f"expected object at {label}")
    return _string_key_mapping(cast(dict[object, object], value))


def _expect_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise MemoryHubError(f"expected string at {label}")
    return value


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _expect_string(value, label)


def _optional_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    raise MemoryHubError(f"expected integer at {label}")


def _optional_string_list(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise MemoryHubError(f"expected string list at {label}")
    values = cast(list[object], value)
    result: list[str] = []
    for item in values:
        if not isinstance(item, str):
            raise MemoryHubError(f"expected string list at {label}")
        result.append(item)
    return tuple(result)
