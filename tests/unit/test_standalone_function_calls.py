"""
Unit tests for standalone function calls.

These tests verify that function calls can be used as standalone statements,
not just as part of expressions. This was a bug where the parser would fail
with confusing error messages when encountering standalone calls.

Issue: Standalone calls like `log("test")` would fail with:
"Unexpected token '}' at line X. Expected one of: LSQB, DOT"

Fix: Added function_call_statement to grammar as a valid statement type.
"""

import pytest

from cy_language import Cy
from cy_language.errors import ToolResolutionError
from cy_language.ui.tools import default_registry


class TestStandaloneFunctionCalls:
    """Test that function calls work as standalone statements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tools = default_registry.get_tools_dict()
        interpreter = Cy(tools=self.tools)
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_standalone_call_at_top_level(self):
        """Test standalone function call at top level of program."""
        program = """
log("hello world")
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_for_loop(self):
        """Test standalone function call inside for loop (original bug case)."""
        program = """
list = [1, 2, 3]
for (i in list) {
    log("${i}")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_while_loop(self):
        """Test standalone function call inside while loop."""
        program = """
x = 3
while (x > 0) {
    log("${x}")
    x = x - 1
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_if_statement(self):
        """Test standalone function call inside if statement."""
        program = """
x = 5
if (x > 0) {
    log("positive")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_elif_clause(self):
        """Test standalone function call inside elif clause."""
        program = """
x = 0
if (x > 0) {
    log("positive")
} elif (x == 0) {
    log("zero")
} else {
    log("negative")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_else_clause(self):
        """Test standalone function call inside else clause."""
        program = """
x = -5
if (x > 0) {
    log("positive")
} else {
    log("not positive")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_try_block(self):
        """Test standalone function call inside try block."""
        program = """
try {
    log("in try")
    x = 1
} catch (e) {
    log("in catch")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_catch_block(self):
        """Test standalone function call inside catch block."""
        program = """
try {
    x = 1 / 0
} catch (e) {
    log("caught error")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_finally_block(self):
        """Test standalone function call inside finally block."""
        program = """
try {
    x = 1
} catch (e) {
    x = 0
} finally {
    log("in finally")
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_multiple_consecutive_standalone_calls(self):
        """Test multiple standalone calls in sequence."""
        program = """
log("first")
log("second")
log("third")
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_mixed_standalone_and_assigned_calls(self):
        """Test mixing standalone calls with assigned calls."""
        program = """
list = [1, 2, 3]
length = len(list)
log("Length: ${length}")
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_with_multiple_arguments(self):
        """Test standalone call with multiple arguments."""

        # Note: log only takes one arg, so we'll use a custom tool
        def multi_arg_tool(a, b, c):
            return f"{a}-{b}-{c}"

        tools = self.tools.copy()
        tools["multi_arg_tool"] = multi_arg_tool
        cy = Cy(tools=tools)

        program = """
multi_arg_tool("a", "b", "c")
output = "done"
return output
"""
        result = cy.run(program)
        assert result == '"done"'

    def test_standalone_call_with_named_arguments(self):
        """Test standalone call with named arguments."""

        def named_tool(x=1, y=2):
            return x + y

        tools = self.tools.copy()
        tools["named_tool"] = named_tool
        cy = Cy(tools=tools)

        program = """
named_tool(x=5, y=10)
output = "done"
return output
"""
        result = cy.run(program)
        assert result == '"done"'

    def test_standalone_call_with_variable_arguments(self):
        """Test standalone call with variable references as arguments."""
        program = """
x = 10
y = 20
log("x=${x}, y=${y}")
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_with_expression_arguments(self):
        """Test standalone call with expression as argument."""
        program = """
x = 5
log("${x + 10}")
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_nested_standalone_calls_in_loops(self):
        """Test nested loops with standalone calls."""
        program = """
matrix = [[1, 2], [3, 4]]
for (row in matrix) {
    for (item in row) {
        log("${item}")
    }
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_standalone_call_in_nested_if_statements(self):
        """Test nested if statements with standalone calls."""
        program = """
x = 5
y = 10
if (x > 0) {
    if (y > 0) {
        log("both positive")
    }
}
output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'


class TestStandaloneFunctionCallErrors:
    """Test error handling for standalone function calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tools = default_registry.get_tools_dict()
        interpreter = Cy(tools=self.tools)
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_standalone_nonexistent_tool_error(self):
        """Test clear error when standalone call uses nonexistent tool."""
        program = """
fake_tool("test")
output = "done"
return output
"""
        with pytest.raises(ToolResolutionError) as exc_info:
            self.cy.run(program)

        error_msg = str(exc_info.value)
        assert "fake_tool" in error_msg.lower()
        assert "not found" in error_msg.lower()

    def test_standalone_nonexistent_tool_in_loop_error(self):
        """Test clear error when standalone call in loop uses nonexistent tool."""
        program = """
for (i in [1, 2, 3]) {
    missing_function("${i}")
}
output = "done"
return output
"""
        with pytest.raises(ToolResolutionError) as exc_info:
            self.cy.run(program)

        error_msg = str(exc_info.value)
        assert "missing_function" in error_msg.lower()
        assert "not found" in error_msg.lower()

    def test_error_line_number_accuracy(self):
        """Test that error line numbers are accurate for standalone calls."""
        program = """
x = 1
y = 2
fake_tool()
z = 3
output = "done"
return output
"""
        with pytest.raises(ToolResolutionError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        # Should point to line 4 where fake_tool is called
        assert error.line == 4


class TestStandaloneFunctionCallReturnValues:
    """Test that standalone calls properly handle return values."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tools = default_registry.get_tools_dict()

        # Add a tool that returns a value
        def return_value_tool(x):
            return x * 2

        self.tools["return_value_tool"] = return_value_tool
        interpreter = Cy(tools=self.tools)
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_standalone_call_return_value_discarded(self):
        """Test that return values from standalone calls are discarded."""
        program = """
return_value_tool(5)
output = "done"
return output
"""
        result = self.cy.run(program)
        # The return value should be discarded, output should be "done"
        assert result == '"done"'

    def test_assigned_call_return_value_captured(self):
        """Test that assigned calls capture return values (for comparison)."""
        program = """
result = return_value_tool(5)
output = "${result}"
return output
"""
        result = self.cy.run(program)
        assert result == '"10"'


class TestStandaloneFunctionCallComplexScenarios:
    """Test complex real-world scenarios with standalone function calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tools = default_registry.get_tools_dict()
        interpreter = Cy(tools=self.tools)
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_data_processing_with_logging(self):
        """Test data processing pipeline with logging via standalone calls."""
        program = """
data = [1, 2, 3, 4, 5]
results = []

log("Starting processing")

for (item in data) {
    log("Processing item: ${item}")
    processed = item * 2
    results = results + [processed]
}

log("Processing complete")

output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_conditional_logging(self):
        """Test conditional execution with logging."""
        program = """
items = [1, 2, 3, 4, 5]

for (item in items) {
    if (item % 2 == 0) {
        log("Even: ${item}")
    } else {
        log("Odd: ${item}")
    }
}

output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_error_handling_with_logging(self):
        """Test error handling with logging statements."""
        program = """
log("Before try block")

try {
    log("Inside try block")
    x = 1 / 0
} catch (e) {
    log("Caught error")
}

log("After try-catch")

output = "done"
return output
"""
        result = self.cy.run(program)
        assert result == '"done"'

    def test_original_bug_case_exact(self):
        """Test the exact case from the original bug report."""
        program = """
list = [1, 2, 3]

d = {}
for (i in list) {
    log("${i}")
}

return d
"""
        result = self.cy.run(program)
        assert result == "{}"
