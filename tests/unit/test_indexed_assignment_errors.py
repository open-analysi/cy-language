"""
Test error handling for indexed assignment functionality.
"""

import pytest

from cy_language import Cy
from cy_language.errors import InterpolationError


class TestIndexedAssignmentErrors:
    """Test error conditions for indexed assignment."""

    def test_list_index_out_of_bounds_assignment(self):
        """Test list index out of bounds assignment should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        arr[5] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(InterpolationError, match="Index out of range"):
            interpreter.run(program)

    def test_assign_to_invalid_index_type(self):
        """Test assignment with invalid index type should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        key = "invalid"
        arr[key] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(InterpolationError, match="List index must be an integer"):
            interpreter.run(program)

    def test_assign_to_non_indexable_type(self):
        """Test assignment to non-indexable type should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        number = 42
        number[0] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(
            InterpolationError, match="Cannot assign to index of type int"
        ):
            interpreter.run(program)

    def test_assign_to_string_should_fail(self):
        """Test that assigning to string indices should fail (strings are immutable)."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        text = "hello"
        text[0] = "H"
        output = "Done"
        return output
        """
        with pytest.raises(
            InterpolationError, match="Cannot assign to index of immutable type str"
        ):
            interpreter.run(program)
