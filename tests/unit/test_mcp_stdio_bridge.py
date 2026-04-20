"""Tests for StdioMCPBridge and --mcp-stdio CLI flag."""

import json
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cy_language.cli import app
from cy_language.cli.mcp_stdio_bridge import parse_mcp_stdio_arg

runner = CliRunner()

# Test server bundled with the test suite — no external dependencies.
_FIXTURES = Path(__file__).parent / "fixtures"
MCP_TEST_SERVER = _FIXTURES / "mcp_test_server.py"
MCP_STDIO_ARG = f"test=poetry run python {MCP_TEST_SERVER}"


# ── parse_mcp_stdio_arg ──────────────────────────────────────────────────


class TestParseMcpStdioArg:
    """Tests for the name=command parser."""

    def test_simple_command(self):
        name, cmd, args = parse_mcp_stdio_arg("demo=python server.py")
        assert name == "demo"
        assert cmd == "python"
        assert args == ["server.py"]

    def test_command_with_multiple_args(self):
        name, cmd, args = parse_mcp_stdio_arg(
            "demo=uv run --with mcp[cli] mcp run server.py"
        )
        assert name == "demo"
        assert cmd == "uv"
        assert args == ["run", "--with", "mcp[cli]", "mcp", "run", "server.py"]

    def test_command_no_args(self):
        name, cmd, args = parse_mcp_stdio_arg("server=my-mcp-server")
        assert name == "server"
        assert cmd == "my-mcp-server"
        assert args == []

    def test_missing_equals(self):
        with pytest.raises(ValueError, match="name=command"):
            parse_mcp_stdio_arg("bad-format")

    def test_empty_name(self):
        with pytest.raises(ValueError, match="required"):
            parse_mcp_stdio_arg("=python server.py")

    def test_empty_command(self):
        with pytest.raises(ValueError, match="required"):
            parse_mcp_stdio_arg("demo=")

    def test_name_with_spaces_stripped(self):
        name, cmd, args = parse_mcp_stdio_arg(" demo = python server.py")
        assert name == "demo"
        assert cmd == "python"


# ── End-to-end --mcp-stdio with bundled test server ──────────────────────


@pytest.mark.mcp_stdio
class TestMcpStdioEndToEnd:
    """End-to-end tests using the bundled test MCP server."""

    def test_call_add_tool(self, tmp_path):
        """Call mcp::test::add via stdio transport."""
        prog = tmp_path / "script.cy"
        prog.write_text("return mcp::test::add(a=10, b=20)")

        result = runner.invoke(
            app,
            ["run", str(prog), "--mcp-stdio", MCP_STDIO_ARG, "--no-check-types"],
        )
        assert result.exit_code == 0
        assert "30" in result.output

    def test_call_echo_tool(self, tmp_path):
        """Call mcp::test::echo via stdio transport."""
        prog = tmp_path / "script.cy"
        prog.write_text('return mcp::test::echo(message="hello world")')

        result = runner.invoke(
            app,
            ["run", str(prog), "--mcp-stdio", MCP_STDIO_ARG, "--no-check-types"],
        )
        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_mcp_result_in_expression(self, tmp_path):
        """Use MCP tool result in a Cy expression."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = mcp::test::add(a=3, b=4)
            b = mcp::test::add(a=10, b=a)
            return {"first": a, "second": b}
        """)
        )

        result = runner.invoke(
            app,
            ["run", str(prog), "--mcp-stdio", MCP_STDIO_ARG, "--no-check-types"],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {"first": 7, "second": 17}

    def test_mcp_with_native_tools(self, tmp_path):
        """Mix MCP tools with native Cy tools."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            items = [1, 2, 3]
            total = mcp::test::add(a=len(items), b=100)
            return total
        """)
        )

        result = runner.invoke(
            app,
            ["run", str(prog), "--mcp-stdio", MCP_STDIO_ARG, "--no-check-types"],
        )
        assert result.exit_code == 0
        assert "103" in result.output
