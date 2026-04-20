"""
Unit tests for Python Type Converter.

Tests verify automatic conversion from Python type hints to JSON Schema
for all common typing patterns.
"""

import contextlib
from typing import Any, Union

from cy_language.type_system import python_type_to_json_schema


class TestBasicTypeConversions:
    """Test basic Python type conversions."""

    def test_int_to_json_schema(self):
        """Verify int → {'type': 'number'}."""
        schema = python_type_to_json_schema(int)
        assert schema == {"type": "number"}

    def test_float_to_json_schema(self):
        """Verify float → {'type': 'number'}."""
        schema = python_type_to_json_schema(float)
        assert schema == {"type": "number"}

    def test_str_to_json_schema(self):
        """Verify str → {'type': 'string'}."""
        schema = python_type_to_json_schema(str)
        assert schema == {"type": "string"}

    def test_bool_to_json_schema(self):
        """Verify bool → {'type': 'boolean'}."""
        schema = python_type_to_json_schema(bool)
        assert schema == {"type": "boolean"}

    def test_none_to_json_schema(self):
        """Verify None → {'type': 'null'}."""
        schema = python_type_to_json_schema(type(None))
        assert schema == {"type": "null"}

    def test_any_to_json_schema(self):
        """Verify Any → {} (any type accepted)."""
        schema = python_type_to_json_schema(Any)
        assert schema == {}


class TestCollectionTypeConversions:
    """Test collection type conversions."""

    def test_list_without_type_param(self):
        """Verify list → {'type': 'array'}."""
        schema = python_type_to_json_schema(list)
        assert schema["type"] == "array"

    def test_list_with_int_items(self):
        """Verify List[int] → {'type': 'array', 'items': {'type': 'number'}}."""
        schema = python_type_to_json_schema(list[int])
        assert schema == {"type": "array", "items": {"type": "number"}}

    def test_list_with_str_items(self):
        """Verify List[str] → array of strings."""
        schema = python_type_to_json_schema(list[str])
        assert schema == {"type": "array", "items": {"type": "string"}}

    def test_list_nested(self):
        """Verify List[List[int]] → nested arrays."""
        schema = python_type_to_json_schema(list[list[int]])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "array"
        assert schema["items"]["items"] == {"type": "number"}

    def test_dict_without_type_params(self):
        """Verify dict → {'type': 'object'}."""
        schema = python_type_to_json_schema(dict)
        assert schema["type"] == "object"

    def test_dict_with_string_values(self):
        """Verify Dict[str, int] → object with number values."""
        schema = python_type_to_json_schema(dict[str, int])
        assert schema["type"] == "object"
        # additionalProperties should indicate value type
        if "additionalProperties" in schema:
            assert schema["additionalProperties"] == {"type": "number"}

    def test_dict_nested(self):
        """Verify Dict[str, Dict[str, int]] → nested objects."""
        schema = python_type_to_json_schema(dict[str, dict[str, int]])
        assert schema["type"] == "object"
        if "additionalProperties" in schema:
            assert schema["additionalProperties"]["type"] == "object"


class TestUnionAndOptionalTypes:
    """Test Union and Optional type conversions."""

    def test_union_two_types(self):
        """Verify Union[int, str] → {'oneOf': [...]}."""
        schema = python_type_to_json_schema(Union[int, str])
        assert "oneOf" in schema
        assert len(schema["oneOf"]) == 2
        assert {"type": "number"} in schema["oneOf"]
        assert {"type": "string"} in schema["oneOf"]

    def test_union_three_types(self):
        """Verify Union[int, str, bool] works correctly."""
        schema = python_type_to_json_schema(Union[int, str, bool])
        assert "oneOf" in schema
        assert len(schema["oneOf"]) == 3

    def test_optional_type(self):
        """Verify Optional[int] → {'oneOf': [{'type': 'number'}, {'type': 'null'}]}."""
        schema = python_type_to_json_schema(int | None)
        assert "oneOf" in schema
        assert {"type": "number"} in schema["oneOf"]
        assert {"type": "null"} in schema["oneOf"]

    def test_optional_complex_type(self):
        """Verify Optional[List[int]] works correctly."""
        schema = python_type_to_json_schema(list[int] | None)
        assert "oneOf" in schema
        # Should have array type and null type
        type_values = [item.get("type") for item in schema["oneOf"]]
        assert "array" in type_values or any(
            "items" in item for item in schema["oneOf"]
        )
        assert "null" in type_values


class TestEdgeCasesAndNegativeTests:
    """Test edge cases and unsupported types."""

    def test_unsupported_type_callable(self):
        """Verify graceful fallback for Callable type."""
        from collections.abc import Callable as CallableType

        # Should return Any or raise NotImplementedError
        try:
            schema = python_type_to_json_schema(CallableType)
            # If it succeeds, should return {} for Any
            assert schema == {} or "type" not in schema
        except NotImplementedError:
            # Acceptable to not support Callable
            pass

    def test_unsupported_type_protocol(self):
        """Verify graceful fallback for Protocol types."""
        try:
            from typing import Protocol

            class MyProtocol(Protocol):
                def method(self) -> int: ...

            schema = python_type_to_json_schema(MyProtocol)
            # Should return Any or raise NotImplementedError
            assert schema == {} or "type" not in schema
        except (NotImplementedError, ImportError):
            # Acceptable to not support Protocol
            pass

    def test_complex_nested_type(self):
        """Verify List[Dict[str, Union[int, str]]] works."""
        schema = python_type_to_json_schema(list[dict[str, Union[int, str]]])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"

    def test_empty_union(self):
        """Verify error or fallback for empty Union."""
        # This is an edge case that might not be valid in Python typing
        # Test that it doesn't crash
        with contextlib.suppress(TypeError, NotImplementedError):
            python_type_to_json_schema(Union)
