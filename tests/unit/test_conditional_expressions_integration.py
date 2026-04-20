"""Integration tests for conditional expressions.

These tests verify conditional expressions work end-to-end with the interpreter.
"""

from cy_language.interpreter import Cy


class TestConditionalExpressionsIntegration:
    """Integration tests for conditional expressions with actual execution."""

    def test_simple_conditional_execution(self):
        """Conditional expression executes correctly."""
        code = """
score = 85
grade = if (score >= 90) { "A" } else { "B" }
output = grade
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"B"'

    def test_conditional_with_elif_execution(self):
        """Conditional with elif executes correctly."""
        code = """
score = 85
grade = if (score >= 90) { "A" } elif (score >= 80) { "B" } else { "C" }
output = grade
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"B"'

    def test_conditional_union_type_number(self):
        """Conditional with union type returns correct number."""
        code = """
flag = True
value = if (flag) { 42 } else { "text" }
output = value
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "42"  # Output is stringified

    def test_conditional_union_type_string(self):
        """Conditional with union type returns correct string."""
        code = """
flag = False
value = if (flag) { 42 } else { "text" }
output = value
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"text"'

    def test_nested_conditional_execution(self):
        """Nested conditional expressions execute correctly."""
        code = """
x = 10
result = if (x > 5) { if (x > 8) { "large" } else { "medium" } } else { "small" }
output = result
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"large"'

    def test_conditional_in_arithmetic_execution(self):
        """Conditional expression in arithmetic works."""
        code = """
x = 5
result = (if (x > 3) { 10 } else { 20 }) + 5
output = result
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "15"  # Output is stringified

    def test_conditional_with_string_concat(self):
        """Conditional expression with string concatenation."""
        code = """
status = "active"
message = "User is " + if (status == "active") { "online" } else { "offline" }
output = message
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"User is online"'

    def test_multiple_conditionals_same_variable(self):
        """Multiple conditional expressions using same variable."""
        code = """
score = 75
grade = if (score >= 90) { "A" } else { "Not A" }
category = if (score >= 70) { "Pass" } else { "Fail" }
output = grade + " - " + category
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Not A - Pass"'

    def test_conditional_with_array_result(self):
        """Conditional returning arrays."""
        code = """
flag = True
items = if (flag) { [1, 2, 3] } else { [4, 5, 6] }
output = items[1]
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "2"  # Output is stringified

    def test_conditional_with_object_result(self):
        """Conditional returning objects."""
        code = """
user_type = "admin"
user = if (user_type == "admin") { {"role": "admin", "level": 10} } else { {"role": "user", "level": 1} }
output = user["level"]
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "10"  # Output is stringified

    def test_conditional_all_numeric_types(self):
        """Conditional with all numeric branches."""
        code = """
x = 5
value = if (x > 10) { 100 } elif (x > 5) { 50 } elif (x > 0) { 25 } else { 0 }
output = value
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "25"  # Output is stringified

    def test_conditional_in_interpolation(self):
        """Conditional expression in string interpolation - not yet supported."""
        # TODO: Conditional expressions in interpolation require interpolation parser updates
        # For now, use a variable approach
        code = """
age = 25
status = if (age >= 18) { "adult" } else { "minor" }
message = "User is " + status
output = message
return output
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"User is adult"'

    def test_conditional_complex_real_world(self):
        """Complex real-world scenario with conditional expressions."""
        code = """
# Calculate discount based on purchase amount
purchase_amount = 150
discount_rate = if (purchase_amount >= 200) { 0.20 } elif (purchase_amount >= 100) { 0.10 } else { 0.0 }
final_amount = purchase_amount * (1 - discount_rate)

# Determine shipping
shipping = if (purchase_amount >= 100) { 0 } else { 10 }
total = final_amount + shipping

# Status message
status = if (discount_rate > 0) { "Discount applied!" } else { "No discount" }

output = total
return output
"""
        cy = Cy()
        result = cy.run(code)
        # 150 * 0.9 (10% discount) = 135, shipping = 0, total = 135
        assert result == "135.0"  # Output is stringified
