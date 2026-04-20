"""Unit tests for indexed access with literal string keys.

Tests that the type checker properly validates literal string keys in
indexed access (e.g., x["key"]) similar to field access (e.g., x.key).
"""

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.type_checker import TypeChecker


class TestIndexedAccessLiteralKeys:
    """Test type checking for indexed access with literal string keys."""

    def test_valid_literal_key(self):
        """Test that accessing existing key with literal string passes."""
        code = """
        x = {"a": 1, "b": 2}
        result = x["a"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Accessing existing key should not produce errors"

    def test_invalid_literal_key(self):
        """Test that accessing non-existent key with literal string produces error."""
        code = """
        x = {"a": 1, "b": 2}
        result = x["missing"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Accessing non-existent key should produce error"
        assert "missing" in errors[0].message.lower()
        assert (
            "not found" in errors[0].message.lower()
            or "available" in errors[0].message.lower()
        )

    def test_variable_key_no_compile_time_check(self):
        """Test that variable keys are not checked at compile-time."""
        code = """
        x = {"a": 1, "b": 2}
        key = "missing"
        result = x[key]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        # Variable keys cannot be checked at compile-time
        assert len(errors) == 0, "Variable keys should not produce compile-time errors"

    def test_consistency_with_field_access(self):
        """Test that x['key'] behaves same as x.key for literal keys."""
        code_field = """
        x = {"a": 1, "b": 2}
        result = x.missing
        return result
        """

        code_indexed = """
        x = {"a": 1, "b": 2}
        result = x["missing"]
        return result
        """

        # Test field access
        parser1 = Parser()
        ast1 = parser1.parse_only(code_field)
        plan1 = compile_cy_program(ast1, source_file="<test>")
        checker1 = TypeChecker(plan1)
        errors1 = checker1.check_types()

        # Test indexed access
        parser2 = Parser()
        ast2 = parser2.parse_only(code_indexed)
        plan2 = compile_cy_program(ast2, source_file="<test>")
        checker2 = TypeChecker(plan2)
        errors2 = checker2.check_types()

        # Both should produce errors
        assert len(errors1) == 1, "Field access should produce error"
        assert len(errors2) == 1, "Indexed access should produce error"

        # Both should mention the missing key
        assert "missing" in errors1[0].message.lower()
        assert "missing" in errors2[0].message.lower()

    def test_multiple_literal_keys(self):
        """Test accessing multiple literal keys."""
        code = """
        x = {"a": 1, "b": 2}
        val1 = x["a"]
        val2 = x["b"]
        val3 = x["c"]
        return val1
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        # Should only error on the missing key "c"
        assert len(errors) == 1, "Should produce error for missing key 'c'"
        assert "c" in errors[0].message.lower()

    def test_nested_object_literal_keys(self):
        """Test nested object access with literal keys."""
        code = """
        x = {"outer": {"inner": 42}}
        result = x["outer"]["inner"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Nested valid access should not produce errors"

    def test_nested_object_literal_keys_invalid(self):
        """Test nested object access with invalid literal key."""
        code = """
        x = {"outer": {"inner": 42}}
        result = x["outer"]["missing"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Should produce error for missing nested key"
        assert "missing" in errors[0].message.lower()

    def test_expression_key_not_checked(self):
        """Test that expression keys (not literals) are not checked."""
        code = """
        x = {"ab": 1}
        result = x["a" + "b"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        # Expression keys are not literals, so not checked
        assert len(errors) == 0, "Expression keys should not be checked at compile-time"

    def test_available_keys_in_error_message(self):
        """Test that error message shows available keys."""
        code = """
        x = {"alpha": 1, "beta": 2, "gamma": 3}
        result = x["delta"]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1
        error_msg = errors[0].message.lower()

        # Should mention available keys
        assert "alpha" in error_msg or "available" in error_msg
        assert "delta" in error_msg or "not found" in error_msg
