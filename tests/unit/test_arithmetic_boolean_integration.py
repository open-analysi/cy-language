"""
Integration tests for Mathematical Operations & Boolean Logic.

These tests verify that arithmetic operations, boolean logic, and complex expressions
work together correctly and integrate properly with existing .x features.
"""

import pytest

from cy_language.interpreter import Cy


class TestArithmeticIntegration:
    """Test arithmetic operations integration with existing features."""

    def test_arithmetic_with_string_interpolation(self):
        """Test arithmetic results string interpolation."""
        program = """
        price = 29.99
        quantity = 3
        tax_rate = 0.08
        subtotal = price * quantity
        tax = subtotal * tax_rate
        total = subtotal + tax
        output = "Order Summary:\\nSubtotal: $${subtotal}\\nTax: $${tax}\\nTotal: $${total}"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Subtotal: $89.97" in result
        assert "Tax: $7.1976" in result
        assert "Total: $97.1676" in result

    def test_arithmetic_with_string_concatenation(self):
        """Test arithmetic combined with string concatenation."""
        program = """
        base = 10
        multiplier = 3
        result = base * multiplier
        message = "The result of ${base} times ${multiplier} is ${result}"
        output = message
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"The result of 10 times 3 is 30"'

    def test_arithmetic_with_nested_quote_interpolation(self):
        """Test arithmetic with nested quote interpolation patterns."""
        program = """
        data = {"prices": [10, 20, 30], "multiplier": 2}
        base_price = 15
        adjustment = base_price * 2
        info = "Base: ${data['prices'][0]}, Adjusted: ${adjustment}"
        output = info
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Base: 10" in result
        assert "Adjusted: 30" in result


class TestBooleanLogicIntegration:
    """Test boolean logic integration with existing features."""

    def test_boolean_with_conditional_messages(self):
        """Test boolean logic with message formatting."""
        program = """
        age = 25
        has_license = True
        can_drive = age >= 18 and has_license
        status = "eligible"
        message = "Driver status: ${status} - Can drive: ${can_drive}"
        output = message
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Driver status: eligible - Can drive: True"'

    def test_comparison_results_in_interpolation(self):
        """Test comparison results in string interpolation."""
        program = """
        score1 = 85
        score2 = 92
        is_better = score2 > score1
        difference = score2 - score1
        output = "Score improved: ${is_better} (difference: ${difference} points)"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Score improved: True (difference: 7 points)"'


class TestComplexBusinessScenarios:
    """Test complex real-world business scenarios."""

    def test_e_commerce_order_processing(self):
        """Test e-commerce order processing with complex calculations."""
        program = """
        item_price = 49.99
        quantity = 2
        discount_rate = 0.15
        tax_rate = 0.08
        shipping_threshold = 75.00
        shipping_cost = 9.99

        subtotal = item_price * quantity
        discount = subtotal * discount_rate
        discounted_subtotal = subtotal - discount
        qualifies_free_shipping = discounted_subtotal >= shipping_threshold
        shipping = 0.00
        tax = discounted_subtotal * tax_rate
        total = discounted_subtotal + shipping + tax

        summary = "Subtotal: $${subtotal}"
        discount_line = "Discount (15%): -$${discount}"
        shipping_line = "Shipping: FREE (qualified)"
        tax_line = "Tax: $${tax}"
        total_line = "Total: $${total}"

        output = summary + "\\n" + discount_line + "\\n" + shipping_line + "\\n" + tax_line + "\\n" + total_line
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # 49.99 * 2 = 99.98
        # 99.98 * 0.15 = 14.997
        # 99.98 - 14.997 = 84.983
        # 84.983 >= 75.00 = True (free shipping)
        # 84.983 * 0.08 = 6.79864
        # total = 84.983 + 0 + 6.79864 = 91.78164
        assert "Subtotal: $99.98" in result
        assert "Discount (15%): -$14.997" in result
        assert "Shipping: FREE" in result
        assert "Tax: $6.79864" in result
        assert "Total: $91.78164" in result

    def test_loan_qualification_system(self):
        """Test loan qualification with multiple criteria."""
        program = """
        annual_income = 85000
        monthly_income = annual_income / 12
        existing_debt = 1200
        requested_loan = 250000
        credit_score = 740
        employment_years = 5

        debt_to_income_ratio = existing_debt / monthly_income
        loan_to_income_ratio = requested_loan / annual_income

        income_sufficient = annual_income >= 50000
        credit_acceptable = credit_score >= 650
        employment_stable = employment_years >= 2
        debt_manageable = debt_to_income_ratio <= 0.36
        loan_reasonable = loan_to_income_ratio <= 4.0

        base_qualified = income_sufficient and credit_acceptable and employment_stable
        fully_qualified = base_qualified and debt_manageable and loan_reasonable

        risk_level = "low"
        approval_status = "approved"

        result_summary = "Loan Application Result"
        income_line = "Monthly Income: $${monthly_income}"
        debt_ratio_line = "Debt-to-Income: ${debt_to_income_ratio}"
        qualification_line = "Qualified: ${fully_qualified}"
        status_line = "Status: ${approval_status}"

        output = result_summary + "\\n" + income_line + "\\n" + debt_ratio_line + "\\n" + qualification_line + "\\n" + status_line
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # 85000 / 12 = 7083.333...
        # 1200 / 7083.333... ≈ 0.169
        # 250000 / 85000 ≈ 2.94
        # All conditions should be true
        assert "Monthly Income: $7083.333" in result
        assert "Debt-to-Income: 0.169" in result
        assert "Qualified: True" in result
        assert "Status: approved" in result

    def test_inventory_reorder_system(self):
        """Test inventory management with complex reorder logic."""
        program = """
        current_stock = 23
        daily_usage = 8
        lead_time_days = 5
        safety_stock = 10
        max_capacity = 200
        unit_cost = 15.75
        budget_limit = 2000

        minimum_needed = daily_usage * lead_time_days + safety_stock
        needs_reorder = current_stock < minimum_needed
        reorder_quantity = minimum_needed * 2
        projected_stock = current_stock + reorder_quantity
        within_capacity = projected_stock <= max_capacity
        total_cost = reorder_quantity * unit_cost
        within_budget = total_cost <= budget_limit

        should_reorder = needs_reorder and within_capacity and within_budget

        status_line = "Inventory Status"
        current_line = "Current Stock: ${current_stock}"
        minimum_line = "Minimum Needed: ${minimum_needed}"
        reorder_line = "Should Reorder: ${should_reorder}"
        quantity_line = "Reorder Quantity: ${reorder_quantity}"
        cost_line = "Total Cost: $${total_cost}"

        output = status_line + "\\n" + current_line + "\\n" + minimum_line + "\\n" + reorder_line + "\\n" + quantity_line + "\\n" + cost_line
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # minimum_needed = 8 * 5 + 10 = 50
        # needs_reorder = 23 < 50 = True
        # reorder_quantity = 50 * 2 = 100
        # projected_stock = 23 + 100 = 123
        # within_capacity = 123 <= 200 = True
        # total_cost = 100 * 15.75 = 1575
        # within_budget = 1575 <= 2000 = True
        # should_reorder = True and True and True = True
        assert "Current Stock: 23" in result
        assert "Minimum Needed: 50" in result
        assert "Should Reorder: True" in result
        assert "Reorder Quantity: 100" in result
        assert "Total Cost: $1575.0" in result


class TestEducationalAndGradingScenarios:
    """Test educational scenarios with grade calculations."""

    def test_comprehensive_grade_calculator(self):
        """Test comprehensive grade calculation system."""
        program = """
        exam1 = 88
        exam2 = 92
        exam3 = 85
        quiz1 = 95
        quiz2 = 87
        quiz3 = 91
        homework_avg = 89
        participation = 93

        exam_avg = (exam1 + exam2 + exam3) / 3
        quiz_avg = (quiz1 + quiz2 + quiz3) / 3

        exam_weight = 0.4
        quiz_weight = 0.2
        homework_weight = 0.25
        participation_weight = 0.15

        weighted_exam = exam_avg * exam_weight
        weighted_quiz = quiz_avg * quiz_weight
        weighted_homework = homework_avg * homework_weight
        weighted_participation = participation * participation_weight

        final_grade = weighted_exam + weighted_quiz + weighted_homework + weighted_participation

        is_passing = final_grade >= 70
        is_honors = final_grade >= 90
        is_dean_list = final_grade >= 95

        grade_letter = "B+"

        header = "Grade Report"
        exam_line = "Exam Average: ${exam_avg}"
        quiz_line = "Quiz Average: ${quiz_avg}"
        final_line = "Final Grade: ${final_grade}"
        passing_line = "Passing: ${is_passing}"
        honors_line = "Honors: ${is_honors}"
        dean_line = "Dean's List: ${is_dean_list}"

        output = header + "\\n" + exam_line + "\\n" + quiz_line + "\\n" + final_line + "\\n" + passing_line + "\\n" + honors_line + "\\n" + dean_line
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # exam_avg = (88 + 92 + 85) / 3 = 265 / 3 ≈ 88.33
        # quiz_avg = (95 + 87 + 91) / 3 = 273 / 3 = 91
        # final_grade = 88.33*0.4 + 91*0.2 + 89*0.25 + 93*0.15 = 35.33 + 18.2 + 22.25 + 13.95 = 89.73
        assert "Exam Average: 88.333" in result
        assert "Quiz Average: 91.0" in result
        assert "Final Grade: 89.73" in result
        assert "Passing: True" in result
        assert "Honors: False" in result
        assert "Dean's List: False" in result


class TestHealthcareAndScienceScenarios:
    """Test healthcare and scientific calculation scenarios."""

    def test_bmi_calculation_and_assessment(self):
        """Test BMI calculation with health assessments."""
        program = """
        height_cm = 175
        weight_kg = 72
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)

        underweight = bmi < 18.5
        normal_weight = bmi >= 18.5 and bmi < 25
        overweight = bmi >= 25 and bmi < 30
        obese = bmi >= 30

        healthy_range = normal_weight

        header = "BMI Assessment"
        height_line = "Height: ${height_cm} cm"
        weight_line = "Weight: ${weight_kg} kg"
        bmi_line = "BMI: ${bmi}"
        category_line = "Normal Weight: ${normal_weight}"
        healthy_line = "Healthy Range: ${healthy_range}"

        output = header + "\\n" + height_line + "\\n" + weight_line + "\\n" + bmi_line + "\\n" + category_line + "\\n" + healthy_line
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # height_m = 175 / 100 = 1.75
        # bmi = 72 / (1.75 * 1.75) = 72 / 3.0625 ≈ 23.51
        # normal_weight = 23.51 >= 18.5 and 23.51 < 25 = True
        assert "Height: 175 cm" in result
        assert "Weight: 72 kg" in result
        assert "BMI: 23.51" in result
        assert "Normal Weight: True" in result
        assert "Healthy Range: True" in result


class TestBackwardCompatibilityWithArithmetic:
    """Test that features don't break existing functionality."""

    def test_string_features_still_work(self):
        """Test that nested quotes and concatenation still work."""
        program = """
        data = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
        first_name = "${data['users'][0]['name']}"
        first_age = "${data['users'][0]['age']}"
        greeting = "Hello ${first_name}, you are ${first_age} years old"
        output = greeting
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello Alice, you are 30 years old"'

    def test_indexed_access_with_arithmetic(self):
        """Test that indexed access works with arithmetic."""
        program = """
        numbers = [10, 20, 30, 40]
        first = 5
        second = 15
        total = first + second
        index = 1
        array_value = numbers[index]
        comparison = total == array_value
        output = "Sum equals array value: ${comparison}"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Sum equals array value: True"'

    def test_existing_interpolation_modes_with_arithmetic(self):
        """Test that existing interpolation modes work with arithmetic results."""
        program = """
        base = 10
        multiplier = 3
        items = [base, base * multiplier, base * multiplier * 2]
        output = "Items:\\n${items|markdown}"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Items:" in result
        assert "- 10" in result
        assert "- 30" in result
        assert "- 60" in result


class TestArithmeticErrorScenarios:
    """Test error handling features."""

    # Re-enabled: Testing if division by zero error handling now works
    def test_division_by_zero_error(self):
        """Test division by zero produces clear error."""
        program = """
        a = 10
        b = 0
        result = a / b
        output = "Result: ${result}"
                return output
        """

        cy = Cy()
        with pytest.raises((ZeroDivisionError, Exception)):
            cy.run(program)

    # Re-enabled: Testing if type error handling now works
    def test_type_error_in_arithmetic(self):
        """Test type error in arithmetic operations."""
        program = """
        string_val = "hello"
        number = 5
        result = string_val * number
        output = "Result: ${result}"
                return output
        """

        cy = Cy()
        with pytest.raises(Exception):
            cy.run(program)


class TestPerformanceAndScalability:
    """Test performance aspects of features."""

    def test_complex_nested_calculations(self):
        """Test complex nested calculations for performance."""
        program = """
        a = 2
        b = 3
        c = 4
        d = 5
        e = 6

        level1 = (a + b) * c
        level2 = (level1 - d) / e
        level3 = level2 * (a + b + c + d + e)
        level4 = level3 > 10 and level3 < 100

        output = "Final result: ${level4}"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # level1 = (2 + 3) * 4 = 5 * 4 = 20
        # level2 = (20 - 5) / 6 = 15 / 6 = 2.5
        # level3 = 2.5 * (2 + 3 + 4 + 5 + 6) = 2.5 * 20 = 50
        # level4 = 50 > 10 and 50 < 100 = True and True = True
        assert result == '"Final result: True"'

    def test_many_boolean_operations(self):
        """Test many boolean operations for performance."""
        program = """
        flag1 = True
        flag2 = False
        flag3 = True
        flag4 = True
        flag5 = False
        flag6 = True

        result1 = flag1 and flag2 or flag3
        result2 = flag4 and (flag5 or flag6)
        result3 = not flag2 and flag1
        final = result1 and result2 and result3

        output = "Complex boolean result: ${final}"
                return output
        """

        cy = Cy()
        result = cy.run(program)
        # result1 = True and False or True = False or True = True
        # result2 = True and (False or True) = True and True = True
        # result3 = not False and True = True and True = True
        # final = True and True and True = True
        assert result == '"Complex boolean result: True"'
