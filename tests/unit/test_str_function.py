"""Tests for the str() native function."""

import json

from cy_language import Cy


class TestStrFunction:
    """Test the str() native function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Import native functions to register them
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_str_with_number(self):
        """Test str() function with numbers."""
        program = """number = 42
result = str(number)
output = result
return output
"""
        result = self.cy.run(program)
        assert result == '"42"'

    def test_str_with_float(self):
        """Test str() function with float."""
        program = """number = 3.14
result = str(number)
output = result
return output
"""
        result = self.cy.run(program)
        assert result == '"3.14"'

    def test_str_with_boolean(self):
        """Test str() function with boolean values."""
        program = """val1 = True
val2 = False
result1 = str(val1)
result2 = str(val2)
output = {
    "true": result1,
    "false": result2
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        assert result_dict["true"] == "True"
        assert result_dict["false"] == "False"

    def test_str_with_list(self):
        """Test str() function with list."""
        program = """data = [1, 2, 3]
result = str(data)
output = result
return output
"""
        result = self.cy.run(program)
        assert "[1, 2, 3]" in result or '"[1, 2, 3]"' in result

    def test_str_with_dict(self):
        """Test str() function with dictionary."""
        program = """data = {"name": "Alice", "age": 30}
result = str(data)
output = result
return output
"""
        result = self.cy.run(program)
        # Dictionary string representation should contain the keys
        assert "name" in result
        assert "Alice" in result
        assert "age" in result

    def test_str_with_none(self):
        """Test str() function with None/null."""
        program = """val = null
result = str(val)
output = result
return output
"""
        result = self.cy.run(program)
        assert result == '"None"'

    def test_str_with_string(self):
        """Test str() function with string (should return as-is)."""
        program = """text = "hello"
result = str(text)
output = result
return output
"""
        result = self.cy.run(program)
        assert result == '"hello"'

    def test_str_in_concatenation(self):
        """Test str() function in string building without interpolation."""
        program = """number = 42
str_num = str(number)
output = "The answer is " + str_num
return output
"""
        result = self.cy.run(program)
        assert result == '"The answer is 42"'

    def test_str_with_arithmetic_result(self):
        """Test str() function with arithmetic operations."""
        program = """a = 10
b = 20
total = a + b
result = str(total)
output = "Result: " + result
return output
"""
        result = self.cy.run(program)
        assert result == '"Result: 30"'

    def test_str_multiple_conversions(self):
        """Test multiple str() conversions in same program."""
        program = """number = 42
pi = 3.14
active = True

str1 = str(number)
str2 = str(pi)
str3 = str(active)

output = str1 + ", " + str2 + ", " + str3
return output
"""
        result = self.cy.run(program)
        assert result == '"42, 3.14, True"'

    def test_str_in_list(self):
        """Test str() function results in a list."""
        program = """nums = [1, 2, 3]
strings = [str(nums[0]), str(nums[1]), str(nums[2])]
output = {
    "strings": strings,
    "count": len(strings)
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        assert result_dict["strings"] == ["1", "2", "3"]
        assert result_dict["count"] == 3

    def test_str_nested_data(self):
        """Test str() with nested data structures."""
        program = """user = {
    "name": "Bob",
    "scores": [85, 92, 78]
}
result = str(user)
output = result
return output
"""
        result = self.cy.run(program)
        # Should contain the structure
        assert "name" in result
        assert "Bob" in result
        assert "scores" in result

    def test_str_vs_interpolation(self):
        """Test difference between str() and string interpolation."""
        program = """number = 42
data = [1, 2, 3]

# Using str() - no interpolation
str1 = str(number)
str2 = str(data)

# Using interpolation
interp1 = "Value: ${number}"
interp2 = "Data: ${data}"

output = {
    "str_num": str1,
    "str_data": str2,
    "interp_num": interp1,
    "interp_data": interp2
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)

        # str() returns plain string representation
        assert result_dict["str_num"] == "42"
        assert "[1, 2, 3]" in result_dict["str_data"]

        # Interpolation includes context
        assert "Value: 42" in result_dict["interp_num"]
        assert "Data:" in result_dict["interp_data"]

    def test_str_function_registered(self):
        """Test that str function is properly registered under its namespaced name."""
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        tools_info = default_registry.get_tool_descriptions()
        # str() is now registered as "type::str" (flat "str" removed to avoid
        # duplicate short-name entries in the resolver).
        str_tool = next(
            (tool for tool in tools_info if tool["name"] == "type::str"), None
        )

        assert str_tool is not None, "str() function should be registered as type::str"
        assert "convert" in str_tool["description"].lower()
        assert "string" in str_tool["description"].lower()
