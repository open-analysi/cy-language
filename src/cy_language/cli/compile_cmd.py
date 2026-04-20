"""cy compile — compile a Cy program and emit its execution plan as JSON."""

import sys
from pathlib import Path

import typer

from cy_language.cli._error_handler import (
    handle_cli_errors,
    load_external_tools,
    require_file,
)
from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.tool_resolver import build_tool_resolver


def compile(
    file: Path = typer.Argument(..., help="Path to a .cy program file."),
    pretty: bool = typer.Option(
        False, "--pretty", "-p", help="Pretty-print the JSON output."
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write plan to a file instead of stdout."
    ),
    no_check_types: bool = typer.Option(
        False, "--no-check-types", help="Disable type checking (enabled by default)."
    ),
    tools: Path | None = typer.Option(
        None,
        "--tools",
        help="Python file with a `tools` dict to register as external tools.",
    ),
    stub_tools: bool = typer.Option(
        False,
        "--stub-tools",
        help="Accept unknown tools (they return null). Useful for dry-runs.",
    ),
) -> None:
    """Compile a Cy program and emit the execution plan as JSON."""
    require_file(file)
    external_tools = load_external_tools(tools)

    code = file.read_text()
    check_types = not no_check_types

    def _do_compile() -> None:
        parser = Parser()
        ast = parser.parse_only(code)
        tool_resolver = build_tool_resolver(
            custom_tools=external_tools,
            stub_unknown=stub_tools,
        )
        plan = compile_cy_program(
            ast,
            source_file=str(file),
            tool_resolver=tool_resolver,
            check_types=check_types,
        )

        if pretty:
            import json

            plan_dict = json.loads(plan.to_json())
            json_output = json.dumps(plan_dict, indent=2)
        else:
            json_output = plan.to_json()

        if output:
            output.write_text(json_output)
            print(f"Plan written to {output}", file=sys.stderr)
        else:
            print(json_output)

    handle_cli_errors(_do_compile)
