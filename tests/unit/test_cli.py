"""Tests for the Typer-based CLI interface of the Cy language."""

import json
from pathlib import Path

from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()


# ── cy --version ───────────────────────────────────────────────────────────


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "cy " in result.output


def test_version_short_flag():
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert "cy " in result.output


# ── cy run ─────────────────────────────────────────────────────────────────


def test_run_basic_program(tmp_path):
    prog = tmp_path / "hello.cy"
    prog.write_text('name = "World"\noutput = "Hello, ${name}!"\nreturn output')

    result = runner.invoke(app, ["run", str(prog)])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_run_with_input(tmp_path):
    prog = tmp_path / "echo.cy"
    prog.write_text('output = "Got: ${input}"\nreturn output')

    result = runner.invoke(app, ["run", str(prog), "--input", "test data"])
    assert result.exit_code == 0
    assert "Got: test data" in result.output


def test_run_with_input_file(tmp_path):
    prog = tmp_path / "echo.cy"
    prog.write_text('output = "Got: ${input}"\nreturn output')

    input_f = tmp_path / "data.txt"
    input_f.write_text("file input")

    result = runner.invoke(app, ["run", str(prog), "--input-file", str(input_f)])
    assert result.exit_code == 0
    assert "Got: file input" in result.output


def test_run_csv_mode(tmp_path):
    prog = tmp_path / "list.cy"
    prog.write_text(
        'items = ["a", "b", "c"]\noutput = "Items: ${items}"\nreturn output'
    )

    result = runner.invoke(app, ["run", str(prog), "--mode", "csv"])
    assert result.exit_code == 0
    assert "a,b,c" in result.output


def test_run_file_not_found():
    result = runner.invoke(app, ["run", "/nonexistent/file.cy"])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_run_syntax_error(tmp_path):
    prog = tmp_path / "bad.cy"
    prog.write_text('output = "Unclosed string\nreturn output')

    result = runner.invoke(app, ["run", str(prog)])
    assert result.exit_code == 1


def test_run_type_checks_by_default(tmp_path):
    """cy run now type-checks by default (Model A pipeline)."""
    prog = tmp_path / "typed.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["run", str(prog)])
    assert result.exit_code == 0


def test_run_no_check_types_flag(tmp_path):
    """--no-check-types disables type checking."""
    prog = tmp_path / "typed.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["run", str(prog), "--no-check-types"])
    assert result.exit_code == 0


def test_run_from_json_plan(tmp_path):
    """cy run can execute a pre-compiled JSON plan."""
    # First compile a .cy file to get a plan
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")

    compile_result = runner.invoke(
        app,
        ["compile", str(prog), "-o", str(tmp_path / "plan.json"), "--no-check-types"],
    )
    assert compile_result.exit_code == 0

    # Now run from the plan
    result = runner.invoke(app, ["run", str(tmp_path / "plan.json")])
    assert result.exit_code == 0
    assert "42" in result.output


def test_run_from_json_plan_with_input(tmp_path):
    """cy run can execute a JSON plan with input data."""
    prog = tmp_path / "echo.cy"
    prog.write_text('output = "Got: ${input}"\nreturn output')

    compile_result = runner.invoke(
        app,
        ["compile", str(prog), "-o", str(tmp_path / "plan.json"), "--no-check-types"],
    )
    assert compile_result.exit_code == 0

    result = runner.invoke(
        app, ["run", str(tmp_path / "plan.json"), "--input", "hello"]
    )
    assert result.exit_code == 0
    assert "Got: hello" in result.output


def test_run_malformed_json_plan(tmp_path):
    """cy run errors on malformed JSON."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("not valid json {{{")

    result = runner.invoke(app, ["run", str(bad_json)])
    assert result.exit_code == 1
    assert "Invalid plan file" in result.output


def test_run_invalid_plan_structure(tmp_path):
    """cy run errors on valid JSON with an invalid node type."""
    bad_plan = tmp_path / "bad_plan.json"
    bad_plan.write_text(
        '{"version": "2.0", "nodes": [{"type": "bogus", "line": 1, "column": 1, "node_id": "n1"}]}'
    )

    result = runner.invoke(app, ["run", str(bad_plan)])
    assert result.exit_code == 1


# ── cy check ───────────────────────────────────────────────────────────────


def test_check_valid_program(tmp_path):
    prog = tmp_path / "valid.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["check", str(prog)])
    assert result.exit_code == 0
    assert "No errors found" in result.output


def test_check_file_not_found():
    result = runner.invoke(app, ["check", "/nonexistent/file.cy"])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_check_syntax_error(tmp_path):
    prog = tmp_path / "bad.cy"
    prog.write_text('output = "Unclosed string\nreturn output')

    result = runner.invoke(app, ["check", str(prog)])
    assert result.exit_code == 1


# ── cy compile ─────────────────────────────────────────────────────────────


def test_compile_outputs_json(tmp_path):
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["compile", str(prog)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "version" in data
    assert "nodes" in data


def test_compile_pretty(tmp_path):
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["compile", str(prog), "--pretty"])
    assert result.exit_code == 0
    # Pretty output has newlines and indentation
    assert "\n  " in result.output
    data = json.loads(result.output)
    assert "version" in data


def test_compile_file_not_found():
    result = runner.invoke(app, ["compile", "/nonexistent/file.cy"])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_compile_syntax_error(tmp_path):
    prog = tmp_path / "bad.cy"
    prog.write_text('output = "Unclosed string\nreturn output')

    result = runner.invoke(app, ["compile", str(prog)])
    assert result.exit_code == 1


def test_compile_type_checks_by_default(tmp_path):
    """cy compile now type-checks by default (Model A pipeline)."""
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["compile", str(prog)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data


def test_compile_no_check_types_flag(tmp_path):
    """--no-check-types disables type checking in compile."""
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")

    result = runner.invoke(app, ["compile", str(prog), "--no-check-types"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data


def test_compile_output_flag(tmp_path):
    """cy compile -o writes plan to a file."""
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 42\nreturn x")
    out = tmp_path / "plan.json"

    result = runner.invoke(
        app, ["compile", str(prog), "-o", str(out), "--no-check-types"]
    )
    assert result.exit_code == 0
    assert out.exists()

    data = json.loads(out.read_text())
    assert "version" in data
    assert "nodes" in data


# ── cy install ─────────────────────────────────────────────────────────────


def test_install_claude_code_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["install", "claude-code", "--project"])
    assert result.exit_code == 0
    assert "Installed" in result.output

    skill_dir = tmp_path / ".claude" / "skills" / "cy-language-programming"
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "reference").is_dir()


def test_install_claude_code_global(tmp_path, monkeypatch):
    # Use a fake home directory to avoid touching real ~/.claude/
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = runner.invoke(app, ["install", "claude-code"])
    assert result.exit_code == 0
    assert "Installed" in result.output

    skill_dir = tmp_path / ".claude" / "skills" / "cy-language-programming"
    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()


def test_install_claude_code_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Create a fake pre-existing skill directory with a marker file
    skill_dir = tmp_path / ".claude" / "skills" / "cy-language-programming"
    skill_dir.mkdir(parents=True)
    marker = skill_dir / "marker.txt"
    marker.write_text("old")

    # Install — should replace the entire directory
    result = runner.invoke(app, ["install", "claude-code", "--project"])
    assert result.exit_code == 0
    assert not marker.exists()  # marker was removed by the overwrite
    assert (skill_dir / "SKILL.md").exists()


def test_install_unknown_target():
    result = runner.invoke(app, ["install", "unknown-tool"])
    assert result.exit_code == 1
    assert "Unknown target" in result.output


def test_install_codex_not_supported():
    result = runner.invoke(app, ["install", "codex"])
    assert result.exit_code == 1
    assert "not yet supported" in result.output


# ── end-to-end: compile → run pipeline ──────────────────────


def test_compile_then_run_pipeline(tmp_path):
    """Full pipeline: cy compile -o plan.json && cy run plan.json."""
    prog = tmp_path / "add.cy"
    prog.write_text("x = len([1, 2, 3])\nreturn x")
    plan_file = tmp_path / "plan.json"

    # Compile to file
    c_result = runner.invoke(
        app, ["compile", str(prog), "-o", str(plan_file), "--no-check-types"]
    )
    assert c_result.exit_code == 0
    assert plan_file.exists()

    # Run from compiled plan
    r_result = runner.invoke(app, ["run", str(plan_file)])
    assert r_result.exit_code == 0
    assert "3" in r_result.output


def test_compile_then_run_with_input(tmp_path):
    """Pipeline: compile with interpolation, run with input."""
    prog = tmp_path / "greet.cy"
    prog.write_text('msg = "Hello, ${input}!"\nreturn msg')
    plan_file = tmp_path / "plan.json"

    c_result = runner.invoke(
        app, ["compile", str(prog), "-o", str(plan_file), "--no-check-types"]
    )
    assert c_result.exit_code == 0

    r_result = runner.invoke(app, ["run", str(plan_file), "--input", "World"])
    assert r_result.exit_code == 0
    assert "Hello, World!" in r_result.output


def test_compile_source_and_plan_produce_same_output(tmp_path):
    """Verify running from source and from plan give identical output."""
    prog = tmp_path / "calc.cy"
    prog.write_text("x = 10 + 5\nreturn x")
    plan_file = tmp_path / "plan.json"

    # Run from source (no type checking to match plan execution)
    source_result = runner.invoke(app, ["run", str(prog), "--no-check-types"])
    assert source_result.exit_code == 0

    # Compile and run from plan
    runner.invoke(app, ["compile", str(prog), "-o", str(plan_file), "--no-check-types"])
    plan_result = runner.invoke(app, ["run", str(plan_file)])
    assert plan_result.exit_code == 0

    assert source_result.output == plan_result.output


# ── no subcommand ──────────────────────────────────────────────────────────


def test_no_args_shows_help():
    result = runner.invoke(app, [])
    # Typer/Click may exit with 0 or 2 when showing help via no_args_is_help
    assert result.exit_code in (0, 2)
    assert "Usage" in result.output


# ── cy visualize ───────────────────────────────────────────────────────────


def test_visualize_dot_stdout(tmp_path):
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 1\ny = x + 2\nreturn y")

    result = runner.invoke(app, ["visualize", str(prog)])
    assert result.exit_code == 0
    assert "digraph ExecutionPlan" in result.output
    assert "rankdir=LR" in result.output


def test_visualize_dot_to_file(tmp_path):
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 1\ny = x + 2\nreturn y")
    out = tmp_path / "graph.dot"

    result = runner.invoke(app, ["visualize", str(prog), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "digraph ExecutionPlan" in out.read_text()


def test_visualize_invalid_format(tmp_path):
    prog = tmp_path / "simple.cy"
    prog.write_text("x = 1\nreturn x")

    result = runner.invoke(app, ["visualize", str(prog), "--format", "mermaid"])
    assert result.exit_code == 1


def test_visualize_file_not_found():
    result = runner.invoke(app, ["visualize", "nonexistent.cy"])
    assert result.exit_code == 1


def test_visualize_contains_node_types(tmp_path):
    prog = tmp_path / "cond.cy"
    prog.write_text(
        'x = 5\nif (x > 3) {\n    y = "big"\n} else {\n    y = "small"\n}\nreturn y'
    )

    result = runner.invoke(app, ["visualize", str(prog)])
    assert result.exit_code == 0
    dot = result.output
    # Should have assignment, comparison, conditional, and return nodes
    assert "assign" in dot
    assert "comparison" in dot
    assert "conditional" in dot
    assert "return" in dot


def test_visualize_no_check_types_flag(tmp_path):
    """--no-check-types should allow visualizing scripts that fail type checking."""
    prog = tmp_path / "typed.cy"
    # Access fields on a null-typed result — will fail type checking
    prog.write_text("x = some_tool()\ny = x.field\nreturn y")

    result = runner.invoke(app, ["visualize", str(prog), "--stub-tools"])
    # With stub tools, type errors may still occur; --no-check-types bypasses them
    result2 = runner.invoke(
        app, ["visualize", str(prog), "--stub-tools", "--no-check-types"]
    )
    assert result2.exit_code == 0
    assert "digraph ExecutionPlan" in result2.output
