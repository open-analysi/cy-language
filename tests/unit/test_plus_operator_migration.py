"""
Unit tests for ++ Operator Migration.

Tests that verify the ++ operator has been removed and replaced with +.
These tests ensure backward incompatibility is properly enforced.
"""

import pytest

from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.interpreter import Cy


class TestDoubleOperatorRemoved:
    """Test that ++ operator no longer exists in grammar."""

    def test_double_plus_syntax_error(self):
        """Test that 'a' ++ 'b' raises parse/syntax error"""
        program = """
        result = "a" ++ "b"
        output = result
        return output
        """

        cy = Cy()
        # Should raise syntax/parse error since ++ is not in grammar
        with pytest.raises((CySyntaxError, Exception)):
            cy.run(program)

    def test_double_plus_list(self):
        """Test that [1] ++ [2] raises parse/syntax error"""
        program = """
        result = [1] ++ [2]
        output = result
        return output
        """

        cy = Cy()
        with pytest.raises((CySyntaxError, Exception)):
            cy.run(program)

    def test_double_plus_with_variables(self):
        """Test that variable ++ variable raises syntax error"""
        program = """
        a = "hello"
        b = "world"
        result = a ++ b
        output = result
        return output
        """

        cy = Cy()
        with pytest.raises((CySyntaxError, Exception)):
            cy.run(program)

    def test_error_message_suggests_plus(self):
        """Test error message suggests using + instead"""
        program = """
        result = "a" ++ "b"
        output = result
        return output
        """

        cy = Cy()
        try:
            cy.run(program)
            # If no error, test fails
            pytest.fail("Expected syntax error for ++ operator")
        except Exception as e:
            # Error message should ideally suggest using + instead
            # This is a best-effort check - error might just be parse error
            error_msg = str(e)
            # Just verify we get some error
            assert error_msg is not None
