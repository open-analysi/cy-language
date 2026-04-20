"""
Unit tests for indexed assignment type inference.

Tests verify that analyze_types() correctly handles IndexedAssignNode
for dict and list element assignments.
"""

import pytest

from cy_language import analyze_types


class TestIndexedAssignDict:
    """Test indexed assignment with dictionaries."""

    def test_simple_dict_indexed_assign(self):
        """Test simple dictionary indexed assignment."""
        script = """
        data = {"name": "Alice"}
        data["age"] = 30
        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"
        # Note: We don't track element updates yet, so age won't appear
        # This just validates that the code doesn't raise an error

    def test_multiple_dict_indexed_assigns(self):
        """Test multiple dictionary indexed assignments."""
        script = """
        user = {}
        user["name"] = "Bob"
        user["age"] = 25
        user["active"] = True
        return user
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_dict_indexed_assign_with_variable_key(self):
        """Test dictionary assignment with variable as key."""
        script = """
        scores = {}
        player = "alice"
        scores[player] = 95
        return scores
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_dict_indexed_assign_with_expression_value(self):
        """Test dictionary assignment with expression as value.

        Requires ?? operator for indexed access in expressions.
        """
        script = """
        data = {"base": 100}
        data["calculated"] = (data["base"] ?? 0) * 2 + 50
        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_nested_dict_indexed_assign(self):
        """Test assignment to nested dictionary."""
        script = """
        config = {"server": {"host": "localhost"}}
        config["server"]["port"] = 8080
        return config
        """

        result = analyze_types(script)
        assert result["type"] == "object"


class TestIndexedAssignList:
    """Test indexed assignment with lists."""

    def test_simple_list_indexed_assign(self):
        """Test simple list indexed assignment."""
        script = """
        arr = ["a", "b", "c"]
        arr[0] = "x"
        return arr
        """

        result = analyze_types(script)
        assert result["type"] == "array"

    def test_multiple_list_indexed_assigns(self):
        """Test multiple list indexed assignments."""
        script = """
        nums = [1, 2, 3, 4, 5]
        nums[0] = 10
        nums[2] = 30
        nums[4] = 50
        return nums
        """

        result = analyze_types(script)
        assert result["type"] == "array"

    def test_list_indexed_assign_with_variable_index(self):
        """Test list assignment with variable as index."""
        script = """
        items = ["a", "b", "c"]
        idx = 1
        items[idx] = "modified"
        return items
        """

        result = analyze_types(script)
        assert result["type"] == "array"

    def test_list_indexed_assign_with_expression(self):
        """Test list assignment with expression as value.

        Requires ?? operator for indexed access in expressions.
        """
        script = """
        numbers = [1, 2, 3]
        numbers[0] = (numbers[1] ?? 0) + (numbers[2] ?? 0)
        return numbers
        """

        result = analyze_types(script)
        assert result["type"] == "array"


class TestIndexedAssignWithInputSchema:
    """Test indexed assignment with input schema."""

    def test_indexed_assign_with_input_dict(self):
        """Test indexed assignment using input dictionary.

        strict_input=True needed to get precise types from input access.
        """
        script = """
        config = input["config"]
        config["modified"] = True
        return config
        """

        input_schema = {"type": "object", "properties": {"config": {"type": "object"}}}

        # strict_input=True ensures input["config"] returns object, not (object | null)
        result = analyze_types(script, input_schema=input_schema, strict_input=True)
        assert result["type"] == "object"

    def test_indexed_assign_with_input_list(self):
        """Test indexed assignment using input list.

        strict_input=True needed to get precise types from input access.
        """
        script = """
        items = input["items"]
        items[0] = "modified"
        return items
        """

        input_schema = {"type": "object", "properties": {"items": {"type": "array"}}}

        # strict_input=True ensures input["items"] returns array, not (array | null)
        result = analyze_types(script, input_schema=input_schema, strict_input=True)
        assert result["type"] == "array"

    def test_workflow_pattern_accumulating_results(self):
        """Test real-world pattern: accumulating results in dict."""
        script = """
        results = {}
        ip = input["ip"]
        context = input["context"]

        results["ip"] = ip
        results["context"] = context
        results["status"] = "processed"

        return results
        """

        input_schema = {
            "type": "object",
            "properties": {"ip": {"type": "string"}, "context": {"type": "string"}},
        }

        result = analyze_types(script, input_schema=input_schema)
        assert result["type"] == "object"


class TestIndexedAssignComplexCases:
    """Test complex indexed assignment scenarios."""

    def test_indexed_assign_in_conditional(self):
        """Test indexed assignment inside conditional."""
        script = """
        data = {"count": 0}
        flag = True

        if (flag) {
            data["count"] = 10
        } else {
            data["count"] = 0
        }

        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_indexed_assign_in_loop(self):
        """Test indexed assignment inside while loop."""
        script = """
        results = []
        i = 0

        while (i < 3) {
            results[i] = i * 2
            i = i + 1
        }

        return results
        """

        result = analyze_types(script)
        assert result["type"] == "array"

    def test_indexed_assign_with_tool_call(self):
        """Test indexed assignment with tool call result."""
        script = """
        data = {}
        data["length"] = len([1, 2, 3])
        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_mixed_dict_and_list_indexed_assigns(self):
        """Test both dict and list indexed assignments in same script."""
        script = """
        data = {
            "items": [1, 2, 3],
            "name": "test"
        }

        data["items"][0] = 10
        data["status"] = "modified"

        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"


class TestIndexedAssignEdgeCases:
    """Test edge cases for indexed assignment."""

    def test_indexed_assign_return_value(self):
        """Test that indexed assignment itself doesn't have a return value."""
        script = """
        data = {}
        # Assignment doesn't return a value, so can't use it in expression
        data["key"] = "value"
        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_indexed_assign_with_null_value(self):
        """Test indexed assignment with null value."""
        script = """
        data = {"key": "value"}
        data["key"] = null
        return data
        """

        result = analyze_types(script)
        assert result["type"] == "object"

    def test_indexed_assign_creating_nested_structure(self):
        """Test building structure with multiple indexed assigns.

        Tests that indexed assignment works for building objects.
        """
        script = """
        result = {}
        result["data"] = {"nested": "value"}
        result["status"] = "complete"
        result["count"] = 42
        return result
        """

        result = analyze_types(script)
        assert result["type"] == "object"


class TestIndexedAssignStrictInput:
    """Test indexed assignment does not trigger strict_input read validation.

    Regression tests for GitHub issue #13: _infer_indexed_assign calls
    infer_node(node.target) which triggers _validate_indexed_access →
    _validate_strict_input_field on write targets.  When strict_input=True,
    writing to a new key (e.g., input["new_key"] = value) was incorrectly
    rejected as "field not found".
    """

    def test_indexed_assign_new_key_on_input_dict(self):
        """Writing a new key to an input dict must not fail strict_input validation."""
        script = """
        data = input["config"]
        data["new_key"] = "hello"
        return data
        """
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {"existing": {"type": "string"}},
                },
            },
        }
        # Should succeed — "new_key" is a write target, not a read
        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result["type"] == "object"

    def test_direct_indexed_assign_on_input(self):
        """Writing directly to input['new_field'] must not fail strict_input."""
        script = """
        input["extra"] = "added"
        return input
        """
        schema = {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
        }
        # "extra" is not in the schema but we're writing, not reading
        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result is not None

    def test_indexed_assign_existing_key_on_input_dict(self):
        """Overwriting an existing key should also work fine."""
        script = """
        data = input["config"]
        data["existing"] = "overwritten"
        return data
        """
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {"existing": {"type": "string"}},
                },
            },
        }
        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result["type"] == "object"

    def test_indexed_read_still_validated_under_strict_input(self):
        """Reading a non-existent field should still fail under strict_input."""
        script = """
        val = input["nonexistent"]
        return val
        """
        schema = {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
        }
        with pytest.raises(TypeError):
            analyze_types(script, input_schema=schema, strict_input=True)

    def test_indexed_assign_with_variable_key_on_input(self):
        """Variable-key indexed assignment on input should not fail strict_input."""
        script = """
        key = "dynamic_key"
        input[key] = "value"
        return input
        """
        schema = {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
        }
        # Variable keys can't be validated at compile time anyway
        result = analyze_types(script, input_schema=schema, strict_input=True)
        assert result is not None

    def test_index_expression_is_still_inferred(self):
        """The index sub-expression must be type-inferred even for writes.

        Even though we skip the full _infer_indexed_access path (to avoid
        strict_input field-exists validation on writes), we must still infer
        the index sub-expression so variable types flow correctly.
        """
        script = """
        data = {}
        key = "hello"
        data[key] = "value"
        return data
        """
        # key is a variable reference — inferring it exercises the index path
        result = analyze_types(script)
        assert result["type"] == "object"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
