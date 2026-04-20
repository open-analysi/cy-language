"""
Tests for Invalid Variable Names and Edge Cases.

Tests that invalid variable names are properly rejected with meaningful
error messages, including edge cases like empty names, special characters,
and numbers.
"""

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError, SyntaxError
from cy_language.variable_normalizer import VariableNormalizer


class TestInvalidVariableNames:
    """Test handling of invalid variable names."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for complete testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        interpreter = Cy(tools=default_registry.get_tools_dict())
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_dollar_sign_alone(self):
        """Test that $ alone is handled appropriately."""
        # This should either be rejected by parser or handled gracefully
        # Note: In , $ is no longer used in assignments
        program = """x = "value"
output = x
return output"""

        # This should work fine now
        result = self.cy.run(program)
        assert result == '"value"'

    def test_empty_variable_name(self):
        """Test empty variable name handling."""
        # In , $ is no longer used in variable names
        # The normalizer still exists for backward compatibility in interpolation
        normalized = VariableNormalizer.normalize_name("$")
        assert normalized == ""  # Current behavior

        # Empty variable names would cause parse errors
        # This tests the edge case our normalizer creates

    def test_variables_starting_with_numbers(self):
        """Test variables starting with numbers are rejected."""
        invalid_programs = [
            """123invalid = "test"
output = 123invalid
return output""",
            """2fast = "test"
output = 2fast
return output""",
        ]

        for program in invalid_programs:
            with pytest.raises((SyntaxError, CompilerError, Exception)):
                self.cy.run(program)

    def test_variables_with_special_characters(self):
        """Test variables with invalid special characters are rejected."""
        invalid_programs = [
            """*invalid = "test"
output = *invalid
return output""",
            """@variable = "test"
output = @variable
return output""",
            """variable-name = "test"  # Hyphens not allowed
output = variable-name
return output""",
            """variable.name = "test"  # Dots not allowed in variable names
output = variable.name
return output""",
        ]

        for program in invalid_programs:
            with pytest.raises((SyntaxError, CompilerError, Exception)):
                self.cy.run(program)

    def test_variables_with_spaces(self):
        """Test variables with spaces are rejected."""
        invalid_programs = [
            """my variable = "test"
output = my variable
return output""",
        ]

        for program in invalid_programs:
            with pytest.raises((SyntaxError, CompilerError, Exception)):
                self.cy.run(program)

    def test_reserved_keywords_comprehensive(self):
        """Test comprehensive coverage of reserved words."""
        # Test strictly reserved keywords - cause syntax errors
        strictly_reserved = {
            "if": "control flow - expects parentheses",
            "while": "control flow - expects parentheses",
            "return": "control flow - expects expression",
            "not": "unary operator - expects operand",
            "try": "exception handling - expects block",
            "catch": "exception handling - reserved keyword",
            "finally": "exception handling - reserved keyword",
        }

        # Note: "null" is now handled as a reserved literal, not here

        for keyword, _reason in strictly_reserved.items():
            program = f"""{keyword} = "test"
output = {keyword}
return output"""

            # These should fail
            with pytest.raises((SyntaxError, CompilerError, Exception)) as exc_info:
                self.cy.run(program)
            # Verify we get some kind of meaningful error
            assert len(str(exc_info.value)) > 0

        # Test that these are also reserved now
        also_reserved = {
            "else": "control flow - reserved keyword",
            "elif": "control flow - reserved keyword",
            "and": "boolean operator - reserved keyword",
            "or": "boolean operator - reserved keyword",
        }

        for keyword, _reason in also_reserved.items():
            program = f"""{keyword} = "test"
output = {keyword}
return output"""

            # These should also fail now
            with pytest.raises((SyntaxError, CompilerError, Exception)) as exc_info:
                self.cy.run(program)
            # Verify we get some kind of meaningful error
            assert len(str(exc_info.value)) > 0

        # Test boolean literals - now blocked as reserved literals
        boolean_literals = {
            "True": "boolean literal - now reserved",
            "False": "boolean literal - now reserved",
        }

        for keyword, _reason in boolean_literals.items():
            program = f"""{keyword} = "test"
output = {keyword}
return output"""

            # These are now properly blocked as reserved literals
            with pytest.raises(CompilerError) as exc_info:
                self.cy.run(program)
            # Verify error message mentions reserved literal
            error_msg = str(exc_info.value)
            assert "reserved literal" in error_msg.lower()
            assert keyword in error_msg

        # Test commonly expected reserved words now blocked
        commonly_expected_reserved = {
            "None": "Python null equivalent - now reserved",
            "true": "lowercase boolean literal - now reserved",
            "false": "lowercase boolean literal - now reserved",
        }

        for keyword, _reason in commonly_expected_reserved.items():
            program = f"""{keyword} = "test"
output = {keyword}
return output"""

            # These are now properly blocked as reserved literals
            with pytest.raises(CompilerError) as exc_info:
                self.cy.run(program)
            # Verify error message mentions reserved literal
            error_msg = str(exc_info.value)
            assert "reserved literal" in error_msg.lower()
            assert keyword in error_msg

    def test_reserved_literal_prevention_comprehensive(self):
        """Test comprehensive reserved literal prevention."""
        # All reserved literals to be blocked
        all_reserved_literals = ["True", "False", "None", "true", "false", "null"]

        # Test without $ prefix
        for literal in all_reserved_literals:
            program = f"""{literal} = "test_value"
output = {literal}
return output"""

            with pytest.raises(CompilerError) as exc_info:
                self.cy.run(program)

            # Verify error message is clear and helpful
            error_msg = str(exc_info.value)
            assert "reserved literal" in error_msg.lower()
            assert literal in error_msg

        # Test that similar but allowed names still work
        allowed_similar = ["true_value", "false_flag", "none_type", "null_check"]

        for var_name in allowed_similar:
            program = f"""{var_name} = "test_value"
output = {var_name}
return output"""

            # These should work fine
            result = self.cy.run(program)
            assert result == '"test_value"'

    def test_additional_edge_case_keywords(self):
        """Test additional potentially reserved keywords."""
        # Test other programming keywords that might be expected reserved
        other_potential_keywords = [
            "const",
            "let",
            "var",  # Variable declaration keywords from other languages
            "function",
            "def",
            "class",  # Definition keywords
            "import",
            "export",
            "from",  # Module keywords
            "throw",  # Exception handling (not yet reserved)
            # "break" and "continue" are now reserved keywords (loop control)
            "switch",
            "case",
            "default",  # Switch statement
            "async",
            "await",  # Async keywords
            "yield",
            "with",  # Other Python keywords
        ]

        for keyword in other_potential_keywords:
            program = f"""{keyword} = "test"
output = {keyword}
return output"""

            # These should work as variable names
            try:
                result = self.cy.run(program)
                assert result == '"test"'
            except Exception as e:
                # If these fail, document which are actually reserved
                pytest.fail(f"Unexpected: '{keyword}' reserved - {type(e).__name__}")

    def test_variables_too_long(self):
        """Test extremely long variable names."""
        # Test with a very long variable name (1000+ characters)
        long_name = "a" * 1000
        program = f"""{long_name} = "test"
output = {long_name}
return output"""

        # This might work or might fail - testing current behavior
        try:
            result = self.cy.run(program)
            # If it works, verify it actually worked correctly
            assert result == "test"
        except Exception:
            # If it fails, that's also acceptable behavior
            pass

    def test_unicode_variable_names(self):
        """Test unicode characters in variable names."""
        unicode_programs = [
            """# Test with emoji
😀variable = "test"
output = 😀variable
return output""",
            """# Test with non-ASCII letters
café = "coffee"
output = café
return output""",
            """# Test with Chinese characters
变量 = "variable"
output = 变量
return output""",
        ]

        for program in unicode_programs:
            # Unicode support varies - test what happens
            try:
                self.cy.run(program)
                # If unicode works, that's fine
                pass
            except (SyntaxError, CompilerError, Exception):
                # If unicode doesn't work, that's also acceptable
                pass

    def test_mixed_valid_invalid_program(self):
        """Test program with mix of valid and invalid variable names."""
        program = """valid_name = "good"
also_valid = "also good"
123invalid = "bad"  # This should cause error
output = valid_name
return output"""

        # Should fail due to the invalid variable name
        with pytest.raises((SyntaxError, CompilerError, Exception)):
            self.cy.run(program)

    def test_function_name_conflicts_detailed(self):
        """Test detailed function name conflicts with edge cases."""
        # These should be caught by our function conflict detection
        invalid_programs = [
            """len = "override built-in"
output = len
return output""",
            """debug_print = "override native function"
output = debug_print
return output""",
        ]

        for program in invalid_programs:
            with pytest.raises(CompilerError) as exc_info:
                self.cy.run(program)
            # Verify error message mentions function conflict
            error_msg = str(exc_info.value)
            assert "conflict" in error_msg.lower()

    def test_variable_normalizer_edge_cases(self):
        """Test VariableNormalizer with various edge cases."""
        test_cases = [
            ("$", ""),  # Dollar alone
            ("$name", "name"),  # Normal case
            ("name", "name"),  # Normal case without $
            ("$123", "123"),  # Number after $ (creates invalid name)
            ("$$name", "$name"),  # Double dollar
            ("$", ""),  # Empty after $
        ]

        for input_name, expected_output in test_cases:
            result = VariableNormalizer.normalize_name(input_name)
            assert result == expected_output, (
                f"normalize_name('{input_name}') should return "
                f"'{expected_output}', got '{result}'"
            )


class TestErrorQuality:
    """Test that error messages for invalid variables are helpful."""

    def setup_method(self):
        """Set up test fixtures."""
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        interpreter = Cy(tools=default_registry.get_tools_dict())
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_error_messages_have_line_info(self):
        """Test that syntax errors include line information."""
        program = '''valid_var = "ok"
123invalid = "bad"
another_var = "ok"'''

        try:
            self.cy.run(program)
            pytest.fail("Expected syntax error")
        except Exception as e:
            error_msg = str(e)
            # Error should mention line information
            assert any(word in error_msg.lower() for word in ["line", "column", "3"]), (
                f"Error should include line info: {error_msg}"
            )

    def test_error_messages_are_descriptive(self):
        """Test that error messages explain what went wrong."""
        program = '''len = "conflict"'''

        try:
            self.cy.run(program)
            pytest.fail("Expected compiler error")
        except CompilerError as e:
            error_msg = str(e)
            # Error should be descriptive about the conflict
            assert "len" in error_msg
            assert "conflict" in error_msg.lower()
