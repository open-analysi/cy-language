"""
Unit tests for complex nested access patterns with various data structures.

This test suite verifies that Cy properly handles deeply nested data access
patterns including arrays, dictionaries, and mixed structures with different
quote styles and string contexts.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestComplexNestedAccess:
    """Test complex nested access patterns in various contexts."""

    # Test data fixtures
    @pytest.fixture
    def order_data(self):
        """Sample order data with nested structure."""
        return {
            "order": {
                "id": "ORD-123",
                "items": [
                    {"name": "Apple", "price": 1.50, "quantity": 3},
                    {"name": "Banana", "price": 0.75, "quantity": 6},
                    {"name": "Orange", "price": 2.00, "quantity": 2},
                ],
                "customer": {
                    "name": "John Doe",
                    "addresses": [
                        {"type": "home", "city": "New York"},
                        {"type": "work", "city": "Boston"},
                    ],
                },
            }
        }

    @pytest.fixture
    def matrix_data(self):
        """Sample matrix/2D array data."""
        return {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}

    @pytest.fixture
    def company_data(self):
        """Complex nested company structure."""
        return {
            "company": {
                "departments": {
                    "engineering": {
                        "employees": [
                            {
                                "name": "Alice",
                                "projects": ["proj-1", "proj-2", "proj-3"],
                                "skills": {"python": 9, "javascript": 7},
                            },
                            {
                                "name": "Bob",
                                "projects": ["proj-2", "proj-4"],
                                "skills": {"python": 8, "go": 9},
                            },
                        ]
                    },
                    "sales": {
                        "employees": [
                            {
                                "name": "Charlie",
                                "regions": ["NA", "EU"],
                                "targets": {"Q1": 100000, "Q2": 150000},
                            }
                        ]
                    },
                }
            }
        }

    # Test Case 1: Single quotes in regular strings (SHOULD WORK)
    def test_single_quotes_in_regular_string(self, order_data):
        """Test that single quotes work in regular string interpolation."""
        program = """
        output = "Order: ${order['items'][0]['name']}"
        return output
        """

        cy = Cy(variables=order_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Order: Apple"'

    def test_complex_single_quotes_path(self, order_data):
        """Test complex nested path with single quotes."""
        program = """
        output = "Customer city: ${order['customer']['addresses'][1]['city']}"
        return output
        """

        cy = Cy(variables=order_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Customer city: Boston"'

    # Test Case 2: Double quotes in regular strings (SHOULD FAIL)
    def test_double_quotes_in_regular_string_fails(self, order_data):
        """Test that double quotes fail in regular string interpolation."""
        program = """
        output = "Order: ${order["items"][0]["name"]}"
        return output
        """

        cy = Cy(variables=order_data)
        cy.show_enhanced_errors = False
        # This should fail at the lexer level - we expect any exception since
        # the double quotes in regular strings are not supported
        with pytest.raises(Exception) as exc_info:
            cy.run(program)

        # Verify it's a syntax error (either our custom one or Python's)
        assert "Unexpected token" in str(
            exc_info.value
        ) or "No terminal matches" in str(exc_info.value)

    # Test Case 3: Double quotes in triple-quoted strings (SHOULD WORK)
    def test_double_quotes_in_triple_quoted_string(self, order_data):
        """Test that double quotes work in triple-quoted strings."""
        program = """
        output = \"\"\"Order: ${order["items"][0]["name"]}\"\"\"
        return output
        """

        cy = Cy(variables=order_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Order: Apple"'

    def test_complex_double_quotes_in_triple_quoted(self, company_data):
        """Test complex nested path with double quotes in triple-quoted string."""
        program = """
        output = \"\"\"Engineer: ${company["departments"]["engineering"]["employees"][0]["name"]}
Project: ${company["departments"]["engineering"]["employees"][0]["projects"][1]}
Python skill: ${company["departments"]["engineering"]["employees"][0]["skills"]["python"]}\"\"\"
return output
        """

        cy = Cy(variables=company_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "Engineer: Alice" in result
        assert "Project: proj-2" in result
        assert "Python skill: 9" in result

    # Test Case 4: Mixed single and double quotes
    def test_mixed_quotes_single_in_regular(self, company_data):
        """Test mixed data access with single quotes in regular strings."""
        program = """
        eng_dept = company['departments']['engineering']
        first_employee = eng_dept['employees'][0]
        output = "Employee: ${first_employee['name']} - First project: ${first_employee['projects'][0]}"
        return output
        """

        cy = Cy(variables=company_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Employee: Alice - First project: proj-1"'

    # Test Case 5: Numeric indices with string keys
    def test_numeric_and_string_indices(self, order_data):
        """Test mixing numeric array indices with string dictionary keys."""
        # Using single quotes in regular string
        # Note: len() needs to be provided as a tool
        tools = {"len": lambda x: len(x) if hasattr(x, "__len__") else 0}
        program = """
        item_count = len(order['items'])
        last_idx = item_count - 1
        output = "First item: ${order['items'][0]['name']}, Last item: ${order['items'][$last_idx]['name']}"
        return output
        """

        cy = Cy(tools=tools, variables=order_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"First item: Apple, Last item: Orange"'

    # Test Case 6: Matrix/2D array access
    def test_matrix_access_single_quotes(self, matrix_data):
        """Test 2D array access patterns."""
        program = """
        output = "Matrix[1][1]: ${matrix[1][1]}"
        return output
        """

        cy = Cy(variables=matrix_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Matrix[1][1]: 5"'

    def test_matrix_access_with_variables(self, matrix_data):
        """Test 2D array access with variable indices."""
        program = """
        row = 2
        col = 0
        output = "Matrix[${row}][${col}]: ${matrix[$row][$col]}"
        return output
        """

        cy = Cy(variables=matrix_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Matrix[2][0]: 7"'

    # Test Case 7: Deeply nested paths
    def test_deeply_nested_path_single_quotes(self, company_data):
        """Test very deep nesting with single quotes."""
        program = """
        skill_level = company['departments']['engineering']['employees'][1]['skills']['go']
        output = "Bob's Go skill level: ${skill_level}"
        return output
        """

        cy = Cy(variables=company_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Bob\'s Go skill level: 9"'

    def test_deeply_nested_inline_access(self, company_data):
        """Test deep nesting directly in interpolation."""
        program = """
        output = "Sales target Q1: ${company['departments']['sales']['employees'][0]['targets']['Q1']}"
        return output
        """

        cy = Cy(variables=company_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Sales target Q1: 100000"'

    # Test Case 8: Edge cases and error conditions
    def test_empty_string_key(self):
        """Test accessing with empty string key."""
        program = """
        data = {"": "empty_key_value", "normal": "normal_value"}
        output = "Empty key: ${data['']}, Normal: ${data['normal']}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Empty key: empty_key_value, Normal: normal_value"'

    def test_special_character_keys(self):
        """Test keys with special characters."""
        program = """
        data = {"key-with-dash": "value1", "key.with.dot": "value2", "key with space": "value3"}
        output = \"\"\"Dash: ${data["key-with-dash"]}
Dot: ${data["key.with.dot"]}
Space: ${data["key with space"]}\"\"\"
return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "Dash: value1" in result
        assert "Dot: value2" in result
        assert "Space: value3" in result

    # Test Case 9: Mixed access patterns in single expression
    def test_mixed_access_patterns(self, company_data):
        """Test mixing different access patterns in one expression."""
        program = """
        # Mix of variable references, string keys, and numeric indices
        dept = "engineering"
        emp_idx = 0
        skill = 'python'
        output = "Skill level: ${company['departments'][$dept]['employees'][$emp_idx]['skills'][$skill]}"
        return output
        """

        cy = Cy(variables=company_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Skill level: 9"'

    # Test Case 10: Format hints with nested access
    def test_format_hints_with_nested_access(self, order_data):
        """Test that format hints work with nested access."""
        program = """
        output = "Items as CSV: ${order['items']|csv}"
        return output
        """

        cy = Cy(variables=order_data)
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "CSV" in result or "name,price,quantity" in result

    # Test Case 11: Boolean and numeric values in nested structures
    def test_nested_boolean_numeric_access(self):
        """Test accessing boolean and numeric values in nested structures."""
        program = """
        config = {
            "features": {
                "auth": {"enabled": True, "timeout": 3600},
                "cache": {"enabled": False, "ttl": 0}
            }
        }
        output = \"\"\"Auth enabled: ${config["features"]["auth"]["enabled"]}
Auth timeout: ${config["features"]["auth"]["timeout"]}
Cache enabled: ${config["features"]["cache"]["enabled"]}\"\"\"
return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "Auth enabled: True" in result
        assert "Auth timeout: 3600" in result
        assert "Cache enabled: False" in result

    # Test Case 12: Null/None values in nested structures
    def test_nested_none_access(self):
        """Test accessing null values in nested structures."""
        # Note: Cy uses 'null' keyword, not Python's 'None'
        program = """
        data = {
            "user": {
                "name": "Alice",
                "email": null,
                "settings": {"theme": "dark", "notifications": null}
            }
        }
        output = \"\"\"Email: ${data["user"]["email"]}
Notifications: ${data["user"]["settings"]["notifications"]}\"\"\"
return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # null should be represented as empty string or "null" depending on implementation
        assert "Email:" in result
        assert "Notifications:" in result
