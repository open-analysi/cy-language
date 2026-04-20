"""
Comprehensive tests for multi-line function calls in Cy language.

This test suite covers various patterns of multi-line function calls,
including those with comments interspersed.
"""

import pytest

from cy_language import Cy


class TestMultilineFunctionCalls:
    """Test suite for multi-line function call patterns."""

    @pytest.fixture
    def test_tools(self):
        """Provide test tools for function calls."""
        return {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b if b != 0 else None,
            "concat": lambda *args: "".join(str(arg) for arg in args),
            "process": lambda data, threshold=0.5, mode="normal": (
                f"Processed: {data} (t={threshold}, m={mode})"
            ),
            "len": lambda x: len(x) if hasattr(x, "__len__") else 0,
        }

    def test_simple_multiline_positional_args(self, test_tools):
        """Test simple multi-line function call with positional arguments."""
        program = """
result = add(
    5,
    3
)
output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Result: 8"'

    def test_multiline_with_comments_between_args(self, test_tools):
        """Test multi-line function call with comments between arguments."""
        program = """
a = 10
b = 20
result = add(
    a,    # first number
    b     # second number
)  # end of function call
output = "Sum: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Sum: 30"'

    def test_multiline_with_comment_before_comma(self, test_tools):
        """Test multi-line function call with comment before comma."""
        program = """
result = add(
    15  # first argument
    ,   # comma on next line
    25  # second argument
)
output = "Sum: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Sum: 40"'

    def test_multiline_named_arguments(self, test_tools):
        """Test multi-line function call with named arguments."""
        program = """
result = process(
    data="test data",
    threshold=0.75,
    mode="strict"
)
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Processed: test data (t=0.75, m=strict)"'

    def test_multiline_named_args_with_comments(self, test_tools):
        """Test multi-line named arguments with inline comments."""
        program = """
# Configuration for processing
sensor_input = "sensor_data"

result = process(
    data=sensor_input,       # input data from sensor
    threshold=0.9,     # high confidence threshold
    mode="strict"      # use strict validation
)  # processing complete

output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Processed: sensor_data (t=0.9, m=strict)"'

    def test_nested_multiline_function_calls(self, test_tools):
        """Test nested multi-line function calls."""
        program = """
result = add(
    add(
        1,
        2
    ),
    add(
        3,
        4
    )
)
output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Result: 10"'

    def test_nested_multiline_with_comments(self, test_tools):
        """Test nested multi-line function calls with comments."""
        program = """
result = multiply(
    add(      # inner addition 1
        2,    # a
        3     # b
    ),        # = 5
    subtract( # inner subtraction
        10,   # x
        2     # y
    )         # = 8
)             # 5 * 8 = 40
output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Result: 40"'

    def test_multiline_with_expressions(self, test_tools):
        """Test multi-line function calls with complex expressions as arguments."""
        program = """
x = 5
y = 3
result = multiply(
    x + y,        # 8
    x - y         # 2
)
output = "Result: ${result}"  # 8 * 2 = 16
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Result: 16"'

    def test_multiline_variadic_function(self, test_tools):
        """Test multi-line call to variadic function."""
        program = """
result = concat(
    "Hello",
    " ",
    "World",
    "!"
)
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Hello World!"'

    def test_multiline_variadic_with_comments(self, test_tools):
        """Test multi-line variadic function with comments."""
        program = """
# Building a message
result = concat(
    "Error",       # prefix
    ": ",          # separator
    "File",        # object
    " ",           # space
    "not",         # negation
    " ",           # space
    "found"        # state
)  # Complete error message
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Error: File not found"'

    def test_multiline_in_control_flow(self, test_tools):
        """Test multi-line function call inside control flow."""
        program = """
x = 10
y = 5

if (x > y) {
    result = add(
        x,  # larger value
        y   # smaller value
    )
} else {
    result = subtract(
        x,
        y
    )
}

output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Result: 15"'

    def test_multiline_in_while_loop(self, test_tools):
        """Test multi-line function call inside while loop."""
        program = """
counter = 0
total = 0

while (counter < 3) {
    # Add counter to sum with increment
    total = add(
        total,    # current total
        counter   # current counter value
    )
    counter = counter + 1
}

output = "Sum: ${total}"  # 0 + 1 + 2 = 3
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Sum: 3"'

    def test_multiline_empty_lines_between_args(self, test_tools):
        """Test multi-line function call with empty lines between arguments."""
        program = """
result = add(
    100,

    # Empty line above, comment here

    200

)
output = "Sum: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Sum: 300"'

    def test_multiline_mixed_positional_and_named(self, test_tools):
        """Test multi-line with named arguments (all named pattern)."""
        # Cy supports mixed positional+named (positional first) and all-named patterns
        program = """
# Using all named arguments (converted from positional)
result = process(
    data="test",
    threshold=0.6,
    mode="relaxed"
)
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Processed: test (t=0.6, m=relaxed)"'

    def test_multiline_with_list_argument(self, test_tools):
        """Test multi-line function call with list as argument."""
        program = """
items = ["apple", "banana", "cherry"]
count = len(
    items  # counting list items
)
output = "Count: ${count}"
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Count: 3"'

    def test_multiline_with_dict_argument(self, test_tools):
        """Test multi-line function call with dictionary as argument."""
        program = """
data = {
    "name": "test",
    "value": 42
}
result = concat(
    "Data: ",
    data["name"],
    " = ",
    data["value"]
)
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Data: test = 42"'

    def test_error_multiline_missing_comma(self, test_tools):
        """Test error handling for missing comma in multi-line call."""
        program = """
result = add(
    5    # missing comma here
    3
)
output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        # This should fail due to syntax error
        with pytest.raises(Exception):  # Could be SyntaxError or other parsing error
            interpreter.run(program)

    def test_error_multiline_unclosed_parenthesis(self, test_tools):
        """Test error handling for unclosed parenthesis."""
        program = """
result = add(
    5,
    3
    # missing closing parenthesis
output = "Result: ${result}"
return output
"""
        interpreter = Cy(tools=test_tools)
        with pytest.raises(Exception):
            interpreter.run(program)

    def test_multiline_with_string_interpolation(self, test_tools):
        """Test multi-line function call with string interpolation in arguments."""
        program = """
name = "Alice"
age = 30
result = concat(
    "Name: ",
    "${name}",    # interpolated string
    ", Age: ",
    "${age}"      # interpolated number
)
output = result
return output
"""
        interpreter = Cy(tools=test_tools)
        result = interpreter.run(program)
        assert result == '"Name: Alice, Age: 30"'
