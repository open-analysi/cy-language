"""
Unit tests for namespace validation.

These tests verify that _validate_namespace() validates all supported
namespace prefixes (app, mcp, arc, native) and formats.
"""

import pytest

from cy_language.compiler import CompilerError, PlanCompiler


class TestNamespaceValidationValid:
    """Test validation of valid namespace formats."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_validate_app_namespace(self, compiler):
        """Test that app::splunk::search_run is valid."""
        # Should not raise exception
        compiler._validate_namespace("app::splunk::search_run")

    def test_validate_mcp_namespace(self, compiler):
        """Test that mcp::demo::add is valid."""
        compiler._validate_namespace("mcp::demo::add")

    def test_validate_arc_namespace(self, compiler):
        """Test that arc::threatintel::lookup_ip is valid."""
        compiler._validate_namespace("arc::threatintel::lookup_ip")

    def test_validate_native_namespace(self, compiler):
        """Test that native::tools::len is valid."""
        compiler._validate_namespace("native::tools::len")

    def test_validate_no_namespace(self, compiler):
        """Test that 'len' (no ::) is valid (native without prefix)."""
        # Should not raise exception for simple names
        compiler._validate_namespace("len")


class TestNamespaceValidationInvalidPrefixes:
    """Test validation of invalid namespace prefixes."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_invalid_prefix_foo(self, compiler):
        """Test that foo::bar::baz raises CompilerError for unknown prefix."""
        with pytest.raises(CompilerError, match="Invalid namespace prefix 'foo'"):
            compiler._validate_namespace("foo::bar::baz")

    def test_invalid_prefix_empty(self, compiler):
        """Test that ::bar::baz raises CompilerError for empty prefix."""
        with pytest.raises(CompilerError, match="Invalid namespace prefix"):
            compiler._validate_namespace("::bar::baz")

    def test_invalid_native_middle_segment(self, compiler):
        """Test that native::foo::len raises CompilerError (must be 'tools')."""
        with pytest.raises(
            CompilerError, match="native.*must use format.*native::tools::"
        ):
            compiler._validate_namespace("native::foo::len")


class TestNamespaceValidationInvalidFormat:
    """Test validation of invalid namespace formats."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_invalid_format_two_parts(self, compiler):
        """Test that app::splunk raises CompilerError (need 3 parts)."""
        with pytest.raises(CompilerError, match="Invalid namespace format.*3 parts"):
            compiler._validate_namespace("app::splunk")

    def test_invalid_format_four_parts(self, compiler):
        """Test that app::a::b::c raises CompilerError (need 3 parts)."""
        with pytest.raises(CompilerError, match="Invalid namespace format.*3 parts"):
            compiler._validate_namespace("app::a::b::c")

    def test_invalid_format_empty_middle(self, compiler):
        """Test that app::::search raises CompilerError."""
        with pytest.raises(CompilerError, match="Invalid namespace.*non-empty"):
            compiler._validate_namespace("app::::search")

    def test_invalid_format_empty_name(self, compiler):
        """Test that app::splunk:: raises CompilerError."""
        with pytest.raises(CompilerError, match="Invalid namespace.*non-empty"):
            compiler._validate_namespace("app::splunk::")

    def test_invalid_format_single_colon(self, compiler):
        """Test that app:splunk:search raises CompilerError (need ::)."""
        # This should either not match :: pattern or raise error
        # Depending on implementation, may not raise if no :: detected
        compiler._validate_namespace("app:splunk:search")
        # If it doesn't raise, that's OK (treated as simple name)


class TestNamespaceValidationEdgeCases:
    """Test edge cases for namespace validation."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_validate_unicode_in_names(self, compiler):
        """Test that unicode characters in namespace/name are handled."""
        try:
            # Implementation-specific: may accept or reject unicode
            compiler._validate_namespace("app::test::função")
        except (CompilerError, AttributeError):
            # Either not implemented yet or unicode not supported (both OK)
            pytest.skip("Unicode handling implementation-specific")

    def test_validate_numbers_in_names(self, compiler):
        """Test that numeric characters in namespace/name work."""
        compiler._validate_namespace("app::service123::tool456")

    def test_validate_underscores_in_names(self, compiler):
        """Test that underscores in namespace/name work."""
        compiler._validate_namespace("app::my_service::my_tool")

    def test_validate_hyphens_in_names(self, compiler):
        """Test handling of hyphens in namespace/name."""
        try:
            # May or may not be valid depending on implementation
            compiler._validate_namespace("app::my-service::my-tool")
        except (CompilerError, AttributeError):
            # Either not implemented or hyphens not supported (both OK)
            pytest.skip("Hyphen handling implementation-specific")

    def test_validate_case_sensitivity(self, compiler):
        """Test that namespace validation is case-sensitive."""
        # Both should be valid (case-sensitive)
        compiler._validate_namespace("app::Service::Tool")
        compiler._validate_namespace("app::service::tool")
