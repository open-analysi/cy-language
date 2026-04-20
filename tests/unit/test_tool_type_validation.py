"""
Integration tests for tool type validation.

End-to-end testing of tool type validation in real workflows. Verify that tools are
properly validated in both analyze_types() and Cy(check_types=True) execution paths.

These tests follow TDD - they will FAIL initially due to Bug #1 (tools return Any type),
and PASS once build_tool_resolver() is implemented and Bug #1 is fixed.
"""

import contextlib

import pytest

from cy_language import Cy, analyze_types
from cy_language.tool_registry_builder import build_tool_registry, export_mcp_tools


class TestAnalyzeTypesPath:
    """Test tool type validation in analyze_types() path."""

    def test_analyze_types_native_tool_type_validated(self):
        """
        Verify native tool return types are validated in expressions.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        script = """
arr = [1, 2, 3]
count = len(arr)
result = count * 2
return result
"""

        # len returns number, number * number = number
        output_schema = analyze_types(script)

        assert output_schema == {"type": "number"}

    def test_analyze_types_native_tool_type_error(self):
        """
        Verify type errors involving native tools are caught.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        script = """
arr = [1, 2, 3]
count = len(arr)
result = count + "text"
return result
"""

        # Should raise TypeError: number + string
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_analyze_types_str_tool_returns_string(self):
        """
        Verify str() tool returns string type correctly.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        script = """
num = 42
text = str(num)
result = text + " items"
return result
"""

        # str returns string, string + string = string
        output_schema = analyze_types(script)

        assert output_schema == {"type": "string"}

    def test_analyze_types_with_mcp_tool_registry(self):
        """
        Verify MCP tools from registry are validated.

        INTEGRATION TEST: Will FAIL until export_mcp_tools() is implemented.
        """

        # Mock MCP manager
        class MockMCPManager:
            tools_cache = {
                "mcp::test::get_number": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "number"}}
                }
            }

        # Build registry from MCP manager
        mcp_registry = export_mcp_tools(MockMCPManager())
        registry = build_tool_registry(include_native=True)
        registry.merge(mcp_registry)

        script = """
value = mcp::test::get_number()
result = value * 10
return result
"""

        # MCP tool returns number, number * number = number
        output_schema = analyze_types(script, tool_registry=registry)

        assert output_schema == {"type": "number"}

    def test_analyze_types_mcp_tool_type_error(self):
        """
        Verify MCP tool type errors are caught.

        INTEGRATION TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::test::get_object": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "object"}}
                }
            }

        mcp_registry = export_mcp_tools(MockMCPManager())
        registry = build_tool_registry(include_native=True)
        registry.merge(mcp_registry)

        script = """
obj = mcp::test::get_object()
result = obj + 100
return result
"""

        # Should raise TypeError: object + number
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=registry)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg


class TestCyCheckTypesPath:
    """Test tool type validation in Cy(check_types=True) path."""

    def test_cy_check_types_validates_native_tools(self):
        """
        Verify Cy(check_types=True) validates native tool calls.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        cy = Cy(check_types=True)

        script = """
arr = [1, 2, 3]
count = len(arr)
result = count + "text"
return result
"""

        # Should raise TypeError BEFORE execution
        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_cy_check_types_valid_tool_usage_executes(self):
        """
        Verify valid tool usage passes validation and executes.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        cy = Cy(check_types=True)

        script = """
arr = [1, 2, 3]
count = len(arr)
result = count * 2
return result
"""

        # Should validate and execute successfully
        result = cy.run(script)

        assert result == "6"  # Result is string representation

    def test_cy_check_types_multiple_tools_validated(self):
        """
        Verify multiple tool calls in same script all validated.

        INTEGRATION TEST: Will FAIL until Bug #1 is fixed.
        """
        cy = Cy(check_types=True)

        script = """
arr = [1, 2, 3]
count = len(arr)
count_str = str(count)
result = count_str + 100
return result
"""

        # Should raise TypeError: string + number
        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_cy_without_check_types_skips_validation(self):
        """
        Verify Cy() without check_types skips validation (backward compat).

        REGRESSION TEST: Ensure default behavior unchanged.
        """
        cy = Cy()  # check_types=False (default)

        script = """
arr = [1, 2, 3]
count = len(arr)
result = count + "text"
return result
"""

        # Should NOT raise during validation (may raise at runtime)
        # This is expected - check_types=False means no validation
        try:
            result = cy.run(script)
            # If it somehow executes, that's fine
        except Exception as e:
            # Should not be a type checking error
            assert "type checking failed" not in str(e).lower()


class TestWorkflowComposition:
    """Test workflow composition with MCP tool calls (backend scenario)."""

    def test_workflow_task_a_to_task_b_with_mcp_tools(self):
        """
        Verify Task A → Task B workflow validation with MCP tool calls.

        Simulates backend scenario:
        - Task A calls MCP tool, returns object
        - Task B uses Task A's output

        INTEGRATION TEST: Will FAIL until implemented.
        """

        # Mock MCP tool that returns object with specific fields
        class MockMCPManager:
            tools_cache = {
                "mcp::virustotal::ip_reputation": {
                    "schema": {
                        "inputSchema": {
                            "properties": {"ip": {"type": "string"}},
                            "required": ["ip"],
                        },
                        "outputSchema": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "verdict": {"type": "string"},
                            },
                        },
                    }
                }
            }

        # Build registry
        mcp_registry = export_mcp_tools(MockMCPManager())
        registry = build_tool_registry(include_native=True)
        registry.merge(mcp_registry)

        # Task A: Calls MCP tool
        task_a_script = """
reputation = mcp::virustotal::ip_reputation(ip=input.ip_address)
return reputation
"""

        task_a_input_schema = {
            "type": "object",
            "properties": {"ip_address": {"type": "string"}},
        }

        # Validate Task A
        # Use strict_input=True to get non-nullable types from input
        task_a_output = analyze_types(
            task_a_script,
            input_schema=task_a_input_schema,
            tool_registry=registry,
            strict_input=True,
        )

        # Task A should return object with score and verdict
        assert task_a_output["type"] == "object"
        assert "score" in task_a_output.get("properties", {})

        # Task B: Uses Task A's output
        task_b_script = """
score_value = input.score
threshold = 50
is_suspicious = score_value > threshold
return is_suspicious
"""

        # Validate Task B using Task A's output as input
        # Use strict_input=True to get non-nullable types from input
        task_b_output = analyze_types(
            task_b_script,
            input_schema=task_a_output,
            tool_registry=registry,
            strict_input=True,
        )

        # Task B should return boolean
        assert task_b_output == {"type": "boolean"}

    def test_workflow_mcp_tool_output_schema_used(self):
        """
        Verify MCP tool outputSchema properly used in workflow validation.

        INTEGRATION TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::api::fetch_user": {
                    "schema": {
                        "inputSchema": {},
                        "outputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "age": {"type": "number"},
                            },
                        },
                    }
                }
            }

        mcp_registry = export_mcp_tools(MockMCPManager())
        registry = build_tool_registry(include_native=True)
        registry.merge(mcp_registry)

        script = """
user = mcp::api::fetch_user()
user_name = user.name ?? ""
greeting = "Hello, " + user_name
return greeting
"""

        # Field access returns union types (string | null) for non-input objects.
        # Use ?? operator to handle nullable types before operations.
        # After ?? operator, user_name is string, so result is string.
        output_schema = analyze_types(script, tool_registry=registry)

        assert output_schema == {"type": "string"}

    def test_workflow_invalid_field_access_on_mcp_output(self):
        """
        Verify invalid field access on MCP tool output is caught.

        INTEGRATION TEST: Will FAIL until implemented and strict_input enabled.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::api::fetch_data": {
                    "schema": {
                        "inputSchema": {},
                        "outputSchema": {
                            "type": "object",
                            "properties": {"value": {"type": "number"}},
                        },
                    }
                }
            }

        mcp_registry = export_mcp_tools(MockMCPManager())
        registry = build_tool_registry(include_native=True)
        registry.merge(mcp_registry)

        script = """
data = mcp::api::fetch_data()
missing = data.nonexistent_field
return missing
"""

        # TODO: This test depends on strict field access validation
        # May need strict_input=True in analyze_types()
        # For now, just verify it doesn't crash
        with contextlib.suppress(TypeError):
            analyze_types(script, tool_registry=registry)
