"""Tests for ?? (null coalescing) operator -

The ?? operator returns the right operand when the left is null,
and returns the left operand otherwise (even if it's falsy like 0, [], {}).

This is different from 'or' which uses truthiness.

Following TDD: All tests should FAIL initially until we implement the operator.
"""

import json

from cy_language import Cy


class TestNullCoalesceBasics:
    """Test basic ?? operator behavior."""

    def test_null_coalesce_with_null_returns_right(self):
        """Test: null ?? 'default' returns 'default'"""
        code = """
result = null ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_null_coalesce_with_value_returns_left(self):
        """Test: 'value' ?? 'default' returns 'value'"""
        code = """
result = "value" ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"value"'

    def test_null_coalesce_with_zero_returns_zero(self):
        """Test: 0 ?? 99 returns 0 (NOT 99 like 'or' would)"""
        code = """
result = 0 ?? 99
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "0"

    def test_null_coalesce_with_false_returns_false(self):
        """Test: False ?? True returns False (NOT True like 'or' would)"""
        code = """
result = False ?? True
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "false"

    def test_null_coalesce_with_empty_string_returns_empty(self):
        """Test: '' ?? 'default' returns '' (NOT 'default' like 'or' would)"""
        code = """
result = "" ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '""'

    def test_null_coalesce_with_empty_array_returns_array(self):
        """Test: [] ?? ['default'] returns [] (NOT ['default'] like 'or' would)"""
        code = """
result = [] ?? ["default"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "[]"

    def test_null_coalesce_with_empty_object_returns_object(self):
        """Test: {} ?? {'a': 1} returns {} (NOT {'a': 1} like 'or' would)"""
        code = """
result = {} ?? {"a": 1}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "{}"


class TestNullCoalesceWithFieldAccess:
    """Test ?? operator with field access (main use case)."""

    def test_missing_field_returns_default(self):
        """Test: obj.missing ?? 'default' returns 'default'"""
        code = """
obj = {}
result = obj.missing ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_existing_field_returns_value(self):
        """Test: obj.name ?? 'default' returns obj.name"""
        code = """
obj = {"name": "Alice"}
result = obj.name ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Alice"'

    def test_zero_field_returns_zero_not_default(self):
        """Test: obj.count ?? 99 returns 0 when count is 0"""
        code = """
obj = {"count": 0}
result = obj.count ?? 99
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "0"

    def test_empty_array_field_returns_array_not_default(self):
        """Test: obj.items ?? ['default'] returns [] when items is []"""
        code = """
obj = {"items": []}
result = obj.items ?? ["default"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "[]"

    def test_nested_field_access_with_null_coalesce(self):
        """Test: obj.user.name ?? 'Unknown' handles nested null"""
        code = """
obj = {}
result = obj.user.name ?? "Unknown"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Unknown"'


class TestNullCoalesceChaining:
    """Test chaining multiple ?? operators."""

    def test_chain_returns_first_non_null(self):
        """Test: null ?? null ?? 'third' returns 'third'"""
        code = """
result = null ?? null ?? "third"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"third"'

    def test_chain_with_falsy_values(self):
        """Test: null ?? 0 ?? 99 returns 0 (first non-null)"""
        code = """
result = null ?? 0 ?? 99
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "0"

    def test_chain_with_field_access(self):
        """Test: a.x ?? b.y ?? 'default'"""
        code = """
a = {}
b = {"y": "value"}
result = a.x ?? b.y ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"value"'


class TestNullCoalesceInInterpolation:
    """Test ?? operator inside string interpolations."""

    def test_null_coalesce_in_interpolation_with_null(self):
        """Test: "Name: ${obj.name ?? 'Unknown'}" """
        code = """
obj = {}
result = "Name: ${obj.name ?? 'Unknown'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Name: Unknown"'

    def test_null_coalesce_in_interpolation_with_zero(self):
        """Test: "Count: ${obj.count ?? 99}" preserves 0"""
        code = """
obj = {"count": 0}
result = "Count: ${obj.count ?? 99}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Count: 0"'

    def test_null_coalesce_in_interpolation_with_value(self):
        """Test: "Name: ${obj.name ?? 'Unknown'}" with name present"""
        code = """
obj = {"name": "Alice"}
result = "Name: ${obj.name ?? 'Unknown'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Name: Alice"'


class TestNullCoalesceVsOr:
    """Test differences between ?? and 'or' operators."""

    def test_or_replaces_zero_but_null_coalesce_doesnt(self):
        """Test: Demonstrate difference with 0"""
        code = """
value = 0
with_or = value or 99
with_coalesce = value ?? 99
result = {"or": with_or, "coalesce": with_coalesce}
return result
"""
        cy = Cy()
        result = cy.run(code)
        parsed = json.loads(result)
        assert parsed["or"] == 99  # 'or' replaces 0 with 99
        assert parsed["coalesce"] == 0  # '??' keeps 0

    def test_or_replaces_empty_array_but_null_coalesce_doesnt(self):
        """Test: Demonstrate difference with []"""
        code = """
value = []
with_or = value or ["default"]
with_coalesce = value ?? ["default"]
result = {"or": with_or, "coalesce": with_coalesce}
return result
"""
        cy = Cy()
        result = cy.run(code)
        parsed = json.loads(result)
        assert parsed["or"] == ["default"]  # 'or' replaces [] with ["default"]
        assert parsed["coalesce"] == []  # '??' keeps []

    def test_both_replace_null_same_way(self):
        """Test: Both ?? and 'or' replace null"""
        code = """
value = null
with_or = value or "default"
with_coalesce = value ?? "default"
result = {"or": with_or, "coalesce": with_coalesce}
return result
"""
        cy = Cy()
        result = cy.run(code)
        parsed = json.loads(result)
        assert parsed["or"] == "default"
        assert parsed["coalesce"] == "default"


class TestNullCoalescePrecedence:
    """Test operator precedence of ??."""

    def test_null_coalesce_lower_precedence_than_arithmetic(self):
        """Test: 1 + 2 ?? 0 means (1 + 2) ?? 0 = 3"""
        code = """
result = 1 + 2 ?? 0
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "3"

    def test_null_coalesce_with_comparison(self):
        """Test: (x > 5) ?? False"""
        code = """
x = 10
result = (x > 5) ?? False
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "true"

    def test_null_coalesce_with_and_operator(self):
        """Test: null ?? True and False = True and False = False"""
        code = """
result = null ?? True and False
return result
"""
        cy = Cy()
        result = cy.run(code)
        # null ?? True = True, then True and False = False
        assert result == "false"


class TestNullCoalesceEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_null_coalesce_with_function_call(self):
        """Test: func() ?? 'default' when func returns null"""
        code = """
result = str(null) ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        # str(null) returns "None", not null itself
        assert result == '"None"'

    def test_null_coalesce_in_assignment(self):
        """Test: x = obj.field ?? 'default'"""
        code = """
obj = {}
x = obj.field ?? "default"
return x
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_null_coalesce_in_conditional(self):
        """Test: if (obj.field ?? 0 > 5) {...}"""
        code = """
obj = {}
value = obj.field ?? 10
if (value > 5) {
    result = "pass"
} else {
    result = "fail"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"pass"'

    def test_null_coalesce_with_indexed_access(self):
        """Test: obj['key'] ?? 'default'"""
        code = """
obj = {}
result = obj['missing'] ?? "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'
