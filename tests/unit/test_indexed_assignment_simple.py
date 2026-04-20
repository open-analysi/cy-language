"""
Simple test to isolate indexed assignment parsing from interpolation issues.
"""

from cy_language import Cy


class TestSimpleIndexedAssignment:
    """Test basic indexed assignment without complex interpolation."""

    def test_simple_dict_assignment(self):
        """Test simple dictionary assignment without interpolation."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        data["age"] = 30
        output = "Done"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Done"'

    def test_simple_list_assignment(self):
        """Test simple list assignment without interpolation."""
        interpreter = Cy()
        program = """
        arr = ["a", "b", "c"]
        arr[1] = "x"
        output = "Done"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Done"'
