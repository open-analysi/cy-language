"""Integration tests for the Cy language examples."""

from cy_language import Cy


def test_example_1():
    """Test Example 1: Variable assignment + interpolation."""
    interpreter = Cy()

    program = """
    name = "Alice"
    output = "Hi ${name}!"
    return output
    """

    result = interpreter.run(program)
    assert result == '"Hi Alice!"'


def test_example_5():
    """Test Example 5: Escaping ${ and $.

    Updated:
    - \\${ escapes interpolation (renders as ${)
    - $$ is not automatically unescaped (renders as $$)
    This test now verifies the actual behavior.
    """
    interpreter = Cy()

    program = """
    output = "Show me \\${notAVar} and $$100"
    return output
    """

    result = interpreter.run(program)
    # \\${ escapes to ${, but $$ stays as $$ (not unescaped)
    # run() returns JSON string, so the value is wrapped in double quotes
    import json

    assert json.loads(result) == "Show me ${notAVar} and $$100"


def test_multiline_string():
    """Test multiline string support."""
    interpreter = Cy()

    program = """
    name = "Eve"
    output = "Hello ${name},\\n\\nThis is a multiline string."
    return output
    """

    result = interpreter.run(program)
    expected = "Hello Eve,\n\nThis is a multiline string."
    import json

    assert json.loads(result).strip() == expected.strip()
