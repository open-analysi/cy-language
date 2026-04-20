"""cy run — compile, typecheck, and execute a Cy program (or run a pre-compiled plan)."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import typer

from cy_language import Cy
from cy_language.cli._error_handler import (
    handle_cli_errors,
    load_external_tools,
    require_file,
)
from cy_language.execution_plan import ExecutionPlan
from cy_language.executor import execute_plan


def _parse_mcp_server(value: str) -> tuple[str, str]:
    """Parse a ``name=url`` string into (name, url).

    Raises:
        typer.BadParameter: If value is not in ``name=url`` format.
    """
    if "=" not in value:
        raise typer.BadParameter(
            f"Invalid format '{value}'. Expected name=url (e.g. demo=http://localhost:8000)"
        )
    name, url = value.split("=", 1)
    if not name or not url:
        raise typer.BadParameter(
            f"Invalid format '{value}'. Both name and url are required."
        )
    return name, url


def run(
    file: Path = typer.Argument(..., help="Path to a .cy program or .json plan file."),
    input: str | None = typer.Option(
        None, "--input", "-i", help="Input data for the program."
    ),
    input_file: Path | None = typer.Option(
        None, "--input-file", "-f", help="Read input data from a file."
    ),
    mode: str = typer.Option(
        "markdown",
        "--mode",
        "-m",
        help="Interpolation mode for lists (markdown, csv, xml).",
    ),
    tag: str = typer.Option("item", "--tag", "-t", help="Item tag name for XML mode."),
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
    mcp_server: list[str] | None = typer.Option(
        None,
        "--mcp-server",
        help="HTTP MCP server in name=url format (repeatable). Requires cy-language[mcp].",
    ),
    mcp_stdio: list[str] | None = typer.Option(
        None,
        "--mcp-stdio",
        help="Stdio MCP server in 'name=command args...' format (repeatable). Requires mcp package.",
    ),
) -> None:
    """Compile, typecheck, and execute a Cy program (or run a pre-compiled JSON plan)."""
    require_file(file)
    external_tools = load_external_tools(tools)

    # Parse HTTP MCP server configs
    mcp_servers: dict[str, dict[str, str]] | None = None
    if mcp_server:
        mcp_servers = {}
        for entry in mcp_server:
            try:
                name, url = _parse_mcp_server(entry)
            except typer.BadParameter as e:
                print(f"Error: {e}", file=sys.stderr)
                raise typer.Exit(code=1)
            mcp_servers[name] = {"base_url": url, "mcp_id": name}

    # Parse stdio MCP server configs
    mcp_stdio_servers: list[tuple[str, str, list[str]]] | None = None
    if mcp_stdio:
        from cy_language.cli.mcp_stdio_bridge import parse_mcp_stdio_arg

        mcp_stdio_servers = []
        for entry in mcp_stdio:
            try:
                name, command, args = parse_mcp_stdio_arg(entry)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                raise typer.Exit(code=1)
            mcp_stdio_servers.append((name, command, args))

    # Resolve input data
    input_data = input
    if input_file is not None:
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            raise typer.Exit(code=1)
        input_data = input_file.read_text()

    check_types = not no_check_types
    needs_async = bool(mcp_servers) or bool(mcp_stdio_servers)

    def _do_run() -> None:
        if file.suffix == ".json":
            if stub_tools:
                print(
                    "Warning: --stub-tools is ignored for pre-compiled plans.",
                    file=sys.stderr,
                )
            if mcp_stdio_servers or mcp_servers:
                print(
                    "Warning: --mcp-stdio/--mcp-server are ignored for pre-compiled plans.",
                    file=sys.stderr,
                )
            _run_from_plan(file, input_data, mode, tag, external_tools)
        elif needs_async:
            _run_from_source_async(
                file,
                input_data,
                mode,
                tag,
                check_types,
                external_tools,
                stub_tools,
                mcp_servers,
                mcp_stdio_servers,
            )
        else:
            _run_from_source(
                file, input_data, mode, tag, check_types, external_tools, stub_tools
            )

    handle_cli_errors(_do_run)


def _run_from_source(
    file: Path,
    input_data: str | None,
    mode: str,
    tag: str,
    check_types: bool,
    external_tools: dict | None = None,
    stub_tools: bool = False,
) -> None:
    """Run a .cy source file."""
    program = file.read_text()
    interpreter = Cy(
        tools=external_tools,
        interpolation_mode=mode,
        item_tag=tag,
        check_types=check_types,
        stub_tools=stub_tools,
    )
    output = interpreter.run(program, input_data)
    print(output)


def _run_from_source_async(
    file: Path,
    input_data: str | None,
    mode: str,
    tag: str,
    check_types: bool,
    external_tools: dict | None = None,
    stub_tools: bool = False,
    mcp_servers: dict[str, dict[str, str]] | None = None,
    mcp_stdio_servers: list[tuple[str, str, list[str]]] | None = None,
) -> None:
    """Run a .cy source file with async support (needed for MCP servers)."""

    async def _async_run() -> str:
        # Connect to stdio MCP servers and collect their tools
        stdio_tools: dict[str, Any] = {}
        bridge = None

        try:
            if mcp_stdio_servers:
                from cy_language.cli.mcp_stdio_bridge import StdioMCPBridge

                bridge = StdioMCPBridge()
                await bridge.__aenter__()
                for name, command, args in mcp_stdio_servers:
                    await bridge.connect(name, command, args)
                stdio_tools = bridge.get_tools()

            # Merge all tool sources: external file tools + stdio MCP tools
            all_tools: dict[str, Any] | None = None
            if external_tools or stdio_tools:
                all_tools = {}
                if external_tools:
                    all_tools.update(external_tools)
                if stdio_tools:
                    all_tools.update(stdio_tools)

            interpreter = await Cy.create_async(
                tools=all_tools,
                interpolation_mode=mode,
                item_tag=tag,
                check_types=check_types,
                mcp_servers=mcp_servers,
                stub_tools=stub_tools,
            )
            return await interpreter.run_async(program, input_data)
        finally:
            if bridge is not None:
                await bridge.__aexit__(None, None, None)

    program = file.read_text()
    output = asyncio.run(_async_run())
    print(output)


def _run_from_plan(
    file: Path,
    input_data: str | None,
    mode: str,
    tag: str,
    external_tools: dict | None = None,
) -> None:
    """Run a pre-compiled JSON plan file."""
    raw = file.read_text()
    try:
        plan = ExecutionPlan.from_json(raw)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error: Invalid plan file: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

    # Create a Cy instance for its tools (no type checking needed — already compiled)
    interpreter = Cy(interpolation_mode=mode, item_tag=tag, tools=external_tools)
    output = execute_plan(
        plan,
        input_data=input_data,
        tools=interpreter.tools,
        interpolation_mode=mode,
        item_tag=tag,
    )
    print(output)
