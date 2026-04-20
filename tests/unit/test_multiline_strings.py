"""Tests for multiline strings in the Cy language."""

import json

from cy_language import Cy


def test_multiline_string_simple():
    """Test a simple multiline string in the CY language."""
    interpreter = Cy()

    program = """
    output = "Basic\\nmultiline\\nstring"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Basic" in decoded
    assert "multiline" in decoded
    assert "string" in decoded
    assert "Basic\nmultiline\nstring" in decoded


def test_multiline_string_with_interpolation():
    """Test variable interpolation in multiline strings."""
    interpreter = Cy()

    program = """
    name = "Alice"
    output = "Hello, \\n${name}!"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Hello," in decoded
    assert "Alice!" in decoded
    assert "Hello, \nAlice!" in decoded


def test_multiline_string_with_nested_structures():
    """Test interpolation of nested structures in multiline strings."""
    interpreter = Cy()

    program = """
    user = { "name": "Bob", "details": { "age": 25, "hobbies": ["reading", "coding"] } }
    output = "User: ${user.name}\\nAge: ${user.details.age}\\nHobbies: ${user.details.hobbies}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "User: Bob" in decoded
    assert "Age: 25" in decoded
    assert "Hobbies:" in decoded
    assert "- reading" in decoded
    assert "- coding" in decoded


def test_multiline_string_with_escapes():
    """Test escape sequences within multiline strings."""
    interpreter = Cy()

    # Use normal string, not raw string, for the program
    program = """
    name = "World"
    output = "Escaped dollar sign: \\${name}\\nNormal interpolation: ${name}\\nEscaped curly braces: \\${name}\\nEscaped backslash: \\\\\\nEscaped quotes: \\\"quoted\\\""
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Escaped dollar sign: ${name}" in decoded
    assert "Normal interpolation: World" in decoded
    assert "Escaped curly braces: ${name}" in decoded
    assert "Escaped backslash: \\" in decoded
    assert 'Escaped quotes: "quoted"' in decoded


def test_multiline_string_indentation_preservation():
    """Test that multiline strings preserve indentation correctly."""
    interpreter = Cy()

    program = """
    output = "\\n    This line has 4 spaces at the start.\\n        This line has 8 spaces at the start.\\n\\tThis line starts with a tab.\\n    \\n    This line has a blank line before it."
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "    This line has 4 spaces at the start." in decoded
    assert "        This line has 8 spaces at the start." in decoded
    assert "\tThis line starts with a tab." in decoded
    assert decoded.count("\n") >= 5  # At least 5 newlines in the result


def test_multiline_string_with_special_characters():
    """Test multiline strings with special characters."""
    interpreter = Cy()

    program = """
    output = "Special chars:\\n* Asterisk\\n# Hash\\n> Greater than\\n$ Dollar\\n\\\" Quote\\n\\\\ Backslash"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Special chars:" in decoded
    assert "* Asterisk" in decoded
    assert "# Hash" in decoded
    assert "> Greater than" in decoded
    assert "$ Dollar" in decoded
    assert '"' in decoded
    assert "\\" in decoded


class TestTripleQuotedStrings:
    """Test triple-quoted multiline string handling with interpolation."""

    def test_basic_multiline_string_interpolation(self):
        """Test basic multiline strings with variable interpolation."""
        interpreter = Cy()

        program = '''
name = "Alice"
age = 30
output = """Hello ${name},
You are ${age} years old.
Welcome to our system!"""
return output
'''
        result = interpreter.run(program.strip())
        decoded = json.loads(result)
        expected = "Hello Alice,\nYou are 30 years old.\nWelcome to our system!"
        assert decoded == expected

    def test_multiline_indentation_preservation(self):
        """Test that proper indentation is preserved in multiline strings."""
        interpreter = Cy()

        program = '''
data = "test"
output = """
    Indented content: ${data}
        More indented: ${data}
    Back to first level
"""
return output
'''
        result = interpreter.run(program.strip())
        decoded = json.loads(result)
        # Should preserve the indentation structure
        lines = decoded.split("\n")
        assert lines[1].startswith("    ")  # First indent level
        assert lines[2].startswith("        ")  # Second indent level
        assert lines[3].startswith("    ")  # Back to first level

    def test_multiline_with_escape_sequences(self):
        """Test escape sequences in multiline string contexts."""
        interpreter = Cy()

        program = r'''
output = """Line 1\nStill line 1
Line 2\tWith tab
Line 3 with \${escaped}"""
return output
'''
        result = interpreter.run(program.strip())
        decoded = json.loads(result)
        lines = decoded.split("\n")
        assert lines[0] == "Line 1"  # First part before \n
        assert lines[1] == "Still line 1"  # Second part after \n
        assert "Line 2\tWith tab" in lines[2]  # Tab processed
        assert "${escaped}" in lines[3]  # Escape prevents interpolation

    def test_multiline_with_format_hints(self):
        """Test format hints in multiline strings."""
        interpreter = Cy()

        program = '''
data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
output = """User Data:
${data|csv}

Raw Data:
${data|xml}"""
return output
'''
        result = interpreter.run(program.strip())
        decoded = json.loads(result)
        # Should properly format data according to hints
        assert "User Data:" in decoded
        assert "Raw Data:" in decoded
