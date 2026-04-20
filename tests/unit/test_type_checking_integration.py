"""Integration tests for type checking system.

These tests verify end-to-end type checking functionality through
the Cy interpreter with the check_types flag enabled.

Update: Type checking now raises TypeError instead of CompilerError.
"""

import pytest

from cy_language import Cy


class TestTypeCheckingIntegration:
    """Test type checking through the Cy interpreter."""

    def test_type_checking_disabled_by_default(self):
        """Test that type checking is disabled by default."""
        interpreter = Cy()

        # This code would fail type checking but should compile without errors when check_types=False
        code = """
        a = 5
        b = "text"
        if (a > 0) {
            result = a + b
        } else {
            result = "default"
        }
        return result
        """

        # Should compile without type error when check_types=False (default)
        # Will fail at runtime, but that's different from compile-time type error
        try:
            result = interpreter.run(code)
            # If it somehow runs, that's fine
        except Exception as e:
            # Should not be a type checking compile error
            # Runtime errors are OK (like "Cannot use + operator with int and str")
            assert "Type checking failed" not in str(e)
            # It's fine if it's a runtime error
            assert "RuntimeError" in str(type(e)) or "Cannot use + operator" in str(e)

    def test_type_checking_enabled_catches_errors(self):
        """Test that enabling check_types catches type errors."""
        interpreter = Cy(check_types=True)

        code = """
        age = 25
        name = "Alice"
        result = age + name
        return result
        """

        # Should raise CompilerError with type checking message
        with pytest.raises(TypeError) as exc_info:
            interpreter.run(code)

        error_msg = str(exc_info.value)
        assert "type" in error_msg.lower() or "add" in error_msg.lower()

    def test_valid_program_passes_type_checking(self):
        """Test that valid program passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        a = 5
        b = 10
        result = a + b
        return result
        """

        result = interpreter.run(code)
        assert "15" in result

    def test_type_error_shows_line_number(self):
        """Test that type errors include line numbers."""
        interpreter = Cy(check_types=True)

        code = """
        x = 10
        y = 20
        z = x + y
        bad = "hello" - "world"
        return bad
        """

        with pytest.raises(TypeError) as exc_info:
            interpreter.run(code)

        error_msg = str(exc_info.value)
        # Should contain line number information
        assert "line" in error_msg.lower() or any(char.isdigit() for char in error_msg)

    def test_multiple_type_errors_reported(self):
        """Test that multiple type errors are collected and reported."""
        interpreter = Cy(check_types=True)

        code = """
        error1 = 5 + "text"
        error2 = "hello" - 10
        error3 = (5 > 3) * (2 < 1)
        return error1
        """

        with pytest.raises(TypeError) as exc_info:
            interpreter.run(code)

        error_msg = str(exc_info.value)
        # Should mention multiple errors or contain multiple error descriptions
        # The exact format depends on implementation
        assert len(error_msg) > 50  # Multiple errors should create longer message


class TestArithmeticTypeChecking:
    """Test arithmetic operation type checking integration."""

    def test_number_addition_valid(self):
        """Test that adding numbers passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        total = 10 + 20 + 30
        return total
        """

        result = interpreter.run(code)
        assert "60" in result

    def test_string_concatenation_valid(self):
        """Test that string concatenation passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        greeting = "Hello" + " " + "World"
        return greeting
        """

        result = interpreter.run(code)
        assert "Hello World" in result

    def test_mixed_addition_invalid(self):
        """Test that adding number and string fails type checking."""
        interpreter = Cy(check_types=True)

        code = """
        mixed = 42 + " is the answer"
        return mixed
        """

        with pytest.raises(TypeError):
            interpreter.run(code)

    def test_subtraction_requires_numbers(self):
        """Test that subtraction only works with numbers."""
        interpreter = Cy(check_types=True)

        code = """
        result = "hello" - "world"
        return result
        """

        with pytest.raises(TypeError):
            interpreter.run(code)

    def test_multiplication_requires_numbers(self):
        """Test that multiplication only works with numbers."""
        interpreter = Cy(check_types=True)

        code = """
        result = "text" * "more"
        return result
        """

        with pytest.raises(TypeError):
            interpreter.run(code)

    def test_division_requires_numbers(self):
        """Test that division only works with numbers."""
        interpreter = Cy(check_types=True)

        code = """
        result = "hello" / "world"
        return result
        """

        with pytest.raises(TypeError):
            interpreter.run(code)


class TestComparisonTypeChecking:
    """Test comparison operation type checking integration."""

    def test_number_comparison_valid(self):
        """Test that comparing numbers passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        is_greater = 10 > 5
        return is_greater
        """

        result = interpreter.run(code)
        assert "true" in result.lower() or "True" in result

    def test_string_comparison_valid(self):
        """Test that comparing strings passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        is_less = "apple" < "banana"
        return is_less
        """

        result = interpreter.run(code)
        assert "true" in result.lower() or "True" in result

    def test_mixed_comparison_invalid(self):
        """Test that comparing different types fails type checking."""
        interpreter = Cy(check_types=True)

        code = """
        result = 42 > "hello"
        return result
        """

        with pytest.raises(TypeError):
            interpreter.run(code)

    def test_equality_allows_any_types(self):
        """Test that == works with any types."""
        interpreter = Cy(check_types=True)

        code = """
        result = 42 == "42"
        return result
        """

        # Should NOT raise type error for equality
        result = interpreter.run(code)
        # Result may be true or false, but should not error


class TestBooleanOperationTypeChecking:
    """Test boolean operation type checking integration."""

    def test_and_with_booleans_valid(self):
        """Test that 'and' with booleans passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        result = (5 > 3) and (2 < 1)
        return result
        """

        result = interpreter.run(code)
        assert "false" in result.lower() or "False" in result

    def test_or_with_booleans_valid(self):
        """Test that 'or' with booleans passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        result = (5 > 3) or (2 < 1)
        return result
        """

        result = interpreter.run(code)
        assert "true" in result.lower() or "True" in result

    def test_not_with_boolean_valid(self):
        """Test that 'not' with boolean passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        result = not (5 > 3)
        return result
        """

        result = interpreter.run(code)
        assert "false" in result.lower() or "False" in result

    def test_and_with_numbers_valid(self):
        """Test that 'and' with numbers works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        result = 5 and 10
        return result
        """

        # Should NOT raise error - 'and' supports truthy/falsy for any type
        result = interpreter.run(code)
        # 'and' returns the actual value (Python-like semantics)
        assert "10" in result

    def test_or_with_strings_valid(self):
        """Test that 'or' with strings works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        result = "hello" or "world"
        return result
        """

        # Should NOT raise error - 'or' supports truthy/falsy for any type
        result = interpreter.run(code)
        # 'or' returns the actual value (Python-like semantics)
        assert "hello" in result

    def test_not_with_string_valid(self):
        """Test that 'not' with string works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        result = not "text"
        return result
        """

        # Should NOT raise error - 'not' supports truthy/falsy for any type
        result = interpreter.run(code)
        assert "false" in result.lower() or "False" in result


class TestConditionalTypeChecking:
    """Test conditional statement type checking integration."""

    def test_if_with_boolean_valid(self):
        """Test that if with boolean condition passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        if (5 > 3) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """

        result = interpreter.run(code)
        assert "yes" in result

    def test_if_with_comparison_valid(self):
        """Test that if with comparison passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        age = 25
        if (age > 18) {
            result = "adult"
        } else {
            result = "minor"
        }
        return result
        """

        result = interpreter.run(code)
        assert "adult" in result

    def test_if_with_string_truthy(self):
        """Test that if with string condition works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        if ("hello") {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """

        # Should pass with truthy/falsy semantics
        result = interpreter.run(code)
        assert "yes" in result

    def test_if_with_number_truthy(self):
        """Test that if with number condition works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        if (42) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """

        # Should pass with truthy/falsy semantics
        result = interpreter.run(code)
        assert "yes" in result


class TestWhileLoopTypeChecking:
    """Test while loop type checking integration."""

    def test_while_with_boolean_valid(self):
        """Test that while with boolean condition passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        count = 0
        running = (1 == 1)
        while (running) {
            count = count + 1
            if (count > 3) {
                running = (1 == 0)
            }
        }
        return count
        """

        result = interpreter.run(code)
        assert "4" in result

    def test_while_with_comparison_valid(self):
        """Test that while with comparison passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        count = 0
        while (count < 5) {
            count = count + 1
        }
        return count
        """

        result = interpreter.run(code)
        assert "5" in result

    def test_while_with_string_truthy(self):
        """Test that while with string condition works (truthy/falsy semantics)."""
        interpreter = Cy(check_types=True)

        code = """
        message = "loop"
        while (message) {
            message = ""
        }
        return message
        """

        # Should pass with truthy/falsy semantics
        result = interpreter.run(code)
        assert result == '""'  # Empty string after loop (JSON-encoded)


class TestFieldAccessTypeChecking:
    """Test field access type checking integration."""

    def test_valid_field_access(self):
        """Test that accessing existing field passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        user = {"name": "Alice", "age": 30}
        name = user.name
        return name
        """

        result = interpreter.run(code)
        assert "Alice" in result

    def test_invalid_field_access(self):
        """Test that accessing non-existent field returns null.

        Operations on nullable fields require ?? operator.
        """
        interpreter = Cy(check_types=True)

        # Field access returns null, no error
        code = """
        user = {"name": "Alice", "age": 30}
        email = user.email
        return email
        """
        result = interpreter.run(code)
        # Returns null (stringified as "null" or "None")
        assert result in ["null", "None", None]

        # But operating on nullable Any field (Any|null) is allowed at compile time
        # because Any type bypasses strict checking (may fail at runtime)
        code_with_operation = """
        user = {"name": "Alice", "age": 30}
        email = (user.email ?? "")
        result = email + "@example.com"
        return result
        """
        result = interpreter.run(code_with_operation)
        assert "@example.com" in result

    def test_nested_field_access(self):
        """Test that nested field access is type checked."""
        interpreter = Cy(check_types=True)

        code = """
        data = {"user": {"name": "Bob"}}
        name = data.user.name
        return name
        """

        result = interpreter.run(code)
        assert "Bob" in result


class TestIndexedAccessTypeChecking:
    """Test indexed access type checking integration."""

    def test_array_with_number_index_valid(self):
        """Test that indexing array with number passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        items = ["a", "b", "c"]
        first = items[0]
        return first
        """

        result = interpreter.run(code)
        assert "a" in result

    def test_array_with_string_index_invalid(self):
        """Test that indexing array with string fails type checking."""
        interpreter = Cy(check_types=True)

        code = """
        items = ["a", "b", "c"]
        item = items["key"]
        return item
        """

        with pytest.raises(TypeError):
            interpreter.run(code)

    def test_object_with_string_index_valid(self):
        """Test that indexing object with string passes type checking."""
        interpreter = Cy(check_types=True)

        code = """
        user = {"name": "Alice"}
        name = user["name"]
        return name
        """

        result = interpreter.run(code)
        assert "Alice" in result

    def test_object_with_number_index_invalid(self):
        """Test that indexing object with number fails type checking."""
        interpreter = Cy(check_types=True)

        code = """
        user = {"name": "Alice"}
        value = user[0]
        return value
        """

        with pytest.raises(TypeError):
            interpreter.run(code)


class TestAnyTypeIntegration:
    """Test that Any type ({}) from input bypasses type checking."""

    def test_input_allows_any_operations(self):
        """Test that input field operations require ?? operator.

        Even with auto-derived schema, field access returns nullable types.
        """
        interpreter = Cy(check_types=True)

        # Field access is nullable, operations require ?? operator
        code = """
        value = (input.data ?? 0)
        result = value + 10
        return result
        """

        result = interpreter.run(code, input_data={"data": 5})
        assert "15" in result

    def test_input_field_access_allowed(self):
        """Test that Any type allows field access."""
        interpreter = Cy(check_types=True)

        code = """
        user = input.user
        name = user.name
        return name
        """

        # Should NOT raise type error for accessing fields on Any type
        result = interpreter.run(code, input_data={"user": {"name": "Alice"}})
        assert "Alice" in result

    def test_input_in_conditionals_allowed(self):
        """Test that Any type can be used in conditionals."""
        interpreter = Cy(check_types=True)

        code = """
        flag = input.condition
        if (flag) {
            result = "yes"
        } else {
            result = "no"
        }
        return result
        """

        # Should NOT raise type error for using Any type as condition
        result = interpreter.run(code, input_data={"condition": True})
        assert "yes" in result


@pytest.mark.asyncio
class TestAsyncTypeChecking:
    """Test type checking with async interpreter."""

    async def test_async_interpreter_type_checking(self):
        """Test that type checking works with async interpreter."""
        interpreter = await Cy.create_async(check_types=True)

        code = """
        result = 5 + "text"
        return result
        """

        with pytest.raises(TypeError):
            await interpreter.run_async(code)

    async def test_async_valid_program(self):
        """Test that valid program works with async type checking."""
        interpreter = await Cy.create_async(check_types=True)

        code = """
        total = 10 + 20
        return total
        """

        result = await interpreter.run_async(code)
        assert "30" in result


class TestComplexPrograms:
    """Test type checking on complex real-world programs."""

    def test_complex_valid_program(self):
        """Test that complex valid program passes all type checks."""
        interpreter = Cy(check_types=True)

        code = """
        # Calculate user stats
        users = [
            {"name": "Alice", "age": 30, "score": 85},
            {"name": "Bob", "age": 25, "score": 92},
            {"name": "Carol", "age": 35, "score": 78}
        ]

        total_score = 0
        count = 0
        highest_score = 0

        for (user in users) {
            score = (user.score ?? 0)
            total_score = total_score + score
            count = count + 1

            if (score > highest_score) {
                highest_score = score
            }
        }

        average = total_score / count
        result = {
            "total": total_score,
            "average": average,
            "highest": highest_score
        }

        return result
        """

        result = interpreter.run(code)
        assert "255" in result  # total: 85 + 92 + 78
        assert "92" in result  # highest

    def test_complex_program_with_type_errors(self):
        """Test that complex program with type errors is caught at compile time.

        Field access on statically-typed objects returns nullable types.
        Operations on nullable types (even typed ones) require ?? operator.
        """
        interpreter = Cy(check_types=True)

        code = """
        users = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]

        for (user in users) {
            # Type error: trying to add number and string without ?? operator
            # Caught at compile-time in
            info = user.age + user.name
        }

        return info
        """

        # Nullable types require ?? operator, error caught at compile-time
        with pytest.raises(TypeError) as exc:
            interpreter.run(code)
        assert "nullable" in str(exc.value).lower()

    def test_nested_control_flow(self):
        """Test type checking in nested control flow."""
        interpreter = Cy(check_types=True)

        code = """
        result = 0
        i = 0
        while (i < 3) {
            j = 0
            while (j < 2) {
                if (i > j) {
                    result = result + 1
                }
                j = j + 1
            }
            i = i + 1
        }
        return result
        """

        result = interpreter.run(code)
        assert "3" in result


class TestToolCallTypeChecking:
    """Test type checking for tool calls."""

    def test_tool_with_correct_types(self):
        """Test that tool call with correct types passes."""
        tools = {"add": lambda a, b: a + b}
        interpreter = Cy(tools=tools, check_types=True)

        code = """
        result = add(a=5, b=10)
        return result
        """

        # Should pass type checking if tool signatures are validated
        # This test may be skipped until tool signature integration is complete
        result = interpreter.run(code)
        assert "15" in result

    def test_tool_with_wrong_types(self):
        """Test that tool call with wrong types raises TypeError."""

        def add(a: int, b: int) -> int:
            return a + b

        interpreter = Cy(tools={"add": add}, check_types=True)

        # Pass a string where an int is expected
        code = """
        result = add(a="not_a_number", b=10)
        return result
        """

        with pytest.raises((TypeError, Exception)) as exc_info:
            interpreter.run(code)

        # The error must relate to a type mismatch, not an unrelated failure
        error_msg = str(exc_info.value).lower()
        assert (
            "type" in error_msg
            or "string" in error_msg
            or "number" in error_msg
            or "parameter" in error_msg
            or "int" in error_msg
        )


class TestErrorMessageQuality:
    """Test that error messages are clear and actionable."""

    def test_error_message_clarity(self):
        """Test that error message is clear and includes helpful info."""
        interpreter = Cy(check_types=True)

        code = """
        age = 25
        name = "Alice"
        result = age + name
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            interpreter.run(code)

        error_msg = str(exc_info.value).lower()

        # Error should mention:
        # - The operation that failed (add/+)
        # - The types involved (number, string)
        # - Line information
        assert "add" in error_msg or "+" in error_msg
        assert "type" in error_msg or "cannot" in error_msg

    def test_error_message_with_line_info(self):
        """Test that error message includes line and column info."""
        interpreter = Cy(check_types=True)

        code = """
        x = 10
        y = 20
        z = x + y
        bad_line = "text" - "more"
        return bad_line
        """

        with pytest.raises(TypeError) as exc_info:
            interpreter.run(code)

        error_msg = str(exc_info.value)

        # Should have line number (4 or 5 depending on how we count)
        assert any(c.isdigit() for c in error_msg), "Error should include line number"


class TestTypeCheckingPerformance:
    """Test that type checking doesn't significantly impact performance."""

    def test_type_checking_performance(self):
        """Test that type checking completes in reasonable time."""
        import time

        interpreter = Cy(check_types=True)

        code = """
        total = 0
        i = 0
        while (i < 100) {
            total = total + i
            i = i + 1
        }
        return total
        """

        start = time.time()
        result = interpreter.run(code)
        duration = time.time() - start

        # Type checking should add minimal overhead
        # This is a sanity check, not a precise benchmark
        assert duration < 5.0, "Type checking should complete in reasonable time"
        assert "4950" in result
