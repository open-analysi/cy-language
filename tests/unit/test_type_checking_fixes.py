"""
Test cases for type checking improvements.

Tests for:
1. Chained field access on primitives should error
2. Null-coalescing type compatibility
"""

import json

import pytest

from cy_language import Cy


class TestChainedFieldAccessTypeChecking:
    """Test that chained field access properly type checks."""

    def test_direct_field_on_number_errors(self):
        """Direct field access on number should error with type checking."""
        code = """
number = 42
result = number.field
return result
"""
        cy = Cy(check_types=True)
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "cannot access field" in str(exc.value).lower()
        assert "number" in str(exc.value).lower()

    def test_chained_field_on_number_errors(self):
        """Chained field access where intermediate is number should error."""
        code = """
x = {"a": 1}
result = x.a.c
return result
"""
        cy = Cy(check_types=True)
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "cannot access field" in str(exc.value).lower()
        # Should specifically mention it's on a number type
        assert "number" in str(exc.value).lower()

    def test_deeper_chain_field_on_primitive_errors(self):
        """Deep chained field access should error when hitting primitive."""
        code = """
x = {"a": {"b": 42}}
result = x.a.b.c.d
return result
"""
        cy = Cy(check_types=True)
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "cannot access field" in str(exc.value).lower()

    def test_valid_chained_field_access_works(self):
        """Valid chained field access on objects should work."""
        code = """
x = {"a": {"b": {"c": 123}}}
result = x.a.b.c
return result
"""
        cy = Cy(check_types=True)
        result = cy.run(code)
        assert result == "123"

    def test_chained_with_null_coalescing_still_type_checks(self):
        """Chained field with ?? should still type check the chain."""
        code = """
x = {"a": 1}
result = x.a.c ?? "default"
return result
"""
        cy = Cy(check_types=True)
        with pytest.raises(TypeError) as exc:
            cy.run(code)
        assert "cannot access field" in str(exc.value).lower()


class TestNullCoalescingTypeCompatibility:
    """Test null-coalescing operator type checking."""

    def test_null_coalesce_with_null_left_any_right(self):
        """null ?? anything should always work."""
        code = """
x = null
result = x ?? "hello"
return result
"""
        cy = Cy(check_types=True)
        result = cy.run(code)
        assert result == '"hello"'

    def test_null_coalesce_same_types(self):
        """Same types should work."""
        code = """
x = 5
result = x ?? 10
return result
"""
        cy = Cy(check_types=True)
        result = cy.run(code)
        assert result == "5"

    def test_null_coalesce_different_types_allowed(self):
        """?? operator accepts any types and returns union."""
        code = """
x = 5
result = x ?? "hello"
return result
"""
        cy = Cy(check_types=True)
        # ?? accepts different types, returns union
        result = cy.run(code)
        assert result == "5"  # x is 5 (non-null), so returns x

    def test_null_coalesce_boolean_string_allowed(self):
        """?? accepts boolean and string."""
        code = """
x = True
result = x ?? "fallback"
return result
"""
        cy = Cy(check_types=True)
        result = cy.run(code)
        assert result == "true"  # x is True (non-null), so returns x

    def test_null_coalesce_object_types_compatible_if_similar(self):
        """Objects with overlapping structure are compatible (both are object type)."""
        code = """
x = {"a": 1}
result = x ?? {"a": 2, "b": 3}
return result
"""
        cy = Cy(check_types=True)
        # Objects are compatible with other objects (simple type compatibility)
        # More sophisticated structural checking could be added later
        result = cy.run(code)
        result_dict = json.loads(result)
        assert result_dict == {"a": 1}  # First non-null value

    def test_null_coalesce_chained_mixed_types(self):
        """Chained null-coalescing accepts mixed types."""
        code = """
a = null
b = 5
c = "hello"
result = a ?? b ?? c
return result
"""
        cy = Cy(check_types=True)
        # ?? accepts any types, even in chains
        # a ?? b evaluates to 5 (since a is null)
        # 5 ?? "hello" evaluates to 5 (since 5 is non-null)
        result = cy.run(code)
        assert result == "5"

    def test_null_coalesce_with_field_access_result(self):
        """Field access that could be null should work with ?? at runtime."""
        # Type compatible example
        code = """
x = {"a": {"b": 1}}
# x.a.b exists and is number, so use number as default
result = x.a.b ?? 10
return result
"""
        cy = Cy(check_types=True)
        # x.a.b exists and is 1 (non-null), so ?? returns 1
        result = cy.run(code)
        assert result == 1 or result == "1" or result == "1"  # API may stringify

        # Runtime behavior without type checking allows missing fields
        code_runtime = """
x = {"a": {"b": 1}}
result = x.a.missing ?? "default"
return result
"""
        cy_runtime = Cy(check_types=False)
        result = cy_runtime.run(code_runtime)
        assert result == '"default"'  # Missing field returns null, ?? uses default


class TestRuntimeBehaviorUnchanged:
    """Ensure runtime behavior (without type checking) is unchanged."""

    def test_runtime_safe_navigation_still_works(self):
        """Without type checking, safe navigation returns null."""
        code = """
x = {"a": 1}
result = x.a.c ?? "default"
return result
"""
        cy = Cy(check_types=False)  # No type checking
        result = cy.run(code)
        assert (
            result == '"default"'
        )  # Safe navigation returns null, ?? provides default

    def test_runtime_null_coalesce_allows_any_types(self):
        """Without type checking, ?? works with any types."""
        code = """
x = 5
result = x ?? "hello"
return result
"""
        cy = Cy(check_types=False)
        result = cy.run(code)
        assert result == "5"
