"""Minimal stdio MCP adapter."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import TextIO, cast

from memoryhub import __version__
from memoryhub.framework.errors import MemoryHubError
from memoryhub.framework.registry import ProjectRegistry

PROTOCOL_VERSION = "2025-06-18"
PROJECT_LIST_TOOL = "project_list"


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
            }
        ]
    }


def _tools_call_result(params: object, registry: ProjectRegistry) -> dict[str, object]:
    params_object = _expect_object(params, "params")
    tool_name = params_object.get("name")
    if tool_name != PROJECT_LIST_TOOL:
        raise MemoryHubError(f"unsupported tool: {tool_name}")

    projects = [project.to_json() for project in registry.list_projects()]
    structured_content: dict[str, object] = {"projects": projects}
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
