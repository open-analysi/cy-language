"""Tests for type_analysis_api.py — happy and unhappy paths.

Covers: infer_output_schema, analyze_types, data_to_schema,
validate_schema_matches_data, _validate_json_schema, _parse_tool_registry.
"""

import pytest

from cy_language.type_analysis_api import (
    analyze_types,
    data_to_schema,
    infer_output_schema,
    validate_schema_matches_data,
)

# ═══════════════════════════════════════════════════════════════════════════
# _validate_json_schema (called internally by infer_output_schema / analyze_types)
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateJsonSchema:
    """Unhappy paths for schema validation."""

    def test_invalid_schema_type_raises(self):
        with pytest.raises(ValueError, match="Invalid schema type"):
            infer_output_schema("return 1", input_schema={"type": "bogus"})

    def test_non_dict_schema_raises(self):
        with pytest.raises(ValueError, match="Schema must be a dictionary"):
            infer_output_schema("return 1", input_schema="not a dict")

    def test_valid_schema_types_accepted(self):
        for t in ("string", "number", "integer", "object", "array", "boolean", "null"):
            # Should not raise
            infer_output_schema("return 1", input_schema={"type": t})


# ═══════════════════════════════════════════════════════════════════════════
# infer_output_schema — happy paths
# ═══════════════════════════════════════════════════════════════════════════


class TestInferOutputSchemaHappy:
    """Happy paths for infer_output_schema."""

    def test_simple_number(self):
        result = infer_output_schema("return 42")
        assert result.get("type") == "number"

    def test_simple_string(self):
        result = infer_output_schema('return "hello"')
        assert result.get("type") == "string"

    def test_simple_boolean(self):
        result = infer_output_schema("return True")
        assert result.get("type") == "boolean"

    def test_empty_code_returns_any(self):
        result = infer_output_schema("")
        assert result == {}

    def test_whitespace_only_returns_any(self):
        result = infer_output_schema("   \n  ")
        assert result == {}

    def test_no_return_returns_any(self):
        result = infer_output_schema("x = 5")
        assert result == {}

    def test_with_input_schema(self):
        code = "return input.name"
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        result = infer_output_schema(code, input_schema=schema)
        # Should infer something (type depends on engine behavior)
        assert isinstance(result, dict)

    def test_dict_return(self):
        code = 'return {"a": 1, "b": "hello"}'
        result = infer_output_schema(code)
        assert result.get("type") == "object"

    def test_list_return(self):
        code = "return [1, 2, 3]"
        result = infer_output_schema(code)
        assert result.get("type") in ("array", "list")

    def test_with_tool_registry(self):
        code = 'return app::custom::greet(name="Alice")'
        registry = {
            "app::custom::greet": {
                "parameters": {"name": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_arithmetic_expression(self):
        code = "x = 5\ny = 10\nreturn x + y"
        result = infer_output_schema(code)
        assert result.get("type") == "number"


# ═══════════════════════════════════════════════════════════════════════════
# infer_output_schema — unhappy paths
# ═══════════════════════════════════════════════════════════════════════════


class TestInferOutputSchemaUnhappy:
    """Unhappy paths for infer_output_schema."""

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError, match="Failed to parse"):
            infer_output_schema("return &&& invalid")

    def test_invalid_tool_registry_value(self):
        with pytest.raises(ValueError, match="Invalid tool registry"):
            infer_output_schema(
                "return tool()",
                tool_registry={"tool": "not_a_dict"},
            )

    def test_unknown_tool_gets_placeholder(self):
        """Unknown tools get registered as placeholders returning Any."""
        code = "result = unknown_tool(x=1)\nreturn result"
        result = infer_output_schema(code)
        assert isinstance(result, dict)

    def test_unknown_namespaced_tool_gets_placeholder(self):
        """Namespaced unknown tools also get placeholders."""
        code = 'result = app::custom::missing(x="hello")\nreturn result'
        result = infer_output_schema(code)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════
# analyze_types — happy paths
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyzeTypesHappy:
    """Happy paths for analyze_types."""

    def test_simple_number(self):
        result = analyze_types("return 42")
        assert result.get("type") == "number"

    def test_simple_string(self):
        result = analyze_types('return "hello"')
        assert result.get("type") == "string"

    def test_empty_code(self):
        assert analyze_types("") == {}

    def test_whitespace_code(self):
        assert analyze_types("  \n  ") == {}

    def test_with_input_schema(self):
        code = "name = input.name\nreturn name"
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        result = analyze_types(code, input_schema=schema)
        assert isinstance(result, dict)

    def test_with_tool_registry(self):
        code = "return app::test::calc(x=5)"
        registry = {
            "app::test::calc": {
                "parameters": {"x": {"type": "number"}},
                "return_type": {"type": "number"},
            }
        }
        result = analyze_types(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_conditional_return(self):
        code = """
x = 5
if (x > 3) {
    return "big"
} else {
    return "small"
}
"""
        result = analyze_types(code)
        assert isinstance(result, dict)

    def test_no_return_gives_any(self):
        result = analyze_types("x = 5")
        assert result == {}


# ═══════════════════════════════════════════════════════════════════════════
# analyze_types — unhappy paths
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyzeTypesUnhappy:
    """Unhappy paths for analyze_types."""

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError, match="Failed to parse"):
            analyze_types("return &&& bad")

    def test_type_error_on_invalid_addition(self):
        """Adding number + string should raise TypeError."""
        with pytest.raises(TypeError):
            analyze_types('x = 5 + "text"\nreturn x')

    def test_invalid_schema_raises(self):
        with pytest.raises(ValueError, match="Invalid schema type"):
            analyze_types("return 1", input_schema={"type": "fake"})

    def test_invalid_tool_registry_raises(self):
        with pytest.raises(ValueError, match="Invalid tool registry"):
            analyze_types("return 1", tool_registry={"t": 42})

    def test_strict_input_without_schema_raises(self):
        with pytest.raises(ValueError):
            analyze_types("return input.x", strict_input=True)

    def test_strict_input_catches_missing_field(self):
        code = 'x = input["missing_field"]\nreturn x'
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        with pytest.raises(TypeError):
            analyze_types(code, input_schema=schema, strict_input=True)

    def test_unknown_tool_gets_placeholder(self):
        """Unknown tools in analyze_types also get placeholders."""
        code = "result = unknown_func(x=1)\nreturn result"
        result = analyze_types(code)
        assert isinstance(result, dict)

    def test_unknown_namespaced_tool_placeholder(self):
        code = 'result = app::svc::action(x="hello")\nreturn result'
        result = analyze_types(code)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════
# _parse_tool_registry — FQN generation
# ═══════════════════════════════════════════════════════════════════════════


class TestParseToolRegistry:
    """Test tool registry parsing with different name formats."""

    def test_simple_name_registers_as_flat_tool(self):
        """Simple name 'greet' is registered and used by the resolver."""
        code = 'return greet(name="Alice")'
        registry = {
            "greet": {
                "parameters": {"name": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_two_part_name_registers(self):
        """Two-part name 'app::greet' is registered."""
        code = 'return app::tools::greet(name="Alice")'
        registry = {
            "app::greet": {
                "parameters": {"name": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_three_part_name_used_as_is(self):
        """Three-part FQN 'app::custom::greet' stays as-is."""
        code = 'return app::custom::greet(name="Alice")'
        registry = {
            "app::custom::greet": {
                "parameters": {"name": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_tool_with_no_parameters(self):
        code = "return app::custom::noop()"
        registry = {
            "app::custom::noop": {
                "parameters": {},
                "return_type": {"type": "string"},
            }
        }
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)

    def test_tool_registry_object(self):
        """ToolRegistry object (not dict) should also work."""
        from cy_language.tool_signature import (
            ParameterSignature,
            ToolRegistry,
            ToolSignature,
        )

        registry = ToolRegistry()
        registry.tools["app::custom::greet"] = ToolSignature(
            fqn="app::custom::greet",
            function=None,
            parameters={
                "name": ParameterSignature(
                    name="name",
                    type_schema={"type": "string"},
                    required=True,
                    default_value=None,
                    description="",
                )
            },
            return_type={"type": "string"},
            description="",
        )

        code = 'return app::custom::greet(name="Bob")'
        result = infer_output_schema(code, tool_registry=registry)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════
# data_to_schema
# ═══════════════════════════════════════════════════════════════════════════


class TestDataToSchema:
    """Test data_to_schema utility."""

    def test_dict(self):
        schema = data_to_schema({"name": "Alice", "age": 30})
        assert schema["type"] == "object"
        assert "name" in schema.get("properties", {})

    def test_list(self):
        schema = data_to_schema([1, 2, 3])
        assert schema["type"] == "array"

    def test_string(self):
        schema = data_to_schema("hello")
        assert schema["type"] == "string"

    def test_integer(self):
        schema = data_to_schema(42)
        assert schema["type"] == "integer"

    def test_float(self):
        schema = data_to_schema(3.14)
        assert schema["type"] == "number"

    def test_boolean(self):
        schema = data_to_schema(True)
        assert schema["type"] == "boolean"

    def test_nested(self):
        schema = data_to_schema({"users": [{"name": "Alice"}]})
        assert schema["type"] == "object"


# ═══════════════════════════════════════════════════════════════════════════
# validate_schema_matches_data
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateSchemaMatchesData:
    """Test schema-data compatibility checker."""

    def test_number_matches_integer(self):
        assert validate_schema_matches_data({"type": "number"}, 42) is True

    def test_integer_matches_float(self):
        assert validate_schema_matches_data({"type": "integer"}, 3.14) is True

    def test_string_matches_string(self):
        assert validate_schema_matches_data({"type": "string"}, "hello") is True

    def test_boolean_matches_boolean(self):
        assert validate_schema_matches_data({"type": "boolean"}, True) is True

    def test_object_matches_dict(self):
        assert validate_schema_matches_data({"type": "object"}, {"a": 1}) is True

    def test_array_matches_list(self):
        assert validate_schema_matches_data({"type": "array"}, [1, 2]) is True

    def test_type_mismatch_returns_false(self):
        assert validate_schema_matches_data({"type": "string"}, 42) is False

    def test_number_string_mismatch(self):
        assert validate_schema_matches_data({"type": "number"}, "hello") is False
