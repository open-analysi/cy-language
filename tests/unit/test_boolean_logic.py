"""
Unit tests for Boolean Logic System.

Tests boolean literals, logical operations (and, or, not),
comparison operators, and mixed type comparisons.
"""

from src.cy_language.interpreter import Cy


class TestBooleanLiteralsAndVariables:
    """Test boolean literals and variable handling."""

    def test_true_literal_assignment(self):
        """Test True boolean literal assignment: $flag = True"""
        program = """
        flag = True
        output = "Flag is: ${flag}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Flag is: True"'

    def test_false_literal_assignment(self):
        """Test False boolean literal assignment: $flag = False"""
        program = """
        flag = False
        output = "Flag is: ${flag}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Flag is: False"'

    def test_boolean_variable_reference(self):
        """Test boolean variable reference in expressions."""
        program = """
        enabled = True
        result = enabled
        output = "Enabled: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Enabled: True"'


class TestBooleanOperations:
    """Test boolean logical operations (and, or, not)."""

    def test_logical_and_true_true(self):
        """Test logical AND: True and True = True"""
        program = """
        a = True
        b = True
        result = a and b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_logical_and_true_false(self):
        """Test logical AND: True and False = False"""
        program = """
        a = True
        b = False
        result = a and b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_logical_and_false_false(self):
        """Test logical AND: False and False = False"""
        program = """
        a = False
        b = False
        result = a and b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_logical_or_true_false(self):
        """Test logical OR: True or False = True"""
        program = """
        a = True
        b = False
        result = a or b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_logical_or_false_false(self):
        """Test logical OR: False or False = False"""
        program = """
        a = False
        b = False
        result = a or b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_logical_not_true(self):
        """Test logical NOT: not True = False"""
        program = """
        a = True
        result = not a
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_logical_not_false(self):
        """Test logical NOT: not False = True"""
        program = """
        a = False
        result = not a
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_boolean_operator_precedence(self):
        """Test boolean operator precedence: not, and, or"""
        program = """
        a = True
        b = False
        c = True
        result = a and b or c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: (True and False) or True = False or True = True
        assert result == '"Result: True"'

    def test_not_operator_precedence(self):
        """Test NOT operator has highest precedence."""
        program = """
        a = True
        b = False
        result = not a and b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: (not True) and False = False and False = False
        assert result == '"Result: False"'


class TestComparisonOperators:
    """Test comparison operators (==, !=, <, >, <=, >=)."""

    def test_equality_true(self):
        """Test equality comparison: equal values"""
        program = """
        a = 5
        b = 5
        result = a == b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_equality_false(self):
        """Test equality comparison: unequal values"""
        program = """
        a = 5
        b = 3
        result = a == b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_inequality_true(self):
        """Test inequality comparison: unequal values"""
        program = """
        a = 5
        b = 3
        result = a != b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_inequality_false(self):
        """Test inequality comparison: equal values"""
        program = """
        a = 5
        b = 5
        result = a != b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_less_than_true(self):
        """Test less than comparison: true case"""
        program = """
        a = 3
        b = 5
        result = a < b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_less_than_false(self):
        """Test less than comparison: false case"""
        program = """
        a = 5
        b = 3
        result = a < b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_greater_than_true(self):
        """Test greater than comparison: true case"""
        program = """
        a = 5
        b = 3
        result = a > b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_greater_than_false(self):
        """Test greater than comparison: false case"""
        program = """
        a = 3
        b = 5
        result = a > b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: False"'

    def test_less_than_or_equal_true_less(self):
        """Test <= comparison: less than case"""
        program = """
        a = 3
        b = 5
        result = a <= b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_less_than_or_equal_true_equal(self):
        """Test <= comparison: equal case"""
        program = """
        a = 5
        b = 5
        result = a <= b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_greater_than_or_equal_true_greater(self):
        """Test >= comparison: greater than case"""
        program = """
        a = 5
        b = 3
        result = a >= b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_greater_than_or_equal_true_equal(self):
        """Test >= comparison: equal case"""
        program = """
        a = 5
        b = 5
        result = a >= b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'


class TestMixedTypeComparisons:
    """Test comparisons with mixed types."""

    def test_integer_float_equality(self):
        """Test numeric equality across int/float types."""
        program = """
        int_val = 5
        float_val = 5.0
        result = int_val == float_val
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_integer_float_less_than(self):
        """Test numeric comparison across int/float types."""
        program = """
        int_val = 3
        float_val = 3.5
        result = int_val < float_val
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_string_equality(self):
        """Test string equality comparison."""
        program = """
        str1 = "hello"
        str2 = "hello"
        result = str1 == str2
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_string_inequality(self):
        """Test string inequality comparison."""
        program = """
        str1 = "hello"
        str2 = "world"
        result = str1 != str2
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'


class TestComplexBooleanExpressions:
    """Test complex boolean expressions combining multiple operations."""

    def test_mixed_boolean_and_comparison(self):
        """Test combining boolean and comparison operations."""
        program = """
        age = 25
        enabled = True
        result = age >= 18 and enabled
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'

    def test_complex_boolean_expression(self):
        """Test complex boolean expression with multiple operators."""
        program = """
        a = 10
        b = 5
        c = True
        d = False
        result = a > b and (c or d)
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert (
            result == '"Result: True"'
        )  # 10 > 5 and (True or False) = True and True = True

    def test_boolean_with_arithmetic_result(self):
        """Test boolean operations with arithmetic results."""
        program = """
        x = 5
        y = 3
        total = x + y
        result = total > 7
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'  # (5 + 3) > 7 = 8 > 7 = True


class TestBooleanErrorHandling:
    """Test error handling for boolean operations."""


class TestRealWorldBooleanScenarios:
    """Test real-world boolean logic scenarios."""

    def test_age_validation(self):
        """Test age validation scenario."""
        program = """
        age = 25
        has_license = True
        can_drive = age >= 18 and has_license
        output = "Can drive: ${can_drive}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Can drive: True"'

    def test_access_control(self):
        """Test access control logic."""
        program = """
        is_admin = False
        is_owner = True
        resource_public = False
        can_access = is_admin or is_owner or resource_public
        output = "Access granted: ${can_access}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Access granted: True"'

    def test_form_validation(self):
        """Test form validation scenario."""
        program = """
        name_valid = True
        email_valid = True
        age_valid = False
        form_valid = name_valid and email_valid and age_valid
        output = "Form is valid: ${form_valid}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Form is valid: False"'

    def test_business_logic_example(self):
        """Test business logic with multiple conditions."""
        program = """
        price = 100
        discount_eligible = True
        is_member = True
        final_discount = price > 50 and discount_eligible and is_member
        output = "Discount applies: ${final_discount}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Discount applies: True"'
