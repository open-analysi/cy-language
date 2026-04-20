# MCP Loop Version (Sequential Only)
# This version uses a loop-based approach
# Note: This will always run sequentially due to while loop structure

domains = [
    "google.com",
    "microsoft.com",
    "amazon.com",
    "github.com",
    "stackoverflow.com",
    "wikipedia.org",
    "eicar.org",
    "apple.com",
    "cloudflare.com",
    "reddit.com"
]

i = 0
count = 0
while (i < len(domains)) {
    result = mcp::demo::count_characters(text=domains[i])
    count = count + result
    i = i + 1
}

domain_list = join(domains, ", ")

output = """
=== MCP LOOP VERSION RESULTS ===

Processed ${len(domains)} domain strings using while loop
Total character count: ${count}
Domains: ${domain_list}

Note: This version uses a while loop, so it runs sequentially.
For parallel execution, use example #22 (parallel timing demo)
which structures independent MCP calls for automatic parallelization.
"""
return output
