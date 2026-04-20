"""
Tests for Variable Normalization Foundation.

Tests the VariableNormalizer class that provides canonical name storage
and function conflict detection for optional $ syntax.
"""

from cy_language.variable_normalizer import VariableNormalizer


class TestVariableNormalizer:
    """Test the VariableNormalizer class functionality."""

    def test_normalize_name_with_dollar_prefix(self):
        """Test normalize_name() with $ prefix variables."""
        # Test basic variable names
        assert VariableNormalizer.normalize_name("$name") == "name"
        assert VariableNormalizer.normalize_name("$user_id") == "user_id"
        assert VariableNormalizer.normalize_name("$data123") == "data123"

        # Test longer variable names
        assert (
            VariableNormalizer.normalize_name("$very_long_variable_name")
            == "very_long_variable_name"
        )
        assert VariableNormalizer.normalize_name("$camelCaseVar") == "camelCaseVar"

    def test_normalize_name_without_dollar_prefix(self):
        """Test normalize_name() without $ prefix variables."""
        # Test basic variable names
        assert VariableNormalizer.normalize_name("name") == "name"
        assert VariableNormalizer.normalize_name("user_id") == "user_id"
        assert VariableNormalizer.normalize_name("data123") == "data123"

        # Test longer variable names
        assert (
            VariableNormalizer.normalize_name("very_long_variable_name")
            == "very_long_variable_name"
        )
        assert VariableNormalizer.normalize_name("camelCaseVar") == "camelCaseVar"

    def test_normalize_name_edge_cases(self):
        """Test normalize_name() with edge cases."""
        # Test edge case: just $ character
        result = VariableNormalizer.normalize_name("$")
        assert result == ""  # Should return empty string or handle appropriately

        # Test empty string
        assert VariableNormalizer.normalize_name("") == ""

        # Test Unicode characters
        assert VariableNormalizer.normalize_name("$名前") == "名前"
        assert VariableNormalizer.normalize_name("名前") == "名前"

        # Test underscores and numbers
        assert VariableNormalizer.normalize_name("$_private_var") == "_private_var"
        assert VariableNormalizer.normalize_name("$var123_test") == "var123_test"

    def test_is_reserved_function_builtin_functions(self):
        """Test is_reserved_function() with built-in functions."""
        empty_tools = {}

        # Test built-in functions
        assert VariableNormalizer.is_reserved_function("len", empty_tools) is True
        assert (
            VariableNormalizer.is_reserved_function("$len", empty_tools) is True
        )  # normalized
        assert (
            VariableNormalizer.is_reserved_function("debug_print", empty_tools) is True
        )
        assert (
            VariableNormalizer.is_reserved_function("$debug_print", empty_tools) is True
        )

        # Test LLM functions
        assert VariableNormalizer.is_reserved_function("llm_run", empty_tools) is True
        assert (
            VariableNormalizer.is_reserved_function("llm_evaluate_results", empty_tools)
            is True
        )
        assert (
            VariableNormalizer.is_reserved_function("llm_give_feedback", empty_tools)
            is True
        )
        assert (
            VariableNormalizer.is_reserved_function("llm_revise_task", empty_tools)
            is True
        )

        # Test json function
        assert (
            VariableNormalizer.is_reserved_function(
                "json_string_to_struct", empty_tools
            )
            is True
        )

    def test_is_reserved_function_custom_tools(self):
        """Test is_reserved_function() with custom tools."""
        custom_tools = {
            "add": lambda x, y: x + y,
            "summarize": lambda text: text[:10],
            "custom_tool": lambda: "test",
        }

        # Test custom tool conflicts
        assert VariableNormalizer.is_reserved_function("add", custom_tools) is True
        assert (
            VariableNormalizer.is_reserved_function("$add", custom_tools) is True
        )  # normalized
        assert (
            VariableNormalizer.is_reserved_function("summarize", custom_tools) is True
        )
        assert (
            VariableNormalizer.is_reserved_function("custom_tool", custom_tools) is True
        )

    def test_is_reserved_function_allowed_names(self):
        """Test is_reserved_function() with allowed variable names."""
        empty_tools = {}

        # Test allowed variable names
        assert VariableNormalizer.is_reserved_function("name", empty_tools) is False
        assert (
            VariableNormalizer.is_reserved_function("user_data", empty_tools) is False
        )
        assert VariableNormalizer.is_reserved_function("my_var", empty_tools) is False
        assert VariableNormalizer.is_reserved_function("count", empty_tools) is False
        assert VariableNormalizer.is_reserved_function("result", empty_tools) is False

        # Test with $ prefix
        assert VariableNormalizer.is_reserved_function("$name", empty_tools) is False
        assert (
            VariableNormalizer.is_reserved_function("$user_data", empty_tools) is False
        )

    def test_normalize_name_special_cases(self):
        """Test normalize_name() with special edge cases."""
        # Test multiple $ characters (though this shouldn't happen in practice)
        assert VariableNormalizer.normalize_name("$$name") == "$name"

        # Test single character variables
        assert VariableNormalizer.normalize_name("$a") == "a"
        assert VariableNormalizer.normalize_name("a") == "a"

        # Test numbers at start (may not be valid variable names, but test normalization)
        assert VariableNormalizer.normalize_name("$1var") == "1var"
        assert VariableNormalizer.normalize_name("1var") == "1var"

    def test_is_reserved_function_case_sensitivity(self):
        """Test that function conflict detection is case-sensitive."""
        empty_tools = {}

        # Test case sensitivity - these should be allowed
        assert VariableNormalizer.is_reserved_function("LEN", empty_tools) is False
        assert VariableNormalizer.is_reserved_function("Len", empty_tools) is False
        assert (
            VariableNormalizer.is_reserved_function("DEBUG_PRINT", empty_tools) is False
        )
        assert (
            VariableNormalizer.is_reserved_function("Debug_Print", empty_tools) is False
        )

        # Original function names should still be reserved
        assert VariableNormalizer.is_reserved_function("len", empty_tools) is True
        assert (
            VariableNormalizer.is_reserved_function("debug_print", empty_tools) is True
        )
