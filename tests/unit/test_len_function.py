"""Tests for the enhanced len() function."""

import json

from cy_language import Cy


class TestLenFunction:
    """Test the len() native function with strings and lists."""

    def setup_method(self):
        """Set up test fixtures."""
        # Import native functions to register them
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        self.cy = Cy(tools=default_registry.get_tools_dict())

    def test_len_with_strings(self):
        """Test len() function with various strings."""
        program = """text1 = "hello"
text2 = "hello world"
text3 = ""
text4 = "a"

len1 = len(text1)
len2 = len(text2)
len3 = len(text3)
len4 = len(text4)

output = {
    "hello": len1,
    "hello_world": len2,
    "empty": len3,
    "single": len4
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {"hello": 5, "hello_world": 11, "empty": 0, "single": 1}
        assert result_dict == expected

    def test_len_with_lists(self):
        """Test len() function with various lists."""
        program = """list1 = [1, 2, 3]
list2 = []
list3 = ["a", "b", "c", "d", "e"]
list4 = [1]

len1 = len(list1)
len2 = len(list2)
len3 = len(list3)
len4 = len(list4)

output = {
    "three_items": len1,
    "empty": len2,
    "five_items": len3,
    "one_item": len4
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {"three_items": 3, "empty": 0, "five_items": 5, "one_item": 1}
        assert result_dict == expected

    def test_len_with_mixed_types(self):
        """Test len() function with both strings and lists in same program."""
        program = """my_string = "python"
my_list = [1, 2, 3, 4]

string_len = len(my_string)
list_len = len(my_list)

output = {
    "string_length": string_len,
    "list_length": list_len,
    "both_equal": string_len == 6,
    "list_bigger": list_len == 4
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {
            "string_length": 6,
            "list_length": 4,
            "both_equal": True,
            "list_bigger": True,
        }
        assert result_dict == expected

    def test_len_with_indexed_access(self):
        """Test len() function with indexed access to strings and lists."""
        program = """data = {
    "name": "Alice",
    "items": ["apple", "banana", "cherry"]
}

name_len = len(data["name"])
items_len = len(data["items"])

output = {
    "name_length": name_len,
    "items_count": items_len
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {"name_length": 5, "items_count": 3}
        assert result_dict == expected

    def test_len_with_nested_structures(self):
        """Test len() function with nested data structures."""
        program = """users = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
]

first_user_name_len = len(users[0]["name"])
second_user_email_len = len(users[1]["email"])
users_count = len(users)

output = {
    "alice_name_length": first_user_name_len,
    "bob_email_length": second_user_email_len,
    "total_users": users_count
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {"alice_name_length": 5, "bob_email_length": 15, "total_users": 2}
        assert result_dict == expected

    def test_len_with_various_types(self):
        """Test len() function with various types - supports strings, lists, and dicts."""
        program = """number = 42
boolean = True
null_value = null
dict_value = {"key": "value"}

number_len = len(number)
boolean_len = len(boolean)
null_len = len(null_value)
dict_len = len(dict_value)

output = {
    "number": number_len,
    "boolean": boolean_len,
    "null": null_len,
    "dict": dict_len,
    "unsupported_types_zero": number_len == 0 and boolean_len == 0 and null_len == 0,
    "dict_has_length": dict_len == 1
}
return output
"""
        result = self.cy.run(program)
        result_dict = json.loads(result)
        expected = {
            "number": 0,
            "boolean": 0,
            "null": 0,
            "dict": 1,  # Dictionary now correctly returns its length
            "unsupported_types_zero": True,  # Number, boolean, null still return 0
            "dict_has_length": True,  # Dictionary correctly returns 1
        }
        assert result_dict == expected

    def test_len_with_string_interpolation(self):
        """Test len() function results used in string interpolation."""
        program = '''name = "Alice"
items = ["apple", "banana"]

name_len = len(name)
items_len = len(items)

output = """
Name: ${name} (${name_len} characters)
Items: ${items_len} total
"""
return output
'''
        result = self.cy.run(program)
        parsed = json.loads(result)
        expected = """
Name: Alice (5 characters)
Items: 2 total
"""
        assert parsed == expected

    def test_len_function_description(self):
        """Test that len function is properly registered with correct description."""
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        tools_info = default_registry.get_tool_descriptions()
        len_tool = next((tool for tool in tools_info if tool["name"] == "len"), None)

        assert len_tool is not None, "len() function should be registered"
        assert (
            "string" in len_tool["description"] and "list" in len_tool["description"]
        ), "Description should mention both strings and lists"
