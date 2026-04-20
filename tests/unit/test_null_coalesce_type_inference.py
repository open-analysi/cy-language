"""Tests for ?? operator type inference -

Tests that the ?? operator correctly infers non-null types,
providing better type safety than the 'or' operator.

Following TDD: Tests for type inference behavior.
"""

from cy_language import analyze_types


class TestNullCoalesceTypeInference:
    """Test type inference for ?? operator."""

    def test_null_coalesce_removes_null_from_union(self):
        """Test: field.name ?? 'default' returns string (not string | null)"""
        code = """
result = input.name ?? "default"
return result
"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # With strict_input=True, field access returns base type, ?? keeps it
        result = analyze_types(code, schema, strict_input=True)
        assert result == {"type": "string"}

    def test_deeply_nested_with_null_coalesce(self):
        """Test: obj.user.address.city ?? 'Unknown' returns string"""
        code = """
city = input.user.address.city ?? "Unknown"
return city
"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                        }
                    },
                }
            },
        }

        # The ?? operator strips null from the union, returning pure string type
        result = analyze_types(code, schema, strict_input=True)
        assert result == {"type": "string"}

    def test_null_coalesce_with_number_field(self):
        """Test: obj.count ?? 0 returns number"""
        code = """
count = input.count ?? 0
return count
"""
        schema = {"type": "object", "properties": {"count": {"type": "number"}}}

        result = analyze_types(code, schema, strict_input=True)
        assert result == {"type": "number"}

    def test_null_coalesce_chain_returns_first_non_null_type(self):
        """Test: null ?? null ?? 'value' returns string"""
        code = """
result = null ?? null ?? "value"
return result
"""
        result = analyze_types(code)
        assert result == {"type": "string"}

    def test_null_coalesce_with_different_types(self):
        """Test: number ?? string returns union of number | string"""
        code = """
x = 42
result = x ?? "default"
return result
"""
        result = analyze_types(code)
        # x is number, "default" is string - union of both (no null)
        assert result == {"oneOf": [{"type": "number"}, {"type": "string"}]}

    def test_null_coalesce_preserves_array_type(self):
        """Test: obj.items ?? [] returns array (union of both array types)"""
        code = """
items = input.items ?? []
return items
"""
        schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
        }

        result = analyze_types(code, schema, strict_input=True)
        # Returns union of array with string items and plain array
        assert "oneOf" in result
        assert {"type": "array", "items": {"type": "string"}} in result["oneOf"]
        assert {"type": "array"} in result["oneOf"]

    def test_null_coalesce_with_object_type(self):
        """Test: obj.config ?? {} returns object (union of both object types)"""
        code = """
config = input.config ?? {}
return config
"""
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {"enabled": {"type": "boolean"}},
                }
            },
        }

        result = analyze_types(code, schema, strict_input=True)
        # Returns union of config object and plain object
        assert "oneOf" in result
        # Both variants should be objects
        assert all(v.get("type") == "object" for v in result["oneOf"])


class TestNullCoalesceVsOrTypeInference:
    """Compare type inference between ?? and 'or' operators."""

    def test_or_returns_union_with_all_types(self):
        """Test: number or string returns union of number | string"""
        code = """
x = 0
result = x or "default"
return result
"""
        result = analyze_types(code)
        # 'or' returns union of both operand types
        assert result == {"oneOf": [{"type": "number"}, {"type": "string"}]}

    def test_null_coalesce_strips_null_from_union(self):
        """Test: (number | null) ?? string returns number | string (no null)"""
        code = """
x = input.value ?? "default"
return x
"""
        schema = {"type": "object", "properties": {"value": {"type": "number"}}}

        # Without strict_input, value is number | null
        # ?? strips null, leaving number | string
        result = analyze_types(code, schema, strict_input=False)
        # Should be union of number and string (null removed)
        assert "oneOf" in result
        types = [t.get("type") for t in result["oneOf"]]
        assert "number" in types
        assert "string" in types
        assert "null" not in types


class TestNullCoalesceTypeInferenceEdgeCases:
    """Test edge cases in type inference."""

    def test_all_null_operands_returns_null(self):
        """Test: null ?? null returns null type"""
        code = """
result = null ?? null
return result
"""
        result = analyze_types(code)
        assert result == {"type": "null"}

    def test_nested_null_coalesce_preserves_type(self):
        """Test: (a ?? b) ?? c preserves proper type"""
        code = """
a = input.x
b = input.y
c = "default"
result = (a ?? b) ?? c
return result
"""
        schema = {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
        }

        result = analyze_types(code, schema, strict_input=True)
        # a and b are numbers, c is string - union of number | string
        assert "oneOf" in result
        types = [t.get("type") for t in result["oneOf"]]
        assert "number" in types
        assert "string" in types

    def test_null_coalesce_in_string_interpolation(self):
        """Test: Type inference works in interpolations"""
        code = """
name = input.name ?? "Guest"
message = "Hello ${name}"
return message
"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        result = analyze_types(code, schema, strict_input=True)
        assert result == {"type": "string"}
