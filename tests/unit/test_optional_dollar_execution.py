"""
Tests for Execution Context Integration for Optional $ Syntax.

Tests that the ExecutionContext correctly normalizes variable names
and uses the scope abstraction layer properly.
"""

import pytest

from cy_language.errors import NameError as CyNameError
from cy_language.executor import ExecutionContext


class TestOptionalDollarExecution:
    """Test execution context integration for optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = ExecutionContext()

    def test_set_variable_normalization(self):
        """Test that set_variable() normalizes variable names."""
        # Test setting with $ prefix
        self.context.set_variable("$name", "Alice")

        # Should be stored under normalized key "name"
        assert "name" in self.context.variables
        assert self.context.variables["name"] == "Alice"

        # Test setting without $ prefix
        self.context.set_variable("age", 25)

        # Should be stored under key "age"
        assert "age" in self.context.variables
        assert self.context.variables["age"] == 25

    def test_get_variable_normalization(self):
        """Test that get_variable() normalizes variable names."""
        # Set variable with $ prefix
        self.context.set_variable("$name", "Alice")

        # Should be retrievable without $ prefix
        result = self.context.get_variable("name")
        assert result == "Alice"

        # Should also be retrievable with $ prefix
        result = self.context.get_variable("$name")
        assert result == "Alice"

        # Test the reverse: set without $, get with $
        self.context.set_variable("age", 25)

        result = self.context.get_variable("$age")
        assert result == 25

        result = self.context.get_variable("age")
        assert result == 25

    def test_both_forms_same_variable(self):
        """Test that both $var and var refer to the same variable."""
        # Set with $ prefix
        self.context.set_variable("$name", "Alice")

        # Override with no $ prefix - should update same variable
        self.context.set_variable("name", "Bob")

        # Both forms should return the latest value
        assert self.context.get_variable("$name") == "Bob"
        assert self.context.get_variable("name") == "Bob"

        # Should only have one entry in variables dict
        normalized_keys = [
            key for key in self.context.variables if key in ["name", "$name"]
        ]
        assert len(normalized_keys) == 1
        assert "name" in self.context.variables

    def test_has_variable_normalization(self):
        """Test that has_variable() normalizes variable names."""
        # Set variable with $ prefix
        self.context.set_variable("$name", "Alice")

        # Should be found with both forms
        assert self.context.has_variable("name") is True
        assert self.context.has_variable("$name") is True

        # Test with variable set without $ prefix
        self.context.set_variable("age", 25)

        assert self.context.has_variable("age") is True
        assert self.context.has_variable("$age") is True

        # Non-existent variables should return False
        assert self.context.has_variable("nonexistent") is False
        assert self.context.has_variable("$nonexistent") is False

    def test_undefined_variable_errors(self):
        """Test that undefined variables raise CyNameError."""
        # Test with no $ prefix
        with pytest.raises(CyNameError) as exc_info:
            self.context.get_variable("undefined")

        error = exc_info.value
        assert "undefined" in str(error)

        # Test with $ prefix
        with pytest.raises(CyNameError) as exc_info:
            self.context.get_variable("$undefined")

        error = exc_info.value
        assert "undefined" in str(error)

    def test_scope_abstraction_delegation(self):
        """Test that variable methods delegate to scope abstraction."""
        # Test that set_variable calls _set_in_current_scope
        self.context.set_variable("$name", "Alice")

        # The abstraction should result in normalized storage
        assert "name" in self.context.variables
        assert self.context.variables["name"] == "Alice"

        # Test that get_variable calls _get_from_scope_chain
        result = self.context.get_variable("name")
        assert result == "Alice"

        # Test with both forms
        result = self.context.get_variable("$name")
        assert result == "Alice"

    def test_multiple_variables_normalization(self):
        """Test normalization with multiple variables."""
        # Set multiple variables with mixed $ usage
        self.context.set_variable("$name", "Alice")
        self.context.set_variable("age", 25)
        self.context.set_variable("$count", 10)
        self.context.set_variable("result", "test")

        # Should have 4 normalized entries
        assert len(self.context.variables) == 4
        assert "name" in self.context.variables
        assert "age" in self.context.variables
        assert "count" in self.context.variables
        assert "result" in self.context.variables

        # All should be retrievable with both forms
        assert self.context.get_variable("name") == "Alice"
        assert self.context.get_variable("$name") == "Alice"
        assert self.context.get_variable("age") == 25
        assert self.context.get_variable("$age") == 25
        assert self.context.get_variable("count") == 10
        assert self.context.get_variable("$count") == 10
        assert self.context.get_variable("result") == "test"
        assert self.context.get_variable("$result") == "test"

    def test_variable_overwrite_normalization(self):
        """Test that variable overwrites work correctly with normalization."""
        # Initial assignment with $
        self.context.set_variable("$data", "initial")
        assert self.context.get_variable("data") == "initial"

        # Overwrite without $
        self.context.set_variable("data", "updated")
        assert self.context.get_variable("$data") == "updated"
        assert self.context.get_variable("data") == "updated"

        # Another overwrite with $
        self.context.set_variable("$data", "final")
        assert self.context.get_variable("data") == "final"
        assert self.context.get_variable("$data") == "final"

        # Should still only have one entry
        assert len([k for k in self.context.variables if k.endswith("data")]) == 1

    def test_error_message_preserves_original_name(self):
        """Test that error messages show the original requested variable name."""
        # Try to get non-existent variable with $
        with pytest.raises(CyNameError) as exc_info:
            self.context.get_variable("$missing")

        # Error should mention the original name form requested
        error_msg = str(exc_info.value)
        assert "missing" in error_msg  # Should show normalized name or original

        # Try without $
        with pytest.raises(CyNameError) as exc_info:
            self.context.get_variable("missing")

        error_msg = str(exc_info.value)
        assert "missing" in error_msg

    def test_edge_case_variable_names(self):
        """Test normalization with edge case variable names."""
        # Test with single character
        self.context.set_variable("$a", "value_a")
        assert self.context.get_variable("a") == "value_a"

        # Test with underscores
        self.context.set_variable("_private", "private_value")
        assert self.context.get_variable("$_private") == "private_value"

        # Test with numbers
        self.context.set_variable("$var123", "numbered_value")
        assert self.context.get_variable("var123") == "numbered_value"

    def test_complex_data_types(self):
        """Test normalization works with complex data types."""
        # Test with dictionary
        test_dict = {"key": "value", "nested": {"inner": "data"}}
        self.context.set_variable("$data", test_dict)

        result = self.context.get_variable("data")
        assert result == test_dict
        assert result["key"] == "value"
        assert result["nested"]["inner"] == "data"

        # Test with list
        test_list = [1, 2, 3, "string", {"key": "value"}]
        self.context.set_variable("items", test_list)

        result = self.context.get_variable("$items")
        assert result == test_list
        assert len(result) == 5
        assert result[3] == "string"
