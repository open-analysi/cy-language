"""
Integration tests for Universal + Operator Real-World Scenarios.

Tests the + operator in realistic program contexts including:
- Data processing workflows
- Complex expressions
- Loop usage
- Conditional logic
"""

import pytest

from cy_language.interpreter import Cy


class TestDataProcessing:
    """Test + operator in data processing scenarios."""

    def test_build_csv_string(self):
        """Test building CSV string with + operator"""
        program = """
        header = "name" + "," + "age" + "," + "city"
        output = header
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"name,age,city"'

    def test_accumulate_list_results(self):
        """Test building result list with + operator"""
        program = """
        results = []
        results = results + [1]
        results = results + [2]
        results = results + [3]
        output = results
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[1, 2, 3]" in result

    def test_numeric_calculations(self):
        """Test chaining numeric additions for calculations"""
        program = """
        price1 = 10.99
        price2 = 20.50
        tax = 2.45
        shipping = 5.00
        total = price1 + price2 + tax + shipping
        output = "Total: $${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Total: $38.94" in result

    def test_string_builder_pattern(self):
        """Test accumulating strings with + operator"""
        program = """
        report = "Report:\\n"
        report = report + "Item 1: Complete\\n"
        report = report + "Item 2: Complete\\n"
        report = report + "Status: Done"
        output = report
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Report:" in result
        assert "Item 1: Complete" in result
        assert "Item 2: Complete" in result
        assert "Status: Done" in result


class TestComplexExpressions:
    """Test + operator in complex expressions."""

    def test_plus_in_interpolation(self):
        """Test + operator inside string interpolation"""
        program = """
        a = 5
        b = 10
        output = "Total: ${a + b}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Total: 15"'

    def test_plus_in_conditions(self):
        """Test + operator in conditional expressions"""
        program = """
        count = 5
        if (count + 1 > 5) {
            output = "Greater than 5"
        } else {
            output = "Not greater"
        }
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Greater than 5"'

    def test_plus_with_parentheses(self):
        """Test + operator with parenthetical grouping"""
        program = """
        a = "Hello"
        b = "World"
        c = "!"
        result = (a + " ") + (b + c)
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World!"'

    def test_plus_with_list_access(self):
        """Test + operator with list element access"""
        program = """
        items = [10, 20, 30]
        bonus = 5
        total = items[0] + items[1] + items[2] + bonus
        output = "Total: ${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Total: 65"'

    def test_plus_with_dict_access(self):
        """Test + operator with dictionary field access"""
        program = """
        person = {"first": "John", "last": "Doe"}
        fullname = person.first + " " + person.last
        output = fullname
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"John Doe"'


class TestLoopUsage:
    """Test + operator in loop contexts."""

    def test_plus_in_for_loop(self):
        """Test + operator inside for loop for accumulation"""
        program = """
        numbers = [1, 2, 3, 4, 5]
        total = 0
        for (num in numbers) {
            total = total + num
        }
        output = "Total: ${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Total: 15"'

    def test_plus_in_while_loop(self):
        """Test + operator in while loop"""
        program = """
        x = 5
        result = 0
        while (x > 0) {
            result = result + x
            x = x - 1
        }
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 15"'

    def test_string_accumulation_in_loop(self):
        """Test string concatenation in loop"""
        program = """
        words = ["Hello", "from", "Cy"]
        sentence = ""
        for (word in words) {
            sentence = sentence + word + " "
        }
        output = sentence
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Hello from Cy" in result

    def test_list_building_in_loop(self):
        """Test list concatenation in loop"""
        program = """
        source = [1, 2, 3]
        doubled = []
        for (num in source) {
            doubled = doubled + [num, num]
        }
        output = "${doubled}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should have [1,1,2,2,3,3]
        assert "1" in result and "2" in result and "3" in result


class TestMixedOperations:
    """Test + operator mixed with other operations."""

    def test_plus_with_arithmetic(self):
        """Test + mixed with other arithmetic operators"""
        program = """
        a = 10
        b = 5
        c = 2
        result = a + b * c
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should be 10 + (5 * 2) = 20
        assert result == '"Result: 20"'

    def test_plus_with_comparison(self):
        """Test + operator result used in comparison"""
        program = """
        a = 5
        b = 10
        total = a + b
        if (total == 15) {
            output = "Sum is correct"
        } else {
            output = "Sum is wrong"
        }
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Sum is correct"'

    def test_plus_in_nested_structures(self):
        """Test + operator with nested data structures"""
        program = """
        data = {"totals": [10, 20, 30]}
        extra = 5
        grand_total = data.totals[0] + data.totals[1] + data.totals[2] + extra
        output = "Grand Total: ${grand_total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Grand Total: 65"'


class TestErrorScenarios:
    """Test error handling in integration scenarios."""

    def test_type_error_in_loop(self):
        """Test type error when mixing types in loop"""
        program = """
        items = [1, "text", 3]
        total = 0
        for (item in items) {
            total = total + item
        }
        output = "Total: ${total}"
        return output
        """

        cy = Cy()
        # Should fail when trying to add int + str
        with pytest.raises(Exception):
            cy.run(program)

    def test_type_error_in_conditional(self):
        """Test type error in conditional branch"""
        program = """
        value = "text"
        if (True) {
            result = value + 123
        } else {
            result = "fallback"
        }
        output = result
        return output
        """

        cy = Cy()
        with pytest.raises(Exception):
            cy.run(program)


class TestRealWorldUseCase:
    """Test complete real-world scenarios."""

    def test_report_generation(self):
        """Test generating a formatted report with + operator"""
        program = """
        title = "Sales Report"
        date = "2024-01-15"
        sales1 = 100
        sales2 = 150
        sales3 = 200
        total = sales1 + sales2 + sales3

        report = title + "\\n"
        report = report + "Date: " + date + "\\n"
        report = report + "Total Sales: $" + "${total}"

        output = report
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Sales Report" in result
        assert "2024-01-15" in result
        assert "450" in result

    def test_data_aggregation(self):
        """Test aggregating data from multiple sources"""
        program = """
        q1_sales = [100, 150, 200]
        q2_sales = [120, 180, 210]

        all_sales = q1_sales + q2_sales

        total = 0
        for (sale in all_sales) {
            total = total + sale
        }

        output = "Total: ${total}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 100+150+200+120+180+210 = 960
        assert "Total: 960" in result

    def test_url_building(self):
        """Test building URL strings with + operator"""
        program = """
        base = "https://api.example.com"
        endpoint = "/users"
        user_id = "123"
        query = "?format=json"

        url = base + endpoint + "/" + user_id + query
        output = url
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"https://api.example.com/users/123?format=json"'

    def test_csv_generation(self):
        """Test generating CSV data with + operator"""
        program = """
        headers = ["Name", "Age", "City"]
        row1 = ["Alice", "30", "NYC"]
        row2 = ["Bob", "25", "LA"]

        csv = headers[0] + "," + headers[1] + "," + headers[2] + "\\n"
        csv = csv + row1[0] + "," + row1[1] + "," + row1[2] + "\\n"
        csv = csv + row2[0] + "," + row2[1] + "," + row2[2]

        output = csv
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Name,Age,City" in result
        assert "Alice,30,NYC" in result
        assert "Bob,25,LA" in result
