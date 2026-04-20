"""Minimal MCP server for testing the --mcp-stdio CLI feature.

Run with: uv run --with mcp[cli] mcp run tests/unit/fixtures/mcp_test_server.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@mcp.tool()
def echo(message: str) -> str:
    """Return the message as-is."""
    return message


if __name__ == "__main__":
    mcp.run(transport="stdio")
