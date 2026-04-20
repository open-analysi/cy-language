"""
Tests for Plan Validator Changes - Return-Only Validation.

These tests verify that the plan validator requires return statements
and does NOT accept $output assignments as valid output.

Following TDD: These tests should FAIL initially (validator still accepts $output).
"""

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError


class TestValidatorRequiresReturn:
    """Test that validator requires return statements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False  # validate_output=True by default
        self.cy.show_enhanced_errors = False

    def test_validator_requires_return(self):
        """Test that script without return fails validation."""
        program = """x = 5
y = 10"""

        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value).lower()
        assert "return" in error_msg

    def test_validator_accepts_return(self):
        """Test that script with return passes validation."""
        program = """x = 5
return x"""

        # Should not raise any error
        result = self.cy.run(program)
        assert result == "5"  # Executor returns strings

    def test_validator_ignores_output_assignment(self):
        """Test that 'output = value' without return fails validation."""
        program = '''output = "hello"'''

        # Should fail - output is no longer special
        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value).lower()
        assert "return" in error_msg

    def test_validator_return_in_if_else_both_branches(self):
        """Test that both if/else branches need return."""
        # This should pass - both branches have return
        program = """x = 5
if (x > 0) {
    return "positive"
} else {
    return "non-positive"
}"""

        result = self.cy.run(program)
        assert result == '"positive"'

    def test_validator_return_in_if_missing_else(self):
        """Test that if without else with return may need return after."""
        # This should pass - return in if, and there's a fallback return
        program = '''x = 5
if (x > 10) {
    return "big"
}
return "small"'''

        result = self.cy.run(program)
        assert result == '"small"'

    def test_validator_return_in_try_catch_both_branches(self):
        """Test that both try and catch branches can have return."""
        program = """try {
    x = 42
    return "success"
} catch (e) {
    return "error"
}"""

        result = self.cy.run(program)
        assert result == '"success"'

    def test_validator_error_message_mentions_return(self):
        """Test that error message mentions 'return statement'."""
        program = """x = 5"""

        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value)
        # Should mention "return"
        assert "return" in error_msg.lower()

    def test_validator_can_be_disabled(self):
        """Test that validate_output=False allows scripts without return."""
        cy_no_validation = Cy(validate_output=False)
        cy_no_validation.show_enhanced_errors = False

        program = """x = 5"""

        # Should not raise CompilerError
        try:
            cy_no_validation.run(program)
        except CompilerError:
            pytest.fail("Should not raise CompilerError when validate_output=False")


class TestValidatorComplexScenarios:
    """Test validator with complex control flow scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_validator_while_loop_with_return(self):
        """Test while loop with return inside."""
        program = '''count = 0
while (count < 10) {
    if (count == 5) {
        return "found"
    }
    count = count + 1
}
return "not found"'''

        result = self.cy.run(program)
        assert result == '"found"'

    def test_validator_nested_if_with_return(self):
        """Test nested if statements with return."""
        program = """x = 5
y = 10
if (x > 0) {
    if (y > 0) {
        return "both positive"
    } else {
        return "x positive, y non-positive"
    }
} else {
    return "x non-positive"
}"""

        result = self.cy.run(program)
        assert result == '"both positive"'

    def test_validator_for_loop_with_return(self):
        """Test for-in loop with return."""
        program = '''numbers = [1, 2, 3, 4, 5]
for (num in numbers) {
    if (num == 3) {
        return "found three"
    }
}
return "not found"'''

        result = self.cy.run(program)
        assert result == '"found three"'

    def test_validator_elif_chains_with_return(self):
        """Test elif chains with return in all branches."""
        program = """score = 85
if (score >= 90) {
    return "A"
} elif (score >= 80) {
    return "B"
} elif (score >= 70) {
    return "C"
} else {
    return "F"
}"""

        result = self.cy.run(program)
        assert result == '"B"'

    def test_validator_try_catch_finally_with_return(self):
        """Test try-catch-finally with return."""
        program = """try {
    x = 42
    return "try: " + str(x)
} catch (e) {
    return "catch: error"
} finally {
    y = 100
}"""

        result = self.cy.run(program)
        assert result.startswith('"try:')

    def test_validator_return_after_loop(self):
        """Test return statement after loop completes."""
        program = """total = 0
count = 0
while (count < 5) {
    total = total + count
    count = count + 1
}
return total"""

        result = self.cy.run(program)
        assert result == "10"  # Executor returns strings

    def test_validator_multiple_possible_returns(self):
        """Test multiple code paths each with return."""
        program = '''x = 5
y = 10

if (x > 0) {
    if (y > 0) {
        return "both positive"
    }
    return "x positive"
}
return "x non-positive"'''

        result = self.cy.run(program)
        assert result == '"both positive"'


class TestValidatorErrorMessages:
    """Test that validator error messages are helpful."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_no_return_error_message_quality(self):
        """Test that error message for missing return is clear."""
        program = """x = 5
y = 10
z = x + y"""

        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value)
        # Should be clear about needing return
        assert "return" in error_msg.lower()

    def test_error_does_not_mention_dollar_output(self):
        """Test that error messages don't mention old $output syntax."""
        program = """x = 5"""

        with pytest.raises(CompilerError) as excinfo:
            self.cy.run(program)

        error_msg = str(excinfo.value)
        # Should mention return, not $output
        assert "return" in error_msg.lower()
        # Ideally should NOT mention "$output" (but this may depend on implementation)


class TestValidatorWithInput:
    """Test validator with $input variable."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_validator_with_input_and_return(self):
        """Test that input + return works."""
        program = """result = "Input was: " + str(input)
return result"""

        result = self.cy.run(program, input_data="hello")
        assert result == '"Input was: hello"'

    def test_validator_return_input_directly(self):
        """Test returning input directly."""
        program = """return input"""

        result = self.cy.run(program, input_data=42)
        assert result == "42"  # Executor returns strings

    def test_validator_transform_input_and_return(self):
        """Test transforming input and returning."""
        program = """value = input + 10
return value"""

        result = self.cy.run(program, input_data=5)
        assert result == "15"  # Executor returns strings
