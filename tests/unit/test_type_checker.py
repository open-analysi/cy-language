"""Unit tests for the TypeChecker class.

These tests verify that the type checking system correctly identifies
type errors in Cy programs. All tests are expected to fail initially
(TDD approach) since TypeChecker methods are stubbed.
"""

import pytest

from cy_language import Cy
from cy_language.compiler import CompilerError, compile_cy_program
from cy_language.parser import Parser
from cy_language.type_checker import TypeChecker, TypeError


class TestTypeCheckerArithmetic:
    """Test type checking for arithmetic operations."""

    def test_addition_number_plus_number_valid(self):
        """Test that adding two numbers is valid."""
        code = """
        a = 5
        b = 3
        result = a + b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Adding two numbers should not produce type errors"

    def test_addition_string_plus_string_valid(self):
        """Test that adding two strings is valid."""
        code = """
        a = "Hello"
        b = "World"
        result = a + b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Adding two strings should not produce type errors"

    def test_addition_number_plus_string_invalid(self):
        """Test that adding number and string produces type error."""
        code = """
        age = 25
        name = "Alice"
        result = age + name
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, (
            "Adding number and string should produce exactly one error"
        )
        assert "Cannot add" in errors[0].message
        assert "number" in errors[0].message.lower()
        assert "string" in errors[0].message.lower()
        assert errors[0].line > 0, "Error should have line number"

    def test_subtraction_number_minus_number_valid(self):
        """Test that subtracting numbers is valid."""
        code = """
        a = 10
        b = 3
        result = a - b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Subtracting numbers should not produce type errors"

    def test_subtraction_string_minus_string_invalid(self):
        """Test that subtracting strings produces type error."""
        code = """
        a = "hello"
        b = "world"
        result = a - b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Subtracting strings should produce error"
        assert (
            "Cannot subtract" in errors[0].message
            or "subtract" in errors[0].message.lower()
        )

    def test_multiplication_number_times_number_valid(self):
        """Test that multiplying numbers is valid."""
        code = """
        a = 5
        b = 7
        result = a * b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Multiplying numbers should not produce type errors"

    def test_division_number_div_number_valid(self):
        """Test that dividing numbers is valid."""
        code = """
        a = 10
        b = 2
        result = a / b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Dividing numbers should not produce type errors"

    def test_modulo_number_mod_number_valid(self):
        """Test that modulo on numbers is valid."""
        code = """
        a = 10
        b = 3
        result = a % b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Modulo on numbers should not produce type errors"

    def test_mixed_arithmetic_invalid(self):
        """Test that mixed type arithmetic produces errors."""
        code = """
        num = 42
        text = "answer"
        result = num * text
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Mixed type multiplication should produce error"


class TestTypeCheckerComparison:
    """Test type checking for comparison operations."""

    def test_comparison_number_less_than_number_valid(self):
        """Test that comparing numbers with < is valid."""
        code = """
        a = 5
        b = 10
        result = a < b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Comparing numbers with < should be valid"

    def test_comparison_string_less_than_string_valid(self):
        """Test that comparing strings with < is valid."""
        code = """
        a = "apple"
        b = "banana"
        result = a < b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Comparing strings with < should be valid"

    def test_comparison_number_less_than_string_invalid(self):
        """Test that comparing number with string produces error."""
        code = """
        num = 5
        text = "hello"
        result = num < text
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Comparing number with string should produce error"
        assert "compare" in errors[0].message.lower()

    def test_comparison_greater_than_valid(self):
        """Test that > comparison works for numbers."""
        code = """
        a = 10
        b = 5
        result = a > b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Number comparison with > should be valid"

    def test_equality_any_types_valid(self):
        """Test that == works with any types."""
        code = """
        a = 5
        b = "5"
        result = a == b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Equality comparison should work with any types"

    def test_inequality_any_types_valid(self):
        """Test that != works with any types."""
        code = """
        a = 5
        b = "hello"
        result = a != b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Inequality comparison should work with any types"


class TestTypeCheckerInOperator:
    """Test type checking for the 'in' membership operator."""

    def test_in_with_list_valid(self):
        """'in' with a list on the right side is valid."""
        code = """
        result = 1 in [1, 2, 3]
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0

    def test_in_with_number_invalid(self):
        """'in' with a number on the right side should produce error."""
        code = """
        x = 42
        result = 1 in x
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1
        assert "'in' requires" in errors[0].message


class TestTypeCheckerBooleanOps:
    """Test type checking for boolean operations."""

    def test_and_boolean_boolean_valid(self):
        """Test that 'and' with booleans is valid."""
        code = """
        a = true
        b = false
        result = a and b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "'and' with booleans should be valid"

    def test_and_number_number_invalid(self):
        """Test that 'and' with numbers is valid."""
        code = """
        a = 5
        b = 10
        result = a and b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        # 'and' now accepts any types (truthy/falsy semantics)
        assert len(errors) == 0, "'and' with numbers should be valid"

    def test_or_boolean_boolean_valid(self):
        """Test that 'or' with booleans is valid."""
        code = """
        a = true
        b = false
        result = a or b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "'or' with booleans should be valid"

    def test_or_string_string_valid(self):
        """Test that 'or' with strings is valid."""
        code = """
        a = "hello"
        b = "world"
        result = a or b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        # 'or' now accepts any types (truthy/falsy semantics)
        assert len(errors) == 0, "'or' with strings should be valid"

    def test_not_boolean_valid(self):
        """Test that 'not' with boolean is valid."""
        code = """
        a = true
        result = not a
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "'not' with boolean should be valid"

    def test_not_number_invalid(self):
        """Test that 'not' with number produces error."""
        code = """
        a = 42
        result = not a
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "'not' with number should produce error"
        assert "boolean" in errors[0].message.lower()


class TestTypeCheckerFieldAccess:
    """Test type checking for field access operations."""

    def test_field_access_valid_field(self):
        """Test that accessing existing field is valid."""
        code = """
        user = {"name": "Alice", "age": 30}
        name = user.name
        return name
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Accessing existing field should be valid"

    def test_field_access_invalid_field(self):
        """Test that accessing non-existent field produces error."""
        code = """
        user = {"name": "Alice", "age": 30}
        email = user.email
        return email
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Accessing non-existent field should produce error"
        assert (
            "field" in errors[0].message.lower()
            or "not found" in errors[0].message.lower()
        )

    def test_field_access_on_non_object_invalid(self):
        """Test that accessing field on non-object produces error."""
        code = """
        num = 42
        value = num.something
        return value
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Accessing field on number should produce error"

    def test_nested_field_access_valid(self):
        """Test that nested field access works."""
        code = """
        user = {"details": {"name": "Alice"}}
        name = user.details.name
        return name
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Nested field access should be valid"


class TestTypeCheckerIndexedAccess:
    """Test type checking for indexed access operations."""

    def test_array_index_with_number_valid(self):
        """Test that indexing array with number is valid."""
        code = """
        items = ["a", "b", "c"]
        first = items[0]
        return first
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Indexing array with number should be valid"

    def test_array_index_with_string_invalid(self):
        """Test that indexing array with string produces error."""
        code = """
        items = ["a", "b", "c"]
        item = items["key"]
        return item
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Indexing array with string should produce error"
        assert "index" in errors[0].message.lower()

    def test_object_index_with_string_valid(self):
        """Test that indexing object with string is valid."""
        code = """
        user = {"name": "Alice", "age": 30}
        name = user["name"]
        return name
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Indexing object with string should be valid"

    def test_object_index_with_number_invalid(self):
        """Test that indexing object with number produces error."""
        code = """
        user = {"name": "Alice"}
        value = user[0]
        return value
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1, "Indexing object with number should produce error"

    def test_string_index_with_number_valid(self):
        """Test that indexing string with number is valid."""
        code = """
        text = "hello"
        char = text[0]
        return char
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Indexing string with number should be valid"


class TestTypeCheckerConditionals:
    """Test type checking for conditional statements."""

    def test_if_with_boolean_condition_valid(self):
        """Test that if statement with boolean condition is valid."""
        code = """
        is_valid = true
        if (is_valid) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "if with boolean condition should be valid"

    def test_if_with_comparison_condition_valid(self):
        """Test that if statement with comparison is valid."""
        code = """
        age = 25
        if (age > 18) {
            result = "adult"
        } else {
            result = "minor"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "if with comparison should be valid"

    def test_if_with_string_condition_truthy(self):
        """Test that if statement with string condition is valid (truthy/falsy semantics)."""
        code = """
        message = "hello"
        if (message) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, (
            "if with string condition should be valid (truthy/falsy)"
        )

    def test_if_with_number_condition_truthy(self):
        """Test that if statement with number condition is valid (truthy/falsy semantics)."""
        code = """
        count = 5
        if (count) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, (
            "if with number condition should be valid (truthy/falsy)"
        )

    def test_nested_if_conditions_truthy(self):
        """Test that nested if statements with truthy/falsy work."""
        code = """
        age = 25
        country = "US"
        if (age > 18) {
            if (country) {
                result = "adult with country"
            } else {
                result = "adult without country"
            }
        } else {
            result = "minor"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, (
            "Nested if with string condition should be valid (truthy/falsy)"
        )


class TestTypeCheckerWhileLoops:
    """Test type checking for while loop statements."""

    def test_while_with_boolean_condition_valid(self):
        """Test that while loop with boolean condition is valid."""
        code = """
        running = true
        count = 0
        while (running) {
            count = count + 1
            if (count > 5) {
                running = false
            }
        }
        return count
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "while with boolean condition should be valid"

    def test_while_with_comparison_condition_valid(self):
        """Test that while loop with comparison is valid."""
        code = """
        count = 0
        while (count < 10) {
            count = count + 1
        }
        return count
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "while with comparison should be valid"

    def test_while_with_string_condition_truthy(self):
        """Test that while loop with string condition is valid (truthy/falsy semantics)."""
        code = """
        message = "loop"
        while (message) {
            message = ""
        }
        return message
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, (
            "while with string condition should be valid (truthy/falsy)"
        )

    def test_while_loop_body_type_errors(self):
        """Test that type errors in while loop body are detected."""
        code = """
        count = 0
        while (count < 10) {
            result = count + "text"
            count = count + 1
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in loop body should be detected"


class TestTypeCheckerAnyType:
    """Test that Any type ({}) bypasses type checking."""

    def test_any_type_addition(self):
        """Test that Any type allows addition with any type."""
        code = """
        dynamic = input.value
        result = dynamic + 5
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Any type should allow operations with any type"

    def test_any_type_field_access(self):
        """Test that Any type allows field access."""
        code = """
        dynamic = input.data
        value = dynamic.anything
        return value
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Any type should allow field access"

    def test_any_type_in_conditionals(self):
        """Test that Any type bypasses conditional type checks."""
        code = """
        condition = input.flag
        if (condition) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Any type should allow use as condition"


class TestTypeCheckerErrorMessages:
    """Test that error messages are clear and actionable."""

    def test_error_message_has_line_number(self):
        """Test that error messages include line numbers."""
        code = """
        a = 5
        b = "hello"
        result = a + b
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1
        assert errors[0].line > 0, "Error should have valid line number"
        assert errors[0].col >= 0, "Error should have column number"

    def test_error_message_has_type_info(self):
        """Test that error messages include type information."""
        code = """
        result = 42 - "text"
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 1
        # Error message should mention the types involved
        msg = errors[0].message.lower()
        assert "number" in msg or "string" in msg or "42" in str(errors[0].message)

    def test_error_str_format(self):
        """Test that __str__ formats error nicely."""
        error = TypeError(
            message="Cannot add number and string", line=5, col=10, node_type="BinaryOp"
        )

        error_str = str(error)

        assert "Line 5" in error_str
        assert "Col 10" in error_str
        assert "Cannot add number and string" in error_str

    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected together."""
        code = """
        error1 = 5 + "text"
        error2 = "hello" - "world"
        error3 = 42 * true
        return error1
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 2, "Should collect multiple errors"


class TestTypeCheckerToolCalls:
    """Test type checking for tool calls (will be implemented with tool_resolver)."""

    def test_tool_call_correct_types(self):
        """Test that tool call with correct argument types is valid."""

        def greet(name: str) -> str:
            return f"Hello, {name}!"

        cy = Cy(check_types=True, tools={"greet": greet})

        script = """
        result = greet(name="Alice")
        return result
        """

        # Correct type — should not raise
        result = cy.run(script)
        assert "Hello" in result

    def test_tool_call_wrong_argument_type(self):
        """Test that tool call with wrong argument type produces error."""

        def greet(name: str) -> str:
            return f"Hello, {name}!"

        cy = Cy(check_types=True, tools={"greet": greet})

        script = """
        result = greet(name=123)
        return result
        """

        # Passing a number where a string is expected — should raise CompilerError
        with pytest.raises((CompilerError, Exception)):
            cy.run(script)

    def test_tool_call_missing_required_argument(self):
        """Test that tool call missing required argument produces error."""

        def greet(name: str, greeting: str) -> str:
            return f"{greeting}, {name}!"

        cy = Cy(check_types=True, tools={"greet": greet})

        script = """
        result = greet(name="Alice")
        return result
        """

        # Missing required 'greeting' parameter — should raise CompilerError
        with pytest.raises((CompilerError, Exception)):
            cy.run(script)


class TestTypeCheckerEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_empty_program(self):
        """Test that empty program produces no errors."""
        code = """
        return "empty"
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Empty program should produce no errors"

    def test_complex_nested_expressions(self):
        """Test complex nested expressions."""
        code = """
        a = 5
        b = 10
        c = 3
        result = (a + b) * c - (b / a)
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Valid complex expressions should produce no errors"

    def test_type_error_in_nested_expression(self):
        """Test that type error in nested expression is caught."""
        code = """
        a = 5
        b = "text"
        result = (a + 10) * (b - 3)
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in nested expression should be caught"


class TestTypeCheckerIndexedAssign:
    """Test type checking for indexed assignment value expressions."""

    def test_indexed_assign_valid(self):
        """Valid indexed assignment should produce no errors."""
        code = """
        data = {}
        data["key"] = 1 + 2
        return data
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Valid indexed assignment should produce no errors"

    def test_indexed_assign_type_error_in_value(self):
        """Type error in indexed assignment value expression should be caught."""
        code = """
        data = {}
        data["key"] = 1 + "bad"
        return data
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in indexed assign value should be detected"
        assert any("Cannot add" in e.message for e in errors)

    def test_indexed_assign_type_error_in_index_expression(self):
        """Type error in the index expression itself should be caught."""
        code = """
        data = {}
        key = 1 + "bad_key"
        data[key] = "value"
        return data
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in index expression should be detected"
        assert any("Cannot add" in e.message for e in errors)


class TestTypeCheckerFieldAssign:
    """Test type checking for field assignment value expressions."""

    def test_field_assign_valid(self):
        """Valid field assignment should produce no errors."""
        code = """
        data = {}
        data.name = "Alice"
        return data
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Valid field assignment should produce no errors"

    def test_field_assign_type_error_in_value(self):
        """Type error in field assignment value expression should be caught."""
        code = """
        data = {}
        data.result = 1 + "bad"
        return data
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in field assign value should be detected"
        assert any("Cannot add" in e.message for e in errors)


class TestTypeCheckerElifConditions:
    """Test type checking for elif condition expressions."""

    def test_elif_condition_with_nested_type_error(self):
        """Type error in elif condition expression should be caught."""
        code = """
        x = 5
        if (x > 0) {
            result = "positive"
        } elif (x + "bad" > 0) {
            result = "other"
        } else {
            result = "negative"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) >= 1, "Type error in elif condition should be detected"

    def test_elif_condition_valid(self):
        """Valid elif conditions should produce no errors."""
        code = """
        x = 5
        y = 10
        if (x > 0) {
            result = "x positive"
        } elif (y > 0) {
            result = "y positive"
        } else {
            result = "both negative"
        }
        return result
        """
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")

        checker = TypeChecker(plan)
        errors = checker.check_types()

        assert len(errors) == 0, "Valid elif conditions should produce no errors"
