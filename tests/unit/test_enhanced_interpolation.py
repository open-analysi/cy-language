"""
Tests for Enhanced Expression Support in String Interpolation

This test suite verifies that full expressions (function calls, arithmetic, boolean logic)
work correctly inside ${} interpolation patterns while maintaining 100% backward compatibility.

All tests in this file should FAIL during Test Creation Cycle (TDD approach).
They will pass once implementation is complete.
"""

import json

import pytest

from cy_language import Cy
from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.errors import ToolNotFoundError


# Test fixtures for common data
@pytest.fixture
def basic_tools():
    """Provide basic tools for testing."""
    return {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else None,
        "len": lambda x: len(x) if hasattr(x, "__len__") else 0,
        "upper": lambda s: str(s).upper(),
        "concat": lambda *args: "".join(str(arg) for arg in args),
    }


@pytest.fixture
def test_data():
    """Provide test data structures."""
    return {
        "items": ["apple", "banana", "cherry"],
        "scores": {"Alice": 95, "Bob": 87, "Charlie": 92},
        "matrix": [[1, 2], [3, 4], [5, 6]],
        "users": [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
        ],
        "config": {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"enabled": True, "ttl": 3600},
        },
    }


@pytest.fixture
def cy_interpreter(basic_tools, test_data):
    """Create Cy interpreter with tools and test data."""
    interpreter = Cy(tools=basic_tools, variables=test_data)
    interpreter.show_enhanced_errors = False
    return interpreter


# ============================================================================
# 1. BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility:
    """Ensure all existing interpolation patterns continue to work."""

    def test_simple_variable_interpolation(self, cy_interpreter):
        """Test that $var and ${var} patterns work unchanged."""
        program = """
        name = "Alice"
        age = 30
        output = "Name: ${name}, Age: ${age}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Name: Alice, Age: 30"'

    def test_field_access_interpolation(self, cy_interpreter):
        """Test ${object.field} pattern continues to work."""
        program = """
        output = "Database: ${config.database.host}:${config.database.port}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Database: localhost:5432"'

    def test_indexed_access_interpolation(self, cy_interpreter):
        """Test ${arr[0]} and ${dict['key']} patterns."""
        program = """
        output = "First item: ${items[0]}, Alice score: ${scores['Alice']}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"First item: apple, Alice score: 95"'

    def test_format_hints_compatibility(self, cy_interpreter):
        """Test ${data|format} hints still work."""
        program = """
        output = "Items as CSV: ${items|csv}"
        return output
        """
        result = cy_interpreter.run(program)
        # CSV format should produce comma-separated values
        assert "apple,banana,cherry" in result or "apple, banana, cherry" in result

    def test_escape_sequences_unchanged(self, cy_interpreter):
        """Test escape sequences remain functional."""
        program = r"""
        output = "Literal: \${not_interpolated} and \$also_literal"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Literal: ${not_interpolated} and $also_literal"'


# ============================================================================
# 2. FUNCTION CALL TESTS
# ============================================================================


class TestFunctionCalls:
    """Verify function calls work correctly inside interpolation."""

    def test_simple_function_calls(self, cy_interpreter):
        """Test ${func()} with literal arguments."""
        program = """
        output = "Sum: ${add(5, 3)}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Sum: 8"'

    def test_function_with_variable_args(self, cy_interpreter):
        """Test ${func($var1, $var2)} with variables."""
        program = """
        a = 10
        b = 20
        output = "Result: ${add($a, $b)}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Result: 30"'

    def test_len_function_in_interpolation(self, cy_interpreter):
        """Test len() function specifically."""
        program = """
        output = "You have ${len($items)} items"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"You have 3 items"'

    def test_string_function_in_interpolation(self, cy_interpreter):
        """Test string manipulation functions."""
        program = """
        name = "alice"
        output = "Welcome, ${upper($name)}!"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Welcome, ALICE!"'

    def test_nested_function_calls(self, cy_interpreter):
        """Test ${func1(func2(arg))} nested calls."""
        program = """
        text = "hello"
        output = "Length of uppercase: ${len(upper($text))}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Length of uppercase: 5"'


# ============================================================================
# 3. ARITHMETIC EXPRESSION TESTS
# ============================================================================


class TestArithmeticExpressions:
    """Verify arithmetic operations work in interpolation."""

    def test_basic_addition(self, cy_interpreter):
        """Test ${$a + $b} addition."""
        program = """
        a = 5
        b = 3
        output = "Sum: ${$a + $b}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Sum: 8"'

    def test_basic_subtraction(self, cy_interpreter):
        """Test ${$a - $b} subtraction."""
        program = """
        x = 10
        y = 4
        output = "Difference: ${$x - $y}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Difference: 6"'

    def test_multiplication(self, cy_interpreter):
        """Test ${$a * $b} multiplication."""
        program = """
        price = 10
        quantity = 3
        output = "Total: ${$price * $quantity}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Total: 30"'

    def test_division(self, cy_interpreter):
        """Test ${$a / $b} division."""
        program = """
        total = 100
        count = 4
        output = "Average: ${$total / $count}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Average: 25"' or result == '"Average: 25.0"'

    def test_operator_precedence(self, cy_interpreter):
        """Test correct operator precedence."""
        program = """
        a = 2
        b = 3
        c = 4
        output = "Result: ${$a + $b * $c}"
        return output
        """
        result = cy_interpreter.run(program)
        assert (
            result == '"Result: 14"'
        )  # Should be 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20

    def test_parentheses_in_expressions(self, cy_interpreter):
        """Test parentheses for grouping."""
        program = """
        a = 2
        b = 3
        c = 4
        output = "Result: ${($a + $b) * $c}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Result: 20"'  # Should be (2 + 3) * 4 = 20


# ============================================================================
# 4. BOOLEAN EXPRESSION TESTS
# ============================================================================


class TestBooleanExpressions:
    """Verify boolean logic works in interpolation."""

    def test_and_operator(self, cy_interpreter):
        """Test ${$a and $b} operator."""
        program = """
        is_valid = True
        is_active = True
        output = "Both true: ${$is_valid and $is_active}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Both true: True"'

    def test_or_operator(self, cy_interpreter):
        """Test ${$a or $b} operator."""
        program = """
        option1 = False
        option2 = True
        output = "Either true: ${$option1 or $option2}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Either true: True"'

    def test_not_operator(self, cy_interpreter):
        """Test ${not $a} operator."""
        program = """
        is_disabled = False
        output = "Is enabled: ${not $is_disabled}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Is enabled: True"'

    def test_comparison_operators(self, cy_interpreter):
        """Test comparison operators in interpolation."""
        program = """
        score = 85
        output = "Pass: ${$score >= 80}, Excellent: ${$score >= 90}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Pass: True, Excellent: False"'

    def test_ternary_style_expression(self, cy_interpreter):
        """Test conditional expressions.

        Cy now supports Python-style short-circuit evaluation where
        'and' returns the last value if all are truthy, and 'or' returns
        the first truthy value. This enables ternary-style expressions.
        """
        program = """
        score = 95
        output = "Grade: ${$score >= 90 and 'A' or $score >= 80 and 'B' or 'C'}"
        return output
        """
        result = cy_interpreter.run(program)
        # Ternary-style expressions now work correctly
        assert result == '"Grade: A"'


# ============================================================================
# 5. COMPLEX EXPRESSION TESTS
# ============================================================================


class TestComplexExpressions:
    """Verify complex combinations work correctly."""

    def test_mixed_arithmetic_and_functions(self, cy_interpreter):
        """Test combining functions and arithmetic."""
        program = """
        output = "Total items value: ${len($items) * 10}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Total items value: 30"'

    def test_expression_with_indexed_access(self, cy_interpreter):
        """Test expressions with array/dict access."""
        program = """
        multiplier = 1.1
        output = "Adjusted Alice score: ${$scores['Alice'] * $multiplier}"
        return output
        """
        result = cy_interpreter.run(program)
        # Should be 95 * 1.1 = 104.5
        assert "104.5" in result or "104" in result

    def test_expression_with_field_access(self, cy_interpreter):
        """Test expressions with field access."""
        program = """
        factor = 2
        output = "Double TTL: ${$config.cache.ttl * $factor}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Double TTL: 7200"'

    def test_boolean_with_comparison_and_math(self, cy_interpreter):
        """Test complex boolean expressions."""
        program = """
        base = 100
        bonus = 20
        threshold = 110
        output = "Qualifies: ${($base + $bonus) >= $threshold}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Qualifies: True"'

    def test_deeply_nested_expression(self, cy_interpreter):
        """Test deeply nested complex expression."""
        program = """
        a = 2
        b = 3
        c = 4
        d = 5
        output = "Complex: ${add(multiply($a, $b), subtract($d, $c))}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Complex: 7"'  # (2 * 3) + (5 - 4) = 6 + 1 = 7


# ============================================================================
# 6. ERROR HANDLING TESTS (NEGATIVE TESTS)
# ============================================================================


class TestErrorHandling:
    """Verify appropriate errors for invalid expressions."""

    def test_undefined_function_error(self, cy_interpreter):
        """Test calling undefined function in interpolation."""
        from cy_language.errors import ToolResolutionError

        program = """
        output = "Result: ${unknown_function(5)}"
        return output
        """
        # May raise SyntaxError during parsing or ToolResolutionError at compile-time
        with pytest.raises(
            (ToolNotFoundError, ToolResolutionError, CySyntaxError)
        ) as exc_info:
            cy_interpreter.run(program)
        assert "unknown_function" in str(exc_info.value)

    def test_syntax_error_unclosed_paren(self, cy_interpreter):
        """Test syntax error for malformed expression."""
        program = """
        output = "Result: ${add(5, 3}"
        return output
        """
        with pytest.raises(CySyntaxError):
            cy_interpreter.run(program)

    def test_syntax_error_invalid_operator(self, cy_interpreter):
        """Test unsupported operator."""
        program = """
        a = 5
        b = 3
        output = "Power: ${$a ** $b}"  # ** not supported
        return output
        """
        with pytest.raises(CySyntaxError):
            cy_interpreter.run(program)

    def test_division_by_zero(self, cy_interpreter):
        """Test division by zero handling."""
        program = """
        x = 10
        y = 0
        output = "Result: ${$x / $y}"
        return output
        """
        # Should either raise error or handle gracefully
        try:
            result = cy_interpreter.run(program)
            # If it doesn't raise, check for graceful handling
            assert (
                "inf" in result.lower()
                or "error" in result.lower()
                or "none" in result.lower()
            )
        except (ZeroDivisionError, Exception) as e:
            # Expected behavior - division by zero error
            # Accept both Python RuntimeError and CyRuntimeError
            if "Division by zero" in str(e) or "ZeroDivisionError" in str(e):
                pass  # Expected
            else:
                raise  # Re-raise unexpected errors

    def test_type_error_len_on_number(self, cy_interpreter):
        """Test type error for invalid function argument."""
        program = """
        number = 42
        output = "Length: ${len($number)}"
        return output
        """
        # Our fixture len() returns 0 for non-sequences
        result = cy_interpreter.run(program)
        assert result == '"Length: 0"'

    def test_quote_constraint_error(self, cy_interpreter):
        """Test lexer-level quote constraint."""
        # This should fail at lexer level due to double quotes
        program = """
        output = "User: ${scores["Alice"]}"
        return output
        """
        with pytest.raises(CySyntaxError):
            cy_interpreter.run(program)


# ============================================================================
# 7. EDGE CASE TESTS
# ============================================================================


class TestAdvancedCornerCases:
    """Test complex nested expressions and edge cases."""

    def test_deeply_nested_parentheses(self, cy_interpreter):
        """Test complex nested parentheses with multiple operations."""
        program = """
        x = 10
        b = 5
        output = "Result: ${(len($items) * $b) / 2 + 11.1}"
        return output
        """
        result = cy_interpreter.run(program)
        # len($items) = 3, so (3 * 5) / 2 + 11.1 = 15 / 2 + 11.1 = 7.5 + 11.1 = 18.6
        assert result == '"Result: 18.6"'

    def test_floating_point_arithmetic(self, cy_interpreter):
        """Test floating point numbers in expressions."""
        program = """
        rate = 0.05
        amount = 1000
        output = "Interest: ${$amount * $rate + 2.5}"
        return output
        """
        result = cy_interpreter.run(program)
        # 1000 * 0.05 + 2.5 = 50 + 2.5 = 52.5
        assert result == '"Interest: 52.5"'

    def test_complex_order_of_operations(self, cy_interpreter):
        """Test complex mathematical precedence."""
        program = """
        a = 2
        b = 3
        c = 4
        d = 5
        output = "Complex: ${$a + $b * $c - $d / 2.0}"
        return output
        """
        result = cy_interpreter.run(program)
        # 2 + 3 * 4 - 5 / 2.0 = 2 + 12 - 2.5 = 11.5
        assert result == '"Complex: 11.5"'

    def test_mixed_functions_and_arithmetic(self, cy_interpreter):
        """Test combining function calls with complex arithmetic."""
        program = """
        multiplier = 2.5
        output = "Advanced: ${(len($items) + 1) * $multiplier - 0.5}"
        return output
        """
        result = cy_interpreter.run(program)
        # (3 + 1) * 2.5 - 0.5 = 4 * 2.5 - 0.5 = 10 - 0.5 = 9.5
        assert result == '"Advanced: 9.5"'

    def test_nested_function_calls_with_arithmetic(self, cy_interpreter):
        """Test nested function calls within arithmetic."""
        program = """
        text1 = "Hello"
        text2 = "World"
        output = "Total: ${len($text1) + len($text2) * 2}"
        return output
        """
        result = cy_interpreter.run(program)
        # len("Hello") + len("World") * 2 = 5 + 5 * 2 = 5 + 10 = 15
        assert result == '"Total: 15"'

    def test_parentheses_with_function_calls(self, cy_interpreter):
        """Test parentheses grouping function calls."""
        program = """
        name1 = "Test"
        name2 = "Data"
        output = "Combined: ${(len($name1) + len($name2)) * 3}"
        return output
        """
        result = cy_interpreter.run(program)
        # (len("Test") + len("Data")) * 3 = (4 + 4) * 3 = 8 * 3 = 24
        assert result == '"Combined: 24"'

    def test_complex_data_access_with_arithmetic(self, cy_interpreter):
        """Test complex data access combined with arithmetic."""
        program = """
        alice_score = scores['Alice']
        first_user = users[0]
        result = len(alice_score) + len(first_user.name) * 2
        output = "Data math: ${$result + 5}"
        return output
        """
        result = cy_interpreter.run(program)
        # len(95) + len("Alice") * 2 + 5 = 0 + 5 * 2 + 5 = 0 + 10 + 5 = 15
        assert result == '"Data math: 15"'

    def test_extremely_nested_expression(self, cy_interpreter):
        """Test very deeply nested expression to stress test the parser."""
        program = """
        a = 1
        b = 2
        c = 3
        output = "Deep: ${((($a + $b) * $c) / 2.0 + len($items)) * (10 - 5) + 1.5}"
        return output
        """
        result = cy_interpreter.run(program)
        # (((1 + 2) * 3) / 2.0 + 3) * (10 - 5) + 1.5
        # = ((3 * 3) / 2.0 + 3) * 5 + 1.5
        # = (9 / 2.0 + 3) * 5 + 1.5
        # = (4.5 + 3) * 5 + 1.5
        # = 7.5 * 5 + 1.5
        # = 37.5 + 1.5 = 39.0
        assert result == '"Deep: 39.0"'


class TestWhitespaceHandling:
    """Test comprehensive whitespace handling in interpolation."""

    def test_multiline_with_newlines(self, cy_interpreter):
        """Test expressions with newlines inside braces."""
        program = """
        r = [1, 2, 3]
        output = "Result: ${
            $r[1]
        }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Result: 2"'

    def test_multiline_with_indentation(self, cy_interpreter):
        """Test expressions with various indentation levels."""
        program = """
        a = 10
        b = 5
        output = "Math: ${
                $a + $b
            }"
            return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Math: 15"'

    def test_multiline_with_tabs(self, cy_interpreter):
        """Test expressions with tab characters."""
        program = """
        x = 7
        output = "Value: ${\t\t$x * 2\t}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Value: 14"'

    def test_mixed_whitespace_types(self, cy_interpreter):
        """Test expressions with mixed spaces, tabs, and newlines."""
        program = """
        data = ["a", "bb", "ccc"]
        output = "Length: ${ \t
        \t len($data[2]) + 1 \t
        \t }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Length: 4"'

    def test_multiline_function_calls(self, cy_interpreter):
        """Test multiline function calls with parameters."""
        program = """
        text = "Hello"
        output = "Result: ${
            upper($text)
        }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Result: HELLO"'

    def test_multiline_arithmetic_complex(self, cy_interpreter):
        """Test complex multiline arithmetic expressions."""
        program = """
        a = 2
        b = 3
        c = 4
        output = "Result: ${
            ($a + $b) * $c
            / 2.0 + 1
        }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Result: 11.0"'

    def test_multiple_multiline_expressions(self, cy_interpreter):
        """Test multiple multiline expressions in same template."""
        program = """
        x = 10
        y = 20
        items = [1, 2, 3, 4, 5]
        result = "Values: ${
            $x + $y
        } and ${
            len($items) * 2
        }"
        output = result
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Values: 30 and 10"'

    def test_nested_data_access_multiline(self, cy_interpreter):
        """Test nested data access with multiline formatting."""
        program = """
        user = users[0]
        score = scores['Alice']
        output = "User ${
            $user.name
        } has score ${
            $score + 5
        }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"User Alice has score 100"'

    def test_multiline_with_format_hints(self, cy_interpreter):
        """Test multiline expressions with format hints."""
        program = """
        numbers = [10, 20, 30]
        output = "Numbers: ${
            $numbers
        |csv}"
        return output
        """
        result = cy_interpreter.run(program)
        # Our CSV formatter produces "10,20,30" without spaces
        assert "10,20,30" in result

    def test_extreme_whitespace_patterns(self, cy_interpreter):
        """Test extreme whitespace patterns to stress test the parser."""
        program = """
        value = 42
        output = "Extreme: ${


                    $value + 8


        }"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Extreme: 50"'

    def test_whitespace_preservation_in_template(self, cy_interpreter):
        """Test that whitespace in template (not expressions) is preserved."""
        program = '''
        name = "World"
        template = """Hello,   ${$name}!

        How are    you?"""
        output = template
        return output
        '''
        result = cy_interpreter.run(program)
        assert "Hello,   World!" in result
        assert "How are    you?" in result

    def test_original_bug_case(self, cy_interpreter):
        """Test the original bug case that was discovered."""
        program = '''
        r = [1,2,3]
        name = """
        ${
            r[1]
        }
        World ${len(r) * 2}"""

        output = "Hello, ${name}!"
        return output
        '''
        result = cy_interpreter.run(program)
        # The indentation from the program is preserved in the multiline string
        expected = json.dumps("Hello, \n        2\n        World 6!")
        assert result == expected


class TestEdgeCases:
    """Test boundary conditions and unusual patterns."""

    def test_empty_expression(self, cy_interpreter):
        """Test empty ${} braces."""
        program = """
        output = "Empty: ${}"
        return output
        """
        # Should either error or handle gracefully
        try:
            result = cy_interpreter.run(program)
            assert "${}" in result or result == '"Empty: "'
        except (CySyntaxError, ValueError):
            pass  # Expected - empty expression error

    def test_whitespace_only_expression(self, cy_interpreter):
        """Test ${  } with only whitespace."""
        program = """
        output = "Whitespace: ${  }"
        return output
        """
        try:
            result = cy_interpreter.run(program)
            assert "${  }" in result or result == '"Whitespace: "'
        except (CySyntaxError, ValueError):
            pass  # Expected - whitespace-only expression error

    def test_format_hint_with_expression(self, cy_interpreter):
        """Test format hints with complex expressions."""
        program = """
        a = 5
        b = 3
        output = "Formatted: ${$a + $b|csv}"
        return output
        """
        result = cy_interpreter.run(program)
        assert "8" in result

    def test_triple_quoted_with_expressions(self, cy_interpreter):
        """Test expressions in triple-quoted strings."""
        program = '''
        x = 10
        y = 20
        output = """
        Addition: ${$x + $y}
        Function: ${add($x, $y)}
        Comparison: ${$x < $y}
        """
        return output
        '''
        result = cy_interpreter.run(program)
        assert "Addition: 30" in result
        assert "Function: 30" in result
        assert "Comparison: True" in result

    def test_mixed_simple_and_complex_interpolations(self, cy_interpreter):
        """Test mixing simple and complex interpolations."""
        program = """
        name = "Alice"
        a = 5
        b = 3
        output = "User ${name} calculated ${$a + $b} and ${multiply($a, $b)}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"User Alice calculated 8 and 15"'


# ============================================================================
# 8. PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Verify performance optimizations work correctly."""

    def test_simple_expression_fast_path(self, cy_interpreter):
        """Test that simple variables use fast path."""
        # This test verifies behavior, not actual performance
        program = """
        name = "Alice"
        output = "${name}"  # Should use fast path
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Alice"'

    def test_complex_expression_uses_parser(self, cy_interpreter):
        """Test that complex expressions use full parser."""
        program = """
        a = 5
        output = "${$a + 3}"  # Should use full parser
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"8"'

    def test_repeated_template_execution(self, cy_interpreter):
        """Test repeated use of same template."""
        program = """
        x = 5
        output1 = "Value: ${$x + 1}"
        x = 10
        output2 = "Value: ${$x + 1}"
        output = "${output1}, ${output2}"
        return output
        """
        result = cy_interpreter.run(program)
        assert result == '"Value: 6, Value: 11"'


# ============================================================================
# TEST PLAN TRACKING
# ============================================================================


def test_all_tests_implemented():
    """Meta-test to verify all planned tests are implemented."""
    # This test helps track that we've implemented all tests from TEST_PLAN.md
    expected_test_classes = [
        "TestBackwardCompatibility",
        "TestFunctionCalls",
        "TestArithmeticExpressions",
        "TestBooleanExpressions",
        "TestComplexExpressions",
        "TestErrorHandling",
        "TestAdvancedCornerCases",
        "TestWhitespaceHandling",
        "TestEdgeCases",
        "TestPerformance",
    ]

    import sys

    module = sys.modules[__name__]

    for class_name in expected_test_classes:
        assert hasattr(module, class_name), f"Missing test class: {class_name}"

    # All test classes exist
    assert True
