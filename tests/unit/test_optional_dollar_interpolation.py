"""
Tests for String Interpolation Compatibility with Optional $ Syntax.

Tests that string interpolation works correctly regardless of how variables
were assigned (with or without $ prefix).
"""

import json

import pytest

from cy_language import Cy


class TestOptionalDollarInterpolation:
    """Test string interpolation compatibility with optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for complete testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_interpolation_after_dollar_assignment(self):
        """Test interpolation after var = value assignment."""
        # Test with ${name} syntax
        program = """name = "Alice"
output = "Hello ${name}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice!"'

        # Test with $name reference in interpolation ($ prefix in interpolation context)
        program = """name = "Alice"
output = "Hello ${$name}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice!"'

    def test_interpolation_after_no_dollar_assignment(self):
        """Test interpolation after var = value assignment."""
        # Test with ${name} syntax
        program = """name = "Alice"
output = "Hello ${name}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice!"'

        # Test with ${$name} syntax
        program = """name = "Alice"
output = "Hello ${$name}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice!"'

    def test_mixed_assignment_interpolation(self):
        """Test interpolation with variables."""
        program = """name = "Alice"
age = 25
output = "Hello ${name}, age ${age}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice, age 25!"'

        # Test with $var reference in interpolation
        program = """name = "Alice"
age = 25
output = "Hello ${$name}, age ${age}!"
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Alice, age 25!"'

    def test_triple_quoted_string_interpolation(self):
        """Test interpolation in triple-quoted strings."""
        program = '''name = "Alice"
age = 25
output = """
Name: ${name}
Age: ${age}
Status: Active
"""
return output'''

        result = self.cy.run(program)
        expected = '"\\nName: Alice\\nAge: 25\\nStatus: Active\\n"'
        assert result == expected

    def test_indexed_variable_interpolation(self):
        """Test interpolation with indexed variables."""
        # Test with dictionary access
        program = """scores = {}
scores["alice"] = 95
output = "Score: ${scores['alice']}"
return output"""

        result = self.cy.run(program)
        assert result == '"Score: 95"'

        # Test mixed forms
        program = """data = {}
player = "alice"
data[player] = 95
# Extract complex expression to variable (as per TUTORIAL.md)
score = data[player]
output = "Player ${player} scored ${score}"
return output"""

        result = self.cy.run(program)
        assert result == '"Player alice scored 95"'

    def test_complex_interpolation_expressions(self):
        """Test complex expressions within interpolation."""
        program = """users = [
    {"name": "Alice", "score": 95},
    {"name": "Bob", "score": 87}
]
index = 0
# Extract complex expressions to variables first (as per TUTORIAL.md)
top_user = users[index]
top_name = top_user["name"]
top_score = top_user["score"]
output = "Top player: ${top_name} with ${top_score} points"
return output"""

        result = self.cy.run(program)
        assert result == '"Top player: Alice with 95 points"'

    def test_interpolation_with_function_calls(self):
        """Test interpolation with function calls."""
        program = """text = "hello world"
items = [1, 2, 3, 4, 5]
# Extract function calls to variables first (as per TUTORIAL.md)
text_len = len(text)
items_len = len(items)
output = "Text length: ${text_len}, List length: ${items_len}"
return output"""

        result = self.cy.run(program)
        assert result == '"Text length: 11, List length: 5"'

    def test_nested_interpolation_structures(self):
        """Test interpolation with deeply nested data structures."""
        program = """config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "admin"
        }
    }
}
output = "DB: ${config['database']['credentials']['username']}@${config['database']['host']}:${config['database']['port']}"
return output"""

        result = self.cy.run(program)
        assert result == '"DB: admin@localhost:5432"'

    def test_interpolation_error_handling(self):
        """Test interpolation with undefined variables."""
        # This should raise an error during execution
        program = """output = "Hello ${undefined_var}!"
return output"""

        with pytest.raises(Exception):  # Should raise variable not found error
            self.cy.run(program)

    def test_multiple_interpolations_same_string(self):
        """Test multiple interpolations in the same string."""
        program = """first = "Alice"
last = "Smith"
age = 25
title = "Dr."
output = "${title} ${first} ${last} is ${age} years old"
return output"""

        result = self.cy.run(program)
        assert result == '"Dr. Alice Smith is 25 years old"'

    def test_interpolation_with_special_characters(self):
        """Test interpolation with special characters in values."""
        program = """message = 'Hello, "World"!'
symbol = "@#$%"
output = "Message: ${message}, Symbol: ${symbol}"
return output"""

        result = self.cy.run(program)
        assert result == '"Message: Hello, \\"World\\"!, Symbol: @#$%"'

    def test_interpolation_backward_compatibility(self):
        """Test that existing interpolation patterns still work."""
        # Test syntax (no $ prefix on assignments)
        program = """name = "Alice"
age = 25
job = "Engineer"
output = "${name} is a ${age}-year-old ${job}"
return output"""

        result = self.cy.run(program)
        assert result == '"Alice is a 25-year-old Engineer"'

    def test_empty_and_null_interpolation(self):
        """Test interpolation with empty and null values."""
        program = """empty_string = ""
null_value = null
number = 0
output = "Empty: '${empty_string}', Null: '${null_value}', Zero: '${number}'"
return output"""

        result = self.cy.run(program)
        # null should be converted to string representation
        assert "Empty: ''" in result
        assert "Zero: '0'" in result

    def test_interpolation_with_json_output(self):
        """Test interpolation in JSON output context."""
        program = """name = "Alice"
age = 25
data = {
    "user": "${name}",
    "years": age,
    "status": "active"
}
output = data
return output"""

        result = self.cy.run(program)
        # Parse as JSON to verify structure (run() now returns JSON directly)
        data = json.loads(result)

        assert data["user"] == "Alice"
        assert data["years"] == 25
        assert data["status"] == "active"

    def test_conditional_interpolation(self):
        """Test interpolation within conditional statements."""
        program = """name = "Alice"
age = 25
if (age >= 18) {
    status = "adult"
} else {
    status = "minor"
}
output = "${name} is an ${status}"
return output"""

        result = self.cy.run(program)
        assert result == '"Alice is an adult"'

    def test_loop_interpolation(self):
        """Test interpolation within loop constructs."""
        program = """names = ["Alice", "Bob", "Charlie"]
messages = []
count = 0
while (count < 3) {
    current_name = names[count]
    message = "Hello ${current_name}!"
    # Note: This test assumes list append functionality
    # For now, just test the interpolation works
    current_message = message
    count = count + 1
}
output = current_message
return output"""

        result = self.cy.run(program)
        assert result == '"Hello Charlie!"'  # Last iteration
