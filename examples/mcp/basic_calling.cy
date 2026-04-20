# Basic MCP Tool Calling
# This example demonstrates calling MCP tools from remote servers
#
# REQUIREMENTS:
# 1. Check "Enable MCP Server Integration" in the sidebar
# 2. MCP service running at localhost:8000

result = mcp::demo::add(a=5, b=3)
output = "Addition result from MCP server: ${result}"
return output
