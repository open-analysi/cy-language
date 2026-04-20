"""
Test cases for enhanced error handling.

This module tests improved error messages with better line/column information
and user-friendly error descriptions for Version 2 features.
"""

import pytest

from cy_language.errors import NameError as CyNameError
from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.errors import ToolNotFoundError
from cy_language.interpreter import Cy


class TestEnhancedErrorLineColumnInfo:
    """Test that errors include precise line and column information."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_undefined_variable_with_line_info(self):
        """Test that undefined variable errors include line information."""
        program = """x = 5
y = undefined_var
output = x
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        # Line 2 contains the undefined variable
        assert error.line == 2
        # Enhanced errors show "at line 2" or "Line 2" format
        error_str = str(error)
        assert "line 2" in error_str.lower() or "Line 2" in error_str
        assert "undefined_var" in str(error)

    def test_tool_not_found_with_line_info(self):
        """Test that tool not found errors include line information."""
        from cy_language.errors import ToolResolutionError

        program = """x = 5
result = nonexistent_tool("arg")
output = result
return output"""

        # Now raises ToolResolutionError at compile time
        with pytest.raises((ToolNotFoundError, ToolResolutionError)) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert error.line == 2  # Line with the tool call
        # Enhanced errors show "at line 2" or "Line 2" format
        error_str = str(error)
        assert "line 2" in error_str.lower() or "Line 2" in error_str
        assert "nonexistent_tool" in str(error)

    def test_division_by_zero_with_line_info(self):
        """Test that division by zero errors include line information."""
        program = """x = 10
y = 0
result = x / y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert error.line == 3  # Line with division
        assert "Division by zero" in str(error)
        error_str = str(error)
        assert "line 3" in error_str.lower() or "Line 3" in error_str

    def test_interpolation_error_with_line_info(self):
        """Test safe navigation with missing fields.

        Accessing fields on ANY type (including primitives)
        returns null for safe navigation. No InterpolationError is raised.
        """
        program = """number = 42
output = "Hello ${number.nonexistent_field}"
return output
"""

        # This no longer raises an error, returns "Hello null" instead
        result = self.interpreter.run(program)
        assert result == '"Hello null"'


class TestControlFlowSyntaxErrors:
    """Test specific error messages for control flow syntax issues."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_missing_opening_brace_if_statement(self):
        """Test error message for missing opening brace in if statement."""
        program = """x = 5
if (x > 0)
    output = "positive"
}
return output"""

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        # Should mention expected brace or similar parsing error
        error_msg = str(exc_info.value)
        # With enhanced errors disabled, old format mentions LBRACE
        assert "LBRACE" in error_msg or "Unexpected" in error_msg

    def test_missing_closing_brace_while_loop(self):
        """Test error message for missing closing brace in while loop."""
        program = """x = 5
while (x > 0) {
    x = x - 1
    output = x
    return output
# Missing closing brace"""

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        # Enhanced errors clean up parser internals, but still mention issues
        # Strip ANSI codes for comparison
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        # Should mention unexpected end or missing brace
        assert any(
            keyword in clean_msg
            for keyword in [
                "Unexpected",
                "unexpected",
                "missing",
                "brace",
                "end of file",
            ]
        )

    def test_invalid_while_condition(self):
        """Test error message for invalid while loop condition."""
        program = """x = 5
while (undefined_var > 0) {
    x = x - 1
    output = x
}
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "undefined_var" in str(error)
        assert error.line == 2  # Line with condition


class TestMathematicalOperationErrors:
    """Test enhanced error messages for mathematical operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_type_error_in_arithmetic(self):
        """Test error message for type errors in + operator."""
        program = """x = "hello"
y = 5
result = x + y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        # + operator has type-specific error message
        assert "Cannot use + operator" in str(error) or "same type" in str(error)
        assert error.line == 3  # Line with arithmetic operation

    def test_modulo_by_zero_error(self):
        """Test error message for modulo by zero."""
        program = """x = 10
y = 0
result = x % y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Modulo by zero" in str(error)
        assert error.line == 3

    def test_invalid_comparison_types(self):
        """Test error message for invalid comparison between incompatible types."""
        program = """x = [1, 2, 3]
y = "hello"
result = x > y
output = result
return output"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "Cannot compare" in str(error)
        assert error.line == 3


class TestUserFriendlyErrorMessages:
    """Test that error messages are clear and helpful for users."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_clear_tool_not_found_message(self):
        """Test that tool not found errors are clear and actionable."""
        from cy_language.errors import ToolResolutionError

        program = """result = calculate_taxes(1000, 0.1)
output = result
return output"""

        # Now raises ToolResolutionError at compile time
        with pytest.raises((ToolNotFoundError, ToolResolutionError)) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "calculate_taxes" in str(error) and "not found" in str(error)
        assert error.line == 1

    def test_clear_variable_not_defined_message(self):
        """Test that undefined variable errors are clear."""
        program = """total = subtotal + tax
output = total
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "is not defined" in str(error)
        assert any(var in str(error) for var in ["subtotal", "tax"])
        assert error.line == 1

    def test_clear_interpolation_field_access_error(self):
        """Test safe navigation with field access on primitives.

        Accessing fields on ANY type (including primitives)
        returns null for safe navigation. No InterpolationError is raised.
        """
        program = """number = 42
output = "Value: ${number.email}"
return output
"""

        # This no longer raises an error, returns "Value: null" instead
        result = self.interpreter.run(program)
        assert result == '"Value: null"'


class TestControlFlowSpecificErrors:
    """Test error handling specific to control flow constructs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_infinite_loop_protection_error(self):
        """Test that infinite loop protection gives clear error."""
        program = """x = 1
while (x > 0) {
    x = x + 1  # This will never make condition false
}
output = "Should not reach here"
return output
"""

        with pytest.raises(CyRuntimeError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "iterations" in str(error).lower()
        assert "loop" in str(error).lower()

    def test_nested_control_flow_error_context(self):
        """Test that errors in nested control flow provide good context."""
        program = """x = 5
if (x > 0) {
    y = 3
    while (y > 0) {
        result = undefined_var * 2  # Error in nested context
        y = y - 1
    }
    output = result
} else {
    output = "negative"
}
return output"""

        with pytest.raises(CyNameError) as exc_info:
            self.interpreter.run(program)

        error = exc_info.value
        assert "undefined_var" in str(error)
        assert error.line == 5  # Line inside nested while loop
