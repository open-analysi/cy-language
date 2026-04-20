"""Tests for ?? operator in control flow statements -

Tests that ?? works correctly in loops, conditionals, and try/catch.

Following TDD: Tests for control flow integration.
"""

from cy_language import Cy


class TestNullCoalesceInLoops:
    """Test ?? operator in for-in and while loops."""

    def test_null_coalesce_in_for_in_loop(self):
        """Test: for (item in obj.items ?? []) works with null"""
        code = """
obj = {}
result = []
for (item in obj.items ?? ["default"]) {
    result = result + [item]
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        import json

        assert json.loads(result) == ["default"]

    def test_null_coalesce_in_for_in_with_actual_items(self):
        """Test: for (item in obj.items ?? []) works with actual items"""
        code = """
obj = {"items": [1, 2, 3]}
result = []
for (item in obj.items ?? ["default"]) {
    result = result + [item]
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        import json

        assert json.loads(result) == [1, 2, 3]

    def test_null_coalesce_in_while_condition(self):
        """Test: while (obj.continue ?? false) works"""
        code = """
obj = {"continue": True, "count": 0}
result = 0
while (obj.continue ?? False) {
    result = result + 1
    if (result >= 3) {
        obj = {"continue": False}
    }
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "3"

    def test_null_coalesce_in_while_with_null(self):
        """Test: while loop with null ?? false doesn't execute"""
        code = """
obj = {}
result = 0
while (obj.continue ?? False) {
    result = result + 1
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "0"

    def test_null_coalesce_loop_counter(self):
        """Test: Using ?? for loop counter initialization"""
        code = """
config = {}
counter = config.start ?? 0
result = []
for (i in [1, 2, 3]) {
    counter = counter + i
}
return counter
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "6"  # 0 + 1 + 2 + 3


class TestNullCoalesceInTryCatch:
    """Test ?? operator in try/catch blocks."""

    def test_null_coalesce_in_try_block(self):
        """Test: ?? works inside try block"""
        code = """
try {
    obj = {}
    result = obj.value ?? "default"
} catch (e) {
    result = "error"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_null_coalesce_in_catch_block(self):
        """Test: ?? works inside catch block"""
        code = """
try {
    result = 1 / 0
} catch (e) {
    obj = {}
    result = obj.fallback ?? "caught"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"caught"'

    def test_null_coalesce_with_exception_value(self):
        """Test: Using ?? with values that might cause exceptions"""
        code = """
obj = {"value": null}
try {
    # This is safe with ??, even if value is null
    result = obj.value ?? "safe"
} catch (e) {
    result = "error"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"safe"'


class TestNullCoalesceWithArithmetic:
    """Test ?? operator combined with arithmetic operations."""

    def test_null_coalesce_then_add(self):
        """Test: (x ?? 0) + 5"""
        code = """
obj = {}
x = obj.value ?? 0
result = x + 5
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "5"

    def test_null_coalesce_then_multiply(self):
        """Test: (x ?? 1) * 10"""
        code = """
obj = {}
x = obj.multiplier ?? 1
result = x * 10
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "10"

    def test_arithmetic_with_inline_null_coalesce(self):
        """Test: Direct arithmetic with ?? in expression"""
        code = """
obj = {}
result = (obj.value ?? 5) + (obj.bonus ?? 10)
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "15"

    def test_null_coalesce_preserves_zero_in_arithmetic(self):
        """Test: (x ?? 999) where x=0 should use 0, not 999"""
        code = """
obj = {"value": 0}
x = obj.value ?? 999
result = x + 1
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "1"  # 0 + 1, NOT 999 + 1

    def test_null_coalesce_in_complex_expression(self):
        """Test: Complex arithmetic with multiple ?? operators"""
        code = """
a = {}
b = {"val": 2}
c = {}
result = (a.val ?? 1) + (b.val ?? 1) * (c.val ?? 3)
return result
"""
        cy = Cy()
        result = cy.run(code)
        # (null ?? 1) + (2 ?? 1) * (null ?? 3) = 1 + 2 * 3 = 1 + 6 = 7
        assert result == "7"


class TestNullCoalesceWithConditionals:
    """Test ?? operator in if/elif/else statements."""

    def test_null_coalesce_in_if_condition(self):
        """Test: if (obj.flag ?? false) works correctly"""
        code = """
obj = {}
if (obj.flag ?? False) {
    result = "true"
} else {
    result = "false"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"false"'

    def test_null_coalesce_in_elif_condition(self):
        """Test: elif with ?? operator"""
        code = """
obj = {"status": null}
if (obj.primary ?? False) {
    result = "primary"
} elif ((obj.status ?? "pending") == "pending") {
    result = "pending"
} else {
    result = "other"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"pending"'

    def test_null_coalesce_in_nested_conditionals(self):
        """Test: Nested if statements with ??"""
        code = """
user = {}
role = user.role ?? "guest"
if (role == "admin") {
    if (user.permissions ?? 0 > 5) {
        result = "full_admin"
    } else {
        result = "limited_admin"
    }
} elif (role == "guest") {
    result = "guest_access"
} else {
    result = "user_access"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"guest_access"'


class TestNullCoalesceWithCompoundOperations:
    """Test ?? operator with complex compound operations."""

    def test_null_coalesce_with_string_concatenation(self):
        """Test: String concatenation after ??"""
        code = """
user = {}
firstName = user.firstName ?? "John"
lastName = user.lastName ?? "Doe"
fullName = firstName + " " + lastName
return fullName
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"John Doe"'

    def test_null_coalesce_with_array_concatenation(self):
        """Test: Array concatenation with ??"""
        code = """
config = {}
defaults = [1, 2, 3]
custom = config.items ?? []
combined = defaults + custom
return combined
"""
        cy = Cy()
        result = cy.run(code)
        import json

        assert json.loads(result) == [1, 2, 3]

    def test_null_coalesce_with_comparison_chains(self):
        """Test: ?? with comparison operators"""
        code = """
data = {}
threshold = data.threshold ?? 10
value = data.value ?? 15
result = value > threshold
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "true"

    def test_null_coalesce_with_logical_and(self):
        """Test: ?? combined with 'and' operator"""
        code = """
config = {}
enabled = config.enabled ?? True
ready = config.ready ?? False
result = enabled and ready
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "false"

    def test_null_coalesce_with_logical_or(self):
        """Test: ?? combined with 'or' operator"""
        code = """
config = {}
# ?? returns True (not null), or returns True (first truthy)
result = (config.flag ?? True) or False
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "true"


class TestNullCoalesceReturnStatements:
    """Test ?? operator in return statements."""

    def test_direct_return_with_null_coalesce(self):
        """Test: return obj.field ?? 'default'"""
        code = """
obj = {}
return obj.value ?? "default"
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_return_complex_expression_with_null_coalesce(self):
        """Test: return with complex ?? expression"""
        code = """
user = {}
admin = {}
return user.name ?? admin.name ?? "Anonymous"
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Anonymous"'

    def test_return_object_with_null_coalesce_fields(self):
        """Test: return object with ?? in field values"""
        code = """
user = {"age": 25}
result = {
    "name": user.name ?? "Unknown",
    "age": user.age ?? 0,
    "role": user.role ?? "user"
}
return result
"""
        cy = Cy()
        result = cy.run(code)
        import json

        parsed = json.loads(result)
        assert parsed["name"] == "Unknown"
        assert parsed["age"] == 25
        assert parsed["role"] == "user"
