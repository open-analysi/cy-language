# MCP + String Interpolation
# Shows MCP tool results in string interpolation

count = mcp::demo::count_characters(text="hello world")
output = "The text has ${count} characters (calculated by MCP server)"
return output
