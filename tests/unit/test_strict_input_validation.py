"""Unit tests for strict_input validation feature.

Tests verify that analyze_types() with strict_input=True validates
that all input field accesses match the provided input_schema.

This is critical for workflow composition - catching composition errors
at validation time instead of runtime.

Following TDD: All tests should FAIL initially.
"""

import pytest

from cy_language import analyze_types


class TestStrictInputBasics:
    """Test basic strict_input validation."""

    def test_strict_input_false_is_permissive(self):
        """Default behavior: accessing non-existent field is OK."""
        script = 'name = input["name"]'
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        # Should NOT raise - permissive mode
        result = analyze_types(script, input_schema=schema, strict_input=False)
        assert result is not None

    def test_strict_input_missing_top_level_field(self):
        """strict_input=True: accessing non-existent field raises TypeError."""
        script = 'name = input["name"]'
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "name" in error_msg.lower()
        assert "user_id" in error_msg.lower() or "available" in error_msg.lower()

    def test_strict_input_valid_field_succeeds(self):
        """strict_input=True: accessing existing field succeeds."""
        script = 'ip = input["ip_address"]\nreturn {"ip": ip}'
        schema = {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string"},
                "extra": {"type": "number"},  # Extra fields OK
            },
        }

        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result["type"] == "object"
        assert "ip" in result["properties"]


class TestStrictInputNestedFields:
    """Test nested field validation."""

    def test_strict_input_missing_nested_field(self):
        """strict_input=True: accessing non-existent nested field raises."""
        script = 'city = input["address"]["city"]'
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}},
                }
            },
        }

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "city" in error_msg.lower()
        assert "street" in error_msg.lower() or "available" in error_msg.lower()

    def test_strict_input_valid_nested_field(self):
        """strict_input=True: accessing existing nested field succeeds."""
        script = 'street = input["address"]["street"]\nreturn street'
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}},
                }
            },
        }

        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result == {"type": "string"}


class TestStrictInputDotNotation:
    """Test field access with dot notation."""

    def test_strict_input_dot_notation_missing_field(self):
        """strict_input=True: accessing non-existent field via dot notation."""
        script = "name = input.name"
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "name" in error_msg.lower()

    def test_strict_input_dot_notation_valid_field(self):
        """strict_input=True: accessing existing field via dot notation."""
        script = "id = input.user_id\nreturn id"
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result == {"type": "string"}


class TestStrictInputMultipleErrors:
    """Test multiple field validation errors."""

    def test_strict_input_multiple_missing_fields(self):
        """strict_input=True: multiple missing fields reported together."""
        script = """
name = input["name"]
age = input["age"]
return {"name": name, "age": age}
"""
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        # Should mention both missing fields
        assert "name" in error_msg.lower()
        assert "age" in error_msg.lower()


class TestStrictInputEdgeCases:
    """Test edge cases for strict validation."""

    def test_strict_input_without_schema_raises(self):
        """strict_input=True without input_schema should raise ValueError."""
        script = 'name = input["name"]'

        with pytest.raises(ValueError) as exc_info:
            analyze_types(script, input_schema=None, strict_input=True)

        assert "strict_input requires input_schema" in str(exc_info.value).lower()

    def test_strict_input_no_input_access_succeeds(self):
        """strict_input=True: script without input access succeeds."""
        script = "x = 5\nreturn x + 10"
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result == {"type": "number"}

    def test_strict_input_array_access(self):
        """strict_input=True: array field access with integer index.

        Array access can return null for out-of-bounds, so we return union.
        strict_input only validates object field access against schema.
        """
        script = 'first = input["items"][0]\nreturn first'
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
        }

        result = analyze_types(script, input_schema=schema, strict_input=True)
        # Array indexing returns union because of potential out-of-bounds
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}


class TestStrictInputErrorMessages:
    """Test error message quality."""

    def test_strict_input_error_includes_line_number(self):
        """Error should include line number for better debugging."""
        script = """
x = 5
y = 10
name = input["name"]
return name
"""
        schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        # Should include line number
        assert "line" in error_msg.lower() or any(c.isdigit() for c in error_msg)

    def test_strict_input_error_suggests_available_fields(self):
        """Error should list available fields."""
        script = 'name = input["name"]'
        schema = {
            "type": "object",
            "properties": {"user_id": {"type": "string"}, "email": {"type": "string"}},
        }

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        # Should suggest available fields
        assert (
            "user_id" in error_msg and "email" in error_msg
        ) or "available" in error_msg.lower()
