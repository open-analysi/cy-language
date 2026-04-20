"""Tests for CLI external tool features: --tools, --stub-tools."""

import json
import textwrap

from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()


# ── --tools: load tools from a Python file ────────────────────────────────


def test_tools_flag_loads_python_file(tmp_path):
    """--tools loads a Python file and registers its `tools` dict."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        tools = {"greet": greet}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text('return greet("Alice")')

    result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_tools_flag_with_namespaced_tools(tmp_path):
    """--tools supports app:: namespaced tool names."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def ip_lookup(ip):
            return {"ip": ip, "risk": "low"}

        tools = {"app::threat_intel::ip_lookup": ip_lookup}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        result = app::threat_intel::ip_lookup("8.8.8.8")
        return result.risk
    """)
    )

    result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 0
    assert "low" in result.output


def test_tools_flag_file_not_found(tmp_path):
    """--tools with a nonexistent file shows a clear error."""
    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    result = runner.invoke(app, ["run", str(prog), "--tools", "/nonexistent/tools.py"])
    assert result.exit_code == 1
    assert (
        "not found" in result.output.lower()
        or "not found" in (result.output + getattr(result, "stderr", "")).lower()
    )


def test_tools_flag_missing_tools_dict(tmp_path):
    """--tools errors when Python file has no `tools` dict."""
    tools_py = tmp_path / "bad_tools.py"
    tools_py.write_text("x = 42\n")

    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 1
    assert "tools" in result.output.lower()


def test_tools_flag_tools_not_a_dict(tmp_path):
    """--tools errors when `tools` attribute is not a dict."""
    tools_py = tmp_path / "bad_tools.py"
    tools_py.write_text('tools = "not a dict"\n')

    prog = tmp_path / "script.cy"
    prog.write_text("return 1")

    result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 1
    assert "dict" in result.output.lower()


def test_tools_flag_native_tools_still_available(tmp_path):
    """--tools adds tools on top of native tools, doesn't replace them."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def double(x):
            return x * 2

        tools = {"double": double}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        items = [1, 2, 3]
        return {"len": len(items), "doubled": double(5)}
    """)
    )

    result = runner.invoke(app, ["run", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 0
    parsed = json.loads(result.output.strip())
    assert parsed == {"len": 3, "doubled": 10}


def test_tools_flag_works_with_check_command(tmp_path):
    """--tools works with cy check (not just cy run)."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        tools = {"greet": greet}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text('return greet("Alice")')

    result = runner.invoke(app, ["check", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 0
    assert "No errors found" in result.output


def test_tools_flag_works_with_compile_command(tmp_path):
    """--tools works with cy compile."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        tools = {"greet": greet}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text('return greet("Alice")')

    result = runner.invoke(app, ["compile", str(prog), "--tools", str(tools_py)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data


# ── --stub-tools: dry-run mode ────────────────────────────────────────────


def test_stub_tools_allows_unknown_tools(tmp_path):
    """--stub-tools lets scripts with unknown tools run (tools return null)."""
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        result = unknown_tool("hello")
        return result ?? "fallback"
    """)
    )

    # Without --stub-tools, this should fail
    result = runner.invoke(app, ["run", str(prog)])
    assert result.exit_code == 1

    # With --stub-tools, unknown tools return null
    result = runner.invoke(app, ["run", str(prog), "--stub-tools"])
    assert result.exit_code == 0
    assert "fallback" in result.output


def test_stub_tools_namespaced_unknown_tools(tmp_path):
    """--stub-tools works with namespaced unknown tool calls."""
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        data = app::threat_intel::ip_lookup(ip="8.8.8.8")
        return data ?? "no data"
    """)
    )

    result = runner.invoke(app, ["run", str(prog), "--stub-tools"])
    assert result.exit_code == 0
    assert "no data" in result.output


def test_stub_tools_native_tools_still_work(tmp_path):
    """--stub-tools doesn't affect native tools — they still execute normally."""
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        items = [1, 2, 3]
        return len(items)
    """)
    )

    result = runner.invoke(app, ["run", str(prog), "--stub-tools"])
    assert result.exit_code == 0
    assert "3" in result.output


def test_stub_tools_works_with_check_command(tmp_path):
    """--stub-tools works with cy check for scripts with unknown tools."""
    # Use multiple unknown tools — analyze_types only retries once for a single
    # unknown tool, so two unknown tools will fail without --stub-tools.
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        a = unknown_tool_1("hello")
        b = unknown_tool_2("world")
        return (a ?? "x") + (b ?? "y")
    """)
    )

    # Without --stub-tools, check should fail
    result = runner.invoke(app, ["check", str(prog)])
    assert result.exit_code == 1

    # With --stub-tools, check should pass
    result = runner.invoke(app, ["check", str(prog), "--stub-tools"])
    assert result.exit_code == 0
    assert "No errors found" in result.output


def test_stub_tools_works_with_compile_command(tmp_path):
    """--stub-tools works with cy compile for scripts with unknown tools."""
    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        result = unknown_tool("hello")
        return result ?? "fallback"
    """)
    )

    # Without --stub-tools, compile should fail
    result = runner.invoke(app, ["compile", str(prog)])
    assert result.exit_code == 1

    # With --stub-tools, compile should succeed
    result = runner.invoke(app, ["compile", str(prog), "--stub-tools"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data


def test_stub_tools_combined_with_tools_flag(tmp_path):
    """--stub-tools and --tools can be combined: known tools run, unknown stubs."""
    tools_py = tmp_path / "my_tools.py"
    tools_py.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        tools = {"greet": greet}
    """)
    )

    prog = tmp_path / "script.cy"
    prog.write_text(
        textwrap.dedent("""\
        greeting = greet("Alice")
        extra = unknown_tool("test")
        return {"greeting": greeting, "extra": extra ?? "stubbed"}
    """)
    )

    result = runner.invoke(
        app,
        ["run", str(prog), "--tools", str(tools_py), "--stub-tools"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output.strip())
    assert parsed == {"greeting": "Hello, Alice!", "extra": "stubbed"}
