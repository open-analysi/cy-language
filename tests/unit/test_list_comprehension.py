"""
Tests for list comprehension syntax.

Syntax: [expr for(x in iterable)]
        [expr for(x in iterable) if(condition)]
"""

import json

from lark import Lark

from src.cy_language.grammar import get_grammar
from src.cy_language.interpreter import Cy


def parse_result(result: str):
    """Parse interpreter string result back to Python object."""
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        # For Python-repr style strings (single quotes), use eval
        import ast

        return ast.literal_eval(result)


class TestListComprehensionParsing:
    """Test that list comprehension syntax parses correctly."""

    def setup_method(self):
        grammar_text = get_grammar()
        self.parser = Lark(grammar_text, parser="lalr")

    def test_basic_comprehension_parses(self):
        """Simple [x for(x in items)] should parse."""
        tree = self.parser.parse("ids = [x for(x in items)]")
        assert tree is not None

    def test_comprehension_with_field_access_parses(self):
        """[u.id for(u in users)] should parse."""
        tree = self.parser.parse("ids = [u.id for(u in users)]")
        assert tree is not None

    def test_comprehension_with_filter_parses(self):
        """[x for(x in items) if(x > 0)] should parse."""
        tree = self.parser.parse("result = [x for(x in items) if(x > 0)]")
        assert tree is not None

    def test_comprehension_with_filter_and_field_access_parses(self):
        """[u.name for(u in users) if(u.active == true)] should parse."""
        tree = self.parser.parse(
            "names = [u.name for(u in users) if(u.active == true)]"
        )
        assert tree is not None

    def test_regular_list_still_parses(self):
        """Regular list literals should not be affected."""
        tree = self.parser.parse("a = [1, 2, 3]")
        assert tree is not None

    def test_empty_list_still_parses(self):
        """Empty list literal should not be affected."""
        tree = self.parser.parse("a = []")
        assert tree is not None

    def test_single_element_list_still_parses(self):
        """Single element list [x] should still parse as a list."""
        tree = self.parser.parse("a = [1]")
        assert tree is not None

    def test_comprehension_in_return_parses(self):
        """List comprehension in a return statement should parse."""
        tree = self.parser.parse("return [x for(x in items)]")
        assert tree is not None

    def test_comprehension_as_function_arg_parses(self):
        """List comprehension as a function argument should parse."""
        tree = self.parser.parse("result = len([x for(x in items)])")
        assert tree is not None


class TestListComprehensionExecution:
    """Test list comprehension execution."""

    def setup_method(self):
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.interpreter = Cy(tools=default_registry.get_tools_dict())

    def test_identity_comprehension(self):
        """[x for(x in items)] returns the same elements."""
        result = self.interpreter.run("return [x for(x in [1, 2, 3])]")
        assert parse_result(result) == [1, 2, 3]

    def test_field_access_comprehension(self):
        """[u.id for(u in users)] extracts field from each element."""
        program = """
users = [{"id": "A", "name": "Alice"}, {"id": "B", "name": "Bob"}]
return [u.id for(u in users)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["A", "B"]

    def test_multiple_field_comprehension(self):
        """[u.name for(u in users)] works for any field."""
        program = """
users = [{"id": "A", "name": "Alice"}, {"id": "B", "name": "Bob"}]
return [u.name for(u in users)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["Alice", "Bob"]

    def test_arithmetic_expression(self):
        """[x * 2 for(x in nums)] applies arithmetic to each element."""
        result = self.interpreter.run("return [x * 2 for(x in [1, 2, 3])]")
        assert parse_result(result) == [2, 4, 6]

    def test_empty_iterable(self):
        """Comprehension over empty list returns empty list."""
        result = self.interpreter.run("return [x for(x in [])]")
        assert parse_result(result) == []

    def test_single_element(self):
        """Comprehension over single element list."""
        result = self.interpreter.run("return [x * 10 for(x in [5])]")
        assert parse_result(result) == [50]

    def test_string_interpolation_in_element_expr(self):
        """Element expression can use string interpolation."""
        program = """
names = ["Alice", "Bob"]
return ["Hello ${name}" for(name in names)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["Hello Alice", "Hello Bob"]

    def test_nested_field_access(self):
        """[u.profile.email for(u in users)] with nested fields."""
        program = """
users = [
    {"profile": {"email": "a@x.com"}},
    {"profile": {"email": "b@x.com"}}
]
return [u.profile.email for(u in users)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["a@x.com", "b@x.com"]


class TestListComprehensionWithFilter:
    """Test list comprehension with if-filter."""

    def setup_method(self):
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.interpreter = Cy(tools=default_registry.get_tools_dict())

    def test_filter_even_numbers(self):
        """[n for(n in nums) if(n % 2 == 0)] filters correctly."""
        result = self.interpreter.run(
            "return [n for(n in [1, 2, 3, 4, 5, 6]) if(n % 2 == 0)]"
        )
        assert parse_result(result) == [2, 4, 6]

    def test_filter_by_field(self):
        """Filter objects by a boolean field."""
        program = """
users = [
    {"name": "Alice", "active": True},
    {"name": "Bob", "active": False},
    {"name": "Charlie", "active": True}
]
return [u.name for(u in users) if(u.active == True)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["Alice", "Charlie"]

    def test_filter_removes_all(self):
        """Filter that removes all elements returns empty list."""
        result = self.interpreter.run("return [x for(x in [1, 2, 3]) if(x > 100)]")
        assert parse_result(result) == []

    def test_filter_keeps_all(self):
        """Filter that keeps all elements returns full list."""
        result = self.interpreter.run("return [x for(x in [1, 2, 3]) if(x > 0)]")
        assert parse_result(result) == [1, 2, 3]

    def test_filter_with_comparison(self):
        """Filter with greater-than comparison."""
        result = self.interpreter.run(
            "return [x for(x in [10, 20, 30, 40, 50]) if(x > 25)]"
        )
        assert parse_result(result) == [30, 40, 50]

    def test_filter_by_string_field(self):
        """Filter by string equality."""
        program = """
items = [
    {"type": "alert", "msg": "fire"},
    {"type": "info", "msg": "ok"},
    {"type": "alert", "msg": "flood"}
]
return [i.msg for(i in items) if(i.type == "alert")]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["fire", "flood"]


class TestListComprehensionInExpressions:
    """Test list comprehension used in various expression positions."""

    def setup_method(self):
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.interpreter = Cy(tools=default_registry.get_tools_dict())

    def test_assign_to_variable(self):
        """Comprehension result assigned to variable then returned."""
        program = """
ids = [x for(x in [1, 2, 3])]
return ids
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == [1, 2, 3]

    def test_as_function_argument(self):
        """Comprehension used as argument to len()."""
        result = self.interpreter.run("return len([x for(x in [10, 20, 30])])")
        assert result == "3"

    def test_in_return_statement(self):
        """Comprehension directly in return."""
        result = self.interpreter.run("return [x for(x in [1, 2])]")
        assert parse_result(result) == [1, 2]

    def test_comprehension_over_variable(self):
        """Comprehension iterates over a variable, not just literal."""
        program = """
data = [10, 20, 30]
doubled = [x * 2 for(x in data)]
return doubled
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == [20, 40, 60]

    def test_comprehension_over_function_result(self):
        """Comprehension iterates over a function call result."""
        program = """
items = [3, 1, 2]
return [x for(x in sort(items))]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == [1, 2, 3]

    def test_comprehension_with_tool_call_in_expression(self):
        """Element expression can contain a tool call."""
        program = """
words = ["hello", "world"]
return [str::uppercase(w) for(w in words)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["HELLO", "WORLD"]


class TestListComprehensionIteratesOverDicts:
    """Test comprehension behavior when iterating over dicts (keys)."""

    def setup_method(self):
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.interpreter = Cy(tools=default_registry.get_tools_dict())

    def test_iterate_over_dict_keys(self):
        """for(k in dict) iterates over keys, matching for-loop behavior."""
        program = """
d = {"a": 1, "b": 2, "c": 3}
return [k for(k in d)]
"""
        result = self.interpreter.run(program)
        assert parse_result(result) == ["a", "b", "c"]
