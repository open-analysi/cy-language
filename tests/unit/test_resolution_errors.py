"""
Unit tests for resolution error types.

These tests verify that AmbiguousToolError and ToolResolutionError
properly format error messages and store error information.
"""

from cy_language.errors import (
    AmbiguousToolError,
    CompilerError,
    ToolResolutionError,
)


class TestAmbiguousToolError:
    """Test AmbiguousToolError class."""

    def test_ambiguous_error_creation(self):
        """Test that AmbiguousToolError can be created with matches list."""
        matches = ["app::splunk::search_run", "app::elastic::search_run"]
        error = AmbiguousToolError("search_run", matches)

        assert error.tool_name == "search_run"
        assert error.matches == matches

    def test_ambiguous_error_message_format(self):
        """Test that error message shows all matches."""
        matches = ["app::virustotal::lookup_ip", "arc::threatintel::lookup_ip"]
        error = AmbiguousToolError("lookup_ip", matches)

        error_msg = str(error)
        assert "lookup_ip" in error_msg
        assert "Ambiguous tool name" in error_msg
        assert "app::virustotal::lookup_ip" in error_msg
        assert "arc::threatintel::lookup_ip" in error_msg
        assert "fully qualified name" in error_msg.lower()

    def test_ambiguous_error_with_line_column(self):
        """Test that error includes line/column info."""
        matches = ["app::splunk::search", "app::elastic::search"]
        error = AmbiguousToolError("search", matches, line=5, col=10)

        error_msg = str(error)
        assert "Line 5" in error_msg
        assert "Column 10" in error_msg
        assert error.line == 5
        assert error.col == 10

    def test_ambiguous_error_matches_attribute(self):
        """Test that error.matches contains all FQNs."""
        matches = ["mcp::demo::add", "native::tools::add"]
        error = AmbiguousToolError("add", matches)

        assert len(error.matches) == 2
        assert "mcp::demo::add" in error.matches
        assert "native::tools::add" in error.matches

    def test_ambiguous_error_inherits_compiler_error(self):
        """Test that AmbiguousToolError inherits from CompilerError."""
        error = AmbiguousToolError("test", ["a", "b"])

        assert isinstance(error, CompilerError)
        assert isinstance(error, Exception)


class TestToolResolutionError:
    """Test ToolResolutionError class."""

    def test_resolution_error_creation(self):
        """Test that ToolResolutionError can be created with suggestions."""
        suggestions = ["app::splunk::search_run", "app::elastic::search_run"]
        error = ToolResolutionError("search", suggestions)

        assert error.tool_name == "search"
        assert error.suggestions == suggestions

    def test_resolution_error_message_with_suggestions(self):
        """Test that error carries suggestions as data, not embedded in message."""
        suggestions = ["app::virustotal::lookup_ip", "mcp::virustotal::domain_report"]
        error = ToolResolutionError("lookup", suggestions)

        error_msg = str(error)
        assert "lookup" in error_msg
        assert "not found" in error_msg.lower()
        # Suggestions are stored as data for the formatting layer to render
        assert error.suggestions == suggestions

    def test_resolution_error_message_without_suggestions(self):
        """Test that error works with empty suggestions list."""
        error = ToolResolutionError("nonexistent", [])

        error_msg = str(error)
        assert "nonexistent" in error_msg
        assert "not found" in error_msg.lower()
        assert "Did you mean" not in error_msg

    def test_resolution_error_with_line_column(self):
        """Test that error includes line/column info."""
        error = ToolResolutionError("missing_tool", [], line=10, col=15)

        error_msg = str(error)
        assert "Line 10" in error_msg
        assert "Column 15" in error_msg
        assert error.line == 10
        assert error.col == 15

    def test_resolution_error_suggestions_attribute(self):
        """Test that error.suggestions contains FQN list."""
        suggestions = ["native::tools::len", "native::tools::length"]
        error = ToolResolutionError("leng", suggestions)

        assert len(error.suggestions) == 2
        assert "native::tools::len" in error.suggestions
        assert "native::tools::length" in error.suggestions

    def test_resolution_error_none_suggestions(self):
        """Test that None suggestions defaults to empty list."""
        error = ToolResolutionError("test", None)

        assert error.suggestions == []
        assert "Did you mean" not in str(error)


class TestResolutionErrorsEdgeCases:
    """Test edge cases for resolution errors."""

    def test_errors_are_catchable(self):
        """Test that errors can be caught as CompilerError."""
        ambiguous = AmbiguousToolError("test", ["a", "b"])
        resolution = ToolResolutionError("test", ["a"])

        try:
            raise ambiguous
        except CompilerError as e:
            assert isinstance(e, AmbiguousToolError)

        try:
            raise resolution
        except CompilerError as e:
            assert isinstance(e, ToolResolutionError)

    def test_ambiguous_error_single_match_unusual(self):
        """Test ambiguous error with only one match (unusual but handled)."""
        error = AmbiguousToolError("test", ["app::single::tool"])

        error_msg = str(error)
        assert "app::single::tool" in error_msg

    def test_resolution_error_many_suggestions(self):
        """Test resolution error with many suggestions stored as data."""
        suggestions = [f"app::service{i}::tool" for i in range(10)]
        error = ToolResolutionError("tool", suggestions)

        # All suggestions preserved as data for the formatting layer
        assert error.suggestions == suggestions
        assert "not found" in str(error).lower()
