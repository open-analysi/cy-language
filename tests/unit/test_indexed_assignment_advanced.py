"""
Test advanced indexed assignment functionality like nested assignments.
"""

from cy_language import Cy


class TestAdvancedIndexedAssignment:
    """Test advanced indexed assignment patterns."""

    def test_nested_dict_assignment(self):
        """Test assignment to nested dictionary structure."""
        interpreter = Cy()
        program = """
        user = {"profile": {"settings": {"theme": "light"}}}
        user["profile"]["settings"]["theme"] = "dark"
        user["profile"]["settings"]["language"] = "en"
        output = "Theme: ${user['profile']['settings']['theme']}, Lang: ${user['profile']['settings']['language']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Theme: dark, Lang: en"'

    def test_multidimensional_array_assignment(self):
        """Test assignment to multi-dimensional arrays."""
        interpreter = Cy()
        program = """
        matrix = [["a", "b"], ["c", "d"]]
        matrix[0][1] = "X"
        matrix[1][0] = "Y"
        output = "Matrix: [${matrix[0][0]}, ${matrix[0][1]}], [${matrix[1][0]}, ${matrix[1][1]}]"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Matrix: [a, X], [Y, d]"'

    def test_inventory_update_pattern(self):
        """Test inventory update pattern."""
        interpreter = Cy()
        program = """
        inventory = {"apples": 50, "bananas": 30}
        item = "apples"
        sold = 5
        inventory[item] = inventory[item] - sold
        inventory["oranges"] = 25
        
        output = "Apples: ${inventory['apples']}, Bananas: ${inventory['bananas']}, Oranges: ${inventory['oranges']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Apples: 45, Bananas: 30, Oranges: 25"'
