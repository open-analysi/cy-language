"""Tests for correct error classification and suggestion quality.

Regression suite: a 429 API error was misreported as ToolNotFoundError with
a misleading "Missing closing parenthesis ')'" suggestion.  These tests
emulate many different failure modes to verify:

1. Error type classification — tool runtime failures → ToolInvocationError
2. Suggestion suppression — runtime errors don't get syntax suggestions
3. Keyword false positives — error messages containing Cy-reserved words
4. Async tool errors — same correctness guarantees
5. Error message preservation — original exception info is carried through
6. Enhanced error integration — ErrorContext enhances without misleading suggestions
"""

import pytest

from cy_language import Cy
from cy_language.error_context import ErrorContext
from cy_language.errors import (
    ToolInvocationError,
    ToolNotFoundError,
)

# ============================================================================
# Helpers
# ============================================================================


def _run(program: str, tools: dict, *, enhanced: bool = False) -> str:
    """Run a Cy program with the given tools.  Returns the result string."""
    cy = Cy(tools=tools)
    cy.show_enhanced_errors = enhanced
    return cy.run(program)


def _run_expect_invocation_error(
    program: str, tools: dict, *, enhanced: bool = False
) -> ToolInvocationError:
    """Run and assert a ToolInvocationError is raised.  Returns the error."""
    cy = Cy(tools=tools)
    cy.show_enhanced_errors = enhanced
    with pytest.raises(ToolInvocationError) as exc_info:
        cy.run(program)
    return exc_info.value


# ============================================================================
# 1. Error type classification — various Python exceptions → ToolInvocationError
# ============================================================================


class TestErrorTypeClassification:
    """Every kind of exception a tool can raise must surface as
    ToolInvocationError, never ToolNotFoundError."""

    SIMPLE_PROGRAM = "result = boom()\nreturn result"

    @pytest.mark.parametrize(
        ("exc_class", "exc_msg"),
        [
            (TypeError, "expected str, got int"),
            (KeyError, "missing_key"),
            (IndexError, "list index out of range"),
            (ValueError, "invalid literal for int()"),
            (ConnectionError, "Connection refused"),
            (TimeoutError, "Read timed out after 30s"),
            (RuntimeError, "Event loop is closed"),
            (OSError, "No such file or directory"),
            (PermissionError, "Permission denied: /etc/shadow"),
            (IOError, "Disk quota exceeded"),
            (AttributeError, "'NoneType' object has no attribute 'status'"),
            (ZeroDivisionError, "division by zero"),
            (StopIteration, "iterator exhausted"),
            (UnicodeDecodeError, ("utf-8", b"\x80", 0, 1, "invalid start byte")),
            (NotImplementedError, "subclass must override process()"),
            (OverflowError, "math range error"),
        ],
        ids=lambda p: p.__name__ if isinstance(p, type) else str(p)[:30],
    )
    def test_tool_exception_becomes_invocation_error(self, exc_class, exc_msg):
        """Tool raising <exc_class> → ToolInvocationError."""

        def boom():
            if isinstance(exc_msg, tuple):
                raise exc_class(*exc_msg)
            raise exc_class(exc_msg)

        err = _run_expect_invocation_error(self.SIMPLE_PROGRAM, {"boom": boom})
        assert not isinstance(err, ToolNotFoundError)

    def test_tool_exception_preserves_message(self):
        """Original exception message is embedded in ToolInvocationError."""

        def boom():
            raise ConnectionError("ECONNREFUSED 10.0.0.1:443")

        err = _run_expect_invocation_error(self.SIMPLE_PROGRAM, {"boom": boom})
        assert "ECONNREFUSED" in str(err)
        assert "10.0.0.1:443" in str(err)

    def test_tool_exception_includes_tool_name(self):
        """Error message includes the failing tool's FQN."""

        def boom():
            raise RuntimeError("kaboom")

        err = _run_expect_invocation_error(self.SIMPLE_PROGRAM, {"boom": boom})
        assert "boom" in str(err)

    def test_tool_exception_has_line_and_col(self):
        """ToolInvocationError carries line/column of the call site."""

        def boom():
            raise RuntimeError("kaboom")

        err = _run_expect_invocation_error(self.SIMPLE_PROGRAM, {"boom": boom})
        assert err.line is not None
        assert err.col is not None


# ============================================================================
# 2. Async tool errors
# ============================================================================


class TestAsyncToolErrors:
    """Async (coroutine) tools that raise must also produce
    ToolInvocationError."""

    def test_async_tool_exception(self):
        """Async tool raising → ToolInvocationError."""

        async def async_boom():
            raise ConnectionError("upstream timeout")

        err = _run_expect_invocation_error(
            "result = async_boom()\nreturn result",
            {"async_boom": async_boom},
        )
        assert "upstream timeout" in str(err)
        assert not isinstance(err, ToolNotFoundError)

    def test_async_tool_api_quota_error(self):
        """Emulate the exact 429 scenario from the original bug report."""

        async def llm_run(prompt):
            raise Exception(
                "Error code: 429 - {'error': {'message': 'You exceeded your "
                "current quota', 'type': 'insufficient_quota'}}"
            )

        err = _run_expect_invocation_error(
            'result = llm_run(prompt="hello")\nreturn result',
            {"llm_run": llm_run},
        )
        assert "429" in str(err)
        assert "quota" in str(err).lower()


# ============================================================================
# 3. Suggestion suppression — runtime errors must NOT get syntax suggestions
# ============================================================================


class TestNoSyntaxSuggestionsOnRuntimeErrors:
    """When a tool fails at runtime the suggestion engine must not produce
    syntax-level hints (bracket mismatches, semicolons, etc.) based on the
    source line of the call site."""

    def _get_suggestion(self, program: str, tools: dict) -> str | None:
        """Run with enhanced errors ON and extract the _suggestion attribute."""
        cy = Cy(tools=tools)
        cy.show_enhanced_errors = True
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run(program)
        return getattr(exc_info.value, "_suggestion", None)

    def test_multiline_call_no_paren_suggestion(self):
        """Opening paren on one line, closing on another → no bracket hint."""

        def failing(prompt):
            raise Exception("API error")

        suggestion = self._get_suggestion(
            'result = failing(\n    prompt="hello"\n)\nreturn result',
            {"failing": failing},
        )
        assert suggestion is None or "parenthesis" not in suggestion.lower()

    def test_dict_arg_no_brace_suggestion(self):
        """Tool call with dict literal → no brace mismatch hint."""

        def failing(data):
            raise Exception("bad data")

        suggestion = self._get_suggestion(
            'result = failing({"key": "val"})\nreturn result',
            {"failing": failing},
        )
        # The dict literal has balanced braces, so this shouldn't fire anyway,
        # but even if the heuristic miscounts, runtime errors shouldn't trigger it.
        assert suggestion is None or "brace" not in suggestion.lower()

    def test_list_arg_no_bracket_suggestion(self):
        """Tool call with list literal spread over lines → no bracket hint."""

        def failing(items):
            raise Exception("processing error")

        suggestion = self._get_suggestion(
            "result = failing([\n    1, 2, 3\n])\nreturn result",
            {"failing": failing},
        )
        assert suggestion is None or "bracket" not in suggestion.lower()

    def test_no_semicolon_suggestion(self):
        """Even if source line somehow had a semicolon, no hint for runtime error.

        Cy would normally reject semicolons at parse time, but this tests
        the suggestion engine path directly via ErrorContext.
        """

        def failing():
            raise Exception("oops")

        # We test the suggestion engine directly since the parser would reject ';'
        source = "result = failing();\nreturn result"
        ctx = ErrorContext(source_code=source, use_color=False)
        suggestion = ctx._get_suggestion_for_error(
            "Tool 'failing' failed: oops", line=1, is_runtime=True
        )
        assert suggestion is None or "semicolon" not in suggestion.lower()

    def test_no_else_if_suggestion(self):
        """Source line containing 'else if' shouldn't trigger hint for runtime error."""

        source = "x = my_tool()\nreturn x"
        ctx = ErrorContext(source_code=source, use_color=False)
        # Fake a source where error line has 'else if' (unlikely but tests the gate)
        source_with_else_if = "} else if (x) {\nresult = boom()\n}"
        ctx2 = ErrorContext(source_code=source_with_else_if, use_color=False)
        suggestion = ctx2._get_suggestion_for_error(
            "Tool 'boom' failed: timeout", line=1, is_runtime=True
        )
        assert suggestion is None or "elif" not in suggestion.lower()

    def test_no_spaces_in_varname_suggestion(self):
        """'Variable names cannot contain spaces' should not trigger for runtime errors."""
        source = "result = my_tool(a, b)\nreturn result"
        ctx = ErrorContext(source_code=source, use_color=False)
        suggestion = ctx._get_suggestion_for_error(
            "Tool 'my_tool' failed: bad arg", line=1, is_runtime=True
        )
        assert suggestion is None or "spaces" not in suggestion.lower()


# ============================================================================
# 4. Keyword false positives in error messages
# ============================================================================


class TestKeywordFalsePositives:
    """Tool error messages can contain words like 'break', 'continue', 'range'
    that happen to be Cy-reserved words.  The suggestion engine must not
    produce Cy-syntax suggestions for these."""

    def _get_suggestion_for_runtime_error(
        self, error_msg: str, source_line: str = "result = my_tool()"
    ) -> str | None:
        """Get suggestion via ErrorContext for a runtime-style error."""
        ctx = ErrorContext(source_code=source_line, use_color=False)
        return ctx._get_suggestion_for_error(error_msg, line=1, is_runtime=True)

    def test_break_in_error_message(self):
        """Error 'circuit breaker tripped' must not suggest 'break doesn't exist'."""
        suggestion = self._get_suggestion_for_runtime_error(
            "Tool 'my_tool' failed: circuit breaker tripped"
        )
        assert (
            suggestion is None
            or "break" not in suggestion.lower()
            or "doesn't exist" not in suggestion.lower()
        )

    def test_continue_in_error_message(self):
        """Error 'cannot continue processing' must not suggest 'continue doesn't exist'."""
        suggestion = self._get_suggestion_for_runtime_error(
            "Tool 'my_tool' failed: cannot continue processing"
        )
        assert (
            suggestion is None
            or "continue" not in suggestion.lower()
            or "doesn't exist" not in suggestion.lower()
        )

    def test_range_in_error_message(self):
        """Error 'value out of range(0, 100)' must not suggest 'range() doesn't exist'."""
        suggestion = self._get_suggestion_for_runtime_error(
            "Tool 'my_tool' failed: value out of range(0, 100)"
        )
        assert (
            suggestion is None
            or "range" not in suggestion.lower()
            or "doesn't exist" not in suggestion.lower()
        )

    def test_print_in_error_message(self):
        """Error containing 'print' must not suggest 'print() is not available'."""
        suggestion = self._get_suggestion_for_runtime_error(
            "Tool 'print_report' failed: printer not found"
        )
        assert suggestion is None or "not available" not in suggestion.lower()

    def test_in_keyword_in_source_line(self):
        """Source line with 'in' (e.g. for-in) must not suggest 'in operator not supported'
        when the error is a runtime ToolInvocationError."""
        source = "for (item in items) {\n    result = process(item)\n}"
        ctx = ErrorContext(source_code=source, use_color=False)
        suggestion = ctx._get_suggestion_for_error(
            "Tool 'process' failed: invalid item", line=1, is_runtime=True
        )
        assert suggestion is None or "'in' operator" not in suggestion


class TestNameErrorKeywordFalsePositives:
    """Variable names containing Cy-reserved keywords as substrings must not
    trigger keyword suggestions on NameError."""

    def _get_suggestion_for_name_error(self, var_name: str) -> str | None:
        """Simulate a NameError for an undefined variable and get the suggestion."""
        source = f"x = {var_name}\nreturn x"
        ctx = ErrorContext(source_code=source, use_color=False)
        return ctx._get_suggestion_for_error(
            f"Variable '{var_name}' is not defined", line=1, is_runtime=False
        )

    def test_variable_named_should_continue(self):
        """'should_continue' must not suggest 'continue doesn't exist'."""
        suggestion = self._get_suggestion_for_name_error("should_continue")
        assert suggestion is None or "doesn't exist" not in suggestion

    def test_variable_named_break_flag(self):
        """'break_flag' must not suggest 'break doesn't exist'."""
        suggestion = self._get_suggestion_for_name_error("break_flag")
        assert suggestion is None or "doesn't exist" not in suggestion

    def test_variable_named_loop_breaker(self):
        """'loop_breaker' must not suggest 'break doesn't exist'."""
        suggestion = self._get_suggestion_for_name_error("loop_breaker")
        assert suggestion is None or "doesn't exist" not in suggestion

    def test_variable_named_continue_loop(self):
        """'continue_loop' must not suggest 'continue doesn't exist'."""
        suggestion = self._get_suggestion_for_name_error("continue_loop")
        assert suggestion is None or "doesn't exist" not in suggestion

    def test_variable_named_range_start(self):
        """'range_start' (no parens) should not match range( check anyway."""
        suggestion = self._get_suggestion_for_name_error("range_start")
        assert suggestion is None or "doesn't exist" not in suggestion


# ============================================================================
# 5. Enhanced error formatting integration
# ============================================================================


class TestEnhancedErrorFormatting:
    """ToolInvocationError should get proper enhanced formatting without
    syntax-specific artifacts."""

    def test_error_type_header_says_invocation(self):
        """Enhanced format header shows 'ToolInvocationError', not 'ToolNotFoundError'."""

        def boom():
            raise RuntimeError("engine failure")

        cy = Cy(tools={"boom": boom})
        cy.show_enhanced_errors = True
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run("result = boom()\nreturn result")
        formatted = str(exc_info.value)
        assert "ToolInvocationError" in formatted

    def test_no_cleaned_message_for_runtime_error(self):
        """ToolInvocationError should NOT get _cleaned_message (that's for parse errors)."""

        def boom():
            raise RuntimeError("engine failure")

        cy = Cy(tools={"boom": boom})
        cy.show_enhanced_errors = True
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run("result = boom()\nreturn result")
        assert not hasattr(exc_info.value, "_cleaned_message")

    def test_source_context_attached(self):
        """Enhanced error has source_code attached for display."""

        def boom():
            raise RuntimeError("engine failure")

        cy = Cy(tools={"boom": boom})
        cy.show_enhanced_errors = True
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run("result = boom()\nreturn result")
        assert hasattr(exc_info.value, "source_code")
        assert "boom()" in exc_info.value.source_code


# ============================================================================
# 6. ToolNotFoundError is still correct for genuinely missing tools
# ============================================================================


class TestToolNotFoundStillWorks:
    """Ensure the fix didn't break legitimate ToolNotFoundError cases."""

    def test_missing_tool_raises_not_found(self):
        """Calling a tool that doesn't exist → ToolNotFoundError (or ToolResolutionError)."""
        from cy_language.errors import ToolResolutionError

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises((ToolNotFoundError, ToolResolutionError)):
            cy.run("result = nonexistent_tool()\nreturn result")

    def test_tool_found_but_fails_is_not_not_found(self):
        """A tool that exists but raises is never ToolNotFoundError."""

        def real_tool():
            raise Exception("internal error")

        cy = Cy(tools={"real_tool": real_tool})
        cy.show_enhanced_errors = False
        with pytest.raises(ToolInvocationError):
            cy.run("result = real_tool()\nreturn result")
        # Verify it's not the wrong subclass
        with pytest.raises(ToolInvocationError) as exc_info:
            cy.run("result = real_tool()\nreturn result")
        assert not isinstance(exc_info.value, ToolNotFoundError)


# ============================================================================
# 7. Edge cases: nested errors, chained tools, error in second tool
# ============================================================================


class TestEdgeCases:
    """Edge cases around tool error handling."""

    def test_tool_raising_cy_error_internally_gets_wrapped(self):
        """A user tool that internally raises ToolNotFoundError gets wrapped
        with the correct Cy call-site location, not the tool's internal location."""

        def meta_tool():
            # Simulate a tool that wraps another tool system
            raise ToolNotFoundError("inner tool 'blah' not found", line=999, col=999)

        err = _run_expect_invocation_error(
            "result = meta_tool()\nreturn result", {"meta_tool": meta_tool}
        )
        # Must be wrapped as ToolInvocationError, not raw ToolNotFoundError
        assert not isinstance(err, ToolNotFoundError)
        # Cy call-site location must be preserved (line 1), not the inner 999
        assert err.line is not None
        assert err.line != 999

    def test_nested_cy_execution_preserves_inner_location(self):
        """A user tool running a nested Cy program that fails
        should preserve the inner error's location, not re-wrap it."""
        from cy_language.errors import ToolResolutionError

        def meta_tool():
            from cy_language import Cy as InnerCy

            inner = InnerCy()
            inner.show_enhanced_errors = False
            inner.run("x = nonexistent()\nreturn x")

        # The inner error should propagate — not get re-wrapped with outer location
        with pytest.raises(
            (ToolInvocationError, ToolNotFoundError, ToolResolutionError)
        ) as exc_info:
            _run(
                "result = meta_tool()\nreturn result",
                {"meta_tool": meta_tool},
                enhanced=False,
            )
        err = exc_info.value
        # The inner error must preserve its original type from the inner Cy,
        # not be re-wrapped as a generic ToolInvocationError with
        # "Tool 'meta_tool' failed: ..." message.
        assert "meta_tool" not in getattr(err, "message", str(err)), (
            f"Inner error was re-wrapped by outer call-site: {err}"
        )

    def test_error_in_second_tool_call(self):
        """First tool succeeds, second fails → error points to second call."""

        def ok_tool():
            return "fine"

        def bad_tool(x):
            raise ValueError("nope")

        program = "a = ok_tool()\nb = bad_tool(a)\nreturn b"
        err = _run_expect_invocation_error(
            program, {"ok_tool": ok_tool, "bad_tool": bad_tool}
        )
        assert "bad_tool" in str(err) or "nope" in str(err)

    def test_tool_returns_none_no_error(self):
        """Tool returning None is valid, not an error."""

        def returns_none():
            return None

        result = _run("x = returns_none()\nreturn x", {"returns_none": returns_none})
        assert result == "null"

    def test_tool_returns_empty_string_no_error(self):
        """Tool returning empty string is valid."""

        def returns_empty():
            return ""

        result = _run("x = returns_empty()\nreturn x", {"returns_empty": returns_empty})
        assert result == '""'

    def test_error_message_with_newlines(self):
        """Exception messages with newlines are handled gracefully."""

        def boom():
            raise Exception("line1\nline2\nline3")

        err = _run_expect_invocation_error(
            "result = boom()\nreturn result", {"boom": boom}
        )
        assert "line1" in str(err)

    def test_error_message_with_special_chars(self):
        """Exception messages with special characters don't break formatting."""

        def boom():
            raise Exception("failed: {'key': 'val', \"nested\": [1,2,3]}")

        err = _run_expect_invocation_error(
            "result = boom()\nreturn result", {"boom": boom}
        )
        assert "failed" in str(err)
