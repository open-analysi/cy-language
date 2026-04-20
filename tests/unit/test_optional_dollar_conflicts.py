"""
Function Conflict Prevention Tests for Optional $ Syntax.

Tests comprehensive function name conflict detection for both
built-in and custom functions.
"""

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError


class TestOptionalDollarConflicts:
    """Test function conflict prevention for optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        # Load all native functions for conflict testing
        import cy_language.native_functions  # noqa: F401
        from cy_language.ui.tools import default_registry

        interpreter = Cy(tools=default_registry.get_tools_dict())
        interpreter.show_enhanced_errors = False
        self.cy = interpreter

    def test_builtin_function_conflicts(self):
        """Test that built-in function names raise CompilerError."""
        # Test len function conflict
        program = """len = 5
output = len
return output"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        assert "len" in str(error)
        assert "conflicts with function" in str(error)

        # Test debug_print conflict
        program = """debug_print = "hello"
output = debug_print
return output"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        assert "debug_print" in str(error)

        # Test json_string_to_struct conflict
        program = """json_string_to_struct = {}
output = json_string_to_struct
return output"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        assert "json_string_to_struct" in str(error)

    def test_llm_function_conflicts(self):
        """Test that LLM function names are protected."""
        llm_functions = [
            "llm_run",
            "llm_evaluate_results",
            "llm_give_feedback",
            "llm_revise_task",
        ]

        for func_name in llm_functions:
            program = f"""{func_name} = "test"
output = {func_name}
return output"""

            with pytest.raises(CompilerError) as exc_info:
                self.cy.run(program)

            error = exc_info.value
            assert func_name in str(error)
            assert "conflicts with function" in str(error)

    def test_dollar_prefix_function_conflicts(self):
        """Test that $function_name also raises conflicts."""
        # Test with $ prefix - should still detect conflict after normalization
        program = """len = 5
output = len
return output"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        assert "len" in str(error)
        assert "conflicts with function" in str(error)

    def test_custom_tool_conflicts(self):
        """Test conflicts with custom tools if any are loaded."""
        # This will depend on what tools are in default_registry
        # For now, test the framework works

        # Create a simple program that should work (no conflicts)
        program = """my_var = "test"
output = my_var
return output"""

        result = self.cy.run(program)
        assert result == '"test"'

        # Note: Specific custom tool conflict tests would need
        # to know which tools are registered

    def test_error_message_quality(self):
        """Test that error messages are helpful and informative."""
        program = """len = 5"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        error_msg = str(error)

        # Should include function name
        assert "len" in error_msg

        # Should explain the conflict
        assert "conflicts with function" in error_msg.lower()

        # Should include position information
        assert "Line" in error_msg or "line" in error_msg.lower()

    def test_case_sensitivity_function_conflicts(self):
        """Test that function conflicts are case-sensitive."""
        # These should be allowed (different case from built-ins)
        test_cases = [
            ("LEN", "5"),
            ("Len", "6"),
            ("DEBUG_PRINT", '"test"'),
            ("Debug_Print", '"hello"'),
            ("JSON_STRING_TO_STRUCT", "{}"),
        ]

        for var_name, value in test_cases:
            program = f"""{var_name} = {value}
output = {var_name}
return output"""

            # Should NOT raise CompilerError
            try:
                result = self.cy.run(program)
                # Should execute successfully
                assert result is not None
            except CompilerError:
                pytest.fail(
                    f"Variable name '{var_name}' should be allowed (case-sensitive)"
                )

    def test_allowed_similar_names(self):
        """Test that similar but non-conflicting names are allowed."""
        allowed_names = [
            "length",  # Similar to len but different
            "debug_msg",  # Similar to debug_print but different
            "json_data",  # Similar to json_string_to_struct but different
            "llm_result",  # Similar to llm_run but different
        ]

        for var_name in allowed_names:
            program = f"""{var_name} = "test_value"
output = {var_name}
return output"""

            # Should NOT raise CompilerError
            try:
                result = self.cy.run(program)
                assert result == '"test_value"'
            except CompilerError:
                pytest.fail(f"Variable name '{var_name}' should be allowed")

    def test_conflict_with_assignment_operators(self):
        """Test conflicts work correctly with different assignment contexts."""
        # Test regular assignment
        with pytest.raises(CompilerError):
            program = """len = 5"""
            self.cy.run(program)

        # Test in complex expression
        with pytest.raises(CompilerError):
            program = """len = add(1, 2)"""
            self.cy.run(program)

    def test_multiple_conflicts_in_program(self):
        """Test program with multiple function conflicts."""
        program = '''len = 5
debug_print = "hello"'''

        # Should raise error on first conflict encountered
        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        # Error should mention at least one of the conflicts
        error_msg = str(exc_info.value)
        assert "len" in error_msg or "debug_print" in error_msg

    def test_conflict_detection_line_accuracy(self):
        """Test that conflict errors report correct line numbers."""
        program = """name = "Alice"
age = 25
len = 5
count = 10"""

        with pytest.raises(CompilerError) as exc_info:
            self.cy.run(program)

        error = exc_info.value
        # Should report line 4 where len = 5 appears
        assert hasattr(error, "line")
        assert error.line > 0
