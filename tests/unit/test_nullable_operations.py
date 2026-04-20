"""
Test cases for nullable type operations -

Tests that operations on nullable types require explicit null handling
with the ?? operator.
"""

import pytest

from cy_language import Cy


class TestNullableArithmeticOperations:
    """Test that arithmetic operations on nullable types require explicit handling."""

    def test_field_access_plus_number_errors(self):
        """obj.a + 1 should error when obj.a has nullable type (safe navigation)."""
        code = """
obj = {"a": 1}
result = obj.a + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()
        assert "??" in str(exc.value)

    def test_field_access_with_null_coalesce_works(self):
        """(input.missing ?? 0) + 1 should work."""
        code = """
obj = {"a": 1}
result = (input.missing ?? 0) + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "1"  # 0 + 1

    def test_existing_field_plus_number_requires_null_handling(self):
        """obj.a + 1 requires ?? even when field exists."""
        code = """
obj = {"a": 5}
result = obj.a + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        # All field access returns nullable type for safe navigation
        # Even when field exists, we require explicit null handling
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()
        assert "??" in str(exc.value)

    def test_existing_field_with_null_coalesce_works(self):
        """obj.a with ?? works even when field exists."""
        code = """
obj = {"a": 5}
result = (obj.a ?? 0) + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "6"  # 5 + 1

    def test_all_arithmetic_operators_reject_nullable(self):
        """All arithmetic operators should reject nullable operands."""
        operators = [
            ("+", "add"),
            ("-", "subtract"),
            ("*", "multiply"),
            ("/", "divide"),
            ("%", "modulo"),
        ]

        for op, _op_name in operators:
            code = f"""
obj = {{"a": 1}}
result = obj.a {op} 2
return result
"""
            cy = Cy(check_types=True)
            cy.show_enhanced_errors = False
            with pytest.raises(TypeError) as exc:
                cy.run(code)
            assert "nullable" in str(exc.value).lower(), f"Failed for {op}"

    def test_nullable_on_both_sides_errors(self):
        """obj.a + obj.b should error when both have nullable types."""
        code = """
obj = {"a": 1, "b": 2}
result = obj.a + obj.b
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_chained_field_access_errors(self):
        """obj.a.b.c + 1 should error when chain has missing fields."""
        code = """
obj = {"a": {"b": 1}}
result = obj.a.b.c + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        # obj.a.b is 1 (number), so obj.a.b.c should error on field access
        assert "cannot access field" in str(exc.value).lower()

    def test_indexed_access_with_missing_key_errors(self):
        """obj["a"] + 1 should error when obj["a"] has nullable type (safe navigation)."""
        code = """
obj = {"a": 1}
result = obj["a"] + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_indexed_access_with_null_coalesce_works(self):
        """(obj["missing"] ?? 0) + 1 should work."""
        code = """
obj = {"a": 1}
result = (obj["missing"] ?? 0) + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "1"  # 0 + 1


class TestNullableComparisonOperations:
    """Test that comparison operations on nullable types require explicit handling."""

    def test_nullable_less_than_errors(self):
        """obj.a < 5 should error when obj.a has nullable type (safe navigation)."""
        code = """
obj = {"a": 1}
result = obj.a < 5
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_nullable_comparison_with_coalesce_works(self):
        """(obj.missing ?? 0) < 5 should work."""
        code = """
obj = {"a": 1}
result = (obj.missing ?? 0) < 5
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "true"  # 0 < 5

    def test_all_comparison_operators_reject_nullable(self):
        """All comparison operators should reject nullable operands."""
        operators = ["<", ">", "<=", ">="]

        for op in operators:
            code = f"""
obj = {{"a": 1}}
result = obj.a {op} 5
return result
"""
            cy = Cy(check_types=True)
            cy.show_enhanced_errors = False
            with pytest.raises(TypeError) as exc:
                cy.run(code)
            assert "nullable" in str(exc.value).lower(), f"Failed for {op}"


class TestNullableStringOperations:
    """Test string concatenation with nullable types."""

    def test_nullable_string_concat_errors(self):
        """obj.name + "hello" should error when obj.name has nullable type."""
        code = """
obj = {"name": "test"}
result = obj.name + "hello"
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_nullable_string_with_coalesce_works(self):
        """(obj.missing ?? "") + "hello" should work."""
        code = """
obj = {"a": "world"}
result = (obj.missing ?? "") + "hello"
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == '"hello"'


class TestNullableListOperations:
    """Test list concatenation with nullable types."""

    def test_nullable_list_concat_errors(self):
        """obj.items + [1, 2] should error when obj.items has nullable type."""
        code = """
obj = {"items": [3, 4]}
result = obj.items + [1, 2]
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_nullable_list_with_coalesce_works(self):
        """(obj.missing ?? []) + [1, 2] should work."""
        code = """
obj = {"a": [3, 4]}
result = (obj.missing ?? []) + [1, 2]
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        # Result might be stringified
        assert "1" in str(result) and "2" in str(result)


class TestNullableBooleanOperations:
    """Test that boolean operations handle nullable types appropriately."""

    def test_nullable_in_if_condition_allowed(self):
        """if statements should handle nullable (falsy) values."""
        code = """
obj = {"a": 1}
missing_val = obj.missing
if (missing_val) {
    result = "found"
} else {
    result = "not found"
}
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == '"not found"'  # null is falsy

    def test_nullable_and_operation_allowed(self):
        """Boolean AND should work with nullable types."""
        code = """
obj = {"a": True}
result = obj.missing and True
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        # null and True returns null (falsy) - API may stringify
        assert result == "null"

    def test_nullable_or_operation_allowed(self):
        """Boolean OR should work with nullable types."""
        code = """
obj = {"a": False}
result = obj.missing or True
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "true"  # null or True returns True


class TestComplexNullableScenarios:
    """Test complex scenarios with nullable types."""

    def test_multiple_null_coalesce_chain(self):
        """Chained ?? operators should work."""
        code = """
obj = {"c": 10}
result = (obj.a ?? obj.b ?? obj.c ?? 0) + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "11"  # 10 + 1

    def test_nested_object_nullable_field(self):
        """Nested object field access with null handling."""
        code = """
data = {"user": {"name": "Alice"}}
result = (data.user.age ?? 25) + 5
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "30"  # 25 + 5

    def test_dynamic_key_access_nullable_handling(self):
        """Dynamic key access that might return null should require handling."""
        code = """
data = {"a": 5}
key = "b"
result = (data[key] ?? 0) + 10
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "10"  # 0 + 10

    def test_loop_with_nullable_operations(self):
        """Loops with nullable operations should require explicit handling."""
        code = """
items = [{"value": 1}, {"other": 2}, {"value": 3}]
total = 0
for (item in items) {
    total = total + (item.value ?? 0)
}
return total
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        result = cy.run(code)
        assert result == "4"  # 1 + 0 + 3


class TestErrorMessages:
    """Test that error messages are helpful and suggest solutions."""

    def test_error_message_suggests_null_coalesce(self):
        """Error message should suggest using ?? operator."""
        code = """
obj = {"a": 1}
result = obj.a + 1
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        error_msg = str(exc.value)
        assert "??" in error_msg
        # Should suggest the pattern - check for the example format
        assert "obj.field ?? 0" in error_msg or "field ?? default" in error_msg

    def test_error_message_identifies_nullable_operand(self):
        """Error should identify which operand is nullable."""
        code = """
obj = {"a": 1}
result = 5 + obj.a
return result
"""
        cy = Cy(check_types=True)
        cy.show_enhanced_errors = False
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "nullable" in str(exc.value).lower()


class TestRuntimeBehaviorUnchanged:
    """Ensure runtime behavior without type checking is unchanged."""

    def test_runtime_null_plus_number_still_errors(self):
        """At runtime, null + 1 should still error."""
        code = """
obj = {"a": 1}
result = obj.missing + 1
return result
"""
        cy = Cy(check_types=False)  # No type checking
        cy.show_enhanced_errors = False
        with pytest.raises(Exception) as exc:
            cy.run(code)
        # Should get runtime error about NoneType + int
        assert "NoneType" in str(exc.value) or "null" in str(exc.value).lower()

    def test_runtime_null_coalesce_still_works(self):
        """At runtime, ?? operator should still work."""
        code = """
obj = {"a": 1}
result = (obj.missing ?? 0) + 1
return result
"""
        cy = Cy(check_types=False)
        result = cy.run(code)
        assert result == "1"
