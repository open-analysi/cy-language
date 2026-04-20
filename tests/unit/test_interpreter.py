"""Tests for the Cy language interpreter."""

import pytest

from cy_language import Cy
from cy_language.errors import CyError, SyntaxError


def test_interpreter_initialization():
    """Test interpreter initialization."""
    interpreter = Cy()
    # Now includes default native tools (len, etc.)
    assert "len" in interpreter.tools  # Check native tools are included
    assert interpreter.external_variables == {}
    assert interpreter.interpolation_mode == "markdown"
    assert interpreter.item_tag == "item"

    # Test with custom parameters
    tools = {"add": lambda a, b: a + b}
    variables = {"greeting": "Hello"}
    interpreter = Cy(
        tools=tools, variables=variables, interpolation_mode="csv", item_tag="element"
    )

    # Tools now include native tools + user tools
    assert "add" in interpreter.tools  # User tool
    assert "len" in interpreter.tools  # Native tool
    assert interpreter.external_variables == variables
    assert interpreter.interpolation_mode == "csv"
    assert interpreter.item_tag == "element"


def test_simple_program():
    """Test running a simple program."""
    interpreter = Cy()

    program = """
    name = "World"
    output = "Hello, World!"
    return output
    """

    result = interpreter.run(program)
    assert result == '"Hello, World!"'


def test_syntax_error():
    """Test handling of syntax errors."""
    interpreter = Cy()

    program = """
    name = "World
    ${output} = "Hello, name!"
    """

    with pytest.raises((SyntaxError, CyError)):
        interpreter.run(program)


def test_input_variable():
    """Test that $input variable is available."""
    interpreter = Cy()

    program = """
    name = input
    output = "Hello, ${name}!"
    return output
    """

    result = interpreter.run(program, "Alice")
    assert result == '"Hello, Alice!"'
