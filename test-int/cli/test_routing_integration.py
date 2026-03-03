"""Integration tests for CLI routing flags in the local-only fork.

These tests verify that the remaining routing-related CLI surface behaves
correctly: removed cloud flags fail fast, `--local` is still accepted where
it remains for compatibility, and the MCP command passes the right transport
options to the server.
"""

import pytest
from typer.testing import CliRunner

from memoryhub.cli.main import app as cli_app


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
    """Tests that MCP command transport wiring matches the local-only fork."""

    def test_mcp_stdio_uses_stdio_transport(self, monkeypatch):
        """Stdio transport should call the MCP server without HTTP-only kwargs."""
        run_kwargs = {}

        import memoryhub.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            run_kwargs.update(kwargs)
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp"])  # default transport is stdio

        assert run_kwargs == {"transport": "stdio"}

    def test_mcp_streamable_http_passes_http_options(self, monkeypatch):
        """Streamable-HTTP transport should pass host/port/path to the MCP server."""
        run_kwargs = {}

        import memoryhub.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            run_kwargs.update(kwargs)
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp", "--transport", "streamable-http"])

        assert run_kwargs == {
            "transport": "streamable-http",
            "host": "0.0.0.0",
            "port": 8000,
            "path": "/mcp",
            "log_level": "INFO",
        }

    def test_mcp_sse_passes_http_options(self, monkeypatch):
        """SSE transport should pass host/port/path to the MCP server."""
        run_kwargs = {}

        import memoryhub.cli.commands.mcp as mcp_mod

        def mock_run(*args, **kwargs):
            run_kwargs.update(kwargs)
            raise SystemExit(0)

        monkeypatch.setattr(mcp_mod.mcp_server, "run", mock_run)
        monkeypatch.setattr(mcp_mod, "init_mcp_logging", lambda: None)

        runner.invoke(cli_app, ["mcp", "--transport", "sse"])

        assert run_kwargs == {
            "transport": "sse",
            "host": "0.0.0.0",
            "port": 8000,
            "path": "/mcp",
            "log_level": "INFO",
        }


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
