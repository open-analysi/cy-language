"""Tests for dot notation and field access in the Cy language."""

from cy_language import Cy


def test_simple_field_access():
    """Test simple dictionary field access with dot notation."""
    interpreter = Cy()

    # Test basic field access with dot notation
    program = """
    user = { "name": "Alice", "age": 30 }
    output = "Hello, ${user.name}!"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Hello, Alice!"'


def test_field_access_requires_braces():
    """Test that $user.name is interpreted as $user + .name (not field access)."""
    interpreter = Cy()

    # Test that $user.name becomes interpolated $user plus literal .name
    program = """
    user = { "name": "Alice", "age": 30 }
    output = "Hello, ${user}.name!"
    return output
    """
    result = interpreter.run(program)
    # $user should be interpolated as markdown, followed by literal .name
    import json

    expected_result = "Hello, **name**: Alice\n**age**: 30.name!"
    assert json.loads(result) == expected_result


def test_nested_field_access():
    """Test nested field access with dot notation."""
    interpreter = Cy()

    # Test nested field access
    program = """
    data = { "user": { "name": "Alice", "age": 30 } }
    output = "Hello, ${data.user.name}!"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Hello, Alice!"'


def test_deep_nested_field_access():
    """Test deeply nested field access with dot notation."""
    interpreter = Cy()

    # Test deeply nested field access
    program = """
    data = { "company": { "dept": { "name": "Engineering" } } }
    output = "Department: ${data.company.dept.name}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Department: Engineering"'


def test_field_access_returns_null_for_nonexistent():
    """Missing fields return null for safe navigation."""
    interpreter = Cy()

    # Test that accessing a non-existent field returns null
    program = """
    user = { "name": "Alice" }
    output = "Age: ${user.age}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Age: null"'

    # Show safe navigation pattern with or
    program_with_default = """
    user = { "name": "Alice" }
    output = "Age: ${user.age or 'Unknown'}"
    return output
    """
    result = interpreter.run(program_with_default)
    assert result == '"Age: Unknown"'


def test_field_access_error_not_dict():
    """Accessing fields on non-dict still raises error (only dict/null supported)."""
    interpreter = Cy()

    # Test that dot notation on a non-dictionary (string, number, etc.) returns null
    # UPDATE: ALL invalid field access returns null, not just dict/null
    program = """
    name = "Alice"
    output = "Hello, ${name.property}!"
    return output
    """

    result = interpreter.run(program)
    # Returns "Hello, null!" instead of raising error
    assert result == '"Hello, null!"'


def test_nested_field_access_returns_null():
    """Missing nested fields return null with null propagation."""
    interpreter = Cy()

    # Test that accessing a non-existent nested field returns null
    # When user.address is missing, it returns null, then null.street also returns null
    program = """
    data = { "user": { "name": "Alice" } }
    output = "Address: ${data.user.address.street}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Address: null"'

    # Show safe navigation pattern with or
    program_with_default = """
    data = { "user": { "name": "Alice" } }
    output = "Address: ${data.user.address.street or 'Not provided'}"
    return output
    """
    result = interpreter.run(program_with_default)
    assert result == '"Address: Not provided"'


def test_dot_notation_with_interpolation_mode():
    """Test dot notation with different interpolation modes."""
    interpreter = Cy()

    # Test dot notation with markdown mode (default)
    program = """
    data = { "user": { "hobbies": ["reading", "coding"] } }
    output = "Hobbies: ${data.user.hobbies}"
    return output
    """
    result = interpreter.run(program)
    assert "reading" in result
    assert "coding" in result

    # Test dot notation with CSV mode
    program = """
    data = { "user": { "hobbies": ["reading", "coding"] } }
    output = "Hobbies: ${data.user.hobbies|csv}"
    return output
    """
    result = interpreter.run(program)
    assert "reading,coding" in result


def test_dot_notation_combined_with_regular_variables():
    """Test combining dot notation and regular variables in interpolation."""
    interpreter = Cy()

    # Test combining dot notation with regular variables
    program = """
    user = { "name": "Alice" }
    greeting = "Hello"
    output = "${greeting}, ${user.name}!"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Hello, Alice!"'
