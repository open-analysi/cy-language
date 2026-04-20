"""Unit tests for try/catch type inference.

Tests that TryCatchNode is properly supported in the type inference engine,
including type checking and strict_input validation within try/catch blocks.
"""

import pytest

from cy_language import analyze_types


class TestTryCatchBasicInference:
    """Test basic type inference for try/catch blocks."""

    def test_try_catch_simple_assignment(self):
        """Type inference: Simple assignment in try block causes type error."""
        script = """
try {
    x = 5
    y = "hello"
} catch (error) {
    x = 10
    y = "error"
}
return x + y
"""
        # x could be 5 or 10 (both numbers), y could be "hello" or "error" (both strings)
        # So x + y should fail type checking (number + string)
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()

    def test_try_catch_with_type_checking(self):
        """Type checking: Valid types in try/catch."""
        script = """
try {
    x = 5
    result = x + 10
} catch (error) {
    result = 0
}
return result
"""
        # Should pass type checking - all number operations
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}

    def test_try_catch_type_error_in_try_block(self):
        """Type checking: Type error in try block detected."""
        script = """
try {
    x = 5
    y = "text"
    result = x + y
} catch (error) {
    result = 0
}
return result
"""
        # Should raise TypeError - cannot add number + string
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()

    def test_try_catch_type_error_in_catch_block(self):
        """Type checking: Type error in catch block detected."""
        script = """
try {
    result = 5
} catch (error) {
    x = 10
    y = "text"
    result = x + y
}
return result
"""
        # Should raise TypeError - cannot add number + string in catch
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()


class TestTryCatchExceptionVariable:
    """Test exception variable type inference."""

    def test_exception_variable_is_string(self):
        """Exception variable should be inferred as string type."""
        script = """
try {
    x = 5
} catch (error) {
    message = error + " occurred"
}
return message
"""
        # Should pass - error is string, can concatenate with string
        output_schema = analyze_types(script)
        assert output_schema == {"type": "string"}

    def test_exception_variable_cannot_add_number(self):
        """Exception variable string type prevents invalid operations."""
        script = """
try {
    x = 5
} catch (error) {
    result = error + 10
}
return result
"""
        # Should raise TypeError - cannot add string + number
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()

    def test_exception_variable_in_string_operation(self):
        """Exception variable works in string operations."""
        script = """
try {
    x = 5
} catch (err) {
    prefix = "Error: "
    full_message = prefix + err
}
return full_message
"""
        # Should pass - both strings
        output_schema = analyze_types(script)
        assert output_schema == {"type": "string"}


class TestTryCatchMultipleClauses:
    """Test try/catch with multiple catch clauses."""

    def test_multiple_catch_clauses(self):
        """Multiple catch clauses should all be processed."""
        script = """
try {
    result = 5
} catch (error1) {
    result = 10
} catch (error2) {
    result = 15
}
return result
"""
        # Should pass - all assignments are numbers
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}

    def test_type_error_in_second_catch_clause(self):
        """Type error in second catch clause detected."""
        script = """
try {
    result = 5
} catch (error1) {
    result = 10
} catch (error2) {
    x = 5
    y = "text"
    result = x + y
}
return result
"""
        # Should raise TypeError in second catch clause
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()


class TestTryCatchFinally:
    """Test try/catch/finally blocks."""

    def test_try_catch_finally_basic(self):
        """Basic try/catch/finally type inference."""
        script = """
try {
    x = 5
} catch (error) {
    x = 10
} finally {
    y = 20
}
return x + y
"""
        # Should pass - all number operations
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}

    def test_type_error_in_finally_block(self):
        """Type error in finally block detected."""
        script = """
try {
    result = 5
} catch (error) {
    result = 10
} finally {
    a = 5
    b = "text"
    result = a + b
}
return result
"""
        # Should raise TypeError in finally block
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()


class TestTryCatchNested:
    """Test nested try/catch blocks."""

    def test_nested_try_catch(self):
        """Nested try/catch type inference."""
        script = """
try {
    outer = 5
    try {
        inner = 10
        result = outer + inner
    } catch (inner_error) {
        result = outer
    }
} catch (outer_error) {
    result = 0
}
return result
"""
        # Should pass - all number operations
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}

    def test_nested_try_catch_type_error_in_inner(self):
        """Type error in inner try/catch detected."""
        script = """
try {
    outer = 5
    try {
        x = 10
        y = "text"
        result = x + y
    } catch (inner_error) {
        result = 0
    }
} catch (outer_error) {
    result = 0
}
return result
"""
        # Should raise TypeError in inner try block
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)

        error_msg = str(exc_info.value)
        assert "cannot add" in error_msg.lower()


class TestTryCatchWithStrictInput:
    """Test strict_input validation within try/catch blocks."""

    def test_strict_input_valid_field_in_try(self):
        """strict_input: Valid field access in try block."""
        script = """
try {
    data = input["valid_field"]
    result = data + " processed"
} catch (error) {
    result = "error"
}
return result
"""
        schema = {"type": "object", "properties": {"valid_field": {"type": "string"}}}

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_invalid_field_in_try(self):
        """strict_input: Invalid field access in try block raises."""
        script = """
try {
    data = input["invalid_field"]
    result = data
} catch (error) {
    result = "error"
}
return result
"""
        schema = {"type": "object", "properties": {"valid_field": {"type": "string"}}}

        # Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "invalid_field" in error_msg.lower()
        assert "valid_field" in error_msg

    def test_strict_input_invalid_field_in_catch(self):
        """strict_input: Invalid field access in catch block raises."""
        script = """
try {
    result = "success"
} catch (error) {
    fallback = input["missing_field"]
    result = fallback
}
return result
"""
        schema = {
            "type": "object",
            "properties": {"existing_field": {"type": "string"}},
        }

        # Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "missing_field" in error_msg.lower()

    def test_strict_input_invalid_field_in_finally(self):
        """strict_input: Invalid field access in finally block raises."""
        script = """
try {
    result = "success"
} catch (error) {
    result = "error"
} finally {
    log_data = input["log_field"]
}
return result
"""
        schema = {"type": "object", "properties": {"result_field": {"type": "string"}}}

        # Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "log_field" in error_msg.lower()


class TestTryCatchWithControlFlow:
    """Test try/catch interaction with other control flow."""

    def test_try_catch_with_if_statement(self):
        """Try/catch containing if statement."""
        script = """
try {
    x = 5
    if (x > 0) {
        result = "positive"
    } else {
        result = "non-positive"
    }
} catch (error) {
    result = "error"
}
return result
"""
        # Should pass
        output_schema = analyze_types(script)
        assert output_schema == {"type": "string"}

    def test_try_catch_with_loop(self):
        """Try/catch containing while loop."""
        script = """
count = 0

try {
    while (count < 5) {
        count = count + 1
    }
} catch (error) {
    count = 0
}

return count
"""
        # Should pass
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}

    def test_if_containing_try_catch(self):
        """If statement containing try/catch."""
        script = """
x = 5

if (x > 0) {
    try {
        result = 10
    } catch (error) {
        result = 0
    }
} else {
    result = -1
}

return result
"""
        # Should pass
        output_schema = analyze_types(script)
        assert output_schema == {"type": "number"}
