"""Tests for function/tool calling in the Cy language."""

import pytest

from cy_language import Cy
from cy_language.errors import ToolInvocationError, ToolNotFoundError


def test_basic_function_call():
    """Test basic function call with no arguments."""
    # Create a simple tool that returns a fixed value
    tools = {"random": lambda: 42}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test calling a function with no arguments
    program = """
    result = random()
    output = "Random: ${result}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Random: 42"'


def test_function_call_with_return_value():
    """Test function call with return value."""
    # Create an addition tool
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function with return value
    program = """
    total = add(1, 2)
    output = "1 + 2 = ${total}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"1 + 2 = 3"'


def test_function_call_with_positional_args():
    """Test function call with multiple positional arguments."""
    # Create a tool with multiple positional arguments
    tools = {"add": lambda a, b, c=0: a + b + c}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function with multiple positional arguments
    program = """
    total = add(1, 2, 3)
    output = "1 + 2 + 3 = ${total}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"1 + 2 + 3 = 6"'


def test_function_call_with_string_args():
    """Test function call with string arguments."""
    # Create a string concatenation tool
    tools = {"concat": lambda *strings: "".join(strings)}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function with string arguments
    program = """
    result = concat("Hello", " ", "World")
    output = "Concatenated: ${result}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"Concatenated: Hello World"'


def test_function_call_with_variable_args():
    """Test function call with variable references as arguments."""
    # Create an addition tool
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function with variable references as arguments
    program = """
    a = 5
    b = 7
    total = add(a, b)
    output = "${a} + ${b} = ${total}"
    return output
    """
    result = interpreter.run(program)
    assert result == '"5 + 7 = 12"'


def test_function_call_with_named_args():
    """Test function call with named arguments."""

    # Create a tool that uses named arguments
    def search(query, limit=10, offset=0):
        return {"query": query, "limit": limit, "offset": offset}

    tools = {"search": search}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function with named arguments
    program = """
    result = search(query="apple", limit=5)
    output = "Search: ${result}"
    return output
    """
    result = interpreter.run(program)
    assert "query" in result
    assert "apple" in result
    assert "limit" in result
    assert "5" in result


def test_function_call_nonexistent_tool():
    """Test error when calling a non-existent tool."""
    interpreter = Cy()
    interpreter.show_enhanced_errors = False

    # Test calling a non-existent tool
    program = """
    result = missing_function()
    output = "Result: ${result}"
    return output
    """

    # Now raises ToolResolutionError at compile time instead of ToolNotFoundError at runtime
    from cy_language.errors import ToolResolutionError

    with pytest.raises((ToolNotFoundError, ToolResolutionError)) as excinfo:
        interpreter.run(program)
    assert "not found" in str(excinfo.value)


def test_function_call_mixed_args_positional_first():
    """Test that positional-first mixed arguments work correctly."""
    # Create a tool
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Positional first, then named — should work
    program = """
    result = add(1, b=2)
    return result
    """

    result = interpreter.run(program)
    assert result == "3"


def test_function_call_named_first_is_parse_error():
    """Test that named-first mixed arguments are a parse error."""
    # Create a tool
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Named arg before positional — should fail at parse time
    program = """
    result = add(a=1, 2)
    output = "Result: ${result}"
    return output
    """

    with pytest.raises(Exception):
        interpreter.run(program)


def test_function_call_complex_return():
    """Test function returning complex data structures."""

    # Create a tool that returns a complex data structure
    def user_info(name, age):
        return {
            "name": name,
            "age": age,
            "hobbies": ["reading", "coding"],
            "contact": {
                "email": f"{name.lower()}@example.com",
                "phone": "123-456-7890",
            },
        }

    tools = {"get_user": user_info}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    # Test function returning a complex data structure
    program = """
    user = get_user("Alice", 30)
    output = "User: ${user} - Email: ${user.contact.email}"
    return output
    """
    result = interpreter.run(program)
    assert "Alice" in result
    assert "30" in result
    assert "reading" in result
    assert "coding" in result
    assert "alice@example.com" in result


def test_tool_runtime_error_raises_invocation_error():
    """Test that a tool raising at runtime gives ToolInvocationError, not ToolNotFoundError.

    Regression: API errors (e.g. 429 quota exceeded) were misreported as
    ToolNotFoundError because the catch-all in the executor used the wrong
    error class.
    """

    def exploding_tool():
        raise Exception("Error code: 429 - quota exceeded")

    tools = {"boom": exploding_tool}
    interpreter = Cy(tools=tools)
    interpreter.show_enhanced_errors = False

    program = """
    result = boom()
    return result
    """

    with pytest.raises(ToolInvocationError) as excinfo:
        interpreter.run(program)
    assert "429" in str(excinfo.value)
    # Must NOT be a ToolNotFoundError
    assert not isinstance(excinfo.value, ToolNotFoundError)


def test_tool_runtime_error_no_bracket_suggestion():
    """Test that runtime tool errors don't get misleading syntax suggestions.

    Regression: multiline tool calls like `llm_run(` would trigger the
    bracket-checking heuristic, suggesting "Missing closing parenthesis ')'"
    for what was actually an API error.
    """

    def failing_api_call(prompt):
        raise Exception("429 - quota exceeded")

    tools = {"llm_run": failing_api_call}
    interpreter = Cy(tools=tools)

    # Multiline call — the opening paren is on a different line than closing
    program = 'result = llm_run(\n    prompt="hello"\n)\nreturn result'

    with pytest.raises(ToolInvocationError) as excinfo:
        interpreter.run(program)
    error_str = str(excinfo.value)
    # The suggestion must NOT be about brackets
    assert "Missing closing parenthesis" not in error_str
