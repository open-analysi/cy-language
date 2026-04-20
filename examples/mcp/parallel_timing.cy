# MCP Parallel Execution Timing Demo
# Demonstrates the performance difference between parallel and sequential execution
#
# REQUIREMENTS:
# 1. Check "Enable MCP Server Integration" in the sidebar
# 2. MCP service running at localhost:8000
#
# TIMING TEST INSTRUCTIONS:
# 1. Run this program with parallel execution DISABLED (default)
# 2. Note the execution time
# 3. Enable "⚡ Enable Parallel Execution" in sidebar (set threshold to 2-3)
# 4. Run again and compare timing - should be 3-5x faster!

# === PARALLEL-FRIENDLY VERSION ===
# These independent calls can be automatically parallelized by our executor

result1 = mcp::demo::count_characters(text="google.com")
result2 = mcp::demo::count_characters(text="microsoft.com")
result3 = mcp::demo::count_characters(text="amazon.com")
result4 = mcp::demo::count_characters(text="github.com")
result5 = mcp::demo::count_characters(text="stackoverflow.com")
result6 = mcp::demo::count_characters(text="wikipedia.org")
result7 = mcp::demo::count_characters(text="eicar.org")
result8 = mcp::demo::count_characters(text="apple.com")
result9 = mcp::demo::count_characters(text="cloudflare.com")
result10 = mcp::demo::count_characters(text="reddit.com")

# Aggregate the results
total_chars = result1 + result2 + result3 + result4 + result5 + result6 + result7 + result8 + result9 + result10

# Create summary output
output = """
=== MCP PARALLEL TIMING DEMO ===

✅ Successfully counted characters for 10 domain strings
📊 Total character count: total_chars

🚀 PERFORMANCE TEST RESULTS:
- Sequential execution: Each MCP call one after another
- Parallel execution: Multiple MCP calls simultaneously

⚡ TO TEST PARALLEL EXECUTION:
1. Note the execution time shown above this output
2. Go to sidebar → Enable "⚡ Enable Parallel Execution"
3. Set "Parallel Threshold" to 2 or 3
4. Click "Run Program" again
5. Compare the new execution time!

Expected improvement: 3-5x faster with parallel execution
(10 MCP calls running simultaneously vs sequentially)

📋 STRINGS PROCESSED:
- google.com (result1 chars)
- microsoft.com (result2 chars)
- amazon.com (result3 chars)
- github.com (result4 chars)
- stackoverflow.com (result5 chars)
- wikipedia.org (result6 chars)
- eicar.org (result7 chars)
- apple.com (result8 chars)
- cloudflare.com (result9 chars)
- reddit.com (result10 chars)

This demonstrates how parallel execution can dramatically improve
performance for programs with multiple independent MCP calls!
"""
return output
