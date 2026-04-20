"""
Unit tests for MCP namespace validation in the compiler.

These tests verify that the compiler correctly validates MCP tool namespace
formats and provides clear error messages for invalid formats.
"""

import pytest
from lark import Token, Tree

from cy_language.compiler import CompilerError, PlanCompiler


class TestMCPNamespaceValidation:
    """Test MCP namespace format validation."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_valid_mcp_namespace_demo(self, compiler):
        """Test valid MCP namespace: mcp::demo::add."""
        # Create a mock tool call tree
        tool_name_token = Token("IDENTIFIER", "mcp::demo::add")
        tree = Tree("tool_call", [tool_name_token])

        # Should not raise exception for valid namespace
        result = compiler._compile_tool_call(tree)
        assert result is not None

    def test_valid_mcp_namespace_virustotal(self, compiler):
        """Test valid MCP namespace: mcp::virustotal::domain_reputation."""
        tool_name_token = Token("IDENTIFIER", "mcp::virustotal::domain_reputation")
        tree = Tree("tool_call", [tool_name_token])

        result = compiler._compile_tool_call(tree)
        assert result is not None

    def test_invalid_mcp_namespace_incomplete(self, compiler):
        """Test invalid MCP namespace: mcp::demo:: (empty function name)."""
        tool_name_token = Token("IDENTIFIER", "mcp::demo::")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(
            CompilerError,
            match="Invalid namespace.*Both namespace and function name must be non-empty",
        ):
            compiler._compile_tool_call(tree)

    def test_invalid_mcp_namespace_no_function(self, compiler):
        """Test invalid MCP namespace: mcp::demo (missing function name)."""
        tool_name_token = Token("IDENTIFIER", "mcp::demo")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(
            CompilerError,
            match="Invalid namespace format.*3 parts",
        ):
            compiler._compile_tool_call(tree)

    def test_invalid_mcp_namespace_empty_server(self, compiler):
        """Test invalid MCP namespace: mcp::::add (empty server name)."""
        tool_name_token = Token("IDENTIFIER", "mcp::::add")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(
            CompilerError,
            match="Invalid namespace.*Both namespace and function name must be non-empty",
        ):
            compiler._compile_tool_call(tree)

    def test_invalid_namespace_wrong_prefix(self, compiler):
        """Test invalid namespace: other::server::tool (not mcp)."""
        tool_name_token = Token("IDENTIFIER", "other::server::tool")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(
            CompilerError,
            match="Invalid namespace prefix.*Supported 3-part prefixes",
        ):
            compiler._compile_tool_call(tree)

    def test_invalid_namespace_too_many_parts(self, compiler):
        """Test invalid namespace: mcp::server::sub::tool (too many parts)."""
        tool_name_token = Token("IDENTIFIER", "mcp::server::sub::tool")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(
            CompilerError,
            match="Invalid namespace format.*3 parts",
        ):
            compiler._compile_tool_call(tree)

    def test_valid_native_tool_name(self, compiler):
        """Test that native tool names without namespace work correctly."""
        tool_name_token = Token("IDENTIFIER", "add")
        tree = Tree("tool_call", [tool_name_token])

        result = compiler._compile_tool_call(tree)
        # Should not raise namespace validation errors
        assert result is not None


class TestNamespaceErrorMessages:
    """Test quality and specificity of namespace validation error messages."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_error_message_includes_tool_name(self, compiler):
        """Test that error messages include the problematic tool name."""
        tool_name = "mcp::demo::"
        tool_name_token = Token("IDENTIFIER", tool_name)
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(CompilerError) as exc_info:
            compiler._compile_tool_call(tree)

        # Error message should include the tool name
        assert tool_name in str(exc_info.value)

    def test_error_message_explains_expected_format(self, compiler):
        """Test that error messages explain the expected format."""
        tool_name_token = Token("IDENTIFIER", "invalid::format")
        tree = Tree("tool_call", [tool_name_token])

        with pytest.raises(CompilerError) as exc_info:
            compiler._compile_tool_call(tree)

        # Error message should mention valid 2-part prefixes
        error_msg = str(exc_info.value)
        assert "Valid 2-part prefixes" in error_msg or "prefix" in error_msg.lower()

    def test_different_error_types(self, compiler):
        """Test that different invalid formats get appropriate error types."""
        # Test cases with expected error patterns
        test_cases = [
            ("mcp::demo::", "Both namespace and function name must be non-empty"),
            ("mcp::demo", "requires 3 parts"),  # Updated for
            ("other::demo::add", "Invalid namespace prefix.*Supported 3-part prefixes"),
            ("mcp::a::b::c", "Invalid namespace format.*3 parts"),
        ]

        for tool_name, expected_pattern in test_cases:
            tool_name_token = Token("IDENTIFIER", tool_name)
            tree = Tree("tool_call", [tool_name_token])

            with pytest.raises(CompilerError, match=expected_pattern):
                compiler._compile_tool_call(tree)
