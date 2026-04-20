"""Tests for $input and $output handling in the Cy language."""

import pytest

from cy_language import Cy


def test_input_handling():
    """Test proper handling of the $input variable."""
    # Test with string input
    interpreter = Cy()
    interpreter.show_enhanced_errors = False
    program = """
    output = "Input was: ${input}"
    return output
    """

    result = interpreter.run(program, "Hello World")
    assert result == '"Input was: Hello World"'

    # Test with numeric input
    result = interpreter.run(program, 42)
    assert result == '"Input was: 42"'

    # Test with boolean input
    result = interpreter.run(program, True)
    assert result == '"Input was: True"'

    # Test with None input
    result = interpreter.run(program, None)
    assert result == '"Input was: null"'


def test_input_with_list():
    """Test handling $input with list values."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False
    program = """
    output = "Input list: ${input}"
    return output
    """

    # Test with a list input
    input_list = ["apple", "banana", "cherry"]
    result = interpreter.run(program, input_list)
    assert "Input list: " in result
    assert "- apple" in result
    assert "- banana" in result
    assert "- cherry" in result


def test_input_with_dict():
    """Test handling $input with dictionary values."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False
    program = """
    output = "Input user: ${input.name}, age: ${input.age}"
    return output
    """

    # Test with a dictionary input
    input_dict = {"name": "Alice", "age": 30}
    result = interpreter.run(program, input_dict)
    assert result == '"Input user: Alice, age: 30"'


def test_input_copy_allowed():
    """Test that copying $input to another variable is allowed."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False

    # Program that copies $input
    program = """
    input_copy = input
    output = "Input: ${input}, Copy: ${input_copy}"
    return output
    """

    result = interpreter.run(program, "Hello World")
    assert result == '"Input: Hello World, Copy: Hello World"'


def test_output_missing_error():
    """Test that omitting the output variable raises the correct error."""
    from cy_language.errors import CompilerError

    interpreter = Cy()
    interpreter.show_enhanced_errors = False

    # Program without output assignment or return
    program = """
    value = "This program has no output"
    """

    # Should raise a CompilerError at compile time
    with pytest.raises(CompilerError) as excinfo:
        interpreter.run(program)

    assert "No return statement found" in str(excinfo.value)


def test_output_multiple_assignments():
    """Test that multiple assignments to $output use the last one."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False

    # Program with multiple $output assignments
    program = """
    output = "First assignment"
    output = "Second assignment"
    output = "Third assignment"
    return output
    """

    result = interpreter.run(program)
    assert result == '"Third assignment"'


def test_input_with_complex_structure():
    """Test using $input with a complex nested structure."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False

    # Program that accesses nested fields in input
    program = """
    user_name = input.user.name
    primary_skill = input.user.skills[0]
    city = input.user.address.city
    all_skills = input.user.skills

    output = "User: ${user_name}, Top Skill: ${primary_skill}, Location: ${city}, All Skills: ${all_skills}"
    return output
    """

    input_data = {
        "user": {
            "name": "Bob",
            "skills": ["Python", "JavaScript", "SQL"],
            "address": {"city": "San Francisco", "state": "CA"},
        }
    }

    result = interpreter.run(program, input_data)

    assert "User: Bob" in result
    assert "Top Skill: Python" in result
    assert "Location: San Francisco" in result
    assert "All Skills: " in result
    assert "Python" in result
    assert "JavaScript" in result
    assert "SQL" in result
