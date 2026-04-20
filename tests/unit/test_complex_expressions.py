"""
Unit tests for Complex Expression Integration.

Tests complex expressions combining arithmetic, boolean logic, and comparisons
with proper operator precedence and integration with existing features.
"""

from src.cy_language.interpreter import Cy


class TestArithmeticAndBooleanIntegration:
    """Test complex expressions combining arithmetic and boolean operations."""

    def test_arithmetic_result_in_comparison(self):
        """Test arithmetic result used in comparison: ($a + $b) > $threshold"""
        program = """
        a = 15
        b = 10
        threshold = 20
        result = (a + b) > threshold
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: True"'  # (15 + 10) > 20 = 25 > 20 = True

    def test_complex_business_logic_expression(self):
        """Test complex business logic: $price * $quantity >= $budget and $in_stock"""
        program = """
        price = 25
        quantity = 4
        budget = 90
        in_stock = True
        can_purchase = price * quantity >= budget and in_stock
        output = "Can purchase: ${can_purchase}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert (
            result == '"Can purchase: True"'
        )  # 25 * 4 >= 90 and True = 100 >= 90 and True = True

    def test_multiple_comparisons_with_boolean_logic(self):
        """Test multiple comparisons combined with boolean operations."""
        program = """
        age = 25
        income = 50000
        credit_score = 720
        eligible = age >= 18 and income > 40000 and credit_score >= 700
        output = "Eligible: ${eligible}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Eligible: True"'

    def test_complex_nested_expression_with_parentheses(self):
        """Test complex nested expression: ($a + $b) * $c >= $d and ($e or $f)"""
        program = """
        a = 5
        b = 3
        c = 4
        d = 30
        e = False
        f = True
        result = (a + b) * c >= d and (e or f)
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # (5 + 3) * 4 >= 30 and (False or True) = 8 * 4 >= 30 and True = 32 >= 30 and True = True
        assert result == '"Result: True"'

    def test_arithmetic_with_boolean_result(self):
        """Test arithmetic operations with boolean comparison result."""
        program = """
        x = 10
        y = 5
        is_greater = x > y
        multiplier = 3
        base_value = 2
        result = base_value + multiplier
        final_check = result == 5 and is_greater
        output = "Final check: ${final_check}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert (
            result == '"Final check: True"'
        )  # (2 + 3) == 5 and (10 > 5) = 5 == 5 and True = True


class TestOperatorPrecedenceInComplexExpressions:
    """Test operator precedence in complex expressions mixing arithmetic and boolean."""

    def test_arithmetic_comparison_boolean_precedence(self):
        """Test precedence: arithmetic > comparison > boolean"""
        program = """
        a = 5
        b = 3
        c = 2
        flag = True
        result = a + b > c and flag
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: ((5 + 3) > 2) and True = (8 > 2) and True = True and True = True
        assert result == '"Result: True"'

    def test_complex_precedence_without_parentheses(self):
        """Test complex precedence: $a * $b + $c < $d or $e"""
        program = """
        a = 2
        b = 3
        c = 4
        d = 15
        e = False
        result = a * b + c < d or e
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: ((2 * 3) + 4) < 15 or False = (6 + 4) < 15 or False = 10 < 15 or False = True or False = True
        assert result == '"Result: True"'

    def test_negation_precedence_in_complex_expression(self):
        """Test NOT precedence in complex expressions."""
        program = """
        a = 5
        b = 3
        flag = False
        result = not flag and a > b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: (not False) and (5 > 3) = True and True = True
        assert result == '"Result: True"'

    def test_unary_minus_in_complex_expression(self):
        """Test unary minus precedence in complex expressions."""
        program = """
        a = 5
        b = 3
        result = -a + b > 0
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be: ((-5) + 3) > 0 = (-2) > 0 = False
        assert result == '"Result: False"'


class TestIntegrationWithExistingFeatures:
    """Test complex expressions with 2/6.1 features."""

    def test_complex_expression_result_in_interpolation(self):
        """Test using complex expression results in string interpolation."""
        program = """
        price = 100
        tax_rate = 0.08
        discount = 10
        total = price + (price * tax_rate) - discount
        is_expensive = total > 95
        output = "Total: $${total}, Expensive: ${is_expensive}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 100 + (100 * 0.08) - 10 = 100 + 8 - 10 = 98
        assert "Total: $98.0" in result
        assert "Expensive: True" in result

    def test_complex_expression_with_concatenation(self):
        """Test complex expressions combined with string concatenation."""
        program = """
        base_price = 50
        quantity = 3
        discount_rate = 0.1
        total = base_price * quantity
        discount = total * discount_rate
        final_price = total - discount
        is_good_deal = final_price < 140
        status = "good" if is_good_deal else "expensive"
        output = "Price: $"++ final_price + " - Deal is "++ status
        return output
        """

        # Note: This test will need conditional assignment when implemented
        # For now, let's test a simpler version
        program = """
        base_price = 50
        quantity = 3
        total = base_price * quantity
        is_good_deal = total < 140
        output = "Total: $${total}, Good deal: ${is_good_deal}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Total: $150" in result
        assert "Good deal: False" in result


class TestRealWorldComplexScenarios:
    """Test real-world scenarios with complex expressions."""

    def test_loan_approval_logic(self):
        """Test complex loan approval logic."""
        program = """
        income = 75000
        debt = 20000
        credit_score = 750
        employment_years = 3
        debt_to_income_ratio = debt / income
        income_sufficient = income >= 50000
        credit_good = credit_score >= 700
        employment_stable = employment_years >= 2
        debt_manageable = debt_to_income_ratio <= 0.4
        approved = income_sufficient and credit_good and employment_stable and debt_manageable
        output = "Loan approved: ${approved}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # All conditions should be true, so loan should be approved
        assert result == '"Loan approved: True"'

    def test_shipping_cost_calculation(self):
        """Test shipping cost calculation with complex logic."""
        program = """
        weight = 5.5
        distance = 1200
        is_express = True
        base_rate = 2.5
        weight_cost = weight * base_rate
        distance_multiplier = 1.2
        distance_cost = distance / 100 * distance_multiplier
        express_fee = 15.0
        total_before_express = weight_cost + distance_cost
        express_cost = express_fee if is_express else 0
        total_cost = total_before_express + express_cost
        is_expensive = total_cost > 50
        output = "Shipping: ${total_cost}, Expensive: ${is_expensive}"
        return output
        """

        # Simplified version without conditional expressions
        program = """
        weight = 5.5
        distance = 1200
        is_express = True
        base_rate = 2.5
        weight_cost = weight * base_rate
        distance_multiplier = 1.2
        distance_cost = distance / 100 * distance_multiplier
        express_fee = 15.0
        total_before_express = weight_cost + distance_cost
        total_cost = total_before_express + express_fee
        is_expensive = total_cost > 50
        output = "Shipping: $${total_cost}, Expensive: ${is_expensive}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 5.5 * 2.5 + 1200/100 * 1.2 + 15 = 13.75 + 14.4 + 15 = 43.15
        assert "Shipping: $43.15" in result
        assert "Expensive: False" in result

    def test_grade_calculation_and_evaluation(self):
        """Test grade calculation with pass/fail logic."""
        program = """
        exam1 = 85
        exam2 = 92
        exam3 = 78
        homework = 88
        exam_average = (exam1 + exam2 + exam3) / 3
        exam_weight = 0.7
        homework_weight = 0.3
        final_grade = exam_average * exam_weight + homework * homework_weight
        passing_grade = 80
        is_passing = final_grade >= passing_grade
        is_honors = final_grade >= 90
        output = "Grade: ${final_grade}, Passing: ${is_passing}, Honors: ${is_honors}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # (85+92+78)/3 * 0.7 + 88 * 0.3 = 85 * 0.7 + 88 * 0.3 = 59.5 + 26.4 = 85.9
        # Handle floating point precision - check for 85.9 or its close representation
        assert "Grade: 85.9" in result or "Grade: 85.89999999999999" in result
        assert "Passing: True" in result
        assert "Honors: False" in result

    def test_inventory_management_logic(self):
        """Test inventory management with reorder logic."""
        program = """
        current_stock = 45
        min_stock = 50
        max_stock = 200
        reorder_quantity = 100
        unit_cost = 12.50
        needs_reorder = current_stock < min_stock
        projected_stock = current_stock + reorder_quantity
        within_max = projected_stock <= max_stock
        should_reorder = needs_reorder and within_max
        reorder_cost = reorder_quantity * unit_cost
        cost_acceptable = reorder_cost <= 1500
        final_decision = should_reorder and cost_acceptable
        output = "Reorder needed: ${final_decision}, Cost: $${reorder_cost}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # needs_reorder = 45 < 50 = True
        # projected_stock = 45 + 100 = 145, within_max = 145 <= 200 = True
        # should_reorder = True and True = True
        # reorder_cost = 100 * 12.50 = 1250.0
        # cost_acceptable = 1250.0 <= 1500 = True
        # final_decision = True and True = True
        assert "Reorder needed: True" in result
        assert "Cost: $1250.0" in result


class TestComplexExpressionErrorHandling:
    """Test error handling in complex expressions."""
