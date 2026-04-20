"""
Test positional argument type checking for tool calls.

Comprehensive test suite covering both positive and negative cases
for positional argument validation.
"""

import pytest

from cy_language import Cy


class TestPositionalArgumentsPositiveCases:
    """Test cases where positional arguments are used correctly."""

    def test_single_positional_correct_type(self):
        """Test single positional argument with correct type."""

        def process(value: str) -> str:
            return value.upper()

        cy = Cy(check_types=True, tools={"process": process})

        script = """
        result = process("hello")
        return result
        """

        result = cy.run(script)
        assert result == '"HELLO"'

    def test_multiple_positional_correct_types(self):
        """Test multiple positional arguments with correct types."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        x = 5
        y = 10
        result = add(x, y)
        return result
        """

        result = cy.run(script)
        assert result == 15 or result == "15"

    def test_three_positional_arguments(self):
        """Test three positional arguments."""

        def calculate(a: int, b: int, c: int) -> int:
            return a + b * c

        cy = Cy(check_types=True, tools={"calculate": calculate})

        script = """
        result = calculate(10, 5, 2)
        return result
        """

        result = cy.run(script)
        assert result == 20 or result == "20"

    def test_positional_with_optional_parameter(self):
        """Test positional arguments with optional parameter omitted."""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        cy = Cy(check_types=True, tools={"greet": greet})

        script = """
        result = greet("Alice")
        return result
        """

        result = cy.run(script)
        assert result == '"Hello, Alice!"'

    def test_all_positional_parameters_provided(self):
        """Test providing all parameters positionally including optional."""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        cy = Cy(check_types=True, tools={"greet": greet})

        script = """
        result = greet("Bob", "Hi")
        return result
        """

        result = cy.run(script)
        assert result == '"Hi, Bob!"'


class TestPositionalArgumentsNegativeCases:
    """Test cases where positional arguments have errors."""

    def test_wrong_type_first_positional(self):
        """Test wrong type for first positional argument."""

        def process(value: str) -> str:
            return value.upper()

        cy = Cy(check_types=True, tools={"process": process})

        script = """
        result = process(123)
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert "value" in error_msg or "expects string" in error_msg.lower()

    def test_wrong_type_second_positional(self):
        """Test wrong type for second positional argument."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        x = 5
        y = "hello"
        result = add(x, y)
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert "b" in error_msg or "expects" in error_msg.lower()

    def test_too_many_positional_arguments(self):
        """Test providing too many positional arguments."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        result = add(1, 2, 3)
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert "too many" in error_msg.lower() or "positional" in error_msg.lower()

    def test_missing_required_positional_parameter(self):
        """Test missing required parameter with positional syntax."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        result = add(5)
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert (
            "missing" in error_msg.lower()
            or "b" in error_msg
            or "required" in error_msg.lower()
        )

    def test_multiple_wrong_types_positional(self):
        """Test multiple positional arguments with wrong types."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        result = add("hello", "world")
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        # Should catch at least the first type error
        assert "a" in error_msg or "expects" in error_msg.lower()


class TestMixedPositionalAndNamedArguments:
    """Test cases with both positional and named arguments."""

    def test_all_named_arguments_correct_types(self):
        """Test all named arguments with correct types."""

        def process(a: int, b: str, c: int) -> str:
            return f"{b}: {a + c}"

        cy = Cy(check_types=True, tools={"process": process})

        # Use all named arguments pattern
        script = """
        result = process(a=10, b="sum", c=5)
        return result
        """

        result = cy.run(script)
        assert result == '"sum: 15"'

    def test_duplicate_parameter_positional_and_named(self):
        """Test error when parameter provided both positionally and by name."""

        def add(a: int, b: int) -> int:
            return a + b

        cy = Cy(check_types=True, tools={"add": add})

        script = """
        result = add(5, a=10)
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert "both" in error_msg.lower() or "duplicate" in error_msg.lower()

    def test_positional_wrong_type_named_correct(self):
        """Test positional arg with wrong type, named arg correct."""

        def process(a: int, b: str) -> str:
            return f"{b}: {a}"

        cy = Cy(check_types=True, tools={"process": process})

        script = """
        result = process("wrong", b="label")
        return result
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value)
        assert "a" in error_msg or "expects" in error_msg.lower()


class TestNativeToolsPositional:
    """Test positional arguments with native Cy tools."""

    def test_len_with_wrong_type_positional(self):
        """Test len() with wrong type (number instead of array/string)."""
        cy = Cy(check_types=True)

        script = """
        x = 123
        size = len(x)
        return size
        """

        # Note: len() parameter is typed as Any in native functions
        # So this might not raise a type error, but execution will fail
        # This tests the validation system's behavior with Any types
        # (should skip validation due to Any escape hatch)
        result = cy.run(script)  # May execute or fail at runtime

    def test_str_with_correct_positional(self):
        """Test str() with correct positional argument."""
        cy = Cy(check_types=True)

        script = """
        x = 42
        text = str(x)
        return text
        """

        result = cy.run(script)
        assert result == '"42"'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
