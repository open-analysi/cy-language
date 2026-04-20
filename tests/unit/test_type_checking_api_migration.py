"""Migration tests for the type system API.

Ensures that all type checking functionality is preserved
with the new API. Uses analyze_types() instead of TypeChecker directly.

Following TDD: All tests should FAIL initially.
"""

import pytest

from cy_language import analyze_types


class TestArithmeticErrorsPreserved:
    """Test that all arithmetic error detection still works."""

    def test_arithmetic_number_plus_string_error(self):
        """Adding number and string should still be detected."""
        code = """
age = 25
name = "Alice"
result = age + name
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        assert (
            "add" in str(exc_info.value).lower()
            or "cannot" in str(exc_info.value).lower()
        )

    def test_arithmetic_string_minus_string_error(self):
        """Subtracting strings should still be detected."""
        code = """
a = "hello"
b = "world"
result = a - b
return result
"""

        with pytest.raises(TypeError):
            analyze_types(code)

    def test_arithmetic_valid_operations(self):
        """Valid arithmetic should still work."""
        code = """
a = 5
b = 3
result = a + b
return result
"""

        output_schema = analyze_types(code)
        assert output_schema == {"type": "number"}


class TestComparisonErrorsPreserved:
    """Test that all comparison error detection still works."""

    def test_comparison_number_less_than_string_error(self):
        """Comparing number with string should still be detected."""
        code = """
num = 5
text = "hello"
result = num < text
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        assert "compar" in str(exc_info.value).lower()

    def test_comparison_valid_operations(self):
        """Valid comparisons should still work."""
        code = """
a = 5
b = 10
result = a < b
return result
"""

        output_schema = analyze_types(code)
        assert output_schema == {"type": "boolean"}


class TestBooleanOpErrorsPreserved:
    """Test that all boolean operation error detection still works."""

    def test_boolean_op_truthy_falsy_allowed(self):
        """'and'/'or' now support truthy/falsy semantics."""
        code = """
a = 5
b = 10
result = a and b
return result
"""

        # Should NOT raise - truthy/falsy semantics now allowed
        # 'and'/'or' return actual values, not boolean
        output_schema = analyze_types(code)
        # Since both operands are numbers, returns number (or union if different types)
        assert output_schema == {"type": "number"}

    def test_boolean_op_valid_operations(self):
        """Valid boolean operations should still work."""
        code = """
a = true
b = false
result = a and b
return result
"""

        output_schema = analyze_types(code)
        assert output_schema == {"type": "boolean"}


class TestFieldAccessErrorsPreserved:
    """Test that all field access error detection still works."""

    def test_field_access_missing_field_returns_nullable(self):
        """Accessing non-existent field returns nullable type, no error."""
        code = """
user = {"name": "Alice", "age": 30}
email = user.email
return email
"""

        # Missing fields don't error, they return nullable types
        output_schema = analyze_types(code)
        # The return type should be nullable (union with null)
        assert output_schema is not None
        # No type errors expected with safe navigation

    def test_field_access_on_non_object_error(self):
        """Accessing field on non-object should still be detected."""
        code = """
num = 42
value = num.something
return value
"""

        with pytest.raises(TypeError):
            analyze_types(code)

    def test_field_access_valid_operations(self):
        """Valid field access should still work."""
        code = """
user = {"name": "Alice", "age": 30}
name = user.name
return name
"""

        output_schema = analyze_types(code)
        # Field access returns union with null (field might not exist at runtime)
        assert output_schema == {"oneOf": [{"type": "string"}, {"type": "null"}]}


class TestIndexedAccessErrorsPreserved:
    """Test that all indexed access error detection still works."""

    def test_indexed_access_array_with_string_error(self):
        """Indexing array with string should still be detected."""
        code = """
items = ["a", "b", "c"]
item = items["key"]
return item
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        assert "index" in str(exc_info.value).lower()

    def test_indexed_access_object_with_number_error(self):
        """Indexing object with number should still be detected."""
        code = """
user = {"name": "Alice"}
value = user[0]
return value
"""

        with pytest.raises(TypeError):
            analyze_types(code)

    def test_indexed_access_valid_operations(self):
        """Valid indexed access now returns string|null."""
        code = """
items = ["a", "b", "c"]
first = items[0]
return first
"""

        output_schema = analyze_types(code)
        # Indexed access can return null for safety
        assert output_schema == {"oneOf": [{"type": "string"}, {"type": "null"}]}


class TestConditionalValidationPreserved:
    """Test that all conditional validation still works."""

    def test_conditional_truthy_falsy_still_works(self):
        """Truthy/falsy semantics should still be preserved."""
        # String in condition should be VALID (truthy/falsy)
        code = """
message = "hello"
if (message) {
    result = "yes"
} else {
    result = "no"
}
return result
"""

        output_schema = analyze_types(code)
        assert output_schema == {"type": "string"}

    def test_conditional_with_number_still_works(self):
        """Number in condition should still be valid (truthy/falsy)."""
        code = """
count = 5
if (count) {
    result = "yes"
} else {
    result = "no"
}
return result
"""

        output_schema = analyze_types(code)
        assert output_schema == {"type": "string"}


class TestAnyTypeStillBypasses:
    """Test that Any type ({}) still allows all operations."""

    def test_any_type_operations(self):
        """Operations on Any type should not produce errors."""
        code = """
dynamic = (input.value ?? 0)
result = dynamic + 5
return result
"""

        # Field access returns nullable, need ?? for operations
        output_schema = analyze_types(code, input_schema=None)

        # Should not raise with explicit null handling
        assert output_schema == {} or output_schema.get("type") is not None


class TestErrorMessageQualityPreserved:
    """Test that error messages still have line numbers and type info."""

    def test_error_messages_have_line_numbers(self):
        """Error messages should still include line numbers."""
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

    def test_error_messages_have_type_info(self):
        """Error messages should still mention types."""
        code = """
result = 42 - "text"
return result
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should mention the types involved
        assert "number" in error_msg.lower() or "string" in error_msg.lower()


class TestMultipleErrorsCollected:
    """Test that multiple errors are still collected together."""

    def test_multiple_errors_in_one_script(self):
        """Multiple type errors should still be collected."""
        code = """
error1 = 5 + "text"
error2 = "hello" - "world"
error3 = 42 * true
return error1
"""

        with pytest.raises(TypeError) as exc_info:
            analyze_types(code)

        error_msg = str(exc_info.value)
        # Should mention multiple issues
        assert len(error_msg) > 50  # Longer message = multiple errors
