"""
Unit tests for string concatenation operations

These tests cover the implementation of the + operator for string concatenation
in both assignment contexts and interpolation contexts.
"""

import pytest

from cy_language.errors import SyntaxError as CySyntaxError
from src.cy_language.interpreter import Cy


class TestBasicStringConcatenation:
    """Test basic string concatenation with + operator."""

    def test_simple_string_concatenation_assignment(self):
        """Test $result = $str1 + $str2 basic concatenation assignment."""
        program = """
        str1 = "Hello"
        str2 = "World"
        result = str1 + str2
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"HelloWorld"'

    def test_string_concatenation_with_spaces(self):
        """Test concatenation with space literals."""
        program = """
        first = "Hello"
        last = "World"
        result = first + " " + last
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World"'

    def test_string_literal_concatenation(self):
        """Test concatenation of string literals directly."""
        program = """
        result = "Hello" + " " + "World"
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World"'

    def test_multiple_string_concatenation(self):
        """Test concatenation of multiple strings in sequence."""
        program = """
        greeting = "Hello"
        space = " "
        name = "Alice"
        punctuation = "!"
        result = greeting + space + name + punctuation
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello Alice!"'


# NOTE: Concatenation within interpolation is NOT supported in
# Examples like ${name + " (" + age + ")"} are excluded from this phase
# Use assignment-level concatenation instead: $result = $name + " (" + $age + ")"


class TestMixedTypeConcatenation:
    """Test that + operator requires same types (no auto-coercion)."""

    def test_string_plus_number_concatenation(self):
        """Test that string + number now raises error (use interpolation instead)."""
        program = """
        name = "User"
        id = 123
        result = name + id
        output = result
        return output
        """

        cy = Cy()
        # + operator no longer auto-converts types
        with pytest.raises(Exception):
            cy.run(program)

    def test_number_plus_string_concatenation(self):
        """Test that number + string now raises error (use interpolation instead)."""
        program = """
        count = 5
        suffix = " items"
        result = count + suffix
        output = result
        return output
        """

        cy = Cy()
        # + operator no longer auto-converts types
        with pytest.raises(Exception):
            cy.run(program)

    def test_mixed_types_in_concatenation(self):
        """Test that mixed type + now raises error (use interpolation instead)."""
        program = """
        score = 95
        score_text = "Your score: " + score + "/100"
        output = score_text
        return output
        """

        cy = Cy()
        # + operator no longer auto-converts types
        with pytest.raises(Exception):
            cy.run(program)


class TestConcatenationWithComplexExpressions:
    """Test concatenation combined with other language features."""

    def test_concatenation_with_field_access(self):
        """Test concatenation with field access expressions at assignment level."""
        program = """
        person = {"first": "John", "last": "Doe"}
        first = person.first
        last = person.last
        output = "Name: " + first + " " + last
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Name: John Doe"'

    def test_concatenation_with_indexed_access(self):
        """Test concatenation with indexed access expressions at assignment level."""
        program = """
        names = ["Alice", "Bob"]
        first_name = names[0]
        second_name = names[1]
        output = "Names: " + first_name + " and " + second_name
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Names: Alice and Bob"'

    def test_concatenation_with_nested_quotes(self):
        """Test concatenation combined with nested quote access at assignment level."""
        program = """
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        first_user = "First: ${data['users'][0]['name']}"
        second_user = "Second: ${data['users'][1]['name']}"
        output = first_user + " & " + second_user
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "First: Alice" in result and "Second: Bob" in result


class TestConcatenationEdgeCases:
    """Test edge cases and error conditions for concatenation."""

    def test_concatenation_with_empty_strings(self):
        """Test concatenation with empty strings."""
        program = """
        empty = ""
        text = "Hello"
        result = empty + text + empty
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello"'

    def test_concatenation_of_only_empty_strings(self):
        """Test concatenation of only empty strings."""
        program = """
        result = "" + "" + ""
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '""'

    def test_single_operand_no_concatenation(self):
        """Test that single operands work without concatenation."""
        program = """
        text = "Hello"
        output = text
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello"'


class TestConcatenationGrammarIntegration:
    """Test that concatenation integrates properly with grammar precedence."""

    def test_concatenation_precedence_at_assignment_level(self):
        """Test that concatenation has proper precedence at assignment level."""
        program = """
        a = "A"
        b = "B"
        c = "C"
        combined = a + b + c
        output = "Result: ${combined}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be left-associative: (a + b) + c
        assert result == '"Result: ABC"'

    def test_concatenation_left_associative(self):
        """Test concatenation is left-associative without parentheses."""
        program = """
        a = "A"
        b = "B"
        c = "C"
        d = "D"
        result = a + b + c + d
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"ABCD"'


class TestConcatenationErrorHandling:
    """Test error handling for malformed concatenation expressions."""

    def test_incomplete_concatenation_expression(self):
        """Test error for incomplete concatenation like 'str + '."""
        program = """
        str = "Hello"
        result = str +
        output = result
        return output
        """

        cy = Cy()
        with pytest.raises(CySyntaxError):
            cy.run(program)

    def test_concatenation_with_undefined_variable(self):
        """Test error handling when concatenating with undefined variables."""
        program = """
        str = "Hello"
        result = str + undefined
        output = result
        return output
        """

        cy = Cy()
        # Should raise an error for undefined variable
        with pytest.raises(Exception):  # Could be various error types
            cy.run(program)


class TestBackwardCompatibilityWithConcatenation:
    """Ensure existing features work alongside new concatenation support."""

    def test_concatenation_does_not_break_existing_interpolation(self):
        """Test that adding + operator doesn't break existing interpolation."""
        program = """
        name = "Alice"
        age = 30
        output = "Person: ${name}, Age: ${age}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Person: Alice, Age: 30"'

    def test_concatenation_with_printer_hints(self):
        """Test concatenation works with printer hints."""
        program = """
        items = ["apple", "banana"]
        prefix = "Items: "
        result = prefix + "${items|csv}"
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should contain the CSV formatted items
        assert "Items:" in result and "apple" in result

    def test_existing_plus_in_strings_unaffected(self):
        """Test that existing + characters in strings are unaffected."""
        program = """
        formula = "2 + 2 = 4"
        output = "Math: ${formula}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Math: 2 + 2 = 4"'
