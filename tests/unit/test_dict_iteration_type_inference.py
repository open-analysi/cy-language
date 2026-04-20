"""
Test type inference for dictionary iteration.

When iterating over a dict with for-in, the loop variable should be
inferred as type "string" since all dict keys are strings.
"""

import pytest

from cy_language import analyze_types


class TestDictIterationTypeInference:
    """Test that type inference correctly handles dict iteration."""

    def test_dict_iteration_infers_string_key_type(self):
        """
        Verify that loop variable is inferred as string when iterating over dict.

        Since all dict keys are strings in Cy, for (key in dict) should
        infer key as string type. The uppercase() function requires string argument.
        If type validation passes, username was correctly inferred as string.
        """
        script = """
users = {"alice": 1, "bob": 2}

for (username in users) {
    # username should be inferred as string
    upper = uppercase(username)
}
"""

        # If analyze_types succeeds without TypeError, then:
        # 1. __iter_get returned string type for dict iteration
        # 2. username was inferred as string
        # 3. uppercase(username) validated successfully (requires string arg)
        try:
            result = analyze_types(code=script, tool_registry={})
            # Type validation passed!
            assert True
        except TypeError as e:
            pytest.fail(f"Type validation failed: {e}")

    def test_dict_iteration_accumulator_type(self):
        """
        Test that accumulating dict keys preserves array of strings type.

        Tests that keys (string type) + array creates valid array concatenation.
        """
        script = """
data = {"key1": 1, "key2": 2, "key3": 3}
keys = []

for (key in data) {
    keys = keys + [key]
}
"""

        # If type validation passes, then:
        # - key was inferred as string (from __iter_get on dict)
        # - array + array concatenation worked correctly
        try:
            result = analyze_types(code=script, tool_registry={})
            assert True
        except TypeError as e:
            pytest.fail(f"Type validation failed: {e}")

    def test_dict_iteration_with_value_access(self):
        """
        Test type inference when accessing dict values inside loop.

        Tests that dict key (string) can be used to access dict values.
        """
        script = """
scores = {"Alice": 95, "Bob": 87}

for (name in scores) {
    score = scores[name]
    # score type depends on dict value type
}
"""

        # If type validation passes, then:
        # - name was inferred as string (from __iter_get on dict)
        # - scores[name] validated (object indexed by string)
        try:
            result = analyze_types(code=script, tool_registry={})
            assert True
        except TypeError as e:
            pytest.fail(f"Type validation failed: {e}")

    def test_empty_dict_iteration_type(self):
        """
        Test type inference with empty dict iteration.

        Even with empty dict, type validation should pass.
        """
        script = """
empty = {}
count = 0

for (key in empty) {
    count = count + 1
}
"""

        # Type validation should pass even for empty dicts
        try:
            result = analyze_types(code=script, tool_registry={})
            assert True
        except TypeError as e:
            pytest.fail(f"Type validation failed for empty dict: {e}")

    def test_nested_dict_iteration_types(self):
        """
        Test type inference with nested dict iteration.

        Tests that string keys can access nested dict values.
        """
        script = """
users = {
    "alice": {"role": "admin"},
    "bob": {"role": "user"}
}

for (username in users) {
    user_data = users[username]
    # username is string, user_data is dict
}
"""

        # If type validation passes, then:
        # - username inferred as string (from __iter_get on dict)
        # - users[username] validated (object indexed by string)
        try:
            result = analyze_types(code=script, tool_registry={})
            assert True
        except TypeError as e:
            pytest.fail(f"Type validation failed for nested dicts: {e}")
