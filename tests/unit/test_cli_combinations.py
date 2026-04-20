"""Exhaustive combination tests for CLI tool flags.

Tests every combination of --tools, --stub-tools, --mcp-server, --mcp-stdio
across cy run, cy check, and cy compile.
"""

import json
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()

# Bundled test MCP server — no external dependencies.
_FIXTURES = Path(__file__).parent / "fixtures"
MCP_TEST_SERVER = _FIXTURES / "mcp_test_server.py"
MCP_STDIO_ARG = f"test=poetry run python {MCP_TEST_SERVER}"


# ── Helpers ───────────────────────────────────────────────────────────────


def _write_tools_file(tmp_path: Path) -> Path:
    """Create a tools.py with a greet() and double() function."""
    tools_py = tmp_path / "tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        def double(x):
            return x * 2

        tools = {"greet": greet, "double": double}
    """)
    )
    return tools_py


def _write_namespaced_tools_file(tmp_path: Path) -> Path:
    """Create a tools.py with app:: namespaced tools."""
    tools_py = tmp_path / "ns_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def lookup(ip):
            return {"ip": ip, "risk": "low"}

        tools = {"app::intel::lookup": lookup}
    """)
    )
    return tools_py


# ══════════════════════════════════════════════════════════════════════════
# cy run — all combinations
# ══════════════════════════════════════════════════════════════════════════


class TestRunCombinations:
    """Test all flag combinations for `cy run`."""

    # ── Single flags (baseline) ───────────────────────────────────────

    def test_run_no_flags(self, tmp_path):
        """Baseline: cy run with no tool flags."""
        prog = tmp_path / "script.cy"
        prog.write_text("return len([1, 2, 3])")

        result = runner.invoke(app, ["run", str(prog)])
        assert result.exit_code == 0
        assert "3" in result.output

    def test_run_tools_only(self, tmp_path):
        """--tools alone."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text('return greet("Alice")')

        result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        assert "Hello, Alice!" in result.output

    def test_run_stub_tools_only(self, tmp_path):
        """--stub-tools alone."""
        prog = tmp_path / "script.cy"
        prog.write_text('return unknown_func("x") ?? "fallback"')

        result = runner.invoke(app, ["run", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        assert "fallback" in result.output

    # ── Two-flag combinations ─────────────────────────────────────────

    def test_run_tools_plus_stub_tools(self, tmp_path):
        """--tools + --stub-tools: known tools execute, unknown return null."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            g = greet("Bob")
            d = double(5)
            u = unknown_tool("test")
            return {"greeting": g, "doubled": d, "unknown": u ?? "stubbed"}
        """)
        )

        result = runner.invoke(
            app, ["run", str(prog), "--tools", str(tools_py), "--stub-tools"]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {
            "greeting": "Hello, Bob!",
            "doubled": 10,
            "unknown": "stubbed",
        }

    def test_run_tools_plus_stub_tools_namespaced(self, tmp_path):
        """--tools + --stub-tools with namespaced tools."""
        tools_py = _write_namespaced_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            known = app::intel::lookup(ip="1.2.3.4")
            unknown = app::other::action(data="test")
            return {"risk": known.risk, "other": unknown ?? "stubbed"}
        """)
        )

        result = runner.invoke(
            app, ["run", str(prog), "--tools", str(tools_py), "--stub-tools"]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {"risk": "low", "other": "stubbed"}

    def test_run_tools_plus_mcp_server_mock(self, tmp_path):
        """--tools + --mcp-server (HTTP): both tool sources available."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        # Only use the file-loaded tool — MCP server is mocked
        prog.write_text("return double(21)")

        with patch(
            "cy_language.mcp_manager.MCPManager.initialize",
            new_callable=AsyncMock,
        ):
            result = runner.invoke(
                app,
                [
                    "run",
                    str(prog),
                    "--tools",
                    str(tools_py),
                    "--mcp-server",
                    "demo=http://localhost:9999",
                ],
            )
        assert result.exit_code == 0
        assert "42" in result.output

    def test_run_stub_tools_plus_mcp_server_mock(self, tmp_path):
        """--stub-tools + --mcp-server (HTTP): unknown tools stubbed."""
        prog = tmp_path / "script.cy"
        prog.write_text('return unknown_func("x") ?? "fallback"')

        with patch(
            "cy_language.mcp_manager.MCPManager.initialize",
            new_callable=AsyncMock,
        ):
            result = runner.invoke(
                app,
                [
                    "run",
                    str(prog),
                    "--stub-tools",
                    "--mcp-server",
                    "demo=http://localhost:9999",
                ],
            )
        assert result.exit_code == 0
        assert "fallback" in result.output

    # ── Three-flag combinations ───────────────────────────────────────

    def test_run_tools_stub_mcp_server_mock(self, tmp_path):
        """--tools + --stub-tools + --mcp-server: all three together."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            g = greet("Eve")
            u = unknown_tool("test")
            return {"greeting": g, "unknown": u ?? "stubbed"}
        """)
        )

        with patch(
            "cy_language.mcp_manager.MCPManager.initialize",
            new_callable=AsyncMock,
        ):
            result = runner.invoke(
                app,
                [
                    "run",
                    str(prog),
                    "--tools",
                    str(tools_py),
                    "--stub-tools",
                    "--mcp-server",
                    "demo=http://localhost:9999",
                ],
            )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {"greeting": "Hello, Eve!", "unknown": "stubbed"}

    # ── MCP stdio combinations ───────────────────────────────────────

    @pytest.mark.mcp_stdio
    def test_run_mcp_stdio_only(self, tmp_path):
        """--mcp-stdio alone."""
        prog = tmp_path / "script.cy"
        prog.write_text("return mcp::test::add(a=7, b=3)")

        result = runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--mcp-stdio",
                MCP_STDIO_ARG,
                "--no-check-types",
            ],
        )
        assert result.exit_code == 0
        assert "10" in result.output

    @pytest.mark.mcp_stdio
    def test_run_tools_plus_mcp_stdio(self, tmp_path):
        """--tools + --mcp-stdio: file tools and MCP tools both work."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            mcp_result = mcp::test::add(a=10, b=20)
            file_result = double(mcp_result)
            return {"mcp": mcp_result, "doubled": file_result}
        """)
        )

        result = runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--tools",
                str(tools_py),
                "--mcp-stdio",
                MCP_STDIO_ARG,
                "--no-check-types",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {"mcp": 30, "doubled": 60}

    @pytest.mark.mcp_stdio
    def test_run_stub_tools_plus_mcp_stdio(self, tmp_path):
        """--stub-tools + --mcp-stdio: MCP tools work, unknown stubbed."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            mcp_result = mcp::test::add(a=1, b=2)
            unknown = other_tool("x")
            return {"mcp": mcp_result, "unknown": unknown ?? "stubbed"}
        """)
        )

        result = runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--stub-tools",
                "--mcp-stdio",
                MCP_STDIO_ARG,
                "--no-check-types",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {"mcp": 3, "unknown": "stubbed"}

    @pytest.mark.mcp_stdio
    def test_run_tools_stub_mcp_stdio_all(self, tmp_path):
        """--tools + --stub-tools + --mcp-stdio: everything combined."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            mcp_val = mcp::test::add(a=5, b=5)
            file_val = greet("World")
            unknown_val = mystery_tool("z")
            return {
                "mcp": mcp_val,
                "file": file_val,
                "unknown": unknown_val ?? "stubbed"
            }
        """)
        )

        result = runner.invoke(
            app,
            [
                "run",
                str(prog),
                "--tools",
                str(tools_py),
                "--stub-tools",
                "--mcp-stdio",
                MCP_STDIO_ARG,
                "--no-check-types",
            ],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output.strip())
        assert parsed == {
            "mcp": 10,
            "file": "Hello, World!",
            "unknown": "stubbed",
        }


# ══════════════════════════════════════════════════════════════════════════
# cy check — all combinations
# ══════════════════════════════════════════════════════════════════════════


class TestCheckCombinations:
    """Test all flag combinations for `cy check`."""

    def test_check_no_flags(self, tmp_path):
        """Baseline: cy check with no tool flags."""
        prog = tmp_path / "script.cy"
        prog.write_text("return len([1, 2, 3])")

        result = runner.invoke(app, ["check", str(prog)])
        assert result.exit_code == 0
        assert "No errors found" in result.output

    def test_check_tools_only(self, tmp_path):
        """--tools alone with cy check."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text('return greet("Alice")')

        result = runner.invoke(app, ["check", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        assert "No errors found" in result.output

    def test_check_tools_rejects_without_flag(self, tmp_path):
        """Without --tools, multiple custom tool calls fail check.

        Note: analyze_types has built-in retry logic that handles a single
        unknown tool. Two or more unknown tools cause failure.
        """
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = greet("Alice")
            b = farewell("Bob")
            return a + b
        """)
        )

        result = runner.invoke(app, ["check", str(prog)])
        assert result.exit_code == 1

    def test_check_stub_tools_only(self, tmp_path):
        """--stub-tools alone with cy check."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = unknown_tool_1("x")
            b = unknown_tool_2("y")
            return (a ?? "a") + (b ?? "b")
        """)
        )

        result = runner.invoke(app, ["check", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        assert "No errors found" in result.output

    def test_check_tools_plus_stub_tools(self, tmp_path):
        """--tools + --stub-tools with cy check."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            g = greet("Bob")
            u = unknown_tool("test")
            return {"greeting": g, "unknown": u ?? "stubbed"}
        """)
        )

        result = runner.invoke(
            app, ["check", str(prog), "--tools", str(tools_py), "--stub-tools"]
        )
        assert result.exit_code == 0
        assert "No errors found" in result.output

    def test_check_namespaced_tools(self, tmp_path):
        """--tools with app:: namespaced tools in cy check."""
        tools_py = _write_namespaced_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            result = app::intel::lookup(ip="1.2.3.4")
            return result.risk
        """)
        )

        result = runner.invoke(app, ["check", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        assert "No errors found" in result.output

    def test_check_stub_tools_with_namespaced_unknown(self, tmp_path):
        """--stub-tools with namespaced unknown tools in cy check."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = app::service_a::action("x")
            b = app::service_b::action("y")
            return (a ?? "a") + (b ?? "b")
        """)
        )

        result = runner.invoke(app, ["check", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        assert "No errors found" in result.output


# ══════════════════════════════════════════════════════════════════════════
# cy compile — all combinations
# ══════════════════════════════════════════════════════════════════════════


class TestCompileCombinations:
    """Test all flag combinations for `cy compile`."""

    def test_compile_no_flags(self, tmp_path):
        """Baseline: cy compile with no tool flags."""
        prog = tmp_path / "script.cy"
        prog.write_text("return len([1, 2, 3])")

        result = runner.invoke(app, ["compile", str(prog)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_tools_only(self, tmp_path):
        """--tools alone with cy compile."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text('return greet("Alice")')

        result = runner.invoke(app, ["compile", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_tools_rejects_without_flag(self, tmp_path):
        """Without --tools, custom tool calls fail compilation."""
        prog = tmp_path / "script.cy"
        prog.write_text('return greet("Alice")')

        result = runner.invoke(app, ["compile", str(prog)])
        assert result.exit_code == 1

    def test_compile_stub_tools_only(self, tmp_path):
        """--stub-tools alone with cy compile."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = unknown_tool_1("x")
            b = unknown_tool_2("y")
            return (a ?? "a") + (b ?? "b")
        """)
        )

        result = runner.invoke(app, ["compile", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_tools_plus_stub_tools(self, tmp_path):
        """--tools + --stub-tools with cy compile."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            g = greet("Bob")
            u = unknown_tool("test")
            return {"greeting": g, "unknown": u ?? "stubbed"}
        """)
        )

        result = runner.invoke(
            app, ["compile", str(prog), "--tools", str(tools_py), "--stub-tools"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_namespaced_tools(self, tmp_path):
        """--tools with app:: namespaced tools in cy compile."""
        tools_py = _write_namespaced_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            result = app::intel::lookup(ip="1.2.3.4")
            return result
        """)
        )

        result = runner.invoke(app, ["compile", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_stub_tools_with_namespaced_unknown(self, tmp_path):
        """--stub-tools with namespaced unknown tools in cy compile."""
        prog = tmp_path / "script.cy"
        prog.write_text(
            textwrap.dedent("""\
            a = app::service_a::action("x")
            b = app::service_b::action("y")
            return (a ?? "a") + (b ?? "b")
        """)
        )

        result = runner.invoke(app, ["compile", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data

    def test_compile_then_run_with_tools(self, tmp_path):
        """Pipeline: compile with --tools, then run the plan with --tools."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text("return double(21)")
        plan_file = tmp_path / "plan.json"

        # Compile
        c_result = runner.invoke(
            app,
            [
                "compile",
                str(prog),
                "--tools",
                str(tools_py),
                "-o",
                str(plan_file),
                "--no-check-types",
            ],
        )
        assert c_result.exit_code == 0
        assert plan_file.exists()

        # Run from plan — need --tools so the executor can find the function
        r_result = runner.invoke(
            app,
            ["run", str(plan_file), "--tools", str(tools_py)],
        )
        assert r_result.exit_code == 0
        assert "42" in r_result.output


# ══════════════════════════════════════════════════════════════════════════
# Error cases — flag misuse
# ══════════════════════════════════════════════════════════════════════════


class TestErrorCombinations:
    """Test error cases and edge conditions."""

    def test_run_tools_file_not_found(self, tmp_path):
        """--tools with nonexistent file."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 1")

        result = runner.invoke(
            app, ["run", str(prog), "--tools", "/nonexistent/tools.py"]
        )
        assert result.exit_code == 1

    def test_check_tools_file_not_found(self, tmp_path):
        """--tools with nonexistent file in cy check."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 1")

        result = runner.invoke(
            app, ["check", str(prog), "--tools", "/nonexistent/tools.py"]
        )
        assert result.exit_code == 1

    def test_compile_tools_file_not_found(self, tmp_path):
        """--tools with nonexistent file in cy compile."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 1")

        result = runner.invoke(
            app, ["compile", str(prog), "--tools", "/nonexistent/tools.py"]
        )
        assert result.exit_code == 1

    def test_run_mcp_server_bad_format(self, tmp_path):
        """--mcp-server with invalid format."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 1")

        result = runner.invoke(
            app, ["run", str(prog), "--mcp-server", "no-equals-sign"]
        )
        assert result.exit_code == 1

    def test_run_mcp_stdio_bad_format(self, tmp_path):
        """--mcp-stdio with invalid format."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 1")

        result = runner.invoke(app, ["run", str(prog), "--mcp-stdio", "no-equals-sign"])
        assert result.exit_code == 1

    def test_run_stub_tools_without_fallback_returns_null(self, tmp_path):
        """--stub-tools: if no ?? fallback, result is null."""
        prog = tmp_path / "script.cy"
        prog.write_text("return unknown_tool()")

        result = runner.invoke(app, ["run", str(prog), "--stub-tools"])
        assert result.exit_code == 0
        assert result.output.strip() == "null"

    def test_run_tools_overrides_native(self, tmp_path):
        """--tools can override a native tool name."""
        tools_py = tmp_path / "tools.py"
        tools_py.write_text(
            textwrap.dedent("""\
            def len(items):
                return 999

            tools = {"len": len}
        """)
        )

        prog = tmp_path / "script.cy"
        prog.write_text("return len([1, 2, 3])")

        result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
        assert result.exit_code == 0
        assert "999" in result.output

    def test_compile_plan_run_without_tools_fails(self, tmp_path):
        """Compile with --tools, run plan without --tools → tool not found."""
        tools_py = _write_tools_file(tmp_path)
        prog = tmp_path / "script.cy"
        prog.write_text('return greet("Alice")')
        plan_file = tmp_path / "plan.json"

        # Compile with tools
        c_result = runner.invoke(
            app,
            [
                "compile",
                str(prog),
                "--tools",
                str(tools_py),
                "-o",
                str(plan_file),
                "--no-check-types",
            ],
        )
        assert c_result.exit_code == 0

        # Run plan WITHOUT tools — should fail at runtime
        r_result = runner.invoke(app, ["run", str(plan_file)])
        assert r_result.exit_code == 1

    def test_run_plan_with_stub_tools_warns(self, tmp_path):
        """--stub-tools with a .json plan warns the user."""
        prog = tmp_path / "script.cy"
        prog.write_text("return 42")
        plan_file = tmp_path / "plan.json"

        runner.invoke(
            app,
            ["compile", str(prog), "-o", str(plan_file), "--no-check-types"],
        )

        # Typer CliRunner mixes stderr into output by default
        r_result = runner.invoke(app, ["run", str(plan_file), "--stub-tools"])
        assert r_result.exit_code == 0
        assert "ignored" in r_result.output.lower()
