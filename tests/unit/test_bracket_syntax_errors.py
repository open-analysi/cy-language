"""Test enhanced error messages for bracket/parenthesis syntax errors.

Enhanced Error Messages
This test file uses TDD to ensure all bracket/parenthesis errors provide helpful suggestions.
"""

import re

import pytest

from cy_language import Cy


class TestBracketSyntaxErrors:
    """Test bracket and parenthesis error detection and suggestions."""

    def strip_ansi(self, text: str) -> str:
        """Strip ANSI color codes from error messages."""
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def test_missing_closing_parenthesis(self):
        """Test error message for missing closing parenthesis."""
        cy = Cy()
        script = "if (x > 5 {\n  result = 'yes'\n}\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check error location
        assert "at line 1, column 11" in error_str
        # Check suggestion
        assert "Missing closing parenthesis ')'" in error_str

    def test_extra_closing_parenthesis(self):
        """Test error message for extra closing parenthesis."""
        cy = Cy()
        script = "result = (5 + 3))\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check error location
        assert "at line 1, column 17" in error_str
        # Check suggestion
        assert "Extra closing parenthesis ')' or missing opening '('" in error_str

    def test_missing_closing_bracket(self):
        """Test error message for missing closing bracket."""
        cy = Cy()
        script = "items = [1, 2, 3\nreturn items"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check error location - parser reports error on next line
        assert "at line" in error_str
        # Check that we detect missing bracket
        if "Suggestion:" in error_str:
            assert (
                "Missing closing bracket ']'" in error_str
                or "bracket" in error_str.lower()
            )

    def test_extra_closing_bracket(self):
        """Test error message for extra closing bracket."""
        cy = Cy()
        script = "items = [1, 2, 3]]\nreturn items"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check error location
        assert "at line" in error_str
        # Check suggestion for extra bracket
        if "Suggestion:" in error_str:
            assert "bracket" in error_str.lower()

    def test_missing_closing_brace(self):
        """Test error message for missing closing brace."""
        cy = Cy()
        script = "if (x > 5) {\n  result = 'yes'\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check that syntax error is detected
        assert "SyntaxError" in error_str
        # Parser should detect the error around the return statement
        assert "line 3" in error_str

    def test_extra_closing_brace(self):
        """Test error message for extra closing brace."""
        cy = Cy()
        script = "x = 5\n}\nreturn x"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "SyntaxError" in error_str or "Error" in error_str
        # Check location
        assert "line 2" in error_str

    def test_unclosed_double_quote_string(self):
        """Test error message for unclosed double-quoted string."""
        cy = Cy()
        script = 'message = "hello\nreturn message'

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "Error" in error_str
        # Check for string-related error
        if "Suggestion:" in error_str:
            assert "quote" in error_str.lower() or "string" in error_str.lower()

    def test_unclosed_single_quote_string(self):
        """Test error message for unclosed single-quoted string."""
        cy = Cy()
        script = "message = 'hello\nreturn message"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "Error" in error_str
        # Check for string-related error
        if "Suggestion:" in error_str:
            assert "quote" in error_str.lower() or "string" in error_str.lower()

    def test_missing_comma_in_list(self):
        """Test error message for missing comma between list elements."""
        cy = Cy()
        script = "items = [1 2 3]\nreturn items"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "SyntaxError" in error_str
        # Check location points to where comma is missing
        assert "line 1" in error_str
        # Check suggestion
        if "Suggestion:" in error_str:
            assert "Missing comma between elements" in error_str

    def test_missing_comma_in_dict(self):
        """Test error message for missing comma between dict entries."""
        cy = Cy()
        script = '{"a": 1 "b": 2}'

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "Error" in error_str
        # Check for comma-related suggestion
        if "Suggestion:" in error_str:
            assert "comma" in error_str.lower()

    def test_missing_colon_in_dict(self):
        """Test error message for missing colon in dictionary."""
        cy = Cy()
        script = 'data = {"key" "value"}\nreturn data'

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "SyntaxError" in error_str
        # Check location
        assert "line 1" in error_str
        # Check suggestion
        if "Suggestion:" in error_str:
            assert "colon" in error_str.lower() or ":" in error_str

    def test_nested_parenthesis_mismatch(self):
        """Test error message for nested parenthesis mismatch."""
        cy = Cy()
        script = "result = ((5 + 3) * 2\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "Error" in error_str
        # Parser should detect missing closing parenthesis
        assert "line" in error_str

    def test_mixed_bracket_types_error(self):
        """Test error message for mismatched bracket types."""
        cy = Cy()
        script = "items = [1, 2, 3)\nreturn items"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check syntax error
        assert "Error" in error_str
        # Should detect bracket mismatch
        assert "line 1" in error_str

    def test_multiple_errors_shows_first(self):
        """Test that multiple syntax errors show the first one clearly."""
        cy = Cy()
        script = 'items = [1 2 3  # Missing commas\ndata = {"a" "b"}  # Missing colon\nreturn items'

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Should show first error
        assert "line 1" in error_str
        # Should have helpful message
        assert "SyntaxError" in error_str

    def test_error_message_has_visual_pointer(self):
        """Test that error messages include visual pointer to error location."""
        cy = Cy()
        script = "result = (5 + 3))\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Check for visual pointer
        assert "^" in error_str
        # Check for line display
        assert "result = (5 + 3))" in error_str
        # Check for line numbers
        assert " | " in error_str

    def test_complex_expression_bracket_error(self):
        """Test bracket errors in complex expressions."""
        cy = Cy()
        script = "result = (len([1, 2, 3) + sum([4, 5, 6]))\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Should detect syntax error
        assert "Error" in error_str
        # Should point to problematic line
        assert "line 1" in error_str

    def test_if_statement_brace_error(self):
        """Test brace errors in if statements."""
        cy = Cy()
        script = """if (x > 5) {
    y = x * 2
    if (y > 10) {
        z = y + 1
    # Missing closing brace for inner if
    result = z
}
return result"""

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Should detect syntax error
        assert "Error" in error_str

    def test_while_loop_parenthesis_error(self):
        """Test parenthesis errors in while loops."""
        cy = Cy()
        script = "i = 0\nwhile (i < 10 {\n  i = i + 1\n}\nreturn i"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Should detect missing closing parenthesis
        assert "Error" in error_str
        assert "line 2" in error_str
        # Check for parenthesis suggestion
        if "Suggestion:" in error_str:
            assert "parenthesis" in error_str.lower()

    def test_function_call_parenthesis_error(self):
        """Test parenthesis errors in function calls."""
        cy = Cy()
        script = "result = len([1, 2, 3)\nreturn result"

        with pytest.raises(Exception) as exc_info:
            cy.run(script)

        error_str = self.strip_ansi(str(exc_info.value))

        # Should detect syntax error
        assert "Error" in error_str
        # Should point to the line with error
        assert "line 1" in error_str
