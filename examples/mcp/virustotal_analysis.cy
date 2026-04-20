# VirusTotal Security Analysis with MCP
# Demonstrates using VirusTotal MCP tools for security analysis
#
# REQUIREMENTS:
# 1. Check "Enable MCP Server Integration" in the sidebar
# 2. MCP service running at localhost:8000
# 3. VirusTotal API key configured in MCP service

domain_to_check = "google.com"
url_to_check = "https://www.google.com"

# Check domain reputation
domain_report = mcp::virustotal::virustotal_domain_reputation(domain=domain_to_check)
d1 = debug_print("Retrieved domain reputation for ${domain_to_check}")

# Check URL reputation
url_report = mcp::virustotal::virustotal_url_reputation(url=url_to_check)
d2 = debug_print("Retrieved URL reputation for ${url_to_check}")

# Analyze the results
if (domain_report and url_report) {
    analysis_complete = True
    status = "Security analysis completed successfully"
} else {
    analysis_complete = False
    status = "Security analysis failed - check MCP service and API keys"
}

output = """
=== VIRUSTOTAL SECURITY ANALYSIS ===

Status: status
Analysis Complete: analysis_complete

Domain Analysis: domain_to_check
domain_report

URL Analysis: url_to_check
url_report

This example demonstrates:
- VirusTotal API integration via MCP
- Security reputation checking
- Remote security analysis tools

Note: Requires:
1. MCP service at localhost:8000
2. VirusTotal API key in MCP service configuration
3. MCP integration enabled in Streamlit sidebar

Check debug output for analysis details!
"""
return output
