"""Integration tests for version command."""

from typer.testing import CliRunner

from memoryhub.cli.main import app
import memoryhub


def test_version_command():
    """Test 'bm --version' command shows version."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert memoryhub.__version__ in result.stdout
