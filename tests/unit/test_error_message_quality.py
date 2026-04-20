"""
Test cases for practical error handling improvements.

This module tests error handling scenarios that work with the current
implementation and focuses on the quality of error messages.
"""

import pytest

from cy_language.errors import NameError as CyNameError
from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.errors import ToolNotFoundError
from src.cy_language.interpreter import Cy


class TestPracticalErrorMessages:
    """Test practical error message improvements for common scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Disable enhanced errors for test compatibility
        self.interpreter.show_enhanced_errors = False

    def test_division_by_zero_error_quality(self):
        """Test that division by zero errors provide clear messages."""
        program = """x = 10
y = 0
result = x / y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Division by zero" in str(error)
        # The error infrastructure is there, line numbers just need improvement
        assert hasattr(error, "line")
        assert hasattr(error, "col")
        # Currently shows Line 1, Col 1 - this is what will improve
        assert "Line" in str(error) and "Col" in str(error)

    def test_modulo_by_zero_error_quality(self):
        """Test that modulo by zero errors provide clear messages."""
        program = """x = 10
y = 0
result = x % y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Modulo by zero" in str(error)
        assert hasattr(error, "line")
        assert hasattr(error, "col")

    def test_undefined_variable_error_quality(self):
        """Test that undefined variable errors are descriptive."""
        program = """x = 5
y = undefined_variable
output = x
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "undefined_variable" in str(error)
        assert "is not defined" in str(error)
        assert hasattr(error, "line")
        assert hasattr(error, "col")

    def test_tool_not_found_error_quality(self):
        """Test that tool not found errors are clear and actionable."""
        from cy_language.errors import ToolResolutionError

        program = """result = nonexistent_function("test")
output = result
return output"""

        # Now raises ToolResolutionError at compile time
        with pytest.raises((ToolNotFoundError, ToolResolutionError)) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "nonexistent_function" in str(error)
        assert "not found" in str(error)
        assert hasattr(error, "line")
        assert hasattr(error, "col")

    def test_type_error_in_arithmetic_quality(self):
        """Test that type errors in arithmetic operations are clear."""
        program = """x = "hello"
y = 5
result = x * y  # String * number should fail
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "numeric operands" in str(error)
        assert hasattr(error, "line")
        assert hasattr(error, "col")

    def test_field_access_error_quality(self):
        """Test safe navigation with field access on primitives.

        Accessing fields on ANY type (including primitives)
        returns null for safe navigation. No InterpolationError is raised.
        """
        program = """number = 42
result = "Value: ${number.email}"  # Accessing field on non-dict
output = result
return output"""

        # This no longer raises an error, returns "Value: null" instead
        result = self.interpreter.run(program)
        assert result == '"Value: null"'


class TestControlFlowErrorScenarios:
    """Test error handling in control flow scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Disable enhanced errors for test compatibility
        self.interpreter.show_enhanced_errors = False

    def test_syntax_error_in_if_statement(self):
        """Test syntax errors in if statements are clear."""
        program = """x = 5
if (x > 0  # Missing closing parenthesis
    output = "positive"
}
return output"""

        with pytest.raises(CySyntaxError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        # Should mention parsing issue
        assert any(keyword in str(error) for keyword in ["Unexpected", "Expected"])

    def test_undefined_variable_in_condition(self):
        """Test undefined variables in conditions provide clear errors."""
        program = """x = 5
if (undefined_condition > 0) {
    output = "positive"
} else {
    output = "not positive"
}
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "undefined_condition" in str(error)
        assert "is not defined" in str(error)

    def test_infinite_loop_protection(self):
        """Test that infinite loop protection provides clear error."""
        program = """x = 1
while (x > 0) {
    x = x + 1  # This will never terminate
}
output = "Should not reach here"
return output
"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "iterations" in str(error).lower()
        assert "loop" in str(error).lower()

    def test_error_in_nested_control_flow(self):
        """Test that errors in nested control flow provide good context."""
        program = """x = 5
if (x > 0) {
    y = 3
    while (y > 0) {
        result = y / 0  # Division by zero in nested context
        y = y - 1
    }
    output = result
} else {
    output = "negative"
}
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Division by zero" in str(error)
        # Error happens inside nested while loop


class TestVersion2FeatureErrors:
    """Test error handling specific to Version 2 features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Disable enhanced errors for test compatibility
        self.interpreter.show_enhanced_errors = False

    def test_boolean_operation_type_error(self):
        """Test type errors in boolean operations."""
        program = """x = "hello"
y = 5
result = x and y  # String and number in boolean operation
output = result
return output"""

        # This might work (convert to boolean), but let's test what happens
        try:
            result = self.interpreter.run(program)
            # If it works, both "hello" and 5 should be truthy
            assert result in ["true", "5"]  # Depending on implementation
        except Exception as e:
            # If it fails, error should be descriptive
            assert any(word in str(e) for word in ["boolean", "type", "operand"])

    def test_comparison_type_compatibility(self):
        """Test comparison between incompatible types."""
        program = """list = [1, 2, 3]
string = "hello"
result = list > string  # Compare list to string
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Cannot compare" in str(error)


class TestErrorMessageQuality:
    """Test the overall quality and helpfulness of error messages."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Disable enhanced errors for test compatibility
        self.interpreter.show_enhanced_errors = False

    def test_error_messages_include_context(self):
        """Test safe navigation with field access on primitives.

        Accessing fields on ANY type (including primitives)
        returns null for safe navigation. No InterpolationError is raised.
        """
        program = """user_data = {"name": "Alice", "profile": {"age": 30}}
number_value = user_data['profile']['age']
invalid_access = number_value.some_field
output = invalid_access
return output"""

        # This no longer raises an error, returns None (serialized as "None")
        result = self.interpreter.run(program)
        assert result == "null"

    def test_complex_expression_error_context(self):
        """Test error context in complex expressions.

        List out-of-bounds returns None, so the error comes from
        trying to multiply None * 2 (arithmetic on NoneType).
        """
        program = """data = {"values": [10, 20, 30]}
index = 5  # Out of bounds — returns null
result = data['values'][index] * 2 + 1  # Error: null * 2
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "NoneType" in str(error)

    def test_multiple_potential_errors_first_one_reported(self):
        """Test that the first error encountered is reported clearly."""
        program = """x = undefined_var  # First error: undefined variable
y = x / 0  # Second error: division by zero (won't be reached)
output = y
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        # Should report the first error (undefined variable)
        assert "undefined_var" in str(error)
        assert "is not defined" in str(error)
        # Should not mention division by zero
        assert "Division by zero" not in str(error)


class TestErrorRecovery:
    """Test error handling doesn't break system state."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Disable enhanced errors for test compatibility
        self.interpreter.show_enhanced_errors = False

    def test_interpreter_still_works_after_error(self):
        """Test that interpreter can handle new programs after an error."""
        # First program with error
        error_program = """result = undefined_variable
output = result
return output"""

        with pytest.raises(CyNameError):
            self.interpreter.run(error_program)

        # Second program should work fine
        working_program = """x = 5
output = "Value is ${x}"
return output
"""

        result = self.interpreter.run(working_program)
        assert result == '"Value is 5"'

    def test_tools_still_available_after_error(self):
        """Test that tools remain available after an error."""
        tools = {"test_tool": lambda x: f"processed: {x}"}
        interpreter = Cy(tools=tools)

        # First program with error
        error_program = """result = test_tool(undefined_var)
output = result
return output"""

        with pytest.raises(CyNameError):
            interpreter.run(error_program)

        # Second program using same tool should work
        working_program = """result = test_tool("hello")
output = result
return output"""

        result = interpreter.run(working_program)
        assert result == '"processed: hello"'
