"""
Unit tests for critical bug fixes.

Tests verify that the two critical bugs being fixed are resolved:
1. Bug #1: Tools now return proper types (not Any) in Cy(check_types=True)
2. Bug #2: FQN preservation in _parse_tool_registry() (already fixed, needs testing)

These tests follow TDD - they will FAIL initially with stubs, and PASS after implementation.
"""

import pytest

from cy_language import Cy, analyze_types
from cy_language.type_analysis_api import _parse_tool_registry


class TestBug1ToolsReturnProperTypes:
    """
    Bug #1: Tools return Any type - type checking doesn't validate tool calls.

    CRITICAL: This is the PRIMARY bug we're fixing
    Root cause: compiler.py registers tools WITHOUT extracting type signatures.
    """

    def test_bug1_tools_return_proper_types_not_any(self):
        """
        Verify that native tools like len() now return proper types (number, not Any).

        EXPECTED BEHAVIOR AFTER FIX:
        - len() should have return_type = {"type": "number"}
        - NOT return_type = {} (Any type)

        This test will PASS once build_tool_resolver() is implemented.
        """
        script = """
arr = [1, 2, 3]
size = len(arr)
return size
"""

        # analyze_types should infer that size is a number
        output_schema = analyze_types(script)

        # Bug #1 VERIFICATION: Should be number, not Any ({})
        assert output_schema == {"type": "number"}, (
            f"Bug #1 NOT FIXED: len() returned {output_schema}, expected number type. "
            "Tools are still returning Any type!"
        )

    def test_bug1_tool_arithmetic_type_error_raised(self):
        """
        Verify that type errors involving tool results are now caught.

        THIS IS THE PRIMARY BUG FIX TEST!

        BROKEN BEHAVIOR (before fix):
        - len([1,2,3]) returns Any (empty dict {})
        - Any + string is allowed (no type error)
        - Script passes type checking (WRONG!)

        FIXED BEHAVIOR (after fix):
        - len([1,2,3]) returns {"type": "number"}
        - number + string raises TypeError
        - Script fails type checking (CORRECT!)

        This test currently FAILS due to bug, will PASS after fix.
        """
        script = """
arr = [1, 2, 3]
size = len(arr)
result = size + "text"
return result
"""

        # Bug #1 VERIFICATION: Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        # Verify error message mentions incompatible types
        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg, (
            f"Bug #1 NOT FIXED: Expected type error for number + string, got: {exc_info.value}"
        )

    def test_bug1_cy_check_types_validates_tools(self):
        """
        Verify that Cy(check_types=True) now validates tool calls.

        BROKEN BEHAVIOR: Cy(check_types=True) doesn't catch tool type errors
        FIXED BEHAVIOR: TypeError raised BEFORE execution

        This test will FAIL with stubs (tools return Any), PASS after fix.
        """
        cy = Cy(check_types=True)

        script = """
arr = [1, 2, 3]
size = len(arr)
result = size + "text"
return result
"""

        # Bug #1 VERIFICATION: Should raise TypeError during type checking
        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_bug1_multiple_tool_calls_validated(self):
        """
        Verify multiple tool calls in same script are all validated.

        Tests that ALL tools (len, str, int) have proper type signatures,
        not just one of them.
        """
        script = """
arr = [1, 2, 3]
count = len(arr)
text = str(count)
result = text + 100
return result
"""

        # Should raise TypeError: string + number
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_bug1_valid_tool_usage_passes(self):
        """
        Verify that VALID tool usage still passes type checking.

        Important: Bug fix shouldn't break correct code!
        """
        script = """
arr = [1, 2, 3]
count = len(arr)
result = count * 2
return result
"""

        # Should NOT raise - this is valid (number * number)
        output_schema = analyze_types(script)

        # Should infer number type correctly
        assert output_schema == {"type": "number"}


class TestBug2FQNPreservation:
    """
    Bug #2: FQN corruption in _parse_tool_registry().

    Root cause: _parse_tool_registry() blindly prepends "custom::" to ALL tool names,
    corrupting FQNs like "app::x::y" into "custom::app::x::y".

    FIX ALREADY IMPLEMENTED: Check if tool_name contains "::", use as-is if yes.
    These tests VALIDATE the fix works correctly.
    """

    def test_bug2_app_tool_fqn_preserved(self):
        """
        Verify app tool FQNs like app::virustotal::ip_reputation are NOT corrupted.

        BROKEN BEHAVIOR: app::x::y becomes custom::app::x::y
        FIXED BEHAVIOR: app::x::y stays app::x::y

        Fix already implemented, this test validates it works.
        """
        tool_registry = {
            "app::virustotal::ip_reputation": {
                "parameters": {"ip": {"type": "string"}},
                "return_type": {
                    "type": "object",
                    "properties": {"score": {"type": "number"}},
                },
            }
        }

        signatures = _parse_tool_registry(tool_registry)

        # Bug #2 VERIFICATION: FQN should be preserved exactly
        fqns = {sig.fqn for sig in signatures}
        assert "app::virustotal::ip_reputation" in fqns, (
            f"Bug #2 NOT FIXED: app FQN corrupted. Found FQNs: {fqns}"
        )

        # Should NOT have corrupted FQN
        assert "custom::app::virustotal::ip_reputation" not in fqns, (
            "Bug #2 NOT FIXED: FQN was corrupted with custom:: prefix"
        )

    def test_bug2_mcp_tool_fqn_preserved(self):
        """Verify MCP tool FQNs are preserved."""
        tool_registry = {
            "mcp::server::tool": {"parameters": {}, "return_type": {"type": "string"}}
        }

        signatures = _parse_tool_registry(tool_registry)

        fqns = {sig.fqn for sig in signatures}
        assert "mcp::server::tool" in fqns
        assert "custom::mcp::server::tool" not in fqns

    def test_bug2_multiple_namespaces_preserved(self):
        """Verify mixed namespaces (app, mcp, native) all preserved correctly."""
        tool_registry = {
            "app::integration::action": {
                "parameters": {},
                "return_type": {"type": "object"},
            },
            "mcp::service::method": {
                "parameters": {},
                "return_type": {"type": "string"},
            },
            "native::tools::custom_func": {
                "parameters": {},
                "return_type": {"type": "number"},
            },
        }

        signatures = _parse_tool_registry(tool_registry)

        fqns = {sig.fqn for sig in signatures}

        # All FQNs should be preserved exactly
        assert "app::integration::action" in fqns
        assert "mcp::service::method" in fqns
        assert "native::tools::custom_func" in fqns

        # None should be corrupted with custom:: prefix
        corrupted_fqns = [fqn for fqn in fqns if fqn.startswith("custom::")]
        assert len(corrupted_fqns) == 0, f"Found corrupted FQNs: {corrupted_fqns}"

    def test_bug2_arc_namespace_preserved(self):
        """Verify arc:: namespace is also preserved."""
        tool_registry = {
            "arc::archetype::task": {
                "parameters": {},
                "return_type": {"type": "object"},
            }
        }

        signatures = _parse_tool_registry(tool_registry)

        fqns = {sig.fqn for sig in signatures}
        assert "arc::archetype::task" in fqns
        assert "custom::arc::archetype::task" not in fqns
