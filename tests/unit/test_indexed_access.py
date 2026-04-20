"""
Comprehensive tests for indexed access functionality.

These tests were created after validation revealed critical gaps in
indexed access coverage, particularly for chained access patterns like $data["users"][0].
"""

import pytest

from cy_language import Cy
from cy_language.errors import InterpolationError


class TestBasicIndexedAccess:
    """Test basic indexed access patterns."""

    def test_list_numeric_indexing(self):
        """Test basic list indexing with numeric indices."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c", "d"]
        first = arr[0]
        second = arr[1]
        last = arr[3]
        output = "First: ${first}, Second: ${second}, Last: ${last}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First: a, Second: b, Last: d"'

    def test_dict_string_indexing(self):
        """Test basic dictionary indexing with string keys."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        name = data["name"]
        age = data["age"]
        city = data["city"]
        output = "Name: ${name}, Age: ${age}, City: ${city}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice, Age: 30, City: NYC"'

    def test_string_character_indexing(self):
        """Test string character indexing."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        text = "Hello World"
        first_char = text[0]
        space_char = text[5]
        last_char = text[10]
        output = "First: '${first_char}', Space: '${space_char}', Last: '${last_char}'"
        return output
        """
        result = interpreter.run(program)
        assert result == "\"First: 'H', Space: ' ', Last: 'd'\""


class TestChainedIndexedAccess:
    """Test chained indexed access patterns that were failing in validation."""

    def test_dict_to_list_chaining(self):
        """Test dictionary key leading to list indexing: data["users"][0]."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"users": ["Alice", "Bob", "Carol"], "scores": [95, 87, 92]}
        first_user = data["users"][0]
        second_user = data["users"][1]
        first_score = data["scores"][0]
        output = "Users: ${first_user}, ${second_user}. Top score: ${first_score}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Users: Alice, Bob. Top score: 95"'

    def test_multidimensional_array_access(self):
        """Test multi-dimensional array access: matrix[1][0]."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        matrix = [["a", "b"], ["c", "d"], ["e", "f"]]
        element_00 = matrix[0][0]
        element_10 = matrix[1][0]
        element_21 = matrix[2][1]
        output = "Elements: ${element_00}, ${element_10}, ${element_21}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Elements: a, c, f"'

    def test_deep_nested_access(self):
        """Test deep nested structure access: obj["a"]["b"]["c"][0]."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        nested = {"level1": {"level2": {"items": [1, 2, 3, 4]}}}
        deep_value = nested["level1"]["level2"]["items"][2]
        output = "Deep nested value: ${deep_value}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Deep nested value: 3"'

    def test_triple_chaining(self):
        """Test triple chained access."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = [{"users": [{"name": "Alice"}]}, {"users": [{"name": "Bob"}]}]
        name = data[0]["users"][0]["name"]
        output = "Name: ${name}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice"'


class TestMixedAccessPatterns:
    """Test mixing field access and indexed access (using separate operations)."""

    def test_field_then_index_separate_operations(self):
        """Test field access then indexing in separate steps."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        obj = {"items": ["x", "y", "z"], "count": 3}
        items = obj["items"]
        first_item = items[0]
        count = obj["count"]
        output = "First item: ${first_item}, Count: ${count}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First item: x, Count: 3"'

    def test_index_then_field_separate_operations(self):
        """Test indexing then field access in separate steps."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        users = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        first_user = users[0]
        second_user = users[1]
        first_name = first_user["name"]
        first_age = first_user["age"]
        second_name = second_user["name"]
        output = "First: ${first_name} (${first_age}), Second: ${second_name}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First: Alice (30), Second: Bob"'

    def test_complex_nested_with_separate_steps(self):
        """Test complex nested access using separate steps."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {
            "users": [
                {"profile": {"settings": {"theme": "dark", "lang": "en"}}},
                {"profile": {"settings": {"theme": "light", "lang": "es"}}}
            ]
        }
        users = data["users"]
        first_user = users[0]
        second_user = users[1]
        first_profile = first_user["profile"]
        second_profile = second_user["profile"]
        first_settings = first_profile["settings"]
        second_settings = second_profile["settings"]
        theme = first_settings["theme"]
        lang = second_settings["lang"]
        output = "Theme: ${theme}, Language: ${lang}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Theme: dark, Language: es"'


class TestToolIntegration:
    """Test indexed access with tool calls (pattern from validation)."""

    def test_indexed_values_in_tool_calls(self):
        """Test using indexed values as tool arguments: add(numbers[0], numbers[4])."""
        tools = {"add": lambda a, b: a + b, "multiply": lambda a, b: a * b}
        interpreter = Cy(tools=tools)
        interpreter.show_enhanced_errors = False

        program = """
        numbers = [10, 20, 30, 40, 50]
        total = add(numbers[0], numbers[4])
        product = multiply(numbers[1], numbers[2])
        output = "Sum: ${total}, Product: ${product}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Sum: 60, Product: 600"'

    def test_chained_access_in_tools(self):
        """Test chained access in tool arguments."""
        tools = {"concat": lambda a, b: f"{a}-{b}"}
        interpreter = Cy(tools=tools)
        interpreter.show_enhanced_errors = False

        program = """
        data = {"teams": [["Alice", "Bob"], ["Carol", "Dave"]]}
        result = concat(data["teams"][0][0], data["teams"][1][1])
        output = "Combined: ${result}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Combined: Alice-Dave"'


class TestIndexedAccessErrorHandling:
    """Test error conditions for indexed access."""

    def test_list_index_out_of_bounds_returns_null(self):
        """Test list index out of bounds returns null (consistent with dict missing key)."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        invalid = arr[5]
        output = "Value: ${invalid}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Value: null"'

    def test_list_index_out_of_bounds_with_null_coalesce(self):
        """Test list[0] ?? {} works on empty list."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        items = []
        first = items[0] ?? {}
        return first
        """
        result = interpreter.run(program)
        assert result == "{}"

    def test_list_negative_index_out_of_bounds_returns_null(self):
        """Test negative list index out of bounds returns null."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b"]
        invalid = arr[-5]
        output = "Value: ${invalid}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Value: null"'

    def test_dict_key_not_found(self):
        """Test dictionary key not found returns null."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"a": 1, "b": 2}
        invalid = data["c"]
        output = "Value: ${invalid}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Value: null"'

    def test_string_index_out_of_bounds(self):
        """Test string index out of bounds error."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        text = "hello"
        invalid = text[10]
        output = "Char: invalid"
        return output
        """
        with pytest.raises(InterpolationError, match="Index out of range"):
            interpreter.run(program)

    def test_invalid_index_type_on_list(self):
        """Test invalid index type on list."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        key = "invalid"
        invalid = arr[key]
        output = "Value: invalid"
        return output
        """
        with pytest.raises(InterpolationError, match="List index must be an integer"):
            interpreter.run(program)

    def test_indexing_non_indexable_type(self):
        """Test indexing on non-indexable type."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        number = 42
        invalid = number[0]
        output = "Value: invalid"
        return output
        """
        with pytest.raises(InterpolationError, match="Cannot index object of type int"):
            interpreter.run(program)


class TestRealWorldPatterns:
    """Test patterns discovered during validation that represent real usage."""

    def test_employee_data_pattern(self):
        """Test the employee data pattern from validation."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        users = [
            {"name": "Alice", "dept": "Engineering", "projects": ["API", "DB"]},
            {"name": "Bob", "dept": "Marketing", "projects": ["Campaign"]}
        ]
        first_user = users[0]
        first_project = first_user["projects"][0]
        second_user_name = users[1]["name"]
        output = "First: ${first_user}, Project: ${first_project}, Second: ${second_user_name}"
        return output
        """
        result = interpreter.run(program)
        expected = '"First: **name**: Alice\\n**dept**: Engineering\\n**projects**:\\n  - API\\n  - DB, Project: API, Second: Bob"'
        assert result == expected

    def test_engineering_team_pattern(self):
        """Test the engineering team selection pattern."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        all_users = [
            {"name": "Alice", "dept": "Engineering"},
            {"name": "Bob", "dept": "Marketing"},
            {"name": "Carol", "dept": "Engineering"}
        ]
        engineering = [all_users[0], all_users[2]]
        top_engineer = engineering[0]
        output = "Top engineer: ${top_engineer}"
        return output
        """
        result = interpreter.run(program)
        expected = '"Top engineer: **name**: Alice\\n**dept**: Engineering"'
        assert result == expected
