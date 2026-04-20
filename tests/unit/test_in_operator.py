"""
Tests for the 'in' membership operator.

Tests that 'in' works as a comparison operator for checking membership
in lists, dictionaries (key lookup), and strings (substring check).
Also verifies that for-in loops and list comprehensions are unaffected.
"""

import pytest

from cy_language import Cy, analyze_types


class TestInOperatorLists:
    """Test 'in' operator with lists."""

    def setup_method(self):
        self.interpreter = Cy()

    def test_value_in_list(self):
        result = self.interpreter.run("""
        x = 2 in [1, 2, 3]
        return x
        """)
        assert result == "true"

    def test_value_not_in_list(self):
        result = self.interpreter.run("""
        x = 5 in [1, 2, 3]
        return x
        """)
        assert result == "false"

    def test_string_in_list(self):
        result = self.interpreter.run("""
        x = "b" in ["a", "b", "c"]
        return x
        """)
        assert result == "true"

    def test_string_not_in_list(self):
        result = self.interpreter.run("""
        x = "z" in ["a", "b", "c"]
        return x
        """)
        assert result == "false"

    def test_in_empty_list(self):
        result = self.interpreter.run("""
        x = 1 in []
        return x
        """)
        assert result == "false"

    def test_in_with_variable_list(self):
        result = self.interpreter.run("""
        items = [10, 20, 30]
        x = 20 in items
        return x
        """)
        assert result == "true"

    def test_in_with_variable_value(self):
        result = self.interpreter.run("""
        needle = 2
        x = needle in [1, 2, 3]
        return x
        """)
        assert result == "true"


class TestInOperatorDicts:
    """Test 'in' operator with dictionaries (key lookup)."""

    def setup_method(self):
        self.interpreter = Cy()

    def test_key_in_dict(self):
        result = self.interpreter.run("""
        x = "a" in {"a": 1, "b": 2}
        return x
        """)
        assert result == "true"

    def test_key_not_in_dict(self):
        result = self.interpreter.run("""
        x = "z" in {"a": 1, "b": 2}
        return x
        """)
        assert result == "false"

    def test_in_empty_dict(self):
        result = self.interpreter.run("""
        x = "a" in {}
        return x
        """)
        assert result == "false"


class TestInOperatorStrings:
    """Test 'in' operator with strings (substring check)."""

    def setup_method(self):
        self.interpreter = Cy()

    def test_substring_in_string(self):
        result = self.interpreter.run("""
        x = "ab" in "abc"
        return x
        """)
        assert result == "true"

    def test_char_in_string(self):
        result = self.interpreter.run("""
        x = "a" in "hello a world"
        return x
        """)
        assert result == "true"

    def test_substring_not_in_string(self):
        result = self.interpreter.run("""
        x = "xyz" in "abc"
        return x
        """)
        assert result == "false"


class TestInOperatorControlFlow:
    """Test 'in' operator used in if conditions and combined with boolean ops."""

    def setup_method(self):
        self.interpreter = Cy()

    def test_if_in_condition(self):
        result = self.interpreter.run("""
        status = "not found"
        if(2 in [1, 2, 3]) {
            status = "found"
        }
        return status
        """)
        assert result == '"found"'

    def test_if_not_in_condition(self):
        result = self.interpreter.run("""
        status = "not found"
        if(not 5 in [1, 2, 3]) {
            status = "absent"
        }
        return status
        """)
        assert result == '"absent"'

    def test_in_with_and(self):
        result = self.interpreter.run("""
        x = 2 in [1, 2, 3] and 5 in [4, 5, 6]
        return x
        """)
        assert result == "true"

    def test_in_with_or(self):
        result = self.interpreter.run("""
        x = 99 in [1, 2, 3] or 5 in [4, 5, 6]
        return x
        """)
        assert result == "true"

    def test_in_with_elif(self):
        result = self.interpreter.run("""
        val = 5
        result = "none"
        if(val in [1, 2, 3]) {
            result = "low"
        } elif(val in [4, 5, 6]) {
            result = "mid"
        } else {
            result = "high"
        }
        return result
        """)
        assert result == '"mid"'


class TestForInStillWorks:
    """Verify that for-in loops and list comprehensions are unaffected."""

    def setup_method(self):
        self.interpreter = Cy()

    def test_for_in_loop(self):
        result = self.interpreter.run("""
        total = 0
        for(i in [1, 2, 3]) {
            total += i
        }
        return total
        """)
        assert result == "6"

    def test_list_comprehension(self):
        result = self.interpreter.run("""
        items = [1, 2, 3]
        doubled = [i for(i in items)]
        return doubled
        """)
        assert result == "[1, 2, 3]"

    def test_list_comprehension_with_filter(self):
        result = self.interpreter.run("""
        items = [1, 2, 3, 4, 5]
        evens = [i for(i in items) if(i % 2 == 0)]
        return evens
        """)
        assert result == "[2, 4]"

    def test_in_operator_inside_for_loop(self):
        """Test using 'in' as membership check inside a for-in loop body."""
        result = self.interpreter.run("""
        allowed = [2, 4, 6]
        matches = []
        for(i in [1, 2, 3, 4, 5]) {
            if(i in allowed) {
                matches = matches + [i]
            }
        }
        return matches
        """)
        assert result == "[2, 4]"


class TestInOperatorTypeChecking:
    """Test 'in' operator type checking with nullable containers."""

    def test_in_with_nullable_array_no_type_error(self):
        """'in' should accept nullable array (array | null) without type error."""
        registry = {
            "app::test::get_items": {
                "parameters": {},
                "return_type": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "number"}},
                        {"type": "null"},
                    ]
                },
            }
        }
        analyze_types(
            "items = app::test::get_items()\nresult = 1 in items\nreturn result",
            tool_registry=registry,
        )

    def test_in_with_nullable_dict_no_type_error(self):
        """'in' should accept nullable dict (object | null) without type error."""
        registry = {
            "app::test::get_map": {
                "parameters": {},
                "return_type": {
                    "oneOf": [
                        {"type": "object", "properties": {"a": {"type": "number"}}},
                        {"type": "null"},
                    ]
                },
            }
        }
        analyze_types(
            'data = app::test::get_map()\nresult = "a" in data\nreturn result',
            tool_registry=registry,
        )

    def test_in_with_non_container_type_raises(self):
        """'in' should reject a non-container type (e.g., number) with type error."""
        registry = {
            "app::test::get_count": {
                "parameters": {},
                "return_type": {"type": "number"},
            }
        }
        with pytest.raises(TypeError, match="'in' requires"):
            analyze_types(
                "count = app::test::get_count()\nresult = 1 in count\nreturn result",
                tool_registry=registry,
            )
