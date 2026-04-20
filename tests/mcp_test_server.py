"""In-process MCP test server for running MCP example programs in tests.

Implements the two HTTP endpoints the MCPManager calls:
  GET  /v1/default/mcps/{mcp_id}/tools   → tool discovery
  POST /v1/default/mcps/{mcp_id}/invoke  → tool execution

Provides mock implementations for 'demo' and 'virustotal' MCP servers
so that example programs can run without external infrastructure.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ── Tool implementations ───────────────────────────────────────────────────


def _add(a: float = 0, b: float = 0, **_: Any) -> float:
    return a + b


def _count_characters(text: str = "", **_: Any) -> int:
    return len(text)


def _virustotal_domain_reputation(domain: str = "", **_: Any) -> dict:
    return {
        "domain": domain,
        "malicious": 0,
        "suspicious": 1,
        "harmless": 75,
        "undetected": 4,
        "total": 80,
        "reputation": "clean",
    }


def _virustotal_url_reputation(url: str = "", **_: Any) -> dict:
    return {
        "url": url,
        "malicious": 0,
        "suspicious": 0,
        "harmless": 70,
        "undetected": 10,
        "total": 80,
        "reputation": "clean",
    }


# ── Tool registry ─────────────────────────────────────────────────────────

# mcp_id → {tool_name → (function, parameter_schema)}
TOOL_REGISTRY: dict[str, dict[str, tuple[Any, dict]]] = {
    "demo": {
        "add": (
            _add,
            {
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                }
            },
        ),
        "count_characters": (
            _count_characters,
            {
                "properties": {
                    "text": {"type": "string", "description": "Text to count"},
                }
            },
        ),
    },
    "virustotal": {
        "virustotal_domain_reputation": (
            _virustotal_domain_reputation,
            {
                "properties": {
                    "domain": {"type": "string", "description": "Domain to check"},
                }
            },
        ),
        "virustotal_url_reputation": (
            _virustotal_url_reputation,
            {
                "properties": {
                    "url": {"type": "string", "description": "URL to check"},
                }
            },
        ),
    },
}


# ── HTTP handler ───────────────────────────────────────────────────────────


class MCPTestHandler(BaseHTTPRequestHandler):
    """Handles MCP tool discovery and invocation over HTTP."""

    def do_GET(self) -> None:
        """Handle tool discovery: GET /v1/default/mcps/{mcp_id}/tools"""
        if "/mcps/" not in self.path or not self.path.endswith("/tools"):
            self._send_json(404, {"error": "not found"})
            return

        mcp_id = self.path.split("/mcps/")[1].split("/tools")[0]
        registry = TOOL_REGISTRY.get(mcp_id, {})

        tools = [
            {
                "name": name,
                "description": f"Mock {name} tool",
                "parameters": schema,
                "schema": {"inputSchema": schema},
            }
            for name, (_fn, schema) in registry.items()
        ]

        self._send_json(200, {"tools": tools})

    def do_POST(self) -> None:
        """Handle tool invocation: POST /v1/default/mcps/{mcp_id}/invoke"""
        if "/mcps/" not in self.path or not self.path.endswith("/invoke"):
            self._send_json(404, {"error": "not found"})
            return

        mcp_id = self.path.split("/mcps/")[1].split("/invoke")[0]
        registry = TOOL_REGISTRY.get(mcp_id, {})

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))

        tool_name = body.get("tool", "")
        arguments = body.get("arguments", {})

        if tool_name not in registry:
            self._send_json(404, {"error": f"tool '{tool_name}' not found"})
            return

        fn, _schema = registry[tool_name]
        result = fn(**arguments)
        self._send_json(200, {"result": result})

    def _send_json(self, status: int, data: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress request logging in test output


# ── Server lifecycle ───────────────────────────────────────────────────────


def start_server() -> tuple[HTTPServer, str]:
    """Start the MCP test server on a random free port.

    Returns (server, base_url) tuple.  Call server.shutdown() to stop.
    """
    server = HTTPServer(("127.0.0.1", 0), MCPTestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"
