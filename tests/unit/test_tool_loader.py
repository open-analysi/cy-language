"""Tests for cy_language.cli.tool_loader — loading tools from Python files."""

import textwrap
from pathlib import Path

import pytest

from cy_language.cli.tool_loader import load_tools_from_file


def test_load_simple_tools(tmp_path):
    """Loads a file with plain callable tools."""
    f = tmp_path / "tools.py"
    f.write_text(
        textwrap.dedent("""\
        def add(a, b):
            return a + b

        tools = {"add": add}
    """)
    )

    result = load_tools_from_file(f)
    assert "add" in result
    assert result["add"](2, 3) == 5


def test_load_multiple_tools(tmp_path):
    """Loads multiple tools from one file."""
    f = tmp_path / "tools.py"
    f.write_text(
        textwrap.dedent("""\
        def greet(name):
            return f"Hello, {name}!"

        def farewell(name):
            return f"Goodbye, {name}!"

        tools = {"greet": greet, "farewell": farewell}
    """)
    )

    result = load_tools_from_file(f)
    assert len(result) == 2
    assert result["greet"]("Alice") == "Hello, Alice!"
    assert result["farewell"]("Bob") == "Goodbye, Bob!"


def test_load_namespaced_tools(tmp_path):
    """Supports app:: namespaced tool keys."""
    f = tmp_path / "tools.py"
    f.write_text(
        textwrap.dedent("""\
        def lookup(ip):
            return {"ip": ip}

        tools = {"app::threat::lookup": lookup}
    """)
    )

    result = load_tools_from_file(f)
    assert "app::threat::lookup" in result


def test_file_not_found():
    """Raises FileNotFoundError for nonexistent file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        load_tools_from_file(Path("/nonexistent/tools.py"))


def test_missing_tools_attribute(tmp_path):
    """Raises ValueError if file has no `tools` variable."""
    f = tmp_path / "tools.py"
    f.write_text("x = 42\n")

    with pytest.raises(ValueError, match="must define a `tools` dict"):
        load_tools_from_file(f)


def test_tools_not_a_dict(tmp_path):
    """Raises ValueError if `tools` is not a dict."""
    f = tmp_path / "tools.py"
    f.write_text('tools = "not a dict"\n')

    with pytest.raises(ValueError, match="must be a dict"):
        load_tools_from_file(f)


def test_tools_list_not_a_dict(tmp_path):
    """Raises ValueError if `tools` is a list instead of dict."""
    f = tmp_path / "tools.py"
    f.write_text("tools = [1, 2, 3]\n")

    with pytest.raises(ValueError, match="must be a dict"):
        load_tools_from_file(f)


def test_import_error_in_tools_file(tmp_path):
    """Propagates import errors from the user's tools file."""
    f = tmp_path / "tools.py"
    f.write_text("import nonexistent_module_xyz\ntools = {}\n")

    with pytest.raises(ModuleNotFoundError):
        load_tools_from_file(f)


def test_syntax_error_in_tools_file(tmp_path):
    """Propagates syntax errors from the user's tools file."""
    f = tmp_path / "tools.py"
    f.write_text("def broken(\ntools = {}\n")

    with pytest.raises(SyntaxError):
        load_tools_from_file(f)
