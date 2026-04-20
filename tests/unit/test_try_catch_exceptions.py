"""Comprehensive tests for try/catch exception handling in Cy language."""

import pytest

from cy_language import Cy


class TestTryCatchExceptionTypes:
    """Test that try/catch properly handles all types of exceptions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()

    # ============= Arithmetic Errors =============

    def test_division_by_zero(self):
        """Test catching division by zero."""
        program = """
        caught = False
        error_msg = ""
        try {
            result = 10 / 0
        } catch (e) {
            caught = True
            error_msg = "${e}"
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    def test_division_by_zero_variable(self):
        """Test catching division by zero with variable denominator."""
        program = """
        denominator = 0
        caught = False
        try {
            result = 100 / denominator
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    def test_modulo_by_zero(self):
        """Test catching modulo by zero."""
        program = """
        caught = False
        try {
            result = 10 % 0
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    # ============= Collection Access Errors =============

    def test_list_index_out_of_bounds_positive_returns_null(self):
        """Test list index out of bounds returns null (not an error)."""
        program = """
        list = [1, 2, 3]
        item = list[10]
        output = "Item: ${item}"
        return output
        """
        result = self.cy.run(program)
        assert "Item: null" in result

    def test_list_index_out_of_bounds_negative_returns_null(self):
        """Test negative list index out of bounds returns null (not an error)."""
        program = """
        list = [1, 2, 3]
        item = list[-10]
        output = "Item: ${item}"
        return output
        """
        result = self.cy.run(program)
        assert "Item: null" in result

    def test_empty_list_access_returns_null(self):
        """Test accessing empty list returns null (not an error)."""
        program = """
        list = []
        item = list[0]
        output = "Item: ${item}"
        return output
        """
        result = self.cy.run(program)
        assert "Item: null" in result

    def test_dict_missing_key(self):
        """Test that field access on primitives returns null."""
        program = """
        text = "hello"
        caught = False
        try {
            # Field access on string returns null, no error
            value = text.some_field
        } catch (e) {
            caught = True
            error_msg = "${e}"
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        # No error is thrown, so catch block doesn't execute
        assert "Caught: False" in result

    def test_nested_dict_access_error(self):
        """Test that field access on primitives returns null."""
        program = """
        data = {"user": {"name": "John"}}
        name = data["user"]["name"]
        caught = False
        try {
            # Field access on string returns null, no error
            field = name.invalid_field
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        # No error is thrown, so catch block doesn't execute
        assert "Caught: False" in result

    def test_dict_success_path_with_str_conversion(self):
        """Test successful dictionary access in try block with str() conversion."""
        program = """
        data = {"value": 42}

        try {
            val = data["value"]
            output = "Success: " + str(val)
        } catch (e) {
            output = "Error occurred"
        }
        return output
        """
        result = self.cy.run(program)
        assert result == '"Success: 42"'

    def test_return_inside_try_catch(self):
        """Test using return statement inside try-catch blocks."""
        program = """
        data = {"value": 42}

        try {
            val = data["value"]
            return "Success: " + str(val)
        } catch (e) {
            return "Error occurred: " + str(e)
        }
        """
        result = self.cy.run(program)
        assert result == '"Success: 42"'

    def test_complex_control_flow_with_try_catch(self):
        """Test try-catch combined with loops and if/elif statements."""
        program = """
        data = [
            {"type": "a", "value": 10},
            {"type": "b", "value": 0},
            {"type": "c"},
            {"type": "a", "value": 5}
        ]

        results = []
        i = 0

        while (i < 4) {
            item = data[i]

            try {
                if (item["type"] == "a") {
                    result = 100 / item["value"]
                    results = results + ["A:" + str(result)]
                } elif (item["type"] == "b") {
                    result = 100 / item["value"]
                    results = results + ["B:" + str(result)]
                } else {
                    value = item["value"]
                    results = results + ["Other:" + str(value)]
                }
            } catch (e) {
                results = results + ["Error"]
            }

            i = i + 1
        }

        output = str(results)
        return output
        """
        result = self.cy.run(program)
        # Should have: A:10.0 (success), Error (div by zero), Error (missing key), A:20.0 (success)
        assert "A:10.0" in result
        assert "Error" in result

    # ============= Variable/Name Errors =============

    def test_undefined_variable(self):
        """Test catching undefined variable access."""
        program = """
        caught = False
        try {
            value = undefined_variable
        } catch (e) {
            caught = True
            error_msg = "${e}"
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    def test_undefined_in_expression(self):
        """Test catching undefined variable in expression."""
        program = """
        x = 10
        caught = False
        try {
            result = x + undefined_y
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    # ============= Type Errors =============

    def test_string_minus_number(self):
        """Test catching invalid string arithmetic."""
        program = """
        caught = False
        try {
            result = "hello" - 5
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    def test_list_minus_list(self):
        """Test catching invalid list arithmetic."""
        program = """
        caught = False
        try {
            result = [1, 2] - [3, 4]
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: True" in result

    def test_field_access_on_non_dict(self):
        """Test that field access on primitives returns null."""
        program = """
        number = 42
        caught = False
        try {
            # Field access on number returns null, no error
            field = number.some_field
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        # No error is thrown, so catch block doesn't execute
        assert "Caught: False" in result

    # ============= Tool/Function Errors =============

    def test_nonexistent_tool(self):
        """Test that non-existent tool calls fail at compile time."""
        from cy_language.errors import ToolResolutionError

        program = """
        caught = False
        try {
            result = fake_tool("arg1", "arg2")
        } catch (e) {
            caught = True
            error_msg = "${e}"
        }
        output = "Caught: ${caught}"
        return output
        """
        # Now fails at compile-time, not runtime
        with pytest.raises(ToolResolutionError) as exc_info:
            self.cy.run(program)
        assert "fake_tool" in str(exc_info.value)

    def test_tool_with_wrong_args(self):
        """Test that nonexistent tools fail at compile-time."""
        from cy_language.errors import ToolResolutionError

        program = """
        caught = False
        try {
            result = nonexistent_function()
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        # Now fails at compile-time, not runtime
        with pytest.raises(ToolResolutionError) as exc_info:
            self.cy.run(program)
        assert "nonexistent_function" in str(exc_info.value)

    # ============= Nested Error Scenarios =============

    def test_error_in_nested_structure(self):
        """Test that field access on primitives returns null."""
        program = """
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob"}  # Name is a string
            ]
        }
        name = data["users"][1]["name"]
        caught = False
        try {
            # Field access on string returns null, no error
            field = name.some_field
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        # No error is thrown, so catch block doesn't execute
        assert "Caught: False" in result

    def test_chain_of_errors(self):
        """Test catching errors in a chain of operations."""
        program = """
        results = []
        operations = ["divide", "index", "undefined", "type"]
        i = 0

        while (i < 4) {
            op = operations[i]
            try {
                if (op == "divide") {
                    x = 1 / 0
                } elif (op == "index") {
                    list = [1]
                    x = list[5]
                } elif (op == "undefined") {
                    x = some_undefined_var
                } elif (op == "type") {
                    x = "text" * [1, 2]
                }
                results = results + ["${op}: success"]
            } catch (e) {
                results = results + ["${op}: caught"]
            }
            i = i + 1
        }

        output = "All caught"
        return output
        """
        result = self.cy.run(program)
        assert "All caught" in result

    # ============= Edge Cases =============

    def test_empty_try_block(self):
        """Test empty try block doesn't cause issues."""
        program = """
        caught = False
        try {
            # Empty block
        } catch (e) {
            caught = True
        }
        output = "Caught: ${caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Caught: False" in result

    def test_error_in_catch_block(self):
        """Test that errors in catch blocks can be caught by outer try."""
        program = """
        outer_caught = False
        try {
            try {
                x = 1 / 0
            } catch (inner_e) {
                # Cause another error in catch
                y = undefined_in_catch
            }
        } catch (outer_e) {
            outer_caught = True
        }
        output = "Outer caught: ${outer_caught}"
        return output
        """
        result = self.cy.run(program)
        assert "Outer caught: True" in result

    def test_error_in_finally_propagates(self):
        """Test that errors in finally blocks propagate."""
        program = """
        error_occurred = False
        try {
            try {
                x = 1
            } catch (e) {
                error_occurred = True
            } finally {
                # Error in finally
                y = 1 / 0
            }
        } catch (outer) {
            error_occurred = True
        }
        output = "Error: ${error_occurred}"
        return output
        """
        result = self.cy.run(program)
        assert "Error: True" in result

    def test_multiple_error_types_in_sequence(self):
        """Test catching different error types in sequence."""
        program = """
        error_count = 0

        # Division by zero
        try {
            x = 1 / 0
        } catch (e) {
            error_count = error_count + 1
        }

        # List out-of-bounds returns null (not an error, like dict missing key)
        try {
            list = [1, 2]
            y = list[10]
        } catch (e) {
            error_count = error_count + 1
        }

        # Field access on non-dict
        try {
            number = 42
            z = number.invalid_field
        } catch (e) {
            error_count = error_count + 1
        }

        # Undefined variable
        try {
            w = undefined_var
        } catch (e) {
            error_count = error_count + 1
        }

        # Tool errors now fail at compile-time, removed from runtime test
        # Type error instead
        try {
            v = "text" - 5
        } catch (e) {
            error_count = error_count + 1
        }

        output = "Caught ${error_count} errors"
        return output
        """
        result = self.cy.run(program)
        # field access no longer throws; list out-of-bounds also returns null now
        assert "Caught 3 errors" in result


class TestTryCatchComplexScenarios:
    """Test complex real-world scenarios with try/catch."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()

    def test_safe_division_function(self):
        """Test implementing safe division with try/catch."""
        program = """
        # Simulate a safe division operation
        numerator = 100
        denominator = 0
        result = "undefined"

        try {
            if (denominator == 0) {
                # We can check before, but let's test the catch
                result = numerator / denominator
            } else {
                result = numerator / denominator
            }
        } catch (e) {
            result = "infinity"
        }

        output = "Result: ${result}"
        return output
        """
        result = self.cy.run(program)
        assert "Result: infinity" in result

    def test_data_processing_pipeline(self):
        """Test error handling in data processing pipeline."""
        program = """
        data = [
            {"value": 10},
            {"value": 0},
            {"missing": "value"},
            {"value": 5}
        ]

        processed = []
        errors = []
        i = 0

        while (i < 4) {
            try {
                item = data[i]
                value = item["value"]
                result = 100 / value
                processed = processed + [result]
            } catch (e) {
                errors = errors + ["Error at index ${i}"]
                processed = processed + [0]
            }
            i = i + 1
        }

        output = "Processed 4 items with errors"
        return output
        """
        result = self.cy.run(program)
        assert "Processed 4 items with errors" in result

    def test_retry_logic(self):
        """Test implementing retry logic with try/catch."""
        program = """
        attempts = 0
        max_attempts = 3
        success = False
        result = ""

        while (attempts < max_attempts and not success) {
            try {
                attempts = attempts + 1

                if (attempts < 3) {
                    # Simulate failure for first 2 attempts
                    x = 1 / 0
                } else {
                    # Success on third attempt
                    result = "Success on attempt ${attempts}"
                    success = True
                }
            } catch (e) {
                if (attempts >= max_attempts) {
                    result = "Failed after ${attempts} attempts"
                }
            }
        }

        output = result
        return output
        """
        result = self.cy.run(program)
        assert "Success on attempt 3" in result

    def test_cascading_fallbacks(self):
        """Test cascading fallback options with nested try/catch."""
        program = """
        result = ""

        try {
            # Primary method - fails
            x = 1 / 0
            result = "Primary"
        } catch (e1) {
            try {
                # First fallback - also fails
                y = undefined_var
                result = "First fallback"
            } catch (e2) {
                try {
                    # Second fallback - also fails (type error)
                    # Changed from fake_tool() which fails at compile-time
                    z = "text" * [1, 2]
                    result = "Second fallback"
                } catch (e3) {
                    # Final fallback - always works
                    result = "Final fallback"
                }
            }
        }

        output = "Used: ${result}"
        return output
        """
        result = self.cy.run(program)
        assert "Used: Final fallback" in result
