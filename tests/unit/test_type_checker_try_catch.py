"""Unit tests for TryCatchNode type checking.

Tests verify that the TypeChecker correctly detects type errors
inside try, catch, and finally blocks — matching the recursive
checking already done for ConditionalNode and WhileLoopNode.

Regression tests for GitHub issue #14.
"""

import pytest

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.type_checker import TypeChecker, TypeError


def _check(code: str) -> list[TypeError]:
    """Helper: parse, compile, type-check, return errors list."""
    parser = Parser()
    ast = parser.parse_only(code)
    plan = compile_cy_program(ast, source_file="<test>")
    checker = TypeChecker(plan)
    return checker.check_types()


class TestTryCatchBasicValid:
    """Valid try/catch code should produce no type errors."""

    def test_try_catch_simple_valid(self):
        """Simple try/catch with valid types should produce no errors."""
        code = """
        try {
            result = 1 + 2
        } catch (e) {
            result = 0
        }
        return result
        """
        errors = _check(code)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_try_catch_finally_valid(self):
        """Try/catch/finally with all valid types should produce no errors."""
        code = """
        status = "pending"
        try {
            result = 10 + 20
            status = "success"
        } catch (e) {
            status = "error"
        } finally {
            log_msg = "done: " + status
        }
        return status
        """
        errors = _check(code)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_try_with_string_concat_valid(self):
        """String concatenation in try body should be valid."""
        code = """
        try {
            greeting = "Hello" + " " + "World"
        } catch (e) {
            greeting = "error"
        }
        return greeting
        """
        errors = _check(code)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"


class TestTryCatchBodyTypeErrors:
    """Type errors in try body should be detected."""

    def test_type_error_in_try_body(self):
        """Adding number + string in try body should produce a type error."""
        code = """
        try {
            result = 42 + "hello"
        } catch (e) {
            result = "fallback"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, "Type error in try body should be detected"
        assert any("Cannot add" in e.message for e in errors), (
            f"Expected 'Cannot add' error, got: {[e.message for e in errors]}"
        )

    def test_multiple_type_errors_in_try_body(self):
        """Multiple type errors in try body should all be detected."""
        code = """
        try {
            a = 1 + "x"
            b = "y" - 2
        } catch (e) {
            result = "ok"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 2, (
            f"Expected at least 2 errors in try body, got {len(errors)}: {errors}"
        )


class TestCatchBodyTypeErrors:
    """Type errors in catch body should be detected."""

    def test_type_error_in_catch_body(self):
        """Adding number + string in catch body should produce a type error."""
        code = """
        try {
            result = 1 + 2
        } catch (e) {
            result = 10 + "bad"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, "Type error in catch body should be detected"
        assert any("Cannot add" in e.message for e in errors), (
            f"Expected 'Cannot add' error, got: {[e.message for e in errors]}"
        )

    def test_type_error_using_exception_var(self):
        """Arithmetic on exception variable (string) should produce type error."""
        code = """
        try {
            result = 1 + 2
        } catch (e) {
            result = e - 10
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, (
            "Subtracting number from exception var (string) should be detected"
        )


class TestFinallyBodyTypeErrors:
    """Type errors in finally body should be detected."""

    def test_type_error_in_finally_body(self):
        """Adding number + string in finally body should produce a type error."""
        code = """
        try {
            result = 1 + 2
        } catch (e) {
            result = 0
        } finally {
            cleanup = 42 + "text"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, "Type error in finally body should be detected"
        assert any("Cannot add" in e.message for e in errors), (
            f"Expected 'Cannot add' error, got: {[e.message for e in errors]}"
        )


class TestTryCatchNested:
    """Type errors in nested try/catch and other control flow should be found."""

    def test_type_error_in_nested_try(self):
        """Nested try/catch should also have its body type-checked."""
        code = """
        try {
            try {
                result = 1 + "nested_bad"
            } catch (inner) {
                result = "inner fallback"
            }
        } catch (outer) {
            result = "outer fallback"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, "Type error in nested try body should be detected"

    def test_type_error_in_if_inside_try(self):
        """Type errors in conditionals nested inside try should be detected."""
        code = """
        try {
            x = 5
            if (x > 0) {
                bad = x + "text"
            }
        } catch (e) {
            result = "caught"
        }
        return result
        """
        errors = _check(code)
        assert len(errors) >= 1, "Type error inside if inside try should be detected"

    def test_mixed_errors_across_try_catch_finally(self):
        """Errors in all three blocks should be detected."""
        code = """
        try {
            a = 1 + "x"
        } catch (e) {
            b = 2 + "y"
        } finally {
            c = 3 + "z"
        }
        return a
        """
        errors = _check(code)
        assert len(errors) >= 3, (
            f"Expected errors in try + catch + finally, got {len(errors)}: "
            f"{[e.message for e in errors]}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
