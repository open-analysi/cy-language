"""Bridge between stdio-based MCP servers and Cy's tool system.

Connects to an MCP server via stdio transport, discovers its tools, and
exposes them as async callables for the Cy runtime.

Requires the ``mcp`` package: ``pip install mcp`` or ``pip install cy-language[mcp]``.
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Any

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError:
    ClientSession = None  # type: ignore[assignment,misc]
    StdioServerParameters = None  # type: ignore[assignment,misc]
    stdio_client = None  # type: ignore[assignment]

_MISSING_MCP_MSG = (
    "The 'mcp' package is required for --mcp-stdio support. "
    "Install it with: pip install mcp"
)


def _require_mcp() -> None:
    if ClientSession is None:
        raise ImportError(_MISSING_MCP_MSG)


class StdioMCPBridge:
    """Manages stdio MCP server connections and exposes tools as callables.

    Usage::

        async with StdioMCPBridge() as bridge:
            await bridge.connect("demo", "uv", ["run", "--with", "mcp[cli]", "mcp", "run", "server.py"])
            tools = bridge.get_tools()  # {"mcp::demo::add": <callable>, ...}
    """

    def __init__(self) -> None:
        _require_mcp()
        self._exit_stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._tool_metadata: dict[str, dict[str, Any]] = {}  # fqn → tool info

    async def __aenter__(self) -> StdioMCPBridge:
        await self._exit_stack.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self._exit_stack.__aexit__(*exc)

    async def connect(self, server_name: str, command: str, args: list[str]) -> None:
        """Connect to a stdio MCP server and discover its tools.

        Args:
            server_name: Logical name for this server (used in tool FQNs).
            command: The executable to run (e.g. "uv", "npx", "python").
            args: Arguments to pass to the command.
        """
        params = StdioServerParameters(command=command, args=args)

        # stdio_client needs a real stderr with fileno() for subprocess.
        # When running inside test runners (e.g. Typer CliRunner), stderr is
        # an in-memory stream without fileno(). Fall back to devnull.
        errlog = sys.stderr
        try:
            errlog.fileno()
        except (io.UnsupportedOperation, AttributeError, OSError):
            errlog = self._exit_stack.enter_context(open(os.devnull, "w"))  # noqa: SIM115

        # stdio_client is a context manager that yields (read_stream, write_stream)
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(params, errlog=errlog)
        )

        # Create and initialize session
        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self._sessions[server_name] = session

        # Discover tools
        result = await session.list_tools()
        for tool in result.tools:
            fqn = f"mcp::{server_name}::{tool.name}"
            self._tool_metadata[fqn] = {
                "server": server_name,
                "tool_name": tool.name,
                "description": tool.description or "",
                "schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
            }

    def get_tools(self) -> dict[str, Any]:
        """Return a dict of tool FQN → async callable for all discovered tools.

        Each callable accepts keyword arguments and returns the tool result.
        """
        return {
            fqn: self._make_tool_callable(meta["server"], meta["tool_name"])
            for fqn, meta in self._tool_metadata.items()
        }

    def _make_tool_callable(self, server_name: str, tool_name: str) -> Any:
        """Create an async callable that invokes a specific MCP tool."""
        session = self._sessions[server_name]

        async def call_tool(**kwargs: Any) -> Any:
            result = await session.call_tool(tool_name, arguments=kwargs)
            if not result.content:
                return None
            texts = [item.text for item in result.content if hasattr(item, "text")]
            if len(texts) == 1:
                try:
                    return json.loads(texts[0])
                except (json.JSONDecodeError, TypeError):
                    return texts[0]
            return "\n".join(texts) if texts else None

        return call_tool

    def get_tool_descriptions(self) -> dict[str, str]:
        """Return a dict of tool FQN → description for all discovered tools."""
        return {fqn: meta["description"] for fqn, meta in self._tool_metadata.items()}


def parse_mcp_stdio_arg(value: str) -> tuple[str, str, list[str]]:
    """Parse a ``name=command args...`` string into (name, command, args).

    Examples:
        "demo=uv run --with mcp mcp run server.py"
        → ("demo", "uv", ["run", "--with", "mcp", "mcp", "run", "server.py"])

        "calc=python server.py"
        → ("calc", "python", ["server.py"])

    Raises:
        ValueError: If the format is invalid.
    """
    if "=" not in value:
        raise ValueError(
            f"Invalid format '{value}'. Expected name=command (e.g. demo=uv run server.py)"
        )

    name, command_str = value.split("=", 1)
    name = name.strip()
    command_str = command_str.strip()

    if not name or not command_str:
        raise ValueError(
            f"Invalid format '{value}'. Both name and command are required."
        )

    parts = command_str.split()
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    return name, command, args
