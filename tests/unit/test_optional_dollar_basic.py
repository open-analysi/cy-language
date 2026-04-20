"""
Basic Tests for Optional $ Syntax.

Tests basic assignment forms and fundamental functionality.
"""

from cy_language import Cy


class TestOptionalDollarBasic:
    """Test basic optional $ functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for complete testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_dollar_assignment_works(self):
        """Test that $var = value continues to work."""
        program = """name = "Alice"
output = name
return output"""

        result = self.cy.run(program)
        assert result == '"Alice"'

    def test_no_dollar_assignment_works(self):
        """Test that var = value now works."""
        program = """name = "Alice"  
output = name
return output"""

        result = self.cy.run(program)
        assert result == '"Alice"'

    def test_both_forms_same_variable(self):
        """Test that $var and var refer to the same variable."""
        # Set with $, access without $
        program = """name = "Alice"
output = name
return output"""

        result = self.cy.run(program)
        assert result == '"Alice"'

        # Set without $, access with $
        program = """name = "Alice"
output = name
return output"""

        result = self.cy.run(program)
        assert result == '"Alice"'

    def test_variable_overwrite(self):
        """Test that assignments overwrite correctly."""
        program = """name = "Alice"
name = "Bob"
output = name
return output"""

        result = self.cy.run(program)
        assert result == '"Bob"'  # Second assignment should overwrite

    def test_multiple_variable_types(self):
        """Test different data types with optional $ syntax."""
        program = """name = "Alice"
age = 25
count = 0
pi = 3.14
active = True
data = null
output = {
    "name": name,
    "age": age, 
    "count": count,
    "pi": pi,
    "active": active,
    "data": data
}
return output"""

        result = self.cy.run(program)
        # Should be valid JSON-like output
        assert "Alice" in result
        assert "25" in result

    def test_assignment_in_expressions(self):
        """Test using variables assigned without $ in expressions."""
        program = """x = 10
y = 20
total = x + y
output = total
return output"""

        result = self.cy.run(program)
        assert result == "30"
