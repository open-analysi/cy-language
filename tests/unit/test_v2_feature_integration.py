"""
Test cases for Version 2 feature integration.

This module tests complex scenarios combining all Version 2 features
and demonstrates that they work together seamlessly.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestVersion2ComplexIntegration:
    """Test complex scenarios combining all Version 2 features."""

    def setup_method(self):
        """Set up test fixtures."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        self.interpreter = interpreter

    def test_complex_business_logic_integration(self):
        """Test complex business logic combining math, control flow, and data access."""
        variables = {
            "temperature": 75,
            "humidity": 60,
            "season": "summer",
            "user_preferences": {"temp_min": 70, "temp_max": 80},
        }
        interpreter = Cy(variables=variables)
        interpreter.show_enhanced_errors = False

        program = """temp = temperature
humid = humidity
prefs = user_preferences
comfort_score = 0

# Calculate base comfort score using math and control flow
if (temp >= prefs['temp_min'] and temp <= prefs['temp_max']) {
    comfort_score = comfort_score + 50
}

if (humid >= 40 and humid <= 60) {
    comfort_score = comfort_score + 30
}

# Apply seasonal adjustments with nested conditions
if (season == "summer") {
    if (temp > 75) {
        comfort_score = comfort_score - 10
    }
}

# Generate detailed output based on score ranges
if (comfort_score >= 70) {
    status = "Perfect"
    recommendation = "Ideal conditions"
} elif (comfort_score >= 50) {
    status = "Good"
    recommendation = "Minor adjustments recommended"
} else {
    status = "Poor"
    recommendation = "Significant improvements needed"
}

output = "Comfort Assessment: ${status} (${comfort_score}/100) - ${recommendation}"
return output
"""

        result = interpreter.run(program)
        assert "Comfort Assessment:" in result
        assert "80/100" in result  # Expected score: 50 (temp) + 30 (humidity) = 80
        assert "Perfect" in result

    def test_mathematical_operations_in_loops(self):
        """Test mathematical operations used in complex loop scenarios."""
        variables = {"data_points": [10, 20, 30, 40, 50]}
        interpreter = Cy(variables=variables)
        interpreter.show_enhanced_errors = False

        program = """points = data_points
total = 0
count = 0
processed_str = ""

# Process each data point with mathematical transformations
while (count < 5) {
    current = points[count]
    transformed = current * 2 + 5
    total = total + transformed
    if (count > 0) {
        processed_str = processed_str + ", "
    }
    # Use interpolation to convert number to string
    processed_str = "${processed_str}${transformed}"
    count = count + 1
}

average = total / 5

if (average > 50) {
    output = "High average: ${average} from processed data [${processed_str}]"
} else {
    output = "Low average: ${average} from processed data [${processed_str}]"
}
return output
"""

        result = interpreter.run(program)
        assert "average:" in result
        assert "processed data" in result
        # Verify mathematical correctness: (10*2+5) + (20*2+5) + ... = 25+45+65+85+105 = 325, avg = 65
        assert "65" in result

    def test_nested_control_flow_with_data_structures(self):
        """Test deeply nested control structures with complex data manipulation."""
        variables = {
            "inventory": {
                "electronics": {"laptop": 5, "phone": 12, "tablet": 8},
                "books": {"fiction": 20, "technical": 15, "educational": 30},
            },
            "min_stock": 10,
        }
        interpreter = Cy(variables=variables)
        interpreter.show_enhanced_errors = False

        program = """stock = inventory
min_level = min_stock
low_stock_items = ""
low_count = 0
total_value = 0

# Check each category
categories = ["electronics", "books"]
cat_index = 0

while (cat_index < 2) {
    category = categories[cat_index]
    items = stock[category]

    # Process electronics items
    if (category == "electronics") {
        if (items['laptop'] < min_level) {
            if (low_count > 0) {
                low_stock_items = low_stock_items + ", "
            }
            low_stock_items = low_stock_items + "laptop"
            low_count = low_count + 1
        }
        if (items['phone'] >= min_level) {
            total_value = total_value + items['phone'] * 500  # $500 per phone
        }
        if (items['tablet'] < min_level) {
            if (low_count > 0) {
                low_stock_items = low_stock_items + ", "
            }
            low_stock_items = low_stock_items + "tablet"
            low_count = low_count + 1
        }
    }

    # Process books items
    if (category == "books") {
        if (items['fiction'] >= min_level) {
            total_value = total_value + items['fiction'] * 20  # $20 per book
        }
        if (items['technical'] >= min_level) {
            total_value = total_value + items['technical'] * 50  # $50 per technical book
        }
        if (items['educational'] >= min_level) {
            total_value = total_value + items['educational'] * 30  # $30 per educational book
        }
    }

    cat_index = cat_index + 1
}

if (low_count > 0) {
    output = "Low stock alert: ${low_stock_items} | Portfolio value: ${total_value}"
} else {
    output = "All items well stocked | Portfolio value: ${total_value}"
}
return output
"""

        result = interpreter.run(program)
        assert "stock" in result
        assert "Portfolio value:" in result
        # Should identify laptop and tablet as low stock
        assert "laptop" in result

    def test_version_2_error_handling_integration(self):
        """Test that errors in complex Version 2 programs provide good context."""
        interpreter = Cy()

        program = """x = 10
y = 5

if (x > y) {
    result = x / 0  # This should cause a division by zero error
    output = result
} else {
    output = "x is not greater than y"
}
return output
"""

        with pytest.raises(Exception) as exc_info:
            interpreter.run(program)

        # Should get a division by zero error
        assert "Division by zero" in str(exc_info.value)

    def test_return_statement_in_complex_control_flow(self):
        """Test return statements work correctly in complex control flow scenarios."""
        variables = {"threshold": 50, "values": [10, 30, 60, 20]}
        interpreter = Cy(variables=variables)
        interpreter.show_enhanced_errors = False

        program = """limit = threshold
data = values
index = 0

while (index < 4) {
    current = data[index]

    if (current > limit) {
        return "Found value ${current} exceeding threshold ${limit} at position ${index}"
    }

    index = index + 1
}

return "No values exceed the threshold of ${limit}"
"""

        result = interpreter.run(program)
        assert result == '"Found value 60 exceeding threshold 50 at position 2"'


class TestBackwardCompatibilityVerification:
    """Verify that all existing examples continue to work with Version 2."""

    def setup_method(self):
        """Set up test fixtures."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        self.interpreter = interpreter

    def test_version_2_features_dont_break_v1_programs(self):
        """Test that Version 1 programs still work correctly."""
        interpreter = Cy()

        # This is a Version 1 style program (no control flow, simple features)
        program = """name = "Alice"
items = ["apple", "banana", "cherry"]
user = {"name": name, "age": 30}

output = "User: ${user.name} has ${items|csv}"
return output
"""

        result = interpreter.run(program)
        assert "User: Alice has" in result
        assert "apple" in result
        assert "banana" in result
        assert "cherry" in result


class TestComplexRealWorldScenarios:
    """Test realistic business scenarios using all Version 2 features."""

    def setup_method(self):
        """Set up test fixtures."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        self.interpreter = interpreter

    def test_loan_approval_system(self):
        """Test a complete loan approval system with complex business logic."""
        variables = {
            "applicant": {
                "credit_score": 720,
                "annual_income": 75000,
                "debt_to_income": 0.3,
                "employment_years": 5,
            },
            "loan_request": {
                "amount": 200000,
                "term_years": 30,
                "property_value": 250000,
            },
        }
        interpreter = Cy(variables=variables)
        interpreter.show_enhanced_errors = False

        program = """applicant = applicant
loan = loan_request
approval_score = 0
conditions = ""

# Credit score evaluation
if (applicant['credit_score'] >= 750) {
    approval_score = approval_score + 40
} elif (applicant['credit_score'] >= 700) {
    approval_score = approval_score + 30
} elif (applicant['credit_score'] >= 650) {
    approval_score = approval_score + 20
    conditions = conditions + "Higher interest rate; "
} else {
    approval_score = approval_score + 0
    conditions = conditions + "Credit score too low; "
}

# Income evaluation
income_ratio = loan['amount'] / applicant['annual_income']
if (income_ratio <= 3.0) {
    approval_score = approval_score + 30
} elif (income_ratio <= 4.0) {
    approval_score = approval_score + 20
} else {
    approval_score = approval_score + 10
    conditions = conditions + "High loan-to-income ratio; "
}

# Debt-to-income evaluation
if (applicant['debt_to_income'] <= 0.28) {
    approval_score = approval_score + 20
} elif (applicant['debt_to_income'] <= 0.36) {
    approval_score = approval_score + 15
} else {
    approval_score = approval_score + 5
    conditions = conditions + "High debt-to-income ratio; "
}

# Final decision
if (approval_score >= 75) {
    decision = "APPROVED"
} elif (approval_score >= 60) {
    decision = "CONDITIONAL_APPROVAL"
} else {
    decision = "DENIED"
}

if (conditions != "") {
    output = "Decision: ${decision} (Score: ${approval_score}/90) - Conditions: ${conditions}"
} else {
    output = "Decision: ${decision} (Score: ${approval_score}/90) - No conditions"
}
return output
"""

        result = interpreter.run(program)
        assert "Decision:" in result
        assert "Score:" in result
        assert "/90)" in result
        # With good credit (720), reasonable income ratio, and good DTI (0.3), should get good score
        assert any(
            decision in result for decision in ["APPROVED", "CONDITIONAL_APPROVAL"]
        )
