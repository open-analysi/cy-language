"""Tests for CLI --mcp-server flag."""

import textwrap
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()


# ── --mcp-server: flag parsing and validation ─────────────────────────────


def test_mcp_server_invalid_format(tmp_path):
    """--mcp-server rejects values not in name=url format."""
    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    result = runner.invoke(app, ["run", str(prog), "--mcp-server", "bad-format"])
    assert result.exit_code == 1
    assert "name=url" in result.output.lower() or "format" in result.output.lower()


def test_mcp_server_multiple_servers(tmp_path):
    """--mcp-server can be specified multiple times."""
    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    # Mock _run_from_source_async to capture the mcp_servers arg
    with patch("cy_language.cli.run_cmd._run_from_source_async") as mock_run:
        mock_run.return_value = None
        runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--mcp-server",
                "server1=http://localhost:8001",
                "--mcp-server",
                "server2=http://localhost:8002",
            ],
        )
        assert mock_run.called
        # mcp_servers is the 8th positional arg (index 7)
        mcp_config = mock_run.call_args[0][7]
        assert "server1" in mcp_config
        assert "server2" in mcp_config


def test_mcp_server_parses_name_and_url(tmp_path):
    """--mcp-server correctly parses name=url into mcp_servers config."""
    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    with patch("cy_language.cli.run_cmd._run_from_source_async") as mock_run:
        mock_run.return_value = None
        runner.invoke(
            app,
            ["run", str(prog), "--mcp-server", "demo=http://localhost:8000"],
        )

        assert mock_run.called
        mcp_config = mock_run.call_args[0][7]
        assert mcp_config["demo"]["base_url"] == "http://localhost:8000"
        assert mcp_config["demo"]["mcp_id"] == "demo"


def test_mcp_server_end_to_end_with_mock(tmp_path):
    """Full end-to-end: --mcp-server flag → async execution with mocked MCP."""
    prog = tmp_path / "script.cy"
    # Use a script that only uses native tools — the MCP server
    # just needs to initialize without failing.
    prog.write_text("return 42")

    # Mock MCPManager to avoid real HTTP calls
    with patch("cy_language.mcp_manager.MCPManager.initialize", new_callable=AsyncMock):
        result = runner.invoke(
            app,
            ["run", str(prog), "--mcp-server", "demo=http://localhost:9999"],
        )
        assert result.exit_code == 0
        assert "42" in result.output


def test_mcp_server_with_stub_tools(tmp_path):
    """--mcp-server and --stub-tools can be combined."""
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        data = mcp::demo::some_tool(query="test")
        return data ?? "no data"
    """)
    )

    # Mock MCPManager initialization
    with patch("cy_language.mcp_manager.MCPManager.initialize", new_callable=AsyncMock):
        result = runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--mcp-server",
                "demo=http://localhost:9999",
                "--stub-tools",
            ],
        )
        assert result.exit_code == 0
        assert "no data" in result.output
