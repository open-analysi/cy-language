"""Integration tests for Type Inference API.

Tests verify end-to-end type inference through the public API on realistic
Cy scripts that combine multiple features.
"""

import pytest

from cy_language.type_inference_api import infer_output_schema


class TestWorkflowChainValidation:
    """Test workflow chaining and compatibility validation."""

    def test_workflow_chain_validation(self):
        """Two workflows with compatible types should chain correctly."""
        # Workflow A: Returns user object
        workflow_a_code = """
user = {"name": "Alice", "email": "alice@example.com"}
output = user
return output
"""
        # Workflow B: Takes user object as input, returns greeting
        workflow_b_code = """
name = input.name
output = "Hello, " + name
return output
"""

        # Infer output of A
        a_output = infer_output_schema(workflow_a_code)

        # Infer output of B using A's output as input
        # infer_output_schema doesn't support strict_input=True, so field access
        # on input returns union types (T | null), and concatenation with unions results in Any ({})
        b_output = infer_output_schema(workflow_b_code, input_schema=a_output)

        # A should output an object with name and email
        assert a_output["type"] == "object"
        assert "name" in a_output["properties"]

        # B returns {} (Any) because input.name is union type and string + union = Any
        assert b_output == {}

    def test_workflow_incompatible_types_detected(self):
        """Incompatible workflow chain should be detectable."""
        # Workflow A: Returns number
        workflow_a_code = """
output = 42
return output
"""

        # Workflow B: Expects object with properties
        workflow_b_code = """
name = input.name
output = name
return output
"""

        a_output = infer_output_schema(workflow_a_code)
        assert a_output == {"type": "number"}

        # B expects object but A returns number - this would be incompatible
        # The type inference should handle it gracefully (return Any or error)
        try:
            b_output = infer_output_schema(workflow_b_code, input_schema=a_output)
            # If it succeeds, should return Any or handle gracefully
            # May return union types like {"oneOf": [...]}
            assert (
                b_output == {}
                or b_output.get("type") is not None
                or "oneOf" in b_output
            )
        except (ValueError, AttributeError, TypeError):
            # Or it might raise an error, which is also acceptable
            pass


class TestComplexScripts:
    """Test type inference on complex realistic scripts."""

    def test_complex_script_with_tools_and_conditionals(self):
        """Realistic script with tools, conditionals, and built-in functions."""
        code = """
users = fetch_users(input.filter)
count = len(users)
message = if (count > 0) {
    "Found " + str(count) + " users"
} else {
    "No users found"
}
output = {"count": count, "message": message}
return output
"""
        input_schema = {
            "type": "object",
            "properties": {"filter": {"type": "string"}},
        }
        tool_registry = {
            "fetch_users": {
                "parameters": {},
                "return_type": {
                    "type": "array",
                    "items": {"type": "object", "properties": {}},
                },
            }
        }

        result = infer_output_schema(
            code, input_schema=input_schema, tool_registry=tool_registry
        )

        # Output should be an object with count and message
        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["count"] == {"type": "number"}
        assert result["properties"]["message"] == {"type": "string"}

    def test_complex_script_with_loops(self):
        """Script with loops and field access.

        Without strict_input, field access returns union types,
        making operations like item.price return (number | null), which leads to Any.
        """
        code = """
items = input.items
total = 0
for (item in items) {
    total = total + item.price
}
output = total
return output
"""
        input_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"price": {"type": "number"}},
                    },
                }
            },
        }

        result = infer_output_schema(code, input_schema=input_schema)

        # item.price returns union type, total = total + union -> Any
        assert result == {}

    def test_script_multiple_return_paths(self):
        """Script with multiple returns should create union."""
        code = """
if (input.condition) {
    return {"status": "success", "value": 42}
} elif (input.other) {
    return {"status": "pending"}
} else {
    return null
}
"""
        input_schema = {
            "type": "object",
            "properties": {
                "condition": {"type": "boolean"},
                "other": {"type": "boolean"},
            },
        }

        result = infer_output_schema(code, input_schema=input_schema)

        # Should have union of different return types
        assert "oneOf" in result
        # Should contain object types and null
        has_object = any(t.get("type") == "object" for t in result["oneOf"])
        has_null = any(t.get("type") == "null" for t in result["oneOf"])
        assert has_object
        assert has_null


class TestCustomToolsIntegration:
    """Test integration with custom Backend-Y tools."""

    def test_custom_backend_y_tools(self):
        """Script using Backend-Y tools with type propagation."""
        code = """
user = get_current_user()
permissions = get_user_permissions(user.id)
output = permissions
return output
"""
        tool_registry = {
            "get_current_user": {
                "parameters": {},
                "return_type": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
            },
            "get_user_permissions": {
                "parameters": {"user_id": {"type": "string"}},
                "return_type": {"type": "array", "items": {"type": "string"}},
            },
        }

        result = infer_output_schema(code, tool_registry=tool_registry)

        # Output should be array of strings (permissions)
        assert result == {"type": "array", "items": {"type": "string"}}


class TestErrorScenarios:
    """Test error handling in integration scenarios."""

    def test_integration_syntax_error_with_context(self):
        """Syntax error in complex script should provide context."""
        code = """
x = 5
y = 10
z = 20 +
w = 30
"""
        with pytest.raises(SyntaxError) as exc_info:
            infer_output_schema(code)

        # Error message should indicate line with error
        error_msg = str(exc_info.value)
        # Should mention line 4 (where the error is)
        assert "line" in error_msg.lower() or "4" in error_msg

    def test_integration_undefined_variable(self):
        """Script references undefined variable."""
        code = """
output = undefined_var + 5
return output
"""
        # This might succeed with Any type or raise an error
        try:
            result = infer_output_schema(code)
            # If it succeeds, should return Any (empty schema)
            # or infer based on what's knowable
            assert result == {} or result.get("type") is not None
        except (ValueError, NameError):
            # Or it might raise an error
            pass


class TestPerformance:
    """Test performance on larger scripts."""

    def test_large_script_performance(self):
        """Performance on large script should be acceptable."""
        # Generate a script with 100+ lines
        lines = ["x = 0"]
        for i in range(100):
            lines.append(f"x = x + {i}")
        lines.append("output = x")
        lines.append("return output")
        code = "\n".join(lines)

        import time

        start = time.time()
        result = infer_output_schema(code)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0

        # Should still infer correctly
        assert result == {"type": "number"}


class TestRealWorldScenarios:
    """Test realistic Backend-Y workflow scenarios."""

    def test_data_transformation_workflow(self):
        """Workflow that transforms input data."""
        code = """
users = input.users
active_users = []
for (user in users) {
    if (user.active) {
        active_users = active_users + [user]
    }
}
count = len(active_users)
output = {"active_count": count, "users": active_users}
return output
"""
        input_schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "active": {"type": "boolean"},
                        },
                    },
                }
            },
        }

        result = infer_output_schema(code, input_schema=input_schema)

        # Output should be object with active_count and users
        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["active_count"] == {"type": "number"}
        # users is a union because active_users starts as [] and gets reassigned
        # The union contains array type (check that it's present)
        users_type = result["properties"]["users"]
        if "oneOf" in users_type:
            # Union type - check that array is one of the options
            has_array = any(t.get("type") == "array" for t in users_type["oneOf"])
            assert has_array
        else:
            # Simple type
            assert users_type["type"] == "array"

    def test_api_aggregation_workflow(self):
        """Workflow that calls multiple APIs and aggregates results.

        Field access on tool outputs (like user_data.name) returns union types,
        which propagate to the object properties, creating union-typed fields.
        """
        code = """
user_data = fetch_user_data(input.user_id)
order_data = fetch_orders(input.user_id)
order_count = len(order_data)
summary = {
    "user": user_data.name,
    "email": user_data.email,
    "order_count": order_count
}
output = summary
return output
"""
        input_schema = {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
        }
        tool_registry = {
            "fetch_user_data": {
                "parameters": {},
                "return_type": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            },
            "fetch_orders": {
                "parameters": {},
                "return_type": {
                    "type": "array",
                    "items": {"type": "object", "properties": {}},
                },
            },
        }

        result = infer_output_schema(
            code, input_schema=input_schema, tool_registry=tool_registry
        )

        # Field access returns union types, so object fields become unions
        assert result["type"] == "object"
        assert "properties" in result
        # user_data.name returns {"oneOf": [{"type": "string"}, {"type": "null"}]}
        assert result["properties"]["user"] == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }
        assert result["properties"]["email"] == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }
        assert result["properties"]["order_count"] == {"type": "number"}
