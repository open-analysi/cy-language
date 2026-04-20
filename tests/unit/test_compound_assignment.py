"""
Unit tests for Compound Assignment Operators.

Tests +=, -=, *=, /=, %= operators with various data types.
"""

import pytest

from cy_language.interpreter import Cy


class TestPlusEqualsOperator:
    """Test += operator with numbers, strings, and lists."""

    def test_plus_equals_integers(self):
        """Test += with integers."""
        program = """
        x = 10
        x += 5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_plus_equals_floats(self):
        """Test += with floats."""
        program = """
        x = 10.5
        x += 2.3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "12.8" in result

    def test_plus_equals_strings(self):
        """Test += with strings (concatenation)."""
        program = """
        text = "Hello"
        text += " World"
        output = text
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World"'

    def test_plus_equals_lists(self):
        """Test += with lists (concatenation)."""
        program = """
        items = [1, 2]
        items += [3, 4]
        output = items
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[1, 2, 3, 4]" in result

    def test_plus_equals_multiple_times(self):
        """Test += used multiple times."""
        program = """
        x = 1
        x += 2
        x += 3
        x += 4
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "10"

    def test_plus_equals_with_expression(self):
        """Test += with complex expression."""
        program = """
        x = 10
        y = 5
        x += y * 2
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "20"


class TestMinusEqualsOperator:
    """Test -= operator with numbers."""

    def test_minus_equals_integers(self):
        """Test -= with integers."""
        program = """
        x = 10
        x -= 3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "7"

    def test_minus_equals_floats(self):
        """Test -= with floats."""
        program = """
        x = 10.5
        x -= 2.3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "8.2" in result

    def test_minus_equals_chain(self):
        """Test -= used multiple times."""
        program = """
        x = 100
        x -= 10
        x -= 20
        x -= 30
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "40"


class TestMultiplyEqualsOperator:
    """Test *= operator with numbers."""

    def test_multiply_equals_integers(self):
        """Test *= with integers."""
        program = """
        x = 5
        x *= 3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_multiply_equals_floats(self):
        """Test *= with floats."""
        program = """
        x = 2.5
        x *= 4.0
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "10" in result

    def test_multiply_equals_chain(self):
        """Test *= used multiple times."""
        program = """
        x = 2
        x *= 3
        x *= 2
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "12"


class TestDivideEqualsOperator:
    """Test /= operator with numbers."""

    def test_divide_equals_integers(self):
        """Test /= with integers."""
        program = """
        x = 20
        x /= 4
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "5" in result

    def test_divide_equals_floats(self):
        """Test /= with floats."""
        program = """
        x = 10.0
        x /= 2.5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "4" in result

    def test_divide_equals_chain(self):
        """Test /= used multiple times."""
        program = """
        x = 100
        x /= 2
        x /= 5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "10" in result


class TestModuloEqualsOperator:
    """Test %= operator with numbers."""

    def test_modulo_equals_integers(self):
        """Test %= with integers."""
        program = """
        x = 17
        x %= 5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "2"

    def test_modulo_equals_chain(self):
        """Test %= used multiple times."""
        program = """
        x = 100
        x %= 17
        x %= 5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 100 % 17 = 15, then 15 % 5 = 0
        assert result == "0"


class TestIndexedCompoundAssignment:
    """Test compound assignment with indexed access."""

    def test_indexed_plus_equals(self):
        """Test list[i] += value."""
        program = """
        numbers = [10, 20, 30]
        numbers[0] += 5
        numbers[1] += 10
        output = numbers
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[15, 30, 30]" in result

    def test_indexed_minus_equals(self):
        """Test list[i] -= value."""
        program = """
        numbers = [100, 50, 25]
        numbers[0] -= 10
        numbers[2] -= 5
        output = numbers
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[90, 50, 20]" in result

    def test_indexed_multiply_equals(self):
        """Test list[i] *= value."""
        program = """
        numbers = [2, 3, 4]
        numbers[0] *= 10
        numbers[1] *= 5
        output = numbers
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[20, 15, 4]" in result


class TestMixedScenarios:
    """Test compound assignment in various contexts."""

    def test_compound_in_loop(self):
        """Test compound assignment in for loop."""
        program = """
        numbers = [1, 2, 3, 4, 5]
        total = 0
        for (num in numbers) {
            total += num
        }
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_compound_in_conditional(self):
        """Test compound assignment in if statement."""
        program = """
        score = 80
        bonus = 10
        if (score >= 75) {
            score += bonus
        }
        output = score
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "90"

    def test_multiple_operators(self):
        """Test different compound operators in same program."""
        program = """
        a = 10
        b = 20
        c = 5
        a += 5
        b -= 3
        c *= 2
        total = a + b + c
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # a=15, b=17, c=10 → total=42
        assert result == "42"

    def test_compound_with_string_building(self):
        """Test += for building strings."""
        program = """
        message = "Hello"
        message += " "
        message += "World"
        message += "!"
        output = message
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World!"'

    def test_compound_with_list_building(self):
        """Test += for building lists."""
        program = """
        results = []
        results += [1]
        results += [2, 3]
        results += [4]
        output = results
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[1, 2, 3, 4]" in result


class TestErrorCases:
    """Test error handling with compound assignment."""

    def test_type_error_plus_equals(self):
        """Test += with incompatible types raises error."""
        program = """
        x = "text"
        x += 123
        output = x
        return output
        """

        cy = Cy()
        with pytest.raises(Exception):  # Should raise runtime error
            cy.run(program)

    def test_type_error_minus_equals(self):
        """Test -= with non-numeric type raises error."""
        program = """
        x = "text"
        x -= 5
        output = x
        return output
        """

        cy = Cy()
        with pytest.raises(Exception):  # Should raise runtime error
            cy.run(program)


class TestBackwardCompatibility:
    """Ensure regular = assignment still works."""

    def test_regular_assignment_still_works(self):
        """Test that regular = assignment is not broken."""
        program = """
        x = 10
        x = x + 5
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_regular_indexed_assignment_still_works(self):
        """Test that regular indexed = assignment is not broken."""
        program = """
        list = [1, 2, 3]
        list[0] = 100
        output = list
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[100, 2, 3]" in result
