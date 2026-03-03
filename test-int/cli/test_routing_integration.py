"""Integration tests for CLI routing flags in the local-only fork.

These tests verify that the routing flags work correctly
across CLI commands, and that MCP routing varies by transport.

Note: Environment variable behavior during command execution is tested
in unit tests (tests/cli/test_routing.py) which can properly monkeypatch
the modules before they are imported. These integration tests focus on
CLI behavior: flag acceptance and error handling.
"""

import os

import pytest
from typer.testing import CliRunner

from basic_memory.cli.main import app as cli_app


runner = CliRunner()


class TestRemovedCloudFlags:
    """Tests for removed cloud flags."""

    @pytest.mark.parametrize(
        "args",
        [
            ["status", "--cloud"],
            ["project", "list", "--cloud"],
            ["project", "ls", "--name", "test", "--cloud"],
            ["tool", "search-notes", "test", "--cloud"],
            ["tool", "read-note", "test", "--cloud"],
            ["tool", "build-context", "memory://test", "--cloud"],
            ["tool", "edit-note", "test", "--operation", "append", "--content", "test", "--cloud"],
        ],
    )
    def test_removed_cloud_flag_errors(self, args):
        """Commands should reject the removed --cloud flag at parse time."""
        result = runner.invoke(cli_app, args)
        assert result.exit_code != 0
        assert "No such option: --cloud" in result.output


class TestMcpCommandRouting:
    """Tests that MCP routing varies by transport."""

    def test_mcp_stdio_does_not_force_local(self, monkeypatch):
        """Stdio transport should not inject explicit local routing env vars."""
        # Ensure env is clean before test
        monkeypatch.delenv("BASIC_MEMORY_FORCE_LOCAL", raising=False)
        monkeypatch.delenv("BASIC_MEMORY_EXPLICIT_ROUTING", raising=False)

        env_at_run = {}

        import basic_memory.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            env_at_run["FORCE_LOCAL"] = os.environ.get("BASIC_MEMORY_FORCE_LOCAL")
            env_at_run["EXPLICIT"] = os.environ.get("BASIC_MEMORY_EXPLICIT_ROUTING")
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp"])  # default transport is stdio

        # Command should not have set these vars
        assert env_at_run["FORCE_LOCAL"] is None
        assert env_at_run["EXPLICIT"] is None

    def test_mcp_stdio_honors_external_local_override(self, monkeypatch):
        """Stdio transport should pass through externally-set local routing env vars."""
        monkeypatch.setenv("BASIC_MEMORY_FORCE_LOCAL", "true")
        monkeypatch.setenv("BASIC_MEMORY_EXPLICIT_ROUTING", "true")

        env_at_run = {}

        import basic_memory.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            env_at_run["FORCE_LOCAL"] = os.environ.get("BASIC_MEMORY_FORCE_LOCAL")
            env_at_run["EXPLICIT"] = os.environ.get("BASIC_MEMORY_EXPLICIT_ROUTING")
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp"])

        # Externally-set vars should be preserved
        assert env_at_run["FORCE_LOCAL"] == "true"
        assert env_at_run["EXPLICIT"] == "true"

    def test_mcp_streamable_http_forces_local(self, monkeypatch):
        """Streamable-HTTP transport should force local routing."""
        env_at_run = {}

        import basic_memory.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            env_at_run["FORCE_LOCAL"] = os.environ.get("BASIC_MEMORY_FORCE_LOCAL")
            env_at_run["EXPLICIT"] = os.environ.get("BASIC_MEMORY_EXPLICIT_ROUTING")
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp", "--transport", "streamable-http"])

        assert env_at_run["FORCE_LOCAL"] == "true"
        assert env_at_run["EXPLICIT"] == "true"

    def test_mcp_sse_forces_local(self, monkeypatch):
        """SSE transport should force local routing."""
        env_at_run = {}

        import basic_memory.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            env_at_run["FORCE_LOCAL"] = os.environ.get("BASIC_MEMORY_FORCE_LOCAL")
            env_at_run["EXPLICIT"] = os.environ.get("BASIC_MEMORY_EXPLICIT_ROUTING")
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp", "--transport", "sse"])

        assert env_at_run["FORCE_LOCAL"] == "true"
        assert env_at_run["EXPLICIT"] == "true"


class TestToolCommandsAcceptFlags:
    """Tests that tool commands accept local routing flags."""

    @pytest.mark.parametrize(
        "command,args",
        [
            ("search-notes", ["test query"]),
            ("recent-activity", []),
            ("read-note", ["test"]),
            ("edit-note", ["test", "--operation", "append", "--content", "test"]),
            ("build-context", ["memory://test"]),
        ],
    )
    def test_tool_commands_accept_local_flag(self, command, args, app_config):
        """Tool commands should accept --local flag without parsing error."""
        full_args = ["tool", command] + args + ["--local"]
        result = runner.invoke(cli_app, full_args)
        # Should not fail due to flag parsing (No such option error)
        assert "No such option: --local" not in result.output

class TestProjectCommandsAcceptFlags:
    """Tests that project commands accept local routing flags."""

    def test_project_list_accepts_local_flag(self, app_config):
        """project list should accept --local flag."""
        result = runner.invoke(cli_app, ["project", "list", "--local"])
        assert "No such option: --local" not in result.output

    def test_project_info_accepts_local_flag(self, app_config):
        """project info should accept --local flag."""
        result = runner.invoke(cli_app, ["project", "info", "--local"])
        assert "No such option: --local" not in result.output

    def test_project_default_accepts_local_flag(self, app_config):
        """project default should accept --local flag."""
        result = runner.invoke(cli_app, ["project", "default", "test", "--local"])
        assert "No such option: --local" not in result.output

    def test_project_sync_config_accepts_local_flag(self, app_config):
        """project sync-config should accept --local flag."""
        result = runner.invoke(cli_app, ["project", "sync-config", "test", "--local"])
        assert "No such option: --local" not in result.output

    def test_project_ls_accepts_local_flag(self, app_config):
        """project ls should accept --local flag."""
        result = runner.invoke(cli_app, ["project", "ls", "--name", "test", "--local"])
        assert "No such option: --local" not in result.output


class TestStatusCommandAcceptsFlags:
    """Tests that status command accepts local routing flags."""

    def test_status_accepts_local_flag(self, app_config):
        """status should accept --local flag."""
        result = runner.invoke(cli_app, ["status", "--local"])
        assert "No such option: --local" not in result.output
