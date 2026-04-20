"""Unit tests for Type Inference API.

Tests verify that the public API for type inference works correctly,
providing accurate output schemas with proper error handling.
"""

import pytest

from cy_language.type_inference_api import (
    data_to_schema,
    infer_output_schema,
    validate_schema_matches_data,
)


class TestBasicAPI:
    """Test basic infer_output_schema() functionality."""

    def test_infer_output_schema_simple_output_variable(self):
        """Script with output variable should return its type."""
        code = """
x = 5
output = x + 10
return output
"""
        result = infer_output_schema(code)
        assert result == {"type": "number"}

    def test_infer_output_schema_output_string(self):
        """String output should infer as string type."""
        code = """
output = "Hello, World!"
return output
"""
        result = infer_output_schema(code)
        assert result == {"type": "string"}

    def test_infer_output_schema_output_object(self):
        """Object output should infer with properties."""
        code = """
output = {"name": "Alice", "age": 30}
return output
"""
        result = infer_output_schema(code)

        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"] == {"type": "string"}
        assert result["properties"]["age"] == {"type": "number"}

    def test_infer_output_schema_single_return(self):
        """Script with return statement (no $output) should use return type."""
        code = """
x = 42
return x
"""
        result = infer_output_schema(code)
        assert result == {"type": "number"}

    def test_infer_output_schema_multiple_returns_union(self):
        """Multiple returns with different types should create union."""
        code = """
if (True) {
    return 1
} else {
    return "text"
}
"""
        result = infer_output_schema(code)

        assert "oneOf" in result
        types_in_union = [t.get("type") for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_infer_output_schema_no_output(self):
        """Script without output or return should return empty schema."""
        code = """
x = 5
y = 10
"""
        result = infer_output_schema(code)
        assert result == {}


class TestInputSchemaParameter:
    """Test input_schema parameter for input variable typing."""

    def test_infer_output_schema_with_input_schema(self):
        """Script using input should use provided schema."""
        code = """
name = input.name
output = "Hello " + name
return output
"""
        input_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        result = infer_output_schema(code, input_schema=input_schema)
        # field access returns union with null, string + union = Any type
        assert result == {}

    def test_infer_output_schema_input_nested_access(self):
        """Nested input field access should resolve types."""
        code = """
email = input.user.email
output = email
return output
"""
        input_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"email": {"type": "string"}},
                }
            },
        }

        result = infer_output_schema(code, input_schema=input_schema)
        # field access returns union with null
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_output_schema_input_array(self):
        """input array access should resolve item type."""
        code = """
first = input.items[0]
output = first
return output
"""
        input_schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "number"}}},
        }

        result = infer_output_schema(code, input_schema=input_schema)
        # indexed access returns union with null
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_output_schema_no_input_schema(self):
        """Script without input_schema should work normally."""
        code = """
x = 5
output = x * 2
return output
"""
        result = infer_output_schema(code, input_schema=None)
        assert result == {"type": "number"}


class TestToolRegistryParameter:
    """Test tool_registry parameter for custom tool definitions."""

    def test_infer_output_schema_with_tool_registry(self):
        """Script using custom tool should use registry return type."""
        code = """
user = fetch_user("123")
output = user.name
return output
"""
        tool_registry = {
            "fetch_user": {
                "parameters": {"user_id": {"type": "string"}},
                "return_type": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            }
        }

        result = infer_output_schema(code, tool_registry=tool_registry)
        # field access returns union with null
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_output_schema_tool_registry_multiple_tools(self):
        """Multiple custom tools should all be available."""
        code = """
user = fetch_user("123")
count = count_records("users")
output = count
return output
"""
        tool_registry = {
            "fetch_user": {
                "parameters": {},
                "return_type": {"type": "object", "properties": {}},
            },
            "count_records": {
                "parameters": {},
                "return_type": {"type": "number"},
            },
        }

        result = infer_output_schema(code, tool_registry=tool_registry)
        assert result == {"type": "number"}

    def test_infer_output_schema_tool_registry_complex_return_type(self):
        """Tool with complex return type (array of objects)."""
        code = """
users = get_all_users()
first_user = users[0]
output = first_user.name
return output
"""
        tool_registry = {
            "get_all_users": {
                "parameters": {},
                "return_type": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                },
            }
        }

        result = infer_output_schema(code, tool_registry=tool_registry)
        # indexed access and field access both return union with null
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_output_schema_tool_not_in_registry(self):
        """Script calls unregistered tool - should return Any for result."""
        code = """
result = unknown_tool()
output = result
"""
        tool_registry = {}

        result = infer_output_schema(code, tool_registry=tool_registry)
        # Unknown tool returns Any, which propagates to output
        assert result == {}


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_infer_output_schema_syntax_error(self):
        """Invalid Cy syntax should raise SyntaxError."""
        code = "x = 5 +"  # Incomplete expression

        with pytest.raises(SyntaxError):
            infer_output_schema(code)

    def test_infer_output_schema_syntax_error_message_quality(self):
        """Syntax error should include line/column information."""
        code = """
x = 5
y = 10 +
z = 20
"""
        try:
            infer_output_schema(code)
            pytest.fail("Expected SyntaxError")
        except SyntaxError as e:
            # Error message should reference line with error
            error_msg = str(e)
            assert "line" in error_msg.lower() or "3" in error_msg

    def test_infer_output_schema_invalid_input_schema(self):
        """Malformed input_schema should raise ValueError."""
        code = "output = 5"
        input_schema = {"type": "invalid_type"}  # Invalid type

        with pytest.raises(ValueError):
            infer_output_schema(code, input_schema=input_schema)

    def test_infer_output_schema_invalid_tool_registry_format(self):
        """Malformed tool_registry should raise ValueError."""
        code = "output = 5"
        tool_registry = {"tool1": "not_a_dict"}  # Invalid format

        with pytest.raises(ValueError):
            infer_output_schema(code, tool_registry=tool_registry)

    def test_infer_output_schema_empty_code(self):
        """Empty script should return empty schema gracefully."""
        code = ""

        result = infer_output_schema(code)
        assert result == {}

    def test_infer_output_schema_whitespace_only(self):
        """Whitespace-only script should handle gracefully."""
        code = "   \n\n   "

        result = infer_output_schema(code)
        assert result == {}


class TestGenSONIntegration:
    """Test GenSON utilities for schema validation and conversion."""

    def test_data_to_schema_object(self):
        """Convert object to schema."""
        data = {"name": "Alice", "age": 30}

        result = data_to_schema(data)

        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"]["type"] == "string"
        assert result["properties"]["age"]["type"] in ["integer", "number"]

    def test_data_to_schema_array(self):
        """Convert array to schema."""
        data = [1, 2, 3]

        result = data_to_schema(data)

        assert result["type"] == "array"
        assert "items" in result
        assert result["items"]["type"] in ["integer", "number"]

    def test_data_to_schema_nested(self):
        """Convert nested structure to schema."""
        data = {"user": {"name": "Bob", "roles": ["admin", "user"]}}

        result = data_to_schema(data)

        assert result["type"] == "object"
        assert "user" in result["properties"]
        user_schema = result["properties"]["user"]
        assert user_schema["type"] == "object"
        assert "roles" in user_schema["properties"]

    def test_validate_schema_matches_data_positive(self):
        """Schema matches data should return True."""
        schema = {"type": "number"}
        data = 42

        result = validate_schema_matches_data(schema, data)
        assert result is True

    def test_validate_schema_matches_data_negative(self):
        """Schema doesn't match data should return False."""
        schema = {"type": "number"}
        data = "text"

        result = validate_schema_matches_data(schema, data)
        assert result is False

    def test_validate_schema_matches_data_complex(self):
        """Complex schema validation should work."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
        }
        data = {"name": "Alice", "age": 30}

        result = validate_schema_matches_data(schema, data)
        assert result is True
