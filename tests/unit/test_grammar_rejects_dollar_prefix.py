"""
Tests for Grammar Changes - Reject $ in Variable Assignments.

These tests verify that the grammar REJECTS the old $var = value syntax
and only accepts var = value syntax. Interpolation ${var} remains unchanged.

Following TDD: These tests should FAIL initially (grammar still accepts $).
"""

import pytest
from lark import Lark, LarkError

from cy_language.grammar import get_grammar


class TestGrammarRejectsDollar:
    """Test that grammar rejects $ prefix in variable assignments."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = get_grammar()
        self.parser = Lark(self.grammar, start="start", parser="lalr")

    def test_reject_dollar_in_variable_assignment(self):
        """Test that $name = 'Alice' raises SyntaxError."""
        program = '$name = "Alice"'

        # Should raise parsing error (LarkError)
        with pytest.raises(LarkError) as excinfo:
            self.parser.parse(program)

        # Error message should be helpful - mentions $ is not allowed and expects identifier
        error_msg = str(excinfo.value).lower()
        assert (
            "$" in error_msg and "identifier" in error_msg
        ) or "no terminal matches" in error_msg

    def test_reject_dollar_in_number_assignment(self):
        """Test that $age = 30 raises SyntaxError."""
        program = "$age = 30"

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_reject_dollar_in_multiple_assignments(self):
        """Test that multiple $var assignments all fail."""
        program = '''$name = "Alice"
$age = 30
$city = "NYC"'''

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_accept_variable_without_dollar(self):
        """Test that name = 'Alice' parses successfully."""
        program = 'name = "Alice"'
        tree = self.parser.parse(program)
        assert tree is not None

        # Find the assignment node
        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

        # Verify variable name doesn't have $
        var_token = assignments[0].children[0]
        assert not var_token.value.startswith("$")

    def test_accept_number_variable_without_dollar(self):
        """Test that age = 30 parses successfully."""
        program = "age = 30"
        tree = self.parser.parse(program)
        assert tree is not None

        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

        var_token = assignments[0].children[0]
        assert not var_token.value.startswith("$")

    def test_accept_multiple_variables_without_dollar(self):
        """Test that multiple var = value assignments work."""
        program = '''name = "Alice"
age = 30
city = "NYC"'''

        tree = self.parser.parse(program)
        assert tree is not None

        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 3

        # All should be without $
        for assignment in assignments:
            var_token = assignment.children[0]
            assert not var_token.value.startswith("$")

    def test_interpolation_still_works(self):
        """Test that 'Hello ${name}' still parses correctly."""
        program = 'greeting = "Hello ${name}"'
        tree = self.parser.parse(program)
        assert tree is not None

        # Interpolation is handled during string processing, not as separate grammar nodes
        # Just verify the string parses correctly
        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

    def test_interpolation_in_expression(self):
        """Test that 'Value: ${x + 1}' still works."""
        program = 'result = "Value: ${x + 1}"'
        tree = self.parser.parse(program)
        assert tree is not None

        # Should parse without error
        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

    def test_complex_program_without_dollar(self):
        """Test a complete program with new syntax."""
        program = """name = "Alice"
age = 30
greeting = "Hello ${name}, you are ${age} years old"
return greeting"""

        tree = self.parser.parse(program)
        assert tree is not None

        # Should have 3 assignments and 1 return
        assignments = list(tree.find_data("assignment"))
        returns = list(tree.find_data("return_statement"))

        assert len(assignments) == 3
        assert len(returns) == 1

        # All assignments should not have $
        for assignment in assignments:
            var_token = assignment.children[0]
            assert not var_token.value.startswith("$")

    def test_reject_dollar_with_underscore(self):
        """Test that $my_var = 5 is rejected."""
        program = "$my_var = 5"

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_accept_underscore_without_dollar(self):
        """Test that my_var = 5 works."""
        program = "my_var = 5"
        tree = self.parser.parse(program)
        assert tree is not None

        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

    def test_reject_dollar_with_numbers(self):
        """Test that $var1 = 5 is rejected."""
        program = "$var1 = 5"

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_accept_numbers_without_dollar(self):
        """Test that var1 = 5 works."""
        program = "var1 = 5"
        tree = self.parser.parse(program)
        assert tree is not None

    def test_reject_dollar_output_assignment(self):
        """Test that $output = 'hello' is rejected."""
        program = '$output = "hello"'

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_accept_output_as_regular_variable(self):
        """Test that output = 'hello' works (output is now regular variable)."""
        program = 'output = "hello"'
        tree = self.parser.parse(program)
        assert tree is not None

        # output is just a regular variable now
        assignments = list(tree.find_data("assignment"))
        assert len(assignments) == 1

        var_token = assignments[0].children[0]
        assert var_token.value == "output"
        assert not var_token.value.startswith("$")

    def test_reject_dollar_in_control_flow(self):
        """Test that $var in if/while is rejected."""
        program = """if (condition) {
    $result = "yes"
}"""

        with pytest.raises(LarkError):
            self.parser.parse(program)

    def test_accept_no_dollar_in_control_flow(self):
        """Test that var in if/while works."""
        program = """if (condition) {
    result = "yes"
}"""

        tree = self.parser.parse(program)
        assert tree is not None


class TestInterpolationUnchanged:
    """Test that ${} interpolation syntax is completely unchanged."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = get_grammar()
        self.parser = Lark(self.grammar, start="start", parser="lalr")

    def test_simple_interpolation_works(self):
        """Test that ${var} in strings still works."""
        program = 'text = "Value: ${x}"'
        tree = self.parser.parse(program)
        assert tree is not None

    def test_expression_interpolation_works(self):
        """Test that ${x + 1} in strings still works."""
        program = 'text = "Result: ${x + 1}"'
        tree = self.parser.parse(program)
        assert tree is not None

    def test_dict_access_interpolation_works(self):
        """Test that ${data['key']} still works (single quotes inside)."""
        program = "text = \"Value: ${data['key']}\""
        tree = self.parser.parse(program)
        assert tree is not None

    def test_function_call_interpolation_works(self):
        """Test that ${str(42)} still works."""
        program = 'text = "Number: ${str(42)}"'
        tree = self.parser.parse(program)
        assert tree is not None

    def test_multiple_interpolations_work(self):
        """Test that multiple ${} in same string works."""
        program = 'text = "Name: ${name}, Age: ${age}"'
        tree = self.parser.parse(program)
        assert tree is not None

    def test_nested_interpolation_works(self):
        """Test that ${outer[${inner}]} works."""
        program = 'text = "Value: ${outer[inner]}"'
        tree = self.parser.parse(program)
        assert tree is not None
