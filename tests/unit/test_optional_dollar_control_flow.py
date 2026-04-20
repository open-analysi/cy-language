"""
Control Flow Integration Tests for Optional $ Syntax.

Tests that variables assigned with optional $ syntax work correctly
in if/while/return statements.
"""

from cy_language import Cy


class TestOptionalDollarControlFlow:
    """Test control flow integration with optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for complete testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_if_condition_with_no_dollar_variable(self):
        """Test using variables assigned without $ in if conditions."""
        program = """
age = 25
if (age >= 18) {
    status = "adult"
} else {
    status = "minor"
}
output = status
return output"""

        result = self.cy.run(program)
        assert result == '"adult"'

    def test_while_loop_with_no_dollar_variable(self):
        """Test using variables assigned without $ in while loops."""
        program = """
count = 0
total = 0
while (count < 3) {
    total = total + count
    count = count + 1
}
output = total
return output"""

        result = self.cy.run(program)
        assert result == "3"  # 0 + 1 + 2

    def test_return_statement_with_no_dollar_variable(self):
        """Test return statements with variables assigned without $."""
        program = """
result = 42
return result"""

        result = self.cy.run(program)
        assert result == "42"

    def test_mixed_dollar_and_no_dollar_in_conditions(self):
        """Test mixed $ and no-$ variables in control flow."""
        program = """
name = "Alice"
age = 25
score = 95
if (name == "Alice" and age >= 18 and score > 90) {
    status = "qualified"
} else {
    status = "not qualified"
}
output = status
return output"""

        result = self.cy.run(program)
        assert result == '"qualified"'

    def test_nested_control_flow(self):
        """Test nested if/while with mixed variable assignment forms."""
        program = """
outer_count = 0
result = 0
while (outer_count < 2) {
    inner_count = 0
    while (inner_count < 2) {
        if (outer_count == inner_count) {
            result = result + 1
        }
        inner_count = inner_count + 1
    }
    outer_count = outer_count + 1
}
output = result
return output"""

        result = self.cy.run(program)
        assert result == "2"  # When outer_count == inner_count

    def test_variable_modification_in_blocks(self):
        """Test that variables can be modified within control blocks."""
        program = """
value = 10
if (value > 5) {
    value = value * 2
    multiplier = 3
    value = value * multiplier
}
output = value
return output"""

        result = self.cy.run(program)
        assert result == "60"  # 10 * 2 * 3

    def test_control_flow_variable_scoping(self):
        """Test variable scoping in control flow (currently global scope)."""
        program = """
if (True) {
    local_var = "inside"
    local_dollar = "inside_dollar"
}
output = local_var + "_" + local_dollar
return output"""

        result = self.cy.run(program)
        assert result == '"inside_inside_dollar"'

    def test_complex_conditional_expressions(self):
        """Test complex expressions in conditional statements."""
        program = """
users = [
    {"name": "Alice", "age": 25, "active": True},
    {"name": "Bob", "age": 17, "active": False}
]
index = 0
current_user = users[index]
if (current_user["age"] >= 18 and current_user["active"]) {
    message = "Welcome " + current_user["name"]
} else {
    message = "Access denied"
}
output = message
return output"""

        result = self.cy.run(program)
        assert result == '"Welcome Alice"'

    def test_loop_with_indexed_variables(self):
        """Test loops with variables assigned without $ used in indexing."""
        program = """
items = ["apple", "banana", "cherry"]
index = 0
results = []
while (index < 3) {
    current_item = items[index]
    index = index + 1
    if (index == 3) {
        last_item = current_item
    }
}
output = last_item
return output"""

        result = self.cy.run(program)
        assert result == '"cherry"'

    def test_elif_chains_with_mixed_variables(self):
        """Test elif chains with mixed variable assignment forms."""
        program = """
score = 85
grade = ""
if (score >= 90) {
    grade = "A"
} elif (score >= 80) {
    grade = "B"
} elif (score >= 70) {
    grade = "C"
} else {
    grade = "F"
}
output = grade
return output"""

        result = self.cy.run(program)
        assert result == '"B"'

    def test_boolean_operations_mixed_variables(self):
        """Test boolean operations with mixed variable forms."""
        program = """
has_permission = True
age = 25
is_member = False
is_premium = True
if (has_permission and age >= 18 and (is_member or is_premium)) {
    access = "granted"
} else {
    access = "denied"
}
output = access
return output"""

        result = self.cy.run(program)
        assert result == '"granted"'  # has_permission=True, age>=18, is_premium=True

    def test_control_flow_with_function_calls(self):
        """Test control flow with function calls using mixed variables."""
        program = """
text_list = ["hello", "world", "test"]
total_length = 0
index = 0
while (index < 3) {
    current_text = text_list[index]
    current_length = len(current_text)
    total_length = total_length + current_length
    index = index + 1
}
output = total_length
return output"""

        result = self.cy.run(program)
        assert result == "14"  # len("hello") + len("world") + len("test") = 5+5+4
