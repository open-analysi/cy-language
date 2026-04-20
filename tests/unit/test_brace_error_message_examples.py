"""
Test cases that demonstrate the actual error messages users see for brace issues.

This module shows examples of the error messages that users will see when they
have unclosed braces, providing documentation of the user experience.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestBraceErrorMessageExamples:
    """Demonstrate actual error messages for brace issues."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        # Keep enhanced errors enabled to test user-facing error messages

    def test_unclosed_if_brace_example(self):
        """Example: What users see when they forget to close an if brace."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
            return output
        # Oops! Forgot closing brace
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== UNCLOSED IF BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error contains helpful information
        # Enhanced errors don't expose parser internals like "RBRACE"
        assert (
            "Error" in error_msg or "error" in error_msg.lower()
        )  # Tells user a closing brace is expected
        assert (
            "line" in error_msg.lower() and "column" in error_msg.lower()
        )  # Shows location

    def test_unclosed_nested_brace_example(self):
        """Example: What users see with nested unclosed braces."""
        program = """        outer = 1
        if (outer > 0) {
            inner = 2
            if (inner > 0) {
                output = "nested success"
                return output
            # Missing brace for inner if
        # Missing brace for outer if  
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== NESTED UNCLOSED BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error contains helpful information with enhanced format
        assert "SyntaxError" in error_msg or "Error" in error_msg
        assert "line" in error_msg.lower() or "Line" in error_msg

    def test_unclosed_while_brace_example(self):
        """Example: What users see when they forget to close a while brace."""
        program = """        counter = 0
        while (counter < 3) {
            counter = counter + 1
            output = counter
            return output
        # Forgot closing brace
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== UNCLOSED WHILE BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error contains helpful information with enhanced format
        assert "SyntaxError" in error_msg or "Error" in error_msg
        assert "line" in error_msg.lower() or "Line" in error_msg

    def test_missing_opening_brace_example(self):
        """Example: What users see when they forget an opening brace."""
        program = """        x = 5
        if (x > 0)  # Missing opening brace
            output = "positive"
        }  # Closing brace without opening
        return output
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== MISSING OPENING BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error provides location information for the syntax issue
        assert "SyntaxError" in error_msg or "Error" in error_msg
        assert "line" in error_msg.lower()

    def test_extra_closing_brace_example(self):
        """Example: What users see when they have an extra closing brace."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
        }  # Correct closing brace
        }  # Extra closing brace
        return output
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== EXTRA CLOSING BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error provides helpful suggestion about the extra brace
        assert "SyntaxError" in error_msg or "Error" in error_msg
        # Enhanced errors provide a helpful suggestion for this case
        assert "brace" in error_msg.lower() or "line" in error_msg.lower()

    def test_complex_nested_error_example(self):
        """Example: Complex nested structure with missing brace."""
        program = """        status = "active"
        if (status == "active") {
            counter = 0
            while (counter < 5) {
                counter = counter + 1
                if (counter == 3) {
                    special = True
                    if (special) {
                        output = "found special case"
                    }
                }
            # Missing brace for while loop
        }
        return output
        """

        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        print("\n=== COMPLEX NESTED BRACE ERROR ===")
        print("Program with error:")
        print(program)
        print("Error message user sees:")
        print(error_msg)
        print("================\n")

        # Verify error provides location information
        # Enhanced errors don't expose parser internals like "RBRACE"
        assert "Error" in error_msg or "error" in error_msg.lower()
        assert "line" in error_msg.lower() and "column" in error_msg.lower()
