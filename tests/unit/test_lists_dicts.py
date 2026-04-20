"""Tests for list and dictionary support in the Cy language."""

from cy_language import Cy


def test_empty_list():
    """Test empty list creation and assignment."""
    interpreter = Cy()

    # Test empty list assignment
    program = """
    empty = []
    output = "Empty list: ${empty}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Empty list: []"'


def test_simple_list():
    """Test simple list creation with string items."""
    interpreter = Cy()

    # Test list with string items
    program = """
    fruits = ["apple", "banana", "cherry"]
    output = "Fruits: ${fruits}"
    return output
    """
    result = interpreter.run(program)
    assert "apple" in result
    assert "banana" in result
    assert "cherry" in result


def test_list_with_mixed_types():
    """Test list creation with mixed types."""
    interpreter = Cy()

    # Test list with mixed types (avoiding booleans)
    program = """
    mixed = [1, "two", 3.0, "active"]
    output = "Mixed types: ${mixed}"
    return output
    """
    result = interpreter.run(program)
    assert "1" in result
    assert "two" in result
    assert "3.0" in result
    assert "active" in result


def test_list_with_trailing_comma():
    """Test list creation with trailing comma."""
    interpreter = Cy()

    # Test list with trailing comma
    program = """
    fruits = ["apple", "banana", "cherry",]
    output = "Fruits: ${fruits}"
    return output
    """
    result = interpreter.run(program)
    assert "apple" in result
    assert "banana" in result
    assert "cherry" in result


def test_nested_lists():
    """Test nested list structures."""
    interpreter = Cy()

    # Test nested lists
    program = """
    nested = [["a", "b"], ["c", "d"]]
    output = "Nested lists: ${nested}"
    return output
    """
    result = interpreter.run(program)
    assert "a" in result
    assert "b" in result
    assert "c" in result
    assert "d" in result


def test_empty_dict():
    """Test empty dictionary creation and assignment."""
    interpreter = Cy()

    # Test empty dictionary assignment
    program = """
    empty = {}
    output = "Empty dict: ${empty}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Empty dict: {}"'


def test_simple_dict():
    """Test simple dictionary creation with string keys and values."""
    interpreter = Cy()

    # Test dictionary with string keys and values
    program = """
    user = { "name": "Alice", "age": 30 }
    output = "User: ${user}"
    return output
    """
    result = interpreter.run(program)
    assert "name" in result
    assert "Alice" in result
    assert "age" in result
    assert "30" in result


def test_dict_with_trailing_comma():
    """Test dictionary creation with trailing comma."""
    interpreter = Cy()

    # Test dictionary with trailing comma
    program = """
    user = { "name": "Alice", "age": 30, }
    output = "User: ${user}"
    return output
    """
    result = interpreter.run(program)
    assert "name" in result
    assert "Alice" in result
    assert "age" in result
    assert "30" in result


def test_nested_dicts():
    """Test nested dictionary structures."""
    interpreter = Cy()

    # Test nested dictionaries
    program = """
    nested = { "user": { "name": "Alice", "age": 30 } }
    output = "Nested dict: ${nested}"
    return output
    """
    result = interpreter.run(program)
    assert "user" in result
    assert "name" in result
    assert "Alice" in result
    assert "age" in result
    assert "30" in result


def test_dict_with_list_values():
    """Test dictionary with list values."""
    interpreter = Cy()

    # Test dictionary with list values
    program = """
    mixed = { "name": "Alice", "favorites": ["apple", "banana"] }
    output = "Mixed dict: ${mixed}"
    return output
    """
    result = interpreter.run(program)
    assert "name" in result
    assert "Alice" in result
    assert "favorites" in result
    assert "apple" in result
    assert "banana" in result


def test_list_with_dict_values():
    """Test list with dictionary values."""
    interpreter = Cy()

    # Test list with dictionary values
    program = """
    users = [{ "name": "Alice", "age": 30 }, { "name": "Bob", "age": 25 }]
    output = "Users: ${users}"
    return output
    """
    result = interpreter.run(program)
    assert "name" in result
    assert "Alice" in result
    assert "Bob" in result
    assert "age" in result
    assert "30" in result
    assert "25" in result
