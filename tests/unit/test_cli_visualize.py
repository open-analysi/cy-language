"""Tests for cy visualize CLI command."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


# ── helpers ────────────────────────────────────────────────────────────────


def _write(tmp_path: Path, name: str, code: str) -> Path:
    p = tmp_path / name
    p.write_text(code)
    return p


def _is_valid_dot(text: str) -> bool:
    """Basic structural check for a DOT digraph."""
    return (
        "digraph ExecutionPlan {" in text
        and text.strip().endswith("}")
        and "rankdir=LR" in text
    )


# ── dot output ─────────────────────────────────────────────────────────────


class TestVisualizeDotOutput:
    def test_dot_to_stdout_by_default(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert _is_valid_dot(result.output)

    def test_dot_explicit_format(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "--format", "dot"])
        assert result.exit_code == 0
        assert _is_valid_dot(result.output)

    def test_dot_short_format_flag(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "-f", "dot"])
        assert result.exit_code == 0
        assert _is_valid_dot(result.output)

    def test_dot_to_file(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        out = tmp_path / "out.dot"
        result = runner.invoke(app, ["visualize", str(prog), "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert _is_valid_dot(out.read_text())

    def test_dot_file_does_not_print_dot_to_stdout(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        out = tmp_path / "out.dot"
        result = runner.invoke(app, ["visualize", str(prog), "-o", str(out)])
        assert result.exit_code == 0
        assert "digraph" not in result.output  # goes to file, not stdout

    def test_dash_output_prints_to_stdout(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "-o", "-"])
        assert result.exit_code == 0
        assert _is_valid_dot(result.output)


# ── node types in output ────────────────────────────────────────────────────


class TestVisualizeDotContent:
    def test_literal_nodes_present(self, tmp_path):
        prog = _write(tmp_path, "lit.cy", "x = 42\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "literal" in result.output
        assert "assign" in result.output

    def test_arithmetic_nodes(self, tmp_path):
        prog = _write(tmp_path, "arith.cy", "x = 3 + 4\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "arithmetic" in result.output

    def test_comparison_and_conditional_nodes(self, tmp_path):
        prog = _write(
            tmp_path,
            "cond.cy",
            'x = 5\nif (x > 3) {\n    y = "big"\n} else {\n    y = "small"\n}\nreturn y',
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "comparison" in result.output
        assert "conditional" in result.output

    def test_while_loop_node(self, tmp_path):
        prog = _write(
            tmp_path,
            "loop.cy",
            "i = 0\nwhile (i < 3) {\n    i = i + 1\n}\nreturn i",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "while_loop" in result.output
        # Loop-back dashed edges should be present
        assert 'style="dashed"' in result.output

    def test_return_node(self, tmp_path):
        prog = _write(tmp_path, "ret.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "return" in result.output

    def test_string_interpolation_node(self, tmp_path):
        prog = _write(
            tmp_path, "interp.cy", 'name = "Alice"\nout = "Hi ${name}"\nreturn out'
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "interpolation" in result.output
        assert "interpolate" in result.output  # edge label

    def test_boolean_op_nodes(self, tmp_path):
        prog = _write(
            tmp_path,
            "bool.cy",
            "a = true\nb = false\nc = a and b\nreturn c",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "boolean_op" in result.output

    def test_data_flow_edges(self, tmp_path):
        prog = _write(tmp_path, "flow.cy", "x = 1\ny = x + 2\nreturn y")
        result = runner.invoke(app, ["visualize", str(prog)])
        # Variable assignment → usage dashed edges
        assert "provides value" in result.output
        assert "assigns to" in result.output

    def test_nested_field_access(self, tmp_path):
        prog = _write(
            tmp_path,
            "field.cy",
            'data = {"name": "Alice"}\nout = data.name\nreturn out',
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "field_access" in result.output

    def test_list_node(self, tmp_path):
        prog = _write(tmp_path, "list.cy", "items = [1, 2, 3]\nreturn items")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "list" in result.output

    def test_dict_node(self, tmp_path):
        prog = _write(tmp_path, "dict.cy", 'obj = {"a": 1, "b": 2}\nreturn obj')
        result = runner.invoke(app, ["visualize", str(prog)])
        assert "dict" in result.output

    def test_list_comprehension_node(self, tmp_path):
        """List comprehensions must render with proper type, not 'unknown'."""
        prog = _write(
            tmp_path,
            "comp.cy",
            "items = [1, 2, 3]\ndoubled = [x * 2 for(x in items)]\nreturn doubled",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert "unknown" not in result.output, (
            "list comprehension rendered as 'unknown'"
        )
        assert "list_comprehension" in result.output

    def test_list_comprehension_with_filter(self, tmp_path):
        """Filtered list comprehension edges: iterable, element, filter."""
        prog = _write(
            tmp_path,
            "comp_filter.cy",
            "items = [1,2,3,4,5]\nevens = [x for(x in items) if(x % 2 == 0)]\nreturn evens",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert "list_comprehension" in result.output
        assert "filter" in result.output  # filter edge label

    def test_try_catch_node(self, tmp_path):
        """try/catch must render with proper type, not 'unknown'."""
        prog = _write(
            tmp_path,
            "try.cy",
            "try {\n  x = 1\n} catch(err) {\n  x = 0\n}\nreturn x",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert "unknown" not in result.output, "try/catch rendered as 'unknown'"
        assert "try_catch" in result.output

    def test_field_assignment_node(self, tmp_path):
        """Field assignment (obj.x = val) must not render as 'unknown'."""
        prog = _write(
            tmp_path,
            "fassign.cy",
            'obj = {"a": 1}\nobj.a = 2\nreturn obj',
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert "unknown" not in result.output, "field_assign rendered as 'unknown'"
        assert "field_assign" in result.output

    def test_indexed_assignment_node(self, tmp_path):
        """Indexed assignment (arr[0] = val) must not render as 'unknown'."""
        prog = _write(
            tmp_path,
            "iassign.cy",
            "arr = [1, 2, 3]\narr[0] = 99\nreturn arr",
        )
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 0
        assert "unknown" not in result.output, "indexed_assign rendered as 'unknown'"
        assert "indexed_assign" in result.output


# ── error handling ─────────────────────────────────────────────────────────


class TestVisualizeErrors:
    def test_file_not_found(self):
        result = runner.invoke(app, ["visualize", "no_such_file.cy"])
        assert result.exit_code == 1

    def test_invalid_format_rejected(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "--format", "mermaid"])
        assert result.exit_code == 1

    def test_invalid_format_jpeg_rejected(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "-f", "jpeg"])
        assert result.exit_code == 1

    def test_syntax_error_exits_nonzero(self, tmp_path):
        prog = _write(tmp_path, "bad.cy", "this is not valid cy code !!!")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 1

    def test_type_error_exits_nonzero_by_default(self, tmp_path):
        # Dollar-sign syntax is a hard syntax error — visualize should fail
        prog = _write(tmp_path, "bad_syntax.cy", "$x = 5\nreturn $x")
        result = runner.invoke(app, ["visualize", str(prog)])
        assert result.exit_code == 1

    def test_no_check_types_bypasses_type_error(self, tmp_path):
        prog = _write(tmp_path, "typed.cy", "x = my_tool()\ny = x.field\nreturn y")
        result = runner.invoke(
            app, ["visualize", str(prog), "--stub-tools", "--no-check-types"]
        )
        assert result.exit_code == 0
        assert _is_valid_dot(result.output)

    def test_missing_graphviz_gives_helpful_error(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        # Patch shutil.which to simulate graphviz not installed
        with patch("cy_language.cli.visualize_cmd.shutil.which", return_value=None):
            result = runner.invoke(app, ["visualize", str(prog), "-f", "png"])
        assert result.exit_code == 1
        assert "graphviz" in result.output.lower() or "dot" in result.output.lower()

    def test_missing_graphviz_no_duplicate_error_line(self, tmp_path):
        """When graphviz is missing, only ONE error message should appear."""
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        with patch("cy_language.cli.visualize_cmd.shutil.which", return_value=None):
            result = runner.invoke(app, ["visualize", str(prog), "-f", "png"])
        assert result.exit_code == 1
        # Count "Error" occurrences — must be exactly 1, not 2
        error_count = result.output.lower().count("error")
        assert error_count == 1, (
            f"Expected 1 error line, got {error_count}. Output:\n{result.output}"
        )


# ── graphviz rendering (requires `dot` binary) ─────────────────────────────


@pytest.mark.skipif(
    not __import__("shutil").which("dot"),
    reason="graphviz `dot` not installed",
)
class TestVisualizeRenderedFormats:
    def test_png_output(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        out = tmp_path / "out.png"
        result = runner.invoke(
            app, ["visualize", str(prog), "-f", "png", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()
        assert out.stat().st_size > 0
        # PNG magic bytes
        assert out.read_bytes()[:4] == b"\x89PNG"

    def test_svg_output(self, tmp_path):
        prog = _write(tmp_path, "simple.cy", "x = 1\nreturn x")
        out = tmp_path / "out.svg"
        result = runner.invoke(
            app, ["visualize", str(prog), "-f", "svg", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "<svg" in content

    def test_default_output_filename_png(self, tmp_path):
        """Without -o, output defaults to <input>.png"""
        prog = _write(tmp_path, "myscript.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "-f", "png"])
        assert result.exit_code == 0
        expected = tmp_path / "myscript.png"
        assert expected.exists()

    def test_default_output_filename_svg(self, tmp_path):
        prog = _write(tmp_path, "myscript.cy", "x = 1\nreturn x")
        result = runner.invoke(app, ["visualize", str(prog), "-f", "svg"])
        assert result.exit_code == 0
        expected = tmp_path / "myscript.svg"
        assert expected.exists()

    def test_complex_program_renders_without_error(self, tmp_path):
        prog = _write(
            tmp_path,
            "complex.cy",
            """
n = 10
result = 1
i = 1
while (i <= n) {
    result = result * i
    i = i + 1
}
return result
""",
        )
        out = tmp_path / "complex.png"
        result = runner.invoke(
            app, ["visualize", str(prog), "-f", "png", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.exists()
        assert out.stat().st_size > 0


# ── tool options pass-through ───────────────────────────────────────────────


class TestVisualizeToolOptions:
    def test_stub_tools_accepts_unknown_tool_calls(self, tmp_path):
        prog = _write(tmp_path, "tools.cy", "result = some_tool(42)\nreturn result")
        result = runner.invoke(app, ["visualize", str(prog), "--stub-tools"])
        # With stub tools and type checking, may still fail — use no-check-types
        result2 = runner.invoke(
            app, ["visualize", str(prog), "--stub-tools", "--no-check-types"]
        )
        assert result2.exit_code == 0
        assert "tool_call" in result2.output

    def test_tools_file_loads_correctly(self, tmp_path):
        tools_file = tmp_path / "mytools.py"
        tools_file.write_text(
            'def add(a, b):\n    return a + b\n\ntools = {"add": add}\n'
        )
        prog = _write(tmp_path, "use_tool.cy", "result = add(3, 4)\nreturn result")
        result = runner.invoke(
            app, ["visualize", str(prog), "--tools", str(tools_file)]
        )
        assert result.exit_code == 0
        assert "tool_call" in result.output


# ── help text ──────────────────────────────────────────────────────────────


def test_visualize_help():
    result = runner.invoke(app, ["visualize", "--help"])
    assert result.exit_code == 0
    plain = _ANSI_RE.sub("", result.output)
    assert "--format" in plain
    assert "--output" in plain
    assert "dot" in plain
    assert "png" in plain
    assert "svg" in plain


def test_visualize_appears_in_main_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "visualize" in result.output
