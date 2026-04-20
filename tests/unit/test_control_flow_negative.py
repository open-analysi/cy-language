"""
Comprehensive negative test cases for control flow constructs.

This module tests error conditions, edge cases, and malformed syntax
with particular focus on nested braces and complex control flow scenarios.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestNestedBraceMismatches:
    """Test various brace mismatch scenarios in nested control flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_if_missing_opening_brace(self):
        """Test if statement with missing opening brace."""
        program = """        x = 5
        if (x > 0)
            output = "positive"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_if_missing_closing_brace(self):
        """Test if statement with missing closing brace."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
        # Missing closing brace
        y = 10
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_while_missing_opening_brace(self):
        """Test while loop with missing opening brace."""
        program = """        counter = 0
        while (counter < 3)
            counter = counter + 1
        }
        output = counter
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_while_missing_closing_brace(self):
        """Test while loop with missing closing brace."""
        program = """        counter = 0
        while (counter < 3) {
            counter = counter + 1
        # Missing closing brace
        output = counter
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_nested_if_missing_inner_opening_brace(self):
        """Test nested if with missing inner opening brace."""
        program = """        x = 5
        y = 3
        if (x > 0) {
            if (y > 0)
                output = "both positive"
            }
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_nested_if_missing_inner_closing_brace(self):
        """Test nested if with missing inner closing brace."""
        program = """        x = 5
        y = 3
        if (x > 0) {
            if (y > 0) {
                output = "both positive"
            # Missing inner closing brace
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_nested_if_missing_outer_closing_brace(self):
        """Test nested if with missing outer closing brace."""
        program = """        x = 5
        y = 3
        if (x > 0) {
            if (y > 0) {
                output = "both positive"
            }
        # Missing outer closing brace
        z = 1
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_if_while_nested_missing_braces(self):
        """Test if containing while with various missing braces."""
        program = """        x = 5
        if (x > 0) {
            counter = 0
            while (counter < 2) {
                counter = counter + 1
            # Missing while closing brace
        }
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_while_if_nested_missing_braces(self):
        """Test while containing if with various missing braces."""
        program = """        counter = 0
        while (counter < 3) {
            if (counter == 1) {
                output = "one"
            # Missing if closing brace
            counter = counter + 1
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)


class TestDeeplyNestedErrorScenarios:
    """Test error conditions in deeply nested control flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_deeply_nested_brace_mismatch_level3(self):
        """Test 3-level nested control flow with brace mismatch."""
        program = """        x = 5
        if (x > 0) {
            y = 3
            if (y > 0) {
                counter = 0
                while (counter < 2) {
                    counter = counter + 1
                # Missing while closing brace
            }
        }
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_deeply_nested_brace_mismatch_level4(self):
        """Test 4-level nested control flow with brace mismatch."""
        program = """        a = 1
        if (a > 0) {
            b = 2
            while (b > 0) {
                c = 3
                if (c > 0) {
                    d = 4
                    if (d > 0) {
                        output = "deep"
                    # Missing innermost if closing brace
                }
                b = b - 1
            }
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_mixed_nesting_with_elif_brace_errors(self):
        """Test nested if/elif/else with while and brace errors."""
        program = """        x = 5
        if (x > 10) {
            output = "large"
        } elif (x > 0) {
            counter = 0
            while (counter < x) {
                if (counter == 2) {
                    output = "found two"
                } else {
                    counter = counter + 1
                # Missing else closing brace
            }
        } else {
            output = "zero or negative"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_return_in_deeply_nested_missing_braces(self):
        """Test return statements in deeply nested control flow with missing braces."""
        program = """        x = 5
        if (x > 0) {
            counter = 0
            while (counter < 3) {
                if (counter == 1) {
                    return "early exit"
                # Missing if closing brace
                counter = counter + 1
            }
        }
        return "normal exit"
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)


class TestMalformedSyntaxEdgeCases:
    """Test malformed syntax and edge cases in control flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_if_with_extra_opening_brace(self):
        """Test if statement with extra opening brace."""
        program = """        x = 5
        if (x > 0) {{
            output = "positive"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_while_with_extra_closing_brace(self):
        """Test while loop with extra closing brace."""
        program = """        counter = 0
        while (counter < 3) {
            counter = counter + 1
        }}
        output = counter
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_mismatched_brace_types(self):
        """Test using wrong brace types (if this ever becomes an issue).

        The parser may interpret '[' in various ways depending on context.
        We just verify that an error is raised.
        """
        program = """        x = 5
        if (x > 0) [
            output = "positive"
        ]
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Accept various error messages related to syntax issues
        error_msg = str(exc_info.value)
        assert any(
            keyword in error_msg
            for keyword in ["Unexpected", "Expected", "Mixed", "bracket", "notation"]
        )

    def test_nested_empty_blocks_with_missing_braces(self):
        """Test nested empty blocks with missing braces."""
        program = """        x = 5
        if (x > 0) {
            if (x > 3) {
            # Missing closing brace for inner if
        }
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_elif_without_if(self):
        """Test elif clause without preceding if."""
        program = """        x = 5
        elif (x > 0) {
            output = "positive"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_else_without_if(self):
        """Test else clause without preceding if."""
        program = """        x = 5
        else {
            output = "fallback"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)

    def test_multiple_else_clauses(self):
        """Test multiple else clauses for same if."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
        } else {
            output = "not positive"
        } else {
            output = "another else"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)


class TestComplexNestedRuntimeErrors:
    """Test runtime errors in complex nested scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_undefined_variable_in_nested_condition(self):
        """Test undefined variable in deeply nested condition."""
        program = """        x = 5
        if (x > 0) {
            counter = 0
            while (counter < 3) {
                if (undefined_var > 0) {
                    output = "found"
                }
                counter = counter + 1
            }
        }
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)

    def test_division_by_zero_in_nested_while_condition(self):
        """Test division by zero in nested while loop condition."""
        program = """        x = 5
        if (x > 0) {
            y = 0
            counter = 0
            while ((counter / y) < 10) {
                counter = counter + 1
            }
        }
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Division by zero" in str(exc_info.value)

    def test_infinite_loop_in_nested_structure(self):
        """Test infinite loop protection in nested structure."""
        program = """        x = 5
        if (x > 0) {
            counter = 0
            while (True) {
                if (counter > 5000) {
                    # This should never be reached due to loop protection
                    output = "should not reach here"
                }
                counter = counter + 1
            }
        }
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "iterations" in str(exc_info.value).lower()

    def test_return_statement_error_propagation(self):
        """Test that return statement errors propagate correctly through nesting."""
        program = """        x = 5
        if (x > 0) {
            counter = 0
            while (counter < 3) {
                if (counter == 1) {
                    return undefined_return_var
                }
                counter = counter + 1
            }
        }
        return "done"
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)


class TestBoundaryConditions:
    """Test boundary conditions and stress scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_maximum_nesting_depth_with_error(self):
        """Test very deep nesting with an error at the bottom."""
        program = """        level = 1
        if (level == 1) {
            level = 2
            if (level == 2) {
                level = 3
                if (level == 3) {
                    level = 4
                    if (level == 4) {
                        level = 5
                        if (level == 5) {
                            level = 6
                            if (level == 6) {
                                # Error at maximum depth
                                output = undefined_deep_var
                            } else {
                                output = "fallback"
                            }
                        } else {
                            output = "fallback"
                        }
                    } else {
                        output = "fallback"
                    }
                } else {
                    output = "fallback"
                }
            } else {
                output = "fallback"
            }
        } else {
            output = "fallback"
        }
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)

    def test_alternating_if_while_nesting_with_error(self):
        """Test alternating if/while nesting with error."""
        program = """        a = 1
        if (a > 0) {
            b = 2
            while (b > 0) {
                c = 3
                if (c > 0) {
                    d = 0
                    while (d < 2) {
                        # Division by zero in deep nesting
                        result = 10 / (d - d)
                        d = d + 1
                    }
                }
                b = b - 1
            }
        }
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Division by zero" in str(exc_info.value)

    def test_empty_nested_blocks_with_syntax_error(self):
        """Test multiple empty nested blocks with syntax error."""
        program = """        x = 5
        if (x > 0) {
            if (x > 3) {
                while (x > 0) {
                    if (x == 5) {
                        # Empty block with syntax error after
                    }
                    x = x - 1
                }
            }
        # Missing closing brace somewhere
        output = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Unexpected" in str(exc_info.value) or "Expected" in str(exc_info.value)
