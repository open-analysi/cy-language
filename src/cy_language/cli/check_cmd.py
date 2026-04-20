"""cy check — typecheck a Cy program without executing it."""

from pathlib import Path

import typer

from cy_language.cli._error_handler import (
    handle_cli_errors,
    load_external_tools,
    require_file,
)
from cy_language.type_analysis_api import analyze_types


def check(
    file: Path = typer.Argument(..., help="Path to a .cy program file."),
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
    """Compile and typecheck a Cy program (no execution)."""
    require_file(file)
    external_tools = load_external_tools(tools)
    code = file.read_text()

    def _do_check() -> None:
        result = analyze_types(
            code,
            custom_tools=external_tools,
            stub_unknown=stub_tools,
        )
        print(f"No errors found. Output type: {result}")

    handle_cli_errors(_do_check)
