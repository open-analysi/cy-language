"""Tests for different interpolation modes in the Cy language."""

from cy_language import Cy


def test_markdown_interpolation_list():
    """Test markdown interpolation of lists."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test list in markdown mode
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "Fruits:\n${fruits}"
    return output
    """
    result = interpreter.run(program)
    assert "- apple" in result
    assert "- banana" in result
    assert "- cherry" in result


def test_markdown_interpolation_dict():
    """Test markdown interpolation of dictionaries."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test dictionary in markdown mode
    program = """
    user = { "name": "Alice", "age": 30 }
    output = "User:\n${user}"
    return output
    """
    result = interpreter.run(program)
    assert "**name**" in result
    assert "Alice" in result
    assert "**age**" in result
    assert "30" in result


def test_markdown_interpolation_nested():
    """Test markdown interpolation of nested structures."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test nested structure in markdown mode
    program = """
    data = { "user": { "name": "Alice", "hobbies": ["reading", "coding"] } }
    output = "User data:\n${data}"
    return output
    """
    result = interpreter.run(program)
    assert "**user**" in result
    assert "**name**" in result
    assert "Alice" in result
    assert "**hobbies**" in result
    assert "reading" in result
    assert "coding" in result


def test_csv_interpolation_list():
    """Test CSV interpolation of lists."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test list in CSV mode
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "Fruits:\n${fruits|csv}"
    return output
    """
    result = interpreter.run(program)
    assert "apple,banana,cherry" in result


def test_csv_interpolation_dict_list():
    """Test CSV interpolation of list of dictionaries."""
    import json

    interpreter = Cy(interpolation_mode="markdown")

    # Test list of dictionaries in CSV mode
    program = """
    users = [{ "name": "Alice", "age": 30 }, { "name": "Bob", "age": 25 }]
    output = "Users:\n${users|csv}"
    return output
    """
    result = interpreter.run(program)
    parsed = json.loads(result)

    # Should have header row and data rows
    lines = parsed.split("\n")
    data_lines = [line.strip() for line in lines if line.strip()]
    assert len(data_lines) >= 3  # "Users:" + header + 2 data rows

    # Check header and data
    data_part = data_lines[1:]  # Skip "Users:"
    # CSV fields are sorted alphanumerically
    assert "age,name" in parsed.replace(" ", "")
    # Values appear in same order as headers
    assert "30,Alice" in parsed.replace(" ", "")
    assert "25,Bob" in parsed.replace(" ", "")


def test_xml_interpolation_list():
    """Test XML interpolation of lists."""
    interpreter = Cy(interpolation_mode="markdown", item_tag="item")

    # Test list in XML mode
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "<fruits>${fruits|xml}</fruits>"
    return output
    """
    result = interpreter.run(program)
    assert "<fruits>" in result
    assert "<item>apple</item>" in result.replace(" ", "")
    assert "<item>banana</item>" in result.replace(" ", "")
    assert "<item>cherry</item>" in result.replace(" ", "")
    assert "</fruits>" in result


def test_xml_interpolation_dict():
    """Test XML interpolation of dictionaries."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test dictionary in XML mode
    program = """
    user = { "name": "Alice", "age": 30 }
    output = "<user>${user|xml}</user>"
    return output
    """
    result = interpreter.run(program)
    assert "<user>" in result
    assert "<name>Alice</name>" in result.replace(" ", "")
    assert "<age>30</age>" in result.replace(" ", "")
    assert "</user>" in result


def test_xml_interpolation_nested():
    """Test XML interpolation of nested structures."""
    interpreter = Cy(interpolation_mode="markdown", item_tag="item")

    # Test nested structure in XML mode
    program = """
    data = { "user": { "name": "Alice", "hobbies": ["reading", "coding"] } }
    output = "<data>${data|xml}</data>"
    return output
    """
    result = interpreter.run(program)
    assert "<data>" in result
    assert "<user>" in result
    assert "<name>Alice</name>" in result.replace(" ", "")
    assert "<hobbies>" in result
    assert "<item>reading</item>" in result.replace(" ", "")
    assert "<item>coding</item>" in result.replace(" ", "")
    assert "</hobbies>" in result
    assert "</user>" in result
    assert "</data>" in result


def test_custom_item_tag():
    """Test XML interpolation with custom item tag."""
    interpreter = Cy(interpolation_mode="markdown", item_tag="element")

    # Test list with custom item tag
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "<fruits>${fruits|xml}</fruits>"
    return output
    """
    result = interpreter.run(program)
    assert "<fruits>" in result
    assert "<element>apple</element>" in result.replace(" ", "")
    assert "<element>banana</element>" in result.replace(" ", "")
    assert "<element>cherry</element>" in result.replace(" ", "")
    assert "</fruits>" in result


def test_per_expression_formatting():
    """Test using different formatting for different expressions."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test overriding default format
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "CSV: ${fruits|csv}, XML: ${fruits|xml}"
    return output
    """
    result = interpreter.run(program)
    assert "CSV:" in result
    assert "apple,banana,cherry" in result
    assert "XML:" in result
    assert "<item>apple</item>" in result.replace(" ", "")


def test_per_expression_formatting_with_dot_notation():
    """Test per-expression formatting with dot notation."""
    interpreter = Cy(interpolation_mode="markdown")

    # Test with nested structures
    program = """
    data = { "user": { "hobbies": ["reading", "coding"] } }
    output = "Hobbies in CSV: ${data.user.hobbies|csv}"
    return output
    """
    result = interpreter.run(program)
    assert "Hobbies in CSV:" in result
    assert "reading,coding" in result
