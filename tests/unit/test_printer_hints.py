"""Tests for printer hints (format pipes) in the Cy language."""

import json

from cy_language import Cy


def test_printer_hint_markdown():
    """Test using the pipe syntax to specify markdown format."""
    interpreter = Cy(interpolation_mode="csv")  # Default is CSV

    program = """
    items = ["apple", "banana", "cherry"]
    output = "Fruits: ${items|markdown}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Fruits: " in decoded
    assert "- apple" in decoded
    assert "- banana" in decoded
    assert "- cherry" in decoded


def test_printer_hint_csv():
    """Test using the pipe syntax to specify CSV format."""
    interpreter = Cy(interpolation_mode="markdown")  # Default is markdown

    program = """
    items = ["apple", "banana", "cherry"]
    output = "Fruits: ${items|csv}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Fruits: apple,banana,cherry" in decoded


def test_printer_hint_xml():
    """Test using the pipe syntax to specify XML format."""
    interpreter = Cy(interpolation_mode="markdown")  # Default is markdown

    program = """
    items = ["apple", "banana", "cherry"]
    output = "<fruits>${items|xml}</fruits>"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "<fruits>" in decoded
    assert "<item>apple</item>" in decoded
    assert "<item>banana</item>" in decoded
    assert "<item>cherry</item>" in decoded
    assert "</fruits>" in decoded


def test_printer_hint_with_nested_structures():
    """Test printer hints with nested data structures."""
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    users = [
        { "name": "Alice", "age": 30, "hobbies": ["reading", "hiking"] },
        { "name": "Bob", "age": 25, "hobbies": ["coding", "gaming"] }
    ]
    output = "Users: ${users|csv}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Users: " in decoded
    # Fields are sorted alphanumerically
    assert "age,hobbies,name" in decoded
    # Values appear in same order as headers
    assert "30,\"['reading', 'hiking']\",Alice" in decoded
    assert "25,\"['coding', 'gaming']\",Bob" in decoded


def test_printer_hint_mixing_formats():
    """Test using different printer hints in the same string."""
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    fruits = ["apple", "banana", "cherry"]
    vegetables = ["carrot", "broccoli", "spinach"]
    output = "Fruits (CSV): ${fruits|csv}\\nVegetables (XML): ${vegetables|xml}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)

    # CSV part
    assert "Fruits (CSV): apple,banana,cherry" in decoded

    # XML part
    assert "Vegetables (XML): " in decoded
    assert "<item>carrot</item>" in decoded
    assert "<item>broccoli</item>" in decoded
    assert "<item>spinach</item>" in decoded


def test_printer_hint_with_dict():
    """Test printer hints with dictionary values."""
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    user = { "name": "Alice", "age": 30, "active": "true" }
    output = "User CSV: ${user|csv}\\nUser XML: ${user|xml}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)

    # CSV part
    assert "User CSV: " in decoded
    # Fields are sorted alphanumerically
    assert "active,age,name" in decoded
    # Values appear in same order as headers
    assert "true,30,Alice" in decoded

    # XML part
    assert "User XML: " in decoded
    assert "<name>Alice</name>" in decoded
    assert "<age>30</age>" in decoded
    assert "<active>true</active>" in decoded


def test_printer_hint_default():
    """Test default behavior when no printer hint is specified."""
    interpreter = Cy(interpolation_mode="csv")

    program = """
    items = ["apple", "banana", "cherry"]
    with_hint = "Fruits (with hint): ${items|markdown}"
    without_hint = "Fruits (default): ${items}"
    output = "${with_hint}\\n${without_hint}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)

    # With markdown hint
    assert "Fruits (with hint): " in decoded
    assert "- apple" in decoded
    assert "- banana" in decoded
    assert "- cherry" in decoded

    # Without hint (should use default csv)
    assert "Fruits (default): apple,banana,cherry" in decoded


def test_printer_hint_with_nested_dot_notation():
    """Test printer hints with nested structure accessed via dot notation."""
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    data = { 
        "user": { 
            "name": "Alice",
            "scores": [85, 92, 78]
        }
    }
    output = "User: ${data.user.name}\\nScores: ${data.user.scores|csv}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "User: Alice" in decoded
    assert "Scores: 85,92,78" in decoded


def test_printer_hint_errors():
    """Test error handling for invalid printer hints."""
    interpreter = Cy()

    # This test is meant to handle future validation of printer hints
    # Currently the interpreter doesn't validate the format type
    # and falls back to str() if an unknown format is provided

    program = """
    items = ["apple", "banana", "cherry"]
    output = "Fruits: ${items|invalid_format}"
    return output
    """

    # For now, this should run without error, treating 'invalid_format' as a format_type
    # but using the default string representation. In the future, we might want to add
    # format validation and this test would change.
    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Fruits: " in decoded
    # We're not asserting the exact format, just that it runs without error


def test_printer_hint_json_dict():
    """Test using the pipe syntax to specify JSON format for dictionaries."""
    interpreter = Cy()

    program = """
    user = {"name": "Alice", "age": 30, "active": True}
    output = "User: ${user|json}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "User: " in decoded
    # Verify it's valid JSON with double quotes (not Python single quotes)
    assert '"name": "Alice"' in decoded
    assert '"age": 30' in decoded
    assert '"active": true' in decoded  # JSON uses lowercase true/false


def test_printer_hint_json_list():
    """Test using the pipe syntax to specify JSON format for lists."""
    interpreter = Cy()

    program = """
    items = ["apple", "banana", "cherry"]
    output = "Fruits: ${items|json}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Fruits: " in decoded
    # Verify it's valid JSON array with double quotes
    assert '["apple", "banana", "cherry"]' in decoded


def test_printer_hint_json_nested():
    """Test JSON format with nested structures."""
    interpreter = Cy()

    program = """
    data = {
        "users": [
            {"name": "Alice", "scores": [85, 92, 78]},
            {"name": "Bob", "scores": [90, 88, 95]}
        ]
    }
    output = "Data: ${data|json}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Data: " in decoded
    # Verify nested structure is properly formatted as JSON
    assert '"users":' in decoded
    assert '"name": "Alice"' in decoded
    assert '"scores": [85, 92, 78]' in decoded
    assert '"name": "Bob"' in decoded
    assert '"scores": [90, 88, 95]' in decoded


def test_printer_hint_json_primitives():
    """Test JSON format with primitive values."""
    interpreter = Cy()

    program = """
    text = "hello"
    number = 42
    flag = True
    empty = null
    output = "String: ${text|json}, Number: ${number|json}, Boolean: ${flag|json}, Null: ${empty|json}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    # Strings should be quoted
    assert 'String: "hello"' in decoded
    # Numbers should not be quoted
    assert "Number: 42" in decoded
    # Booleans should be lowercase
    assert "Boolean: true" in decoded
    # Null should be lowercase
    assert "Null: null" in decoded


def test_printer_hint_json_empty_structures():
    """Test JSON format with empty structures."""
    interpreter = Cy()

    program = """
    empty_list = []
    empty_dict = {}
    output = "Empty list: ${empty_list|json}, Empty dict: ${empty_dict|json}"
    return output
    """

    result = interpreter.run(program)
    decoded = json.loads(result)
    assert "Empty list: []" in decoded
    assert "Empty dict: {}" in decoded
