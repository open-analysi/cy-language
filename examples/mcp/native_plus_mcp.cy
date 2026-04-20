# Mixing Native and MCP Tools
# Demonstrates using both native Cy tools and MCP tools together

# Native tools (always available, no MCP needed)
fruits = ["apple", "banana", "cherry"]
native_len = len(fruits)
native_upper = uppercase("hello")

# MCP tools (require MCP server)
mcp_sum = mcp::demo::add(a=15, b=25)
text_data = "testing remote character counting"
mcp_count = mcp::demo::count_characters(text=text_data)

output = """
=== NATIVE vs MCP TOOLS COMPARISON ===

Native Tools:
- len(fruits) = ${native_len}
- uppercase("hello") = ${native_upper}

MCP Remote Tools:
- mcp::demo::add(a=15, b=25) = ${mcp_sum}
- mcp::demo::count_characters("${text_data}") = ${mcp_count}

Both native and MCP tools work seamlessly together!
"""
return output
