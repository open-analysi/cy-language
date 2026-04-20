"""
Regression tests for backward compatibility.

Ensure changes don't break existing functionality.
All type checking functionality should still work correctly.

These tests verify backward compatibility and that existing features are unchanged.
"""

import pytest

from cy_language import Cy, analyze_types


class TestBackwardCompatibility:
    """Test backward compatibility with previous phases."""

    def test_cy_run_without_check_types_still_works(self):
        """
        Verify Cy().run() without check_types still executes normally.

        REGRESSION TEST: Default behavior should be unchanged.
        """
        cy = Cy()  # check_types=False (default)

        script = """
x = 5
y = 10
result = x + y
return result
"""

        result = cy.run(script)

        assert result == "15"

    def test_cy_run_with_input_data_still_works(self):
        """
        Verify Cy().run() with input_data works.

        REGRESSION TEST: Input data handling unchanged.
        """
        cy = Cy()

        script = """
name = input.name
greeting = "Hello, " + name
return greeting
"""

        result = cy.run(script, input_data={"name": "Alice"})

        assert "Alice" in result

    def test_analyze_types_without_tool_registry(self):
        """
        Verify analyze_types() works without tool_registry parameter.

        REGRESSION TEST: Should work with native tools only.
        """
        script = """
arr = [1, 2, 3]
first = arr[0]
return first
"""

        output_schema = analyze_types(script)

        # Array indexing returns union with null (index might be out of bounds)
        assert output_schema == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_analyze_types_accepts_dict_backward_compat(self):
        """
        Verify analyze_types() still accepts old dict format for tool_registry.

        REGRESSION TEST: Backward compatibility with API.
        """
        # Old dict format (pre-Pydantic)
        # Use simple tool name (not FQN) for backward compat
        tool_registry_dict = {
            "my_tool": {
                "parameters": {"x": {"type": "number"}},
                "return_type": {"type": "string"},
            }
        }

        script = """
result = my_tool(x=5)
return result
"""

        # Should work - my_tool will become custom::my_tool internally
        output_schema = analyze_types(script, tool_registry=tool_registry_dict)
        assert output_schema == {"type": "string"}

    def test_analyze_types_with_input_schema(self):
        """
        Verify analyze_types() with input_schema works.

        Use strict_input=True to get non-nullable types from input.
        """
        script = """
user_age = input.age
is_adult = user_age >= 18
return is_adult
"""

        input_schema = {"type": "object", "properties": {"age": {"type": "number"}}}

        # Use strict_input=True to get non-nullable input.age type
        output_schema = analyze_types(
            script, input_schema=input_schema, strict_input=True
        )

        assert output_schema == {"type": "boolean"}


class TestExistingToolFunctionality:
    """Test that existing tool functionality is unchanged."""

    def test_native_tools_still_work_in_execution(self):
        """
        Verify native tools (len, str, etc.) still execute correctly.

        REGRESSION TEST: Tool execution unchanged.
        """
        cy = Cy()

        script = """
arr = [1, 2, 3, 4, 5]
count = len(arr)
return count
"""

        result = cy.run(script)

        assert result == "5"

    def test_str_tool_execution(self):
        """
        Verify str() tool works correctly.

        REGRESSION TEST: str() execution unchanged.
        """
        cy = Cy()

        script = """
number = 42
text = str(number)
return text
"""

        result = cy.run(script)

        assert result == '"42"'

    def test_int_tool_execution(self):
        """
        Verify int() tool works correctly.

        REGRESSION TEST: int() execution unchanged.
        """
        cy = Cy()

        script = """
text = "123"
number = int(text)
doubled = number * 2
return doubled
"""

        result = cy.run(script)

        assert result == "246"

    def test_tool_resolver_from_native_tools_still_works(self):
        """
        Verify ToolResolver.from_native_tools() unchanged.

        REGRESSION TEST: Existing ToolResolver API works.
        """
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()

        # Should have native tools
        assert resolver.has_tool("native::tools::len")
        assert resolver.has_tool(
            "native::type::str"
        )  # str is registered as native::type::str

        # Should have tool signatures
        len_sig = resolver.get_tool_signature("native::tools::len")
        assert len_sig is not None
        assert len_sig.return_type == {"type": "number"}


class TestTypeCheckingFeatures:
    """Test that type checking features still work."""

    def test_type_checking_with_check_types_flag(self):
        """
        Verify Cy(check_types=True) still works for non-tool type errors.

        REGRESSION TEST: type checking unchanged.
        """
        cy = Cy(check_types=True)

        script = """
x = 5
y = "text"
result = x + y
return result
"""

        # Should raise TypeError for number + string
        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_analyze_types_catches_type_errors(self):
        """
        Verify analyze_types() catches type errors.

        REGRESSION TEST: analyze_types() behavior unchanged.
        """
        script = """
a = 10
b = "hello"
result = a + b
return result
"""

        # Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg or "incompatible" in error_msg

    def test_analyze_types_infers_correct_types(self):
        """
        Verify analyze_types() infers types correctly.

        REGRESSION TEST: Type inference unchanged.
        """
        script = """
x = 5
y = 10
sum_val = x + y
return sum_val
"""

        output_schema = analyze_types(script)

        assert output_schema == {"type": "number"}

    def test_conditional_type_inference(self):
        """
        Verify conditional expressions still type-check correctly.

        REGRESSION TEST: Control flow type inference unchanged.
        """
        script = """
x = 10
if (x > 5) {
    result = "big"
} else {
    result = "small"
}
return result
"""

        output_schema = analyze_types(script)

        assert output_schema == {"type": "string"}

    def test_strict_input_validation_still_works(self):
        """
        Verify strict_input validation still works.

        REGRESSION TEST: strict_input flag unchanged.
        """
        script = """
value = input.nonexistent_field
return value
"""

        input_schema = {
            "type": "object",
            "properties": {"existing_field": {"type": "string"}},
        }

        # With strict_input=True, should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=input_schema, strict_input=True)

        error_msg = str(exc_info.value).lower()
        assert "nonexistent_field" in error_msg or "field" in error_msg


class TestNoRegressions:
    """Test that nothing was accidentally broken."""

    def test_basic_arithmetic_still_works(self):
        """
        Verify basic arithmetic operations work.

        REGRESSION TEST: Core language features unchanged.
        """
        cy = Cy()

        script = """
a = 5
b = 3
sum_val = a + b
diff = a - b
product = a * b
quotient = a / b
return product
"""

        result = cy.run(script)

        assert result == "15"

    def test_string_concatenation_still_works(self):
        """
        Verify string concatenation works.

        REGRESSION TEST: String operations unchanged.
        """
        cy = Cy()

        script = """
first = "Hello"
second = "World"
result = first + " " + second
return result
"""

        result = cy.run(script)

        assert "Hello World" in result

    def test_array_operations_still_work(self):
        """
        Verify array operations work.

        REGRESSION TEST: Array features unchanged.
        """
        cy = Cy()

        script = """
arr = [1, 2, 3]
first = arr[0]
last = arr[2]
return first + last
"""

        result = cy.run(script)

        assert result == "4"

    def test_object_field_access_still_works(self):
        """
        Verify object field access works.

        REGRESSION TEST: Object operations unchanged.
        """
        cy = Cy()

        script = """
user = {"name": "Alice", "age": 30}
user_name = user.name
return user_name
"""

        result = cy.run(script)

        assert result == '"Alice"'
