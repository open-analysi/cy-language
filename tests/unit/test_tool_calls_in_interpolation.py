"""Comprehensive tests for tool calls inside string interpolation.

This test suite verifies that function calls work correctly inside ${...} expressions,
both at runtime and during type checking.

Bug context: Previously, the InterpolationExpressionParser had stub implementations
that didn't parse function arguments, causing "missing required parameter" errors
during type checking. Fixed by switching to UnifiedInterpolationParser.
"""

import pytest

from cy_language import Cy
from cy_language.type_analysis_api import analyze_types


class TestToolCallsInInterpolationRuntime:
    """Test that tool calls execute correctly inside interpolation at runtime."""

    def test_len_in_interpolation(self):
        """Verify len() works inside interpolation."""
        script = """
items = [1, 2, 3]
msg = "Total: ${len(items)}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Total: 3" in result

    def test_uppercase_in_interpolation(self):
        """Verify uppercase() works inside interpolation."""
        script = """
name = "alice"
msg = "Hello ${uppercase(name)}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Hello ALICE" in result

    def test_multiple_tool_calls_in_interpolation(self):
        """Verify multiple tool calls in one interpolation."""
        script = """
items = ["hello", "world"]
msg = "Count: ${len(items)}, First: ${uppercase(items[0])}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Count: 2" in result
        assert "HELLO" in result

    def test_nested_tool_calls_in_interpolation(self):
        """Verify nested tool calls work in interpolation."""
        script = """
name = "alice"
msg = "Length: ${len(uppercase(name))}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Length: 5" in result

    def test_tool_call_with_field_access_in_interpolation(self):
        """Verify tool calls with field access work in interpolation."""
        script = """
user = {"name": "Alice"}
msg = "User: ${uppercase(user.name)}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "User: ALICE" in result

    def test_tool_call_with_indexed_access_in_interpolation(self):
        """Verify tool calls with indexed access work in interpolation."""
        script = """
users = [{"name": "Alice"}, {"name": "Bob"}]
msg = "First: ${uppercase(users[0]['name'])}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "First: ALICE" in result

    def test_multiline_interpolation_with_tool_calls(self):
        """Verify tool calls work in multiline strings."""
        script = """
member_of = ["Group1", "Group2", "Group3"]
sam_account = "user123"
privilege_json = '{"admin": true}'

assessment_prompt = "Username: ${sam_account}\\nTotal Groups: ${len(member_of)}\\nPrivilege: ${privilege_json}"

return assessment_prompt
"""
        cy = Cy()
        result = cy.run(script)
        import json

        parsed = json.loads(result)
        assert "Username: user123" in parsed
        assert "Total Groups: 3" in parsed
        assert 'Privilege: {"admin": true}' in parsed


class TestToolCallsInInterpolationTypeChecking:
    """Test that tool calls type-check correctly inside interpolation."""

    def test_len_type_checking(self):
        """Verify len() type checks correctly in interpolation."""
        script = """
items = [1, 2, 3]
msg = "Total: ${len(items)}"
return msg
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"

    def test_uppercase_type_checking(self):
        """Verify uppercase() type checks correctly in interpolation."""
        script = """
name = "alice"
msg = "Hello ${uppercase(name)}"
return msg
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"

    def test_multiple_tool_calls_type_checking(self):
        """Verify multiple tool calls type check correctly.

        Indexed access returns nullable types, so use ?? operator.
        """
        script = """
items = ["hello", "world"]
msg = "Count: ${len(items)}, First: ${uppercase(items[0] ?? '')}"
return msg
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"

    def test_tool_call_with_wrong_argument_type(self):
        """Verify type errors are caught for wrong argument types."""
        script = """
number = 42
msg = "Uppercase: ${uppercase(number)}"
return msg
"""
        # uppercase expects string, but number is int
        with pytest.raises(TypeError) as exc_info:
            analyze_types(code=script)
        assert "parameter 'text' expects string" in str(exc_info.value)

    def test_tool_call_with_undefined_variable(self):
        """Verify undefined variables are now caught at compile time."""
        script = """
msg = "Length: ${len(undefined_var)}"
return msg
"""
        # Undefined variables are now caught at compile time
        with pytest.raises(TypeError) as exc_info:
            analyze_types(code=script)
        assert "undefined_var" in str(exc_info.value).lower()

    def test_nested_tool_calls_type_checking(self):
        """Verify nested tool calls type check correctly."""
        script = """
name = "alice"
msg = "Length: ${len(uppercase(name))}"
return msg
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"

    def test_multiline_with_tool_calls_type_checking(self):
        """Verify multiline strings with tool calls type check correctly."""
        script = """
member_of = ["Group1", "Group2"]
sam_account = "user123"

assessment_prompt = "Username: ${sam_account}\\nTotal Groups: ${len(member_of)}"
return assessment_prompt
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"


class TestToolCallsWithArithmetic:
    """Test tool calls combined with arithmetic expressions in interpolation."""

    def test_len_plus_number(self):
        """Verify len() + number works in interpolation."""
        script = """
items = [1, 2, 3]
msg = "Total plus one: ${len(items) + 1}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Total plus one: 4" in result

    def test_len_multiply(self):
        """Verify len() * number works in interpolation."""
        script = """
items = [1, 2]
msg = "Doubled: ${len(items) * 2}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Doubled: 4" in result

    def test_arithmetic_type_checking(self):
        """Verify arithmetic with tool calls type checks correctly."""
        script = """
items = [1, 2, 3]
msg = "Result: ${len(items) + 10}"
return msg
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_tool_call_with_empty_list(self):
        """Verify len() works with empty list in interpolation."""
        script = """
items = []
msg = "Count: ${len(items)}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Count: 0" in result

    def test_tool_call_with_string_literal(self):
        """Verify tool calls work with string literals in interpolation."""
        script = """
msg = "Upper: ${uppercase('hello')}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "Upper: HELLO" in result

    def test_multiple_interpolations_same_line(self):
        """Verify multiple ${...} expressions on same line."""
        script = """
items = [1, 2, 3]
name = "test"
msg = "${len(items)} items for ${uppercase(name)}"
return msg
"""
        cy = Cy()
        result = cy.run(script)
        assert "3 items for TEST" in result

    def test_tool_call_in_dict_value(self):
        """Verify tool calls work in dict values with interpolation."""
        script = """
items = [1, 2, 3]
result = {"count": "Total: ${len(items)}"}
return result["count"]
"""
        cy = Cy()
        result = cy.run(script)
        assert "Total: 3" in result


class TestRegressionUserExample:
    """Test the exact example from the user's bug report."""

    def test_ad_ldap_user_check_example(self):
        """Verify the user's exact use case works."""
        script = """
member_of = ["Domain Users", "Administrators", "Remote Desktop Users"]
sam_account = "john.doe"
privilege_json = '{"privileged": true, "admin_groups": 1}'

assessment_prompt = "Username: ${sam_account}\\nTotal Groups: ${len(member_of)}\\nPrivilege Analysis: ${privilege_json}"

return assessment_prompt
"""
        cy = Cy()
        result = cy.run(script)

        assert "Username: john.doe" in result
        assert "Total Groups: 3" in result
        assert "Privilege Analysis:" in result
        assert "privileged" in result

    def test_ad_ldap_type_checking(self):
        """Verify the user's example type checks correctly."""
        script = """
member_of = ["Domain Users", "Administrators"]
sam_account = "john.doe"
privilege_json = '{"privileged": true}'

assessment_prompt = "Username: ${sam_account}\\nTotal Groups: ${len(member_of)}\\nPrivilege: ${privilege_json}"

return assessment_prompt
"""
        result = analyze_types(code=script)
        assert result["type"] == "string"
