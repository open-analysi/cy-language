"""cy visualize — render a Cy program's execution plan as a GraphViz diagram."""

import shutil
import subprocess
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
from cy_language.plan_visualization import PlanVisualizer
from cy_language.tool_resolver import build_tool_resolver

_SUPPORTED_FORMATS = ["dot", "png", "svg", "pdf"]


def visualize(
    file: Path = typer.Argument(..., help="Path to a .cy program file."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file. Defaults to <input>.<format>. Use '-' to print DOT to stdout.",
    ),
    format: str = typer.Option(
        "dot",
        "--format",
        "-f",
        help=f"Output format: {', '.join(_SUPPORTED_FORMATS)}. Requires graphviz for non-dot formats.",
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
    """Visualize a Cy program's execution plan as a GraphViz diagram.

    Outputs DOT source by default. Pass --format png/svg/pdf to render an image
    (requires the `dot` CLI from graphviz to be installed).

    Examples:

        cy visualize script.cy                        # print DOT to stdout
        cy visualize script.cy -f png -o graph.png    # render PNG
        cy visualize script.cy -f svg                 # render SVG to script.svg
    """
    fmt = format.lower()
    if fmt not in _SUPPORTED_FORMATS:
        print(
            f"Error: unsupported format '{fmt}'. Choose from: {', '.join(_SUPPORTED_FORMATS)}",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    require_file(file)
    external_tools = load_external_tools(tools)
    code = file.read_text()
    check_types = not no_check_types

    def _do_visualize() -> None:
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

        viz = PlanVisualizer()
        dot_source = viz.to_graphviz(plan)

        # DOT format: print to stdout or write to file
        if fmt == "dot":
            dest = output
            if dest is None or str(dest) == "-":
                print(dot_source)
            else:
                dest.write_text(dot_source)
                print(f"DOT written to {dest}", file=sys.stderr)
            return

        # Non-dot formats: require graphviz `dot` binary
        if not shutil.which("dot"):
            print(
                "Error: 'dot' (graphviz) not found in PATH. "
                "Install it with: brew install graphviz  OR  apt install graphviz",
                file=sys.stderr,
            )
            raise typer.Exit(code=1)

        dest = output if output is not None else file.with_suffix(f".{fmt}")
        result = subprocess.run(
            ["dot", f"-T{fmt}", "-o", str(dest)],
            input=dot_source.encode(),
            capture_output=True,
        )
        if result.returncode != 0:
            print(
                f"Error: graphviz failed:\n{result.stderr.decode()}",
                file=sys.stderr,
            )
            raise typer.Exit(code=1)

        print(f"Graph written to {dest}", file=sys.stderr)

    handle_cli_errors(_do_visualize)
