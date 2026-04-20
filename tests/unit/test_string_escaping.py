"""Tests for string escaping in the Cy language."""

from cy_language import Cy


def test_escaping_quotes():
    """Test escaping quotes in strings."""
    interpreter = Cy()

    # Test escaping quotes
    program = r"""
    output = "This is a \"quoted\" word."
    return output
    """
    result = interpreter.run(program)
    assert result == '"This is a \\"quoted\\" word."'


def test_escaping_newlines_and_tabs():
    """Test escaping newlines and tabs in strings."""
    interpreter = Cy()

    # Test escaping newlines and tabs
    program = r"""
    output = "Line one\nLine two\tTabbed"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Line one\\nLine two\\tTabbed"'


def test_escaping_dollar_sign():
    """Test escaping dollar sign in strings."""
    interpreter = Cy()

    # Test escaping $
    program = r"""
    output = "Cost is \$5"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Cost is $5"'


def test_escaping_dollar_brace():
    """Test escaping ${} in strings."""
    interpreter = Cy()

    # Test escaping ${
    program = r"""
    output = "The notation \${var} is used for variables"
    return output
    """
    result = interpreter.run(program)
    assert result == '"The notation ${var} is used for variables"'


def test_escaping_backslash():
    """Test escaping backslash in strings."""
    interpreter = Cy()

    # Test double backslash
    program = r"""
    output = "Windows path: C:\\Users\\Name"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Windows path: C:\\\\Users\\\\Name"'


def test_escaping_backslash_at_end():
    """Test escaping backslash at the end of a string."""
    interpreter = Cy()

    # Test backslash at end of string
    program = r"""
    output = "Trailing backslash\\"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Trailing backslash\\\\"'


def test_escaping_in_multiline_strings():
    """Test escaping in multiline strings."""
    interpreter = Cy()

    # Use raw string to avoid Python escaping interference
    program = r"""
    name = "Alice"
    output = "Hello, \n\$name is not interpolated but ${name} is!\nEscaping works with \\ backslashes too.\nAnd \"quotes\" can be escaped.\nUsing \$name to prevent interpolation while ${name} works."
    return output
    """

    result = interpreter.run(program)
    import json

    parsed = json.loads(result)
    assert "Hello," in parsed
    assert "$name is not interpolated but Alice is!" in parsed
    assert "Escaping works with \\ backslashes too." in parsed
    assert 'And "quotes" can be escaped.' in parsed
    assert "Using $name to prevent interpolation while Alice works." in parsed


def test_escaping_with_interpolation():
    """Test escaping with variable interpolation."""
    interpreter = Cy()

    # Test escaping with interpolation
    program = r"""
    name = "Alice"
    output = "Hello, ${name}! That will be \$10."
    return output
    """
    result = interpreter.run(program)
    assert result == '"Hello, Alice! That will be $10."'


def test_escaping_braces_with_interpolation():
    """Test escaping braces with variable interpolation."""
    interpreter = Cy()

    # Test escaping braces with interpolation
    program = r"""
    user = { "name": "Alice", "age": 30 }
    output = "Hello, ${user.name}! The \${user.age} is not defined."
    return output
    """
    result = interpreter.run(program)
    assert result == '"Hello, Alice! The ${user.age} is not defined."'


def test_double_escaping():
    """Test double escaping in strings."""
    interpreter = Cy()

    # Test double escaping
    program = r"""
    output = "This string has a \\$variable but it's escaped twice so it shows the backslash too"
    return output
    """
    result = interpreter.run(program)
    assert (
        result
        == '"This string has a \\\\$variable but it\'s escaped twice so it shows the backslash too"'
    )


def test_escaping_multiple_consecutive_backslashes():
    """Test escaping multiple consecutive backslashes."""
    interpreter = Cy()

    # Test multiple backslashes
    program = """
    output = "One backslash: \\\\, Two backslashes: \\\\\\\\, Three backslashes: \\\\\\\\\\\\"
    return output
    """
    result = interpreter.run(program)
    import json

    parsed = json.loads(result)
    assert (
        parsed == "One backslash: \\, Two backslashes: \\\\, Three backslashes: \\\\\\"
    )


def test_escaping_special_characters():
    """Test escaping special characters in strings."""
    interpreter = Cy()

    # Test escaping special characters
    program = r"""
    output = "Escaped characters: \n (newline), \t (tab), \r (return), \" (quote)"
    return output
    """
    result = interpreter.run(program)
    import json

    parsed = json.loads(result)
    assert "newline" in parsed
    assert "tab" in parsed
    assert "return" in parsed
    assert "quote" in parsed
    assert "\n" in parsed  # Actual newline character
    assert "\t" in parsed  # Actual tab character
    assert "\r" in parsed  # Actual return character
