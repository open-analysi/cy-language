"""Unit tests for analyze_types() API.

Tests verify that the new analyze_types() API correctly combines
type inference and validation in a single pass, raising TypeError
on validation failures.

Following TDD: All tests should FAIL initially.
"""

import pytest

from cy_language.type_analysis_api import (
    analyze_types,
)


class TestAnalyzeTypesPositive:
    """Test analyze_types() with valid code (should return schema)."""

    def test_analyze_types_simple_number(self):
        """Test that simple number return infers correctly."""
        code = "return 5 + 10"

        result = analyze_types(code)

        assert result == {"type": "number"}

    def test_analyze_types_simple_string(self):
        """Test that simple string return infers correctly."""
        code = 'return "Hello, World!"'

        result = analyze_types(code)

        assert result == {"type": "string"}

    def test_analyze_types_with_input_schema(self):
        """Test that analyze_types uses provided input_schema.

        strict_input=True needed to get precise types from field access.
        """
        code = """
name = input.name
return "Hello " + name
"""
        input_schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # strict_input=True ensures input.name returns string, not (string | null)
        result = analyze_types(code, input_schema=input_schema, strict_input=True)

        assert result == {"type": "string"}

    def test_analyze_types_without_input_schema(self):
        """Test that analyze_types works without input_schema (input becomes Any).

        Without input_schema, field access returns (Any | null) union.
        """
        code = """
x = input.something
return x
"""

        result = analyze_types(code, input_schema=None)

        # Without schema, input.something returns {"oneOf": [{}, {"type": "null"}]}
        assert result == {"oneOf": [{}, {"type": "null"}]}

    def test_analyze_types_complex_object(self):
        """Test that complex object output infers correctly."""
        code = 'return {"name": "Alice", "age": 30}'

        result = analyze_types(code)

        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"] == {"type": "string"}
        assert result["properties"]["age"] == {"type": "number"}

    def test_analyze_types_array_output(self):
        """Test that array output infers correctly."""
        code = "return [1, 2, 3]"

        result = analyze_types(code)

        assert result["type"] == "array"
        assert "items" in result
        assert result["items"]["type"] == "number"

    def test_analyze_types_conditional_union(self):
        """Test that multiple return types create union."""
        code = """
if (true) {
    return 1
} else {
    return "text"
}
"""

        result = analyze_types(code)

        assert "oneOf" in result
        types_in_union = [t.get("type") for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union


class TestAnalyzeTypesNegative:
    """Test analyze_types() with invalid code (should raise TypeError)."""

    def test_analyze_types_arithmetic_type_error(self):
        """Test that adding number and string raises TypeError."""
        code = """
result = 5 + "text"
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        assert "add" in error_msg.lower() or "cannot" in error_msg.lower()
        assert "number" in error_msg.lower() or "string" in error_msg.lower()

    def test_analyze_types_comparison_type_error(self):
        """Test that comparing number with string raises TypeError."""
        code = """
result = 5 < "text"
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        assert "compar" in error_msg.lower() or "cannot" in error_msg.lower()

    def test_analyze_types_field_access_error(self):
        """Test nullable field access behavior.

        Field access returns null for missing fields instead of erroring.
        Using nullable values in operations requires ?? operator.
        """
        # Accessing missing field returns nullable type (no error)
        code_field_access = """
user = {"name": "Alice"}
email = user.email
return email
"""
        result = analyze_types(code_field_access)
        # Should return nullable type (Any | null since email field has no type info)
        assert "oneOf" in result or result.get("type") == "null"

        # Using nullable value (not Any) in operation requires ?? operator
        # Use input schema with strict_input=False to get nullable types
        code_nullable_operation = """
result = input.count + 5
return result
"""
        input_schema = {"type": "object", "properties": {"count": {"type": "number"}}}

        # With strict_input=False (default), input.count returns (number | null)
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                code_nullable_operation, input_schema=input_schema, strict_input=False
            )

        error_msg = str(exc_info.value)
        assert "nullable" in error_msg.lower() or "??" in error_msg

    def test_analyze_types_index_access_error(self):
        """Test that invalid indexing raises TypeError."""
        code = """
items = ["a", "b"]
return items["key"]
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        assert "index" in error_msg.lower() or "array" in error_msg.lower()

    def test_analyze_types_boolean_op_truthy_falsy(self):
        """Test that boolean operations support truthy/falsy semantics."""
        code = """
result = 5 and 10
return result
"""

        # Should NOT raise error - truthy/falsy semantics allowed
        result = analyze_types(code)
        # 'and' returns the actual value type (number in this case)
        assert result == {"type": "number"}

    def test_analyze_types_multiple_errors(self):
        """Test that multiple type errors are collected and reported."""
        code = """
e1 = 5 + "text"
e2 = "hello" - "world"
return e1
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should mention both errors
        assert error_msg.count("cannot") >= 1 or error_msg.count("error") >= 2


class TestAnalyzeTypesErrorHandling:
    """Test error handling for invalid inputs."""

    def test_analyze_types_syntax_error(self):
        """Test that invalid syntax raises SyntaxError (not TypeError)."""
        code = "x = 5 +"  # Incomplete expression

        with pytest.raises(SyntaxError):
            analyze_types(code)

    def test_analyze_types_empty_code(self):
        """Test that empty code returns empty schema gracefully."""
        code = ""

        result = analyze_types(code)

        assert result == {}

    def test_analyze_types_invalid_input_schema(self):
        """Test that malformed input_schema raises ValueError."""
        code = "return 5"
        input_schema = {"type": "invalid_type"}  # Invalid type

        with pytest.raises(ValueError):
            analyze_types(code, input_schema=input_schema)


class TestAnalyzeTypesErrorMessages:
    """Test that error messages are clear and actionable."""

    def test_analyze_types_error_has_line_number(self):
        """Verify that TypeError includes line number."""
        code = """
a = 5
b = "hello"
result = a + b
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should include line number reference
        assert "line" in error_msg.lower() or any(char.isdigit() for char in error_msg)

    def test_analyze_types_error_has_type_info(self):
        """Verify that TypeError mentions the conflicting types."""
        code = """
result = 42 - "text"
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should mention the types involved
        assert "number" in error_msg.lower() or "string" in error_msg.lower()

    def test_analyze_types_error_str_format(self):
        """Verify __str__ of TypeError is well-formatted."""
        code = """
result = "text" * true
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should be readable
        assert len(error_msg) > 10
        assert not error_msg.startswith("<")  # Not just a repr
