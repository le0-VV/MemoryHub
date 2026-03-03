"""Tests for the MCP CLI command."""

import os
import sys
import types
from unittest.mock import MagicMock

from typer.testing import CliRunner

from memoryhub.cli.app import app
import memoryhub.cli.commands.mcp as mcp_cmd  # noqa: F401

runner = CliRunner()


def _install_import_stub(monkeypatch, module_name: str) -> None:
    monkeypatch.setitem(sys.modules, module_name, types.ModuleType(module_name))


def test_mcp_command_canonicalizes_project_constraint(monkeypatch):
    """The MCP CLI should canonicalize project constraints before exporting them."""
    _install_import_stub(monkeypatch, "memoryhub.mcp.tools")
    _install_import_stub(monkeypatch, "memoryhub.mcp.prompts")
    _install_import_stub(monkeypatch, "memoryhub.mcp.resources")

    selector = MagicMock()
    selector.require_configured_project.return_value.project = "My Research"

    run_calls = []

    monkeypatch.setattr(mcp_cmd.ProjectSelector, "from_config", lambda: selector)
    monkeypatch.setattr(mcp_cmd, "init_mcp_logging", lambda: None)
    monkeypatch.setattr(mcp_cmd.mcp_server, "run", lambda **kwargs: run_calls.append(kwargs))
    monkeypatch.delenv("BASIC_MEMORY_MCP_PROJECT", raising=False)

    result = runner.invoke(app, ["mcp", "--project", "my-research"])

    assert result.exit_code == 0, result.output
    assert os.environ["BASIC_MEMORY_MCP_PROJECT"] == "My Research"
    assert run_calls == [{"transport": "stdio"}]
