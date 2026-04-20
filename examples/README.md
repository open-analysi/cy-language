# Cy Language Examples

This directory contains organized examples for the Cy programming language. The examples are structured to help you learn Cy progressively, from basic syntax to advanced features.

## Directory Structure

### `/basic/` - Core Language Features
Examples 1-13 demonstrate fundamental Cy language concepts:

- `01_basic_variable_assignment.cy` - Variables and string interpolation
- `02_list_printing.cy` - Working with lists and markdown output
- `03_struct_access_dot_notation.cy` - Object property access
- `04_tool_calling_basic.cy` - Basic tool calls
- `05_string_escaping.cy` - Escaping special characters
- `06_multiline_strings.cy` - Triple-quoted multiline strings
- `07_xml_format_override.cy` - XML output formatting
- `08_csv_format_for_structs.cy` - CSV output formatting
- `09_external_tools_and_variables.cy` - Using external input
- `10_factorial_calculator_version2.cy` - Control flow with factorial
- `11_number_classification_version2.cy` - If/elif/else conditionals
- `12_countdown_while_loop_version2.cy` - While loops
- `13_tools_demonstration.cy` - Multiple tool usage

### `/llm_and_native/` - Native Functions & LLM Integration
Examples 14-17 demonstrate native functions and LLM features:

- `14_native_utility_functions.cy` - len(), debug_print(), json_string_to_struct()
- `15_basic_llm_usage.cy` - Basic LLM function calls (requires OPENAI_API_KEY)
- `16_agentic_execution_loop.cy` - Full agentic workflow with LLM functions
- `17_agentic_while_loop.cy` - Iterative improvement using while loops

### `/mcp_integration/` - MCP Server Integration
Examples 18-21 demonstrate MCP features:

- `18_basic_mcp_calling.cy` - Basic MCP tool calls
- `19_mcp_interpolation.cy` - MCP tools in string interpolation
- `20_native_plus_mcp_tools.cy` - Mixing native and MCP tools
- `21_virustotal_security_analysis.cy` - VirusTotal API integration

### `/unified_calling/` - Unified Calling Patterns
Examples 22-23 demonstrate unified calling patterns:

- `22_human_validation.cy` - Validation test for calling pattern features
- `23_unified_calling_patterns.cy` - Complete demo of all calling patterns

### `/advanced/` - Complex Real-World Examples
Production-ready examples demonstrating complex workflows:

- `complex_example_debugged.cy` - E-commerce order processing
- `ip_reputation_analysis.cy` - Security analysis workflow
- `incident_response_orchestrator.cy` - Security incident response
- `financial_risk_assessment.cy` - Financial analysis
- `security_summary_generator.cy` - Security reporting

### `/archived/` - Legacy Examples
Older examples kept for compatibility (not organized).

## Getting Started

1. **Start with Basic Examples**: Begin with examples 1-13 in `/basic/` to learn core Cy syntax
2. **Try Feature Examples**: Explore features in `/llm_and_native/`, `/mcp_integration/`, `/unified_calling/`
3. **Study Advanced Examples**: Look at `/advanced/` for real-world patterns
4. **Validation**: Run `22_human_validation.cy` to test your setup

## Requirements

- **Basic Examples**: No special setup required
- **LLM Examples**: Set `OPENAI_API_KEY` environment variable
- **MCP Examples**: Enable MCP integration in Streamlit sidebar + MCP service at localhost:8000
- **VirusTotal Examples**: VirusTotal API key configured in MCP service

## Usage in Streamlit UI

All examples in this directory automatically appear in the Streamlit UI's example selector. The organized structure makes it easy to find examples by complexity and feature set.

Choose "Load Example" in the sidebar to load any `.cy` file into the editor.
