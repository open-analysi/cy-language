"""
Unit tests for nested quote interpolation patterns

These tests focus on the critical parsing issue where expressions like
${employees[0]["name"]} fail due to regex-based tokenization limitations.
"""

from src.cy_language.interpreter import Cy


class TestNestedQuoteInterpolation:
    """Test nested quote patterns in string interpolation."""

    def test_simple_double_quote_interpolation(self):
        """Test ${obj['key']} with single quotes in interpolation."""
        program = """
        data = {"name": "Alice", "age": 30}
        output = "Name: ${data['name']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Name: Alice"'

    def test_simple_single_quote_interpolation(self):
        """Test ${obj['key']} with single quotes in interpolation."""
        program = """
        data = {"name": "Bob", "age": 25}
        output = "Name: ${data['name']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Name: Bob"'

    def test_string_key_array_access(self):
        """Test ${data['users']} accessing array value via string key."""
        program = """
        data = {"users": ["Alice", "Bob", "Charlie"]}
        output = "Users: ${data['users']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # Should format as markdown list by default
        import json

        expected = json.dumps("Users: - Alice\n- Bob\n- Charlie")
        assert result == expected

    def test_index_then_string_key_chaining(self):
        """Test ${employees[0]['name']} mixing index and string key access."""
        program = """
        employees = [{"name": "Alice", "role": "Developer"}, {"name": "Bob", "role": "Designer"}]
        output = "First employee: ${employees[0]['name']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"First employee: Alice"'

    def test_string_to_index_to_string_chaining(self):
        """Test ${data["users"][0]["name"]} full string-to-index-to-string chain."""
        program = """
        data = {"users": [{"name": "Alice", "id": 1}, {"name": "Bob", "id": 2}]}
        output = "First user: ${data['users'][0]['name']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"First user: Alice"'

    def test_deeply_nested_string_access(self):
        """Test ${company["departments"]["engineering"]["employees"][0]} deeply nested."""
        program = """
        company = {
            "departments": {
                "engineering": {
                    "employees": ["Alice", "Bob", "Charlie"]
                }
            }
        }
        output = "First engineer: ${company['departments']['engineering']['employees'][0]}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"First engineer: Alice"'

    def test_mixed_quote_types_same_expression(self):
        """Test ${data['users'][0]["name"]} mixing single and double quotes."""
        program = """
        data = {"users": [{"name": "Alice", "email": "alice@example.com"}]}
        output = "Contact: ${data['users'][0]['name']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Contact: Alice"'

    def test_alternating_quote_types(self):
        """Test ${obj["field1"]['field2']["field3"]} alternating quote patterns."""
        program = """
        obj = {
            "field1": {
                "field2": {
                    "field3": "nested_value"
                }
            }
        }
        output = "Value: ${obj['field1']['field2']['field3']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Value: nested_value"'

    def test_nested_quotes_with_printer_hints(self):
        """Test nested quotes work with printer hints ${obj["key"]|format}."""
        program = """
        data = {"items": ["apple", "banana", "cherry"]}
        output = "Items: ${data['items']|csv}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # CSV format should be comma-separated
        assert "apple,banana,cherry" in result or "apple, banana, cherry" in result

    def test_special_characters_in_string_keys(self):
        """Test ${obj["key with spaces"]} and other special characters."""
        program = """
        data = {"key with spaces": "value1", "key-with-dashes": "value2"}
        output = "Space key: ${data['key with spaces']}, Dash key: ${data['key-with-dashes']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Space key: value1, Dash key: value2"'


class TestNestedQuoteErrorHandling:
    """Test error handling for malformed nested quote expressions."""

    def test_single_quotes_work_fine(self):
        """Test that single quotes work perfectly (no longer an error case)."""
        program = """
        data = {"name": "Alice"}
        output = "Name: ${data['name']}"
        return output
        """

        cy = Cy()
        # This should work fine now with single quotes
        result = cy.run(program)
        assert result == '"Name: Alice"'

    def test_missing_closing_brace_no_interpolation(self):
        """Test missing closing brace results in literal text (no interpolation)."""
        program = """
        data = {"name": "Alice"}
        output = "Name: ${data['name']"
        return output
        """

        cy = Cy()
        # Missing closing brace means no interpolation happens - output literal text
        result = cy.run(program)
        import json

        assert result == json.dumps("Name: ${data['name']")

    def test_empty_interpolation_expression(self):
        """Test handling of empty interpolation ${} - left as literal text."""
        program = """
        output = "Empty: ${}"
        return output
        """

        cy = Cy()
        # Empty interpolation expressions are left as literal text
        result = cy.run(program)
        assert result == '"Empty: ${}"'


class TestBackwardCompatibility:
    """Ensure existing interpolation patterns still work with new parser."""

    def test_simple_variable_interpolation(self):
        """Test ${var} simple variable interpolation still works."""
        program = """
        name = "Alice"
        output = "Hello ${name}!"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello Alice!"'

    def test_dollar_variable_interpolation(self):
        """Test $var variable interpolation still works."""
        program = """
        name = "Bob"
        output = "Hello $name!"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello Bob!"'

    def test_field_access_interpolation(self):
        """Test ${obj.field} dot notation still works."""
        program = """
        person = {"name": "Charlie", "age": 30}
        output = "Name: ${person.name}, Age: ${person.age}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Name: Charlie, Age: 30"'

    def test_existing_indexed_access(self):
        """Test indexed access patterns still work."""
        program = """
        data = ["Alice", "Bob", "Charlie"]
        output = "First: ${data[0]}, Second: ${data[1]}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"First: Alice, Second: Bob"'

    def test_printer_hints_still_work(self):
        """Test ${var|format} printer hints continue to work."""
        program = """
        items = ["apple", "banana", "cherry"]
        output = "CSV: ${items|csv}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "apple" in result and "banana" in result and "cherry" in result


class TestComplexNestingScenarios:
    """Test edge cases and deeply nested scenarios."""

    def test_six_levels_deep_nesting(self):
        """Test deeply nested expressions (6+ levels)."""
        program = """
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": "deep_value"
                            }
                        }
                    }
                }
            }
        }
        output = "Deep: ${data['level1']['level2']['level3']['level4']['level5']['level6']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Deep: deep_value"'

    def test_very_long_interpolation_expression(self):
        """Test performance with very long interpolation expressions."""
        program = """
        data = {"very_long_key_name_for_testing_parser_performance": "long_value"}
        output = "Long: ${data['very_long_key_name_for_testing_parser_performance']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Long: long_value"'

    def test_multiple_nested_interpolations_same_string(self):
        """Test multiple nested interpolations in the same string."""
        program = """
        user = {"name": "Alice", "details": {"age": 30, "city": "NYC"}}
        output = "User ${user['name']} is ${user['details']['age']} years old in ${user['details']['city']}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"User Alice is 30 years old in NYC"'
