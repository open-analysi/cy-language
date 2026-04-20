"""
Tests for Executor Changes - Return Only (No $output Fallback).

These tests verify that the executor only returns from ReturnNode
and does NOT fall back to $output variable.

Following TDD: These tests should FAIL initially (executor still has $output fallback).
"""

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError


class TestExecutorReturnOnly:
    """Test that executor only returns from return statement."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_return_statement_produces_output(self):
        """Test that 'return value' produces output."""
        program = '''return "hello"'''

        result = self.cy.run(program)
        assert result == '"hello"'

    def test_return_with_variable(self):
        """Test that 'return var' works."""
        program = """message = "hello world"
return message"""

        result = self.cy.run(program)
        assert result == '"hello world"'

    def test_return_with_expression(self):
        """Test that 'return x + 1' works."""
        program = """x = 5
return x + 1"""

        result = self.cy.run(program)
        assert result == "6"  # Executor returns strings

    def test_no_return_fails_validation(self):
        """Test that script without return fails at compile-time."""
        program = """x = 5"""

        # Should fail validation (with validate_output=True by default)
        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value).lower()
        assert "return" in error_msg

    def test_output_variable_ignored(self):
        """Test that 'output = value' does NOT produce output."""
        # This should fail because there's no return statement
        program = '''output = "hello"'''

        # Should fail validation - output is no longer special
        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value).lower()
        assert "return" in error_msg

    def test_output_variable_is_regular_variable(self):
        """Test that 'output' can be used as regular variable with return."""
        program = """output = "intermediate value"
result = output + " processed"
return result"""

        result = self.cy.run(program)
        assert result == '"intermediate value processed"'

    def test_return_in_if_branch(self):
        """Test that return inside if statement works."""
        program = """x = 10
if (x > 5) {
    return "greater"
} else {
    return "lesser"
}"""

        result = self.cy.run(program)
        assert result == '"greater"'

    def test_return_in_else_branch(self):
        """Test that return inside else statement works."""
        program = """x = 3
if (x > 5) {
    return "greater"
} else {
    return "lesser"
}"""

        result = self.cy.run(program)
        assert result == '"lesser"'

    def test_return_in_while_loop(self):
        """Test that return inside while loop works."""
        program = '''count = 0
while (count < 10) {
    if (count == 5) {
        return "found five"
    }
    count = count + 1
}
return "not found"'''

        result = self.cy.run(program)
        assert result == '"found five"'

    def test_return_in_try_block(self):
        """Test that return inside try block works."""
        program = """try {
    x = 42
    return "success: " + str(x)
} catch (e) {
    return "error"
}"""

        result = self.cy.run(program)
        assert result == '"success: 42"'

    def test_return_in_catch_block(self):
        """Test that return inside catch block works.

        Missing keys return null instead of raising errors,
        so we need to trigger an actual error to test catch blocks.
        """
        program = """data = {}
try {
    # data["missing_key"] returns null, not an error
    # Use an operation that will cause a runtime error
    value = 1 / 0
    return "success"
} catch (e) {
    return "caught error"
}"""

        result = self.cy.run(program)
        assert result == '"caught error"'

    def test_multiple_returns_first_wins(self):
        """Test that first executed return is the output."""
        program = '''x = 5
if (x > 0) {
    return "positive"
}
return "non-positive"'''

        result = self.cy.run(program)
        assert result == '"positive"'

    def test_return_complex_data_structure(self):
        """Test returning complex data structures."""
        program = """data = {"name": "Alice", "scores": [95, 87, 92]}
return data"""

        result = self.cy.run(program)
        # Executor returns JSON representation of dict
        assert isinstance(result, str)
        import json

        parsed = json.loads(result)
        assert parsed["name"] == "Alice"
        assert parsed["scores"] == [95, 87, 92]

    def test_return_from_for_loop(self):
        """Test returning from inside for-in loop."""
        program = '''numbers = [1, 2, 3, 4, 5]
for (num in numbers) {
    if (num == 3) {
        return "found three"
    }
}
return "not found"'''

        result = self.cy.run(program)
        assert result == '"found three"'

    def test_early_return_stops_execution(self):
        """Test that return stops execution immediately."""
        program = '''result = "first"
return result
result = "second"'''

        # With validate_output=False to avoid validation error for unreachable code
        cy_no_validation = Cy(validate_output=False)
        cy_no_validation.show_enhanced_errors = False
        result = cy_no_validation.run(program)
        assert result == '"first"'


class TestReturnValidationDisabled:
    """Test that validation can be disabled for analysis."""

    def test_no_return_with_validation_disabled(self):
        """Test that validation can be turned off."""
        cy_no_validation = Cy(validate_output=False)
        cy_no_validation.show_enhanced_errors = False

        program = """x = 5"""

        # Should not raise error when validation is disabled
        try:
            result = cy_no_validation.run(program)
            # With no return and no output fallback, result should be None or similar
            assert result is None or result == ""
        except CompilerError:
            pytest.fail("Should not raise CompilerError when validate_output=False")

    def test_validation_enabled_by_default(self):
        """Test that validation is enabled by default."""
        cy = Cy()
        cy.show_enhanced_errors = False

        program = """x = 5"""

        # Should raise CompilerError with validation enabled (default)
        with pytest.raises(CompilerError):
            cy.run(program)


class TestReturnTypes:
    """Test returning different types of values."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_return_string(self):
        """Test returning a string."""
        program = '''return "hello"'''

        result = self.cy.run(program)
        assert result == '"hello"'
        assert isinstance(result, str)

    def test_return_number(self):
        """Test returning a number."""
        program = """return 42"""

        result = self.cy.run(program)
        assert result == "42"  # Executor returns strings
        assert isinstance(result, str)

    def test_return_float(self):
        """Test returning a float."""
        program = """return 3.14"""

        result = self.cy.run(program)
        assert result == "3.14"  # Executor returns strings
        assert isinstance(result, str)

    def test_return_boolean(self):
        """Test returning a boolean."""
        program = """return True"""

        result = self.cy.run(program)
        assert result == "true"  # Executor returns JSON strings
        assert isinstance(result, str)

    def test_return_null(self):
        """Test returning null."""
        program = """return null"""

        result = self.cy.run(program)
        assert result == "null"  # Executor returns JSON strings

    def test_return_list(self):
        """Test returning a list."""
        program = """return [1, 2, 3]"""

        result = self.cy.run(program)
        # Executor returns string representation
        assert result == "[1, 2, 3]"
        assert isinstance(result, str)

    def test_return_dict(self):
        """Test returning a dictionary."""
        program = """return {"key": "value"}"""

        result = self.cy.run(program)
        # Executor returns JSON representation
        assert result == '{"key": "value"}'
        assert isinstance(result, str)

    def test_return_interpolated_string(self):
        """Test returning string with interpolation."""
        program = '''name = "Alice"
return "Hello ${name}"'''

        result = self.cy.run(program)
        assert result == '"Hello Alice"'
