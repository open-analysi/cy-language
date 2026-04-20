"""
Test that for-in loops properly reject non-iterable types.

for-in loops should only work with:
- Lists (iterate over elements)
- Dicts (iterate over keys)
- Strings (iterate over characters)

And should raise clear errors for:
- Numbers
- Booleans
- Null
- Other non-iterable types
"""

import pytest

from cy_language import Cy
from cy_language.errors import ToolInvocationError


class TestForInNonIterableErrors:
    """Test error handling for non-iterable types in for-in loops."""

    def test_iterate_over_number_raises_error(self):
        """Verify that iterating over a number raises a clear error."""
        script = """
x = 42
for (item in x) {
    log(item)
}
return "done"
"""

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run(script)

        assert "Cannot iterate over int" in str(exc_info.value)
        assert "for-in loops support lists, dicts, and strings only" in str(
            exc_info.value
        )

    def test_iterate_over_boolean_raises_error(self):
        """Verify that iterating over a boolean raises a clear error."""
        script = """
flag = True
for (item in flag) {
    log(item)
}
return "done"
"""

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run(script)

        assert "Cannot iterate over bool" in str(exc_info.value)

    def test_iterate_over_null_raises_error(self):
        """Verify that iterating over null raises a clear error."""
        script = """
x = null
for (item in x) {
    log(item)
}
return "done"
"""

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run(script)

        assert "Cannot iterate over NoneType" in str(exc_info.value)

    def test_valid_iterables_work(self):
        """Verify that lists, dicts, and strings all work."""
        # List iteration
        script_list = """
items = [1, 2, 3]
count = 0
for (item in items) {
    count = count + 1
}
return count
"""
        cy = Cy()
        cy.show_enhanced_errors = False
        assert cy.run(script_list) == "3"

        # Dict iteration (over keys)
        script_dict = """
data = {"a": 1, "b": 2}
key_list = []
for (key in data) {
    key_list = key_list + [key]
}
return join(key_list, ",")
"""
        assert "a" in cy.run(script_dict)
        assert "b" in cy.run(script_dict)

        # String iteration (over characters)
        script_string = """
text = "hi"
count = 0
for (char in text) {
    count = count + 1
}
return count
"""
        assert cy.run(script_string) == "2"
