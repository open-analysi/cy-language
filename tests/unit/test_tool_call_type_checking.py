"""
Test tool call parameter type checking.

Verifies that _check_tool_call properly validates tool call arguments
against tool signatures.
"""

import pytest

from cy_language import Cy


def test_tool_call_with_wrong_parameter_type():
    """Test that tool calls with wrong parameter types are caught."""

    # Define a tool that expects a string
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    cy = Cy(check_types=True, tools={"greet": greet})

    # Call with number instead of string - should raise TypeError
    script = """
    result = greet(name=123)
    return result
    """

    with pytest.raises(TypeError) as exc_info:
        cy.run(script)

    # Verify error message mentions parameter name and types
    error_msg = str(exc_info.value)
    assert "name" in error_msg or "parameter" in error_msg.lower()
    assert "string" in error_msg or "number" in error_msg


def test_tool_call_with_missing_required_parameter():
    """Test that missing required parameters are caught."""

    def greet(name: str, greeting: str) -> str:
        return f"{greeting}, {name}!"

    cy = Cy(check_types=True, tools={"greet": greet})

    # Missing 'greeting' parameter - should raise TypeError
    script = """
    result = greet(name="Alice")
    return result
    """

    with pytest.raises(TypeError) as exc_info:
        cy.run(script)

    error_msg = str(exc_info.value)
    assert "greeting" in error_msg or "required" in error_msg.lower()


def test_tool_call_with_unknown_parameter():
    """Test that unknown parameters are caught."""

    def greet(name: str) -> str:
        return f"Hello, {name}!"

    cy = Cy(check_types=True, tools={"greet": greet})

    # Pass unknown parameter 'age' - should raise TypeError
    script = """
    result = greet(name="Alice", age=30)
    return result
    """

    with pytest.raises(TypeError) as exc_info:
        cy.run(script)

    error_msg = str(exc_info.value)
    assert "age" in error_msg or "parameter" in error_msg.lower()


def test_tool_call_with_correct_types():
    """Test that tool calls with correct types pass validation."""

    def add_numbers(a: int, b: int) -> int:
        return a + b

    cy = Cy(check_types=True, tools={"add_numbers": add_numbers})

    # Correct types - should work
    script = """
    x = 5
    y = 10
    result = add_numbers(a=x, b=y)
    return result
    """

    result = cy.run(script)
    # cy.run() returns string representation
    assert result == 15 or result == "15"


def test_tool_call_with_optional_parameter():
    """Test that optional parameters can be omitted."""

    def greet(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    cy = Cy(check_types=True, tools={"greet": greet})

    # Omit optional 'greeting' parameter - should work
    script = """
    result = greet(name="Alice")
    return result
    """

    result = cy.run(script)
    assert result == '"Hello, Alice!"'


def test_tool_call_with_fqn():
    """Test that tool calls with FQN work correctly."""

    def ip_reputation(ip_address: str) -> dict:
        return {"ip": ip_address, "score": 8}

    cy = Cy(check_types=True, tools={"app::virustotal::ip_reputation": ip_reputation})

    # Wrong type for ip_address - should raise TypeError
    script = """
    result = app::virustotal::ip_reputation(ip_address=12345)
    return result
    """

    with pytest.raises(TypeError) as exc_info:
        cy.run(script)

    error_msg = str(exc_info.value)
    assert "ip_address" in error_msg


def test_tool_call_any_type_escape_hatch():
    """Test that Any types allow any argument (escape hatch)."""

    # Tool without type hints - parameters are Any
    def process_data(data):
        return f"Processed: {data}"

    cy = Cy(check_types=True, tools={"process_data": process_data})

    # Any type can receive anything - should work
    script = """
    result1 = process_data(data=123)
    result2 = process_data(data="text")
    result3 = process_data(data=[1, 2, 3])
    return result1
    """

    result = cy.run(script)
    assert "Processed" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
