"""
Debug test to isolate the interpolation vs main parser issue.
"""

from cy_language import Cy


class TestInterpolationDebug:
    """Test to debug interpolation parsing issues."""

    def test_simple_interpolation_works(self):
        """Test that simple interpolation works fine."""
        interpreter = Cy()
        program = """
        name = "Alice"
        output = "Hello ${name}!"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Hello Alice!"'

    def test_indexed_access_without_interpolation(self):
        """Test that indexed access works without interpolation."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        name_value = data["name"]
        output = "Done"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Done"'

    def test_single_quote_in_interpolation(self):
        """Test that single quotes work in interpolation."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        output = "Name: ${data['name']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice"'

    def test_double_quote_problem_isolated(self):
        """Test that double quotes now work in triple-quoted strings.

        Updated: fixed malformed syntax where 'return output' was on same line as string.
        """
        interpreter = Cy()
        program = '''
        data = {"name": "Alice"}
        output = """Name: ${data["name"]}"""
        return output
        '''
        result = interpreter.run(program)
        print(f"Result: {result}")  # Should work now with triple quotes
        assert result == '"Name: Alice"'

    def test_extract_to_variable_workaround(self):
        """Test the workaround of extracting to variable."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        name_value = data["name"]
        output = "Name: ${name_value}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice"'
