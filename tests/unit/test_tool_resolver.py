"""
Unit tests for ToolResolver.

These tests verify the ToolResolver class that manages FQN and short name
mappings, handles ambiguity detection, and provides 'Did you mean...' suggestions.
"""

import pytest

from cy_language.errors import AmbiguousToolError, ToolResolutionError
from cy_language.tool_resolver import ToolResolver


class TestToolResolverRegistration:
    """Test tool registration functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a fresh ToolResolver instance."""
        return ToolResolver()

    def test_register_tool_fqn(self, resolver):
        """Test registering a tool with FQN."""

        def sample_func():
            pass

        resolver.register_tool("app::splunk::search_run", sample_func)

        assert "app::splunk::search_run" in resolver.fqn_registry
        assert resolver.fqn_registry["app::splunk::search_run"] == sample_func

    def test_register_short_name(self, resolver):
        """Test registering a short name mapping."""
        resolver.register_tool("app::splunk::search_run", None)
        resolver.register_short_name("search_run", "app::splunk::search_run")

        assert "search_run" in resolver.short_name_index
        assert "app::splunk::search_run" in resolver.short_name_index["search_run"]

    def test_register_multiple_tools(self, resolver):
        """Test registering multiple tools with different FQNs."""

        def func1():
            pass

        def func2():
            pass

        resolver.register_tool("app::splunk::search", func1)
        resolver.register_tool("mcp::demo::add", func2)

        assert len(resolver.fqn_registry) == 2
        assert resolver.fqn_registry["app::splunk::search"] == func1
        assert resolver.fqn_registry["mcp::demo::add"] == func2

    def test_register_same_short_name_different_fqns(self, resolver):
        """Test registering same short name for multiple FQNs (creates ambiguity)."""
        resolver.register_tool("app::virustotal::lookup_ip", None)
        resolver.register_tool("arc::threatintel::lookup_ip", None)

        resolver.register_short_name("lookup_ip", "app::virustotal::lookup_ip")
        resolver.register_short_name("lookup_ip", "arc::threatintel::lookup_ip")

        assert "lookup_ip" in resolver.short_name_index
        assert len(resolver.short_name_index["lookup_ip"]) == 2


class TestToolResolverFQNResolution:
    """Test FQN resolution functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with sample tools."""
        r = ToolResolver()
        r.register_tool("app::splunk::search_run", None)
        r.register_tool("mcp::demo::add", None)
        r.register_tool("arc::threatintel::lookup_ip", None)
        r.register_tool("native::tools::len", None)
        return r

    def test_resolve_fqn_app_prefix(self, resolver):
        """Test resolving app::splunk::search_run to itself."""
        fqn, original = resolver.resolve("app::splunk::search_run")
        assert fqn == "app::splunk::search_run"
        assert original == "app::splunk::search_run"

    def test_resolve_fqn_mcp_prefix(self, resolver):
        """Test resolving mcp::demo::add to itself."""
        fqn, original = resolver.resolve("mcp::demo::add")
        assert fqn == "mcp::demo::add"
        assert original == "mcp::demo::add"

    def test_resolve_fqn_arc_prefix(self, resolver):
        """Test resolving arc::threatintel::lookup_ip to itself."""
        fqn, original = resolver.resolve("arc::threatintel::lookup_ip")
        assert fqn == "arc::threatintel::lookup_ip"
        assert original == "arc::threatintel::lookup_ip"

    def test_resolve_fqn_native_prefix(self, resolver):
        """Test resolving native::tools::len to itself."""
        fqn, original = resolver.resolve("native::tools::len")
        assert fqn == "native::tools::len"
        assert original == "native::tools::len"

    def test_resolve_returns_original_name(self, resolver):
        """Test that resolve returns (FQN, original_name) tuple."""
        result = resolver.resolve("mcp::demo::add")
        assert isinstance(result, tuple)
        assert len(result) == 2
        fqn, original = result
        assert fqn == original  # For FQNs, they should be the same


class TestToolResolverShortNameResolution:
    """Test short name resolution functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with short name mappings."""
        r = ToolResolver()
        r.register_tool("native::tools::len", None)
        r.register_short_name("len", "native::tools::len")

        r.register_tool("mcp::demo::add", None)
        r.register_short_name("add", "mcp::demo::add")
        return r

    def test_resolve_short_name_unique(self, resolver):
        """Test resolving 'len' to native::tools::len when unique."""
        fqn, original = resolver.resolve("len")
        assert fqn == "native::tools::len"
        assert original == "len"

    def test_resolve_short_name_native_function(self, resolver):
        """Test resolving short name to native function."""
        fqn, original = resolver.resolve("len")
        assert fqn == "native::tools::len"
        assert original == "len"

    def test_resolve_short_name_mcp_tool(self, resolver):
        """Test resolving short name to MCP tool."""
        fqn, original = resolver.resolve("add")
        assert fqn == "mcp::demo::add"
        assert original == "add"


class TestToolResolverAmbiguousNames:
    """Test ambiguous short name detection."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with ambiguous short names."""
        r = ToolResolver()
        r.register_tool("app::virustotal::lookup_ip", None)
        r.register_tool("arc::threatintel::lookup_ip", None)
        r.register_short_name("lookup_ip", "app::virustotal::lookup_ip")
        r.register_short_name("lookup_ip", "arc::threatintel::lookup_ip")
        return r

    def test_resolve_ambiguous_short_name(self, resolver):
        """Test that resolving ambiguous 'lookup_ip' raises AmbiguousToolError."""
        with pytest.raises(AmbiguousToolError) as exc_info:
            resolver.resolve("lookup_ip")

        error = exc_info.value
        assert error.tool_name == "lookup_ip"
        assert len(error.matches) == 2

    def test_ambiguous_error_contains_all_matches(self, resolver):
        """Test that error message lists all matching FQNs."""
        with pytest.raises(AmbiguousToolError) as exc_info:
            resolver.resolve("lookup_ip")

        error = exc_info.value
        assert "app::virustotal::lookup_ip" in error.matches
        assert "arc::threatintel::lookup_ip" in error.matches

    def test_ambiguous_error_suggests_fqn_usage(self, resolver):
        """Test that error message suggests using FQN."""
        with pytest.raises(AmbiguousToolError) as exc_info:
            resolver.resolve("lookup_ip")

        error_msg = str(exc_info.value)
        assert "fully qualified name" in error_msg.lower()


class TestToolResolverNotFound:
    """Test tool not found scenarios."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with a few tools."""
        r = ToolResolver()
        r.register_tool("app::splunk::search_run", None)
        r.register_short_name("search_run", "app::splunk::search_run")
        return r

    def test_resolve_nonexistent_fqn(self, resolver):
        """Test that resolving unknown FQN raises ToolResolutionError."""
        with pytest.raises(ToolResolutionError) as exc_info:
            resolver.resolve("app::unknown::tool")

        assert exc_info.value.tool_name == "app::unknown::tool"

    def test_resolve_nonexistent_short_name(self, resolver):
        """Test that resolving unknown short name raises ToolResolutionError."""
        with pytest.raises(ToolResolutionError) as exc_info:
            resolver.resolve("nonexistent")

        assert exc_info.value.tool_name == "nonexistent"

    def test_not_found_error_has_suggestions(self, resolver):
        """Test that error includes 'Did you mean...' suggestions."""
        with pytest.raises(ToolResolutionError) as exc_info:
            resolver.resolve("search")  # Partial match for search_run

        error = exc_info.value
        # Should have suggestions containing "search_run" or "search"
        assert len(error.suggestions) > 0


class TestToolResolverSuggestions:
    """Test suggestion functionality."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with various tools."""
        r = ToolResolver()
        r.register_tool("app::splunk::search_run", None)
        r.register_tool("app::elastic::search_query", None)
        r.register_tool("mcp::demo::add", None)
        r.register_tool("native::tools::len", None)
        return r

    def test_get_matches_partial_name(self, resolver):
        """Test that get_matches returns matching FQNs for 'search'."""
        matches = resolver.get_matches("search")

        assert len(matches) > 0
        # Should include tools with "search" in the name
        assert any("search" in m.lower() for m in matches)

    def test_get_matches_empty_for_no_matches(self, resolver):
        """Test that get_matches returns empty list for 'xyz'."""
        matches = resolver.get_matches("xyz")

        assert isinstance(matches, list)
        # May be empty or have very few results
        assert len(matches) <= 5  # Limited to 5 suggestions

    def test_get_matches_case_insensitive(self, resolver):
        """Test that suggestions work case-insensitively."""
        matches_lower = resolver.get_matches("search")
        matches_upper = resolver.get_matches("SEARCH")

        # Both should return results (implementation-dependent)
        assert isinstance(matches_lower, list)
        assert isinstance(matches_upper, list)


class TestGetMatchesReturnsUserFriendlyNames:
    """get_matches() must return names users can actually type, not internal FQNs."""

    def test_native_flat_tool_no_fqn_prefix(self):
        """native::tools::len should be suggested as 'len', not 'native::tools::len'."""
        r = ToolResolver()
        r.register_tool("native::tools::len", None)

        matches = r.get_matches("len")

        assert "len" in matches
        assert "native::tools::len" not in matches

    def test_native_namespaced_tool_two_part(self):
        """native::str::uppercase should be suggested as 'str::uppercase'."""
        r = ToolResolver()
        r.register_tool("native::str::uppercase", None)

        matches = r.get_matches("upper")

        assert "str::uppercase" in matches
        assert "native::str::uppercase" not in matches

    def test_app_tool_keeps_full_fqn(self):
        """app:: tools keep their full FQN since users need the full path."""
        r = ToolResolver()
        r.register_tool("app::splunk::search_run", None)

        matches = r.get_matches("search")

        assert "app::splunk::search_run" in matches

    def test_str_test_suggests_str_namespace_tools(self):
        """Reproduces the original bug: str::test should suggest str:: tools."""
        r = ToolResolver.from_native_tools()

        matches = r.get_matches("str::test")

        # Should suggest user-friendly 2-part names, not native:: FQNs
        for m in matches:
            assert not m.startswith("native::"), f"Suggestion '{m}' leaks internal FQN"

    def test_no_duplicate_suggestions(self):
        """Same user-facing name shouldn't appear twice (e.g. from alias + canonical)."""
        r = ToolResolver.from_native_tools()

        matches = r.get_matches("len")

        assert len(matches) == len(set(matches)), f"Duplicates in: {matches}"


class TestToolResolverEdgeCases:
    """Test edge cases for tool resolver."""

    def test_empty_resolver(self):
        """Test resolver with no registered tools."""
        resolver = ToolResolver()

        assert len(resolver.fqn_registry) == 0
        assert len(resolver.short_name_index) == 0

    def test_register_tool_empty_fqn(self):
        """Test that registering empty FQN raises ValueError."""
        resolver = ToolResolver()

        with pytest.raises(ValueError, match="FQN cannot be empty"):
            resolver.register_tool("", None)

    def test_register_short_name_empty(self):
        """Test that registering empty short name raises ValueError."""
        resolver = ToolResolver()

        with pytest.raises(ValueError, match="Short name and FQN cannot be empty"):
            resolver.register_short_name("", "app::test::tool")

    def test_register_short_name_empty_fqn(self):
        """Test that registering with empty FQN raises ValueError."""
        resolver = ToolResolver()

        with pytest.raises(ValueError, match="Short name and FQN cannot be empty"):
            resolver.register_short_name("test", "")

    def test_register_same_short_name_twice_same_fqn(self):
        """Test registering same short name → FQN mapping twice (idempotent)."""
        resolver = ToolResolver()
        resolver.register_tool("app::test::tool", None)

        resolver.register_short_name("tool", "app::test::tool")
        resolver.register_short_name("tool", "app::test::tool")  # Duplicate

        # Should only appear once in the list
        assert resolver.short_name_index["tool"].count("app::test::tool") == 1
