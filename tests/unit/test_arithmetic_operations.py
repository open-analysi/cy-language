"""
Unit tests for Arithmetic Operations.

Tests basic arithmetic operators (+, -, *, /) at assignment level,
operator precedence, parenthetical grouping, and type handling.
"""

import pytest

from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.interpreter import Cy


class TestBasicArithmeticOperators:
    """Test basic arithmetic operators at assignment level."""

    def test_basic_addition(self):
        """Test basic addition: $result = $a + $b"""
        program = """
        a = 5
        b = 3
        result = a + b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 8"'

    def test_basic_subtraction(self):
        """Test basic subtraction: $result = $a - $b"""
        program = """
        a = 10
        b = 3
        result = a - b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 7"'

    def test_basic_multiplication(self):
        """Test basic multiplication: $result = $a * $b"""
        program = """
        a = 6
        b = 4
        result = a * b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 24"'

    def test_basic_division(self):
        """Test basic division: $result = $a / $b"""
        program = """
        a = 15
        b = 3
        result = a / b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 5.0"'  # Division should return float

    def test_division_with_float_result(self):
        """Test division that produces a float result."""
        program = """
        a = 10
        b = 3
        result = a / b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be approximately 3.333...
        assert "3.333" in result


class TestOperatorPrecedenceAndGrouping:
    """Test operator precedence and parenthetical grouping."""

    def test_multiplication_precedence_over_addition(self):
        """Test that * has higher precedence than +: $result = $a + $b * $c"""
        program = """
        a = 2
        b = 3
        c = 4
        result = a + b * c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 14"'  # 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20

    def test_division_precedence_over_subtraction(self):
        """Test that / has higher precedence than -: $result = $a - $b / $c"""
        program = """
        a = 10
        b = 8
        c = 2
        result = a - b / c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 6.0"'  # 10 - (8 / 2) = 6.0, not (10 - 8) / 2 = 1.0

    def test_left_to_right_same_precedence_addition(self):
        """Test left-to-right evaluation for same precedence: $result = $a + $b + $c"""
        program = """
        a = 1
        b = 2
        c = 3
        result = a + b + c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 6"'  # ((1 + 2) + 3) = 6

    def test_left_to_right_same_precedence_multiplication(self):
        """Test left-to-right evaluation for same precedence: $result = $a * $b * $c"""
        program = """
        a = 2
        b = 3
        c = 4
        result = a * b * c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 24"'  # ((2 * 3) * 4) = 24

    def test_parentheses_override_precedence(self):
        """Test parentheses override precedence: $result = ($a + $b) * $c"""
        program = """
        a = 2
        b = 3
        c = 4
        result = (a + b) * c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 20"'  # (2 + 3) * 4 = 20

    def test_nested_parentheses(self):
        """Test nested parentheses: $result = (($a + $b) * $c) / $d"""
        program = """
        a = 1
        b = 2
        c = 3
        d = 2
        result = ((a + b) * c) / d
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 4.5"'  # ((1 + 2) * 3) / 2 = 9 / 2 = 4.5

    def test_complex_precedence_expression(self):
        """Test complex expression with multiple precedence levels."""
        program = """
        a = 2
        b = 3
        c = 4
        d = 5
        result = a + b * c - d
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 9"'  # 2 + (3 * 4) - 5 = 2 + 12 - 5 = 9


class TestUnaryOperators:
    """Test unary operators (-, +)."""

    def test_unary_minus_with_variable(self):
        """Test unary minus: $result = -$value"""
        program = """
        value = 5
        result = -value
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: -5"'

    def test_unary_plus_with_variable(self):
        """Test unary plus: $result = +$value"""
        program = """
        value = 5
        result = +value
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 5"'

    def test_unary_minus_with_expression(self):
        """Test unary minus with parentheses: $result = -($a + $b)"""
        program = """
        a = 3
        b = 4
        result = -(a + b)
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: -7"'

    def test_double_negative(self):
        """Test double negative: $result = -(-$value)"""
        program = """
        value = 5
        result = -(-value)
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 5"'


class TestMixedTypeArithmetic:
    """Test arithmetic with mixed types (int, float)."""

    def test_integer_plus_float(self):
        """Test integer + float operations with type promotion."""
        program = """
        int_val = 5
        float_val = 2.5
        result = int_val + float_val
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 7.5"'

    def test_float_times_integer(self):
        """Test float * integer operations."""
        program = """
        float_val = 3.5
        int_val = 2
        result = float_val * int_val
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 7.0"'

    def test_integer_division_produces_float(self):
        """Test that integer division produces float result."""
        program = """
        a = 7
        b = 2
        result = a / b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 3.5"'


class TestArithmeticErrorHandling:
    """Test error handling for arithmetic operations."""

    def test_division_by_zero(self):
        """Test division by zero error handling."""
        program = """
        a = 10
        result = a / 0
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        with pytest.raises((CyRuntimeError, ZeroDivisionError)):
            cy.run(program)

    def test_division_by_zero_variable(self):
        """Test division by zero with variable."""
        program = """
        a = 10
        b = 0
        result = a / b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        with pytest.raises((CyRuntimeError, ZeroDivisionError)):
            cy.run(program)

    # Re-enabled: Testing if type error handling now works
    def test_string_arithmetic_error(self):
        """Test error when trying arithmetic with strings."""
        program = """
        a = "hello"
        b = 5
        result = a + b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        with pytest.raises(CyRuntimeError):
            cy.run(program)


class TestArithmeticWithExistingFeatures:
    """Test arithmetic integration with existing 2/6.1 features."""

    def test_arithmetic_result_in_interpolation(self):
        """Test using arithmetic results in string interpolation."""
        program = """
        price = 10
        tax = 2
        total = price + tax
        output = "Total cost: $${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Total cost: $12"'

    def test_arithmetic_with_concatenation(self):
        """Test arithmetic combined with string interpolation."""
        program = """
        a = 5
        b = 3
        total = a + b
        output = "The sum of ${a} and ${b} is ${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"The sum of 5 and 3 is 8"'

    def test_arithmetic_with_indexed_access(self):
        """Test arithmetic with indexed access."""
        program = """
        numbers = [10, 20, 30]
        result = numbers[0] + numbers[1]
        output = "Sum: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Sum: 30"'


class TestRealWorldArithmeticScenarios:
    """Test real-world arithmetic scenarios."""

    def test_price_calculation(self):
        """Test price calculation scenario."""
        program = """
        price = 100
        tax_rate = 0.08
        tax = price * tax_rate
        total = price + tax
        output = "Price: $${price}, Tax: $${tax}, Total: $${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Price: $100" in result
        assert "Tax: $8.0" in result
        assert "Total: $108.0" in result

    def test_area_calculation(self):
        """Test geometric area calculation."""
        program = """
        length = 12
        width = 8
        area = length * width
        output = "Rectangle area: ${area} square units"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Rectangle area: 96 square units"'

    def test_average_calculation(self):
        """Test average calculation."""
        program = """
        total = 85 + 92 + 78 + 96
        count = 4
        average = total / count
        output = "Average score: ${average}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Average score: 87.75" in result
