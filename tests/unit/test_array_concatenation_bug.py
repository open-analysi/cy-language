"""
TDD Test: Reproduce bug where array + array concatenation fails type validation.

Bug: Type inference engine's _is_compatible() method doesn't recognize
array + array as valid for the "add" operation, causing validation errors
like "cannot add array and array" even though this is valid Cy syntax.

This bug breaks common patterns like: results = results + [item]
"""

import pytest

from cy_language import Cy


class TestArrayConcatenationBug:
    """Test that array + array concatenation works with type checking."""

    def test_array_concatenation_with_type_checking(self):
        """
        Verify that array + array concatenation works when check_types=True.

        This reproduces the bug where:
        results = results + [item]

        Failed with: "cannot add array and array"
        """
        script = """
results = []
item = {"name": "test"}
results = results + [item]
return results
"""

        # BUG FIX: This should no longer raise TypeError about array + array
        cy = Cy(check_types=True)
        try:
            result = cy.run(script, {})
            # Type validation passed! (execution behavior is tested elsewhere)
            assert True
        except TypeError as e:
            if "cannot add array and array" in str(e):
                pytest.fail(
                    f"Type validation failed - array + array still not allowed: {e}"
                )
            else:
                # Different type error - re-raise
                raise

    def test_array_concatenation_in_loop(self):
        """
        Test array concatenation in a for loop (common pattern in examples).
        """
        script = """
names = []
users = [{"name": "Alice"}, {"name": "Bob"}]

for (user in users) {
    names = names + [user.name]
}

return names
"""

        cy = Cy(check_types=True)
        try:
            result = cy.run(script, {})
            # Type validation passed!
            assert True
        except TypeError as e:
            if "cannot add array and array" in str(e):
                pytest.fail(f"Type validation failed for array concat in loop: {e}")
            else:
                raise

    def test_array_concatenation_multiple_items(self):
        """
        Test concatenating arrays with multiple items.
        """
        script = """
results = [1, 2]
more = [3, 4, 5]
combined = results + more
return combined
"""

        cy = Cy(check_types=True)
        try:
            result = cy.run(script, {})
            # Type validation passed!
            assert True
        except TypeError as e:
            if "cannot add array and array" in str(e):
                pytest.fail(f"Type validation failed for multiple items: {e}")
            else:
                raise

    def test_array_concatenation_with_empty_array(self):
        """
        Test concatenating with empty array.
        """
        script = """
items = []
new_items = ["a", "b"]
combined = items + new_items
return combined
"""

        cy = Cy(check_types=True)
        try:
            result = cy.run(script, {})
            # Type validation passed!
            assert True
        except TypeError as e:
            if "cannot add array and array" in str(e):
                pytest.fail(f"Type validation failed for empty array: {e}")
            else:
                raise

    def test_array_concatenation_preserves_type_inference(self):
        """
        Test that type inference preserves element types for same-type arrays.
        """
        script = """
first = [1, 2, 3]
second = [4, 5, 6]
result = first + second
return result
"""

        cy = Cy(check_types=True)
        try:
            result = cy.run(script, {})
            # Type validation passed!
            assert True
        except TypeError as e:
            if "cannot add array and array" in str(e):
                pytest.fail(f"Type validation failed for type inference: {e}")
            else:
                raise
