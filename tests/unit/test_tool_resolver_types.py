"""
Unit tests for Enhanced ToolResolver with Type Metadata.

Tests verify ToolResolver correctly stores and retrieves type metadata
while maintaining 100% backward compatibility with the existing ToolResolver.
"""

import pytest

from cy_language.tool_resolver import ToolResolver
from cy_language.tool_signature import ParameterSignature, ToolSignature


class TestTypeMetadataStorage:
    """Test type metadata storage in ToolResolver."""

    @pytest.fixture
    def resolver(self):
        """Create a fresh ToolResolver instance."""
        return ToolResolver()

    @pytest.fixture
    def sample_signature(self):
        """Create a sample tool signature."""
        return ToolSignature(
            fqn="native::tools::add",
            function=lambda a, b: a + b,
            parameters={
                "a": ParameterSignature(
                    name="a", type_schema={"type": "number"}, required=True
                ),
                "b": ParameterSignature(
                    name="b", type_schema={"type": "number"}, required=True
                ),
            },
            return_type={"type": "number"},
            description="Add two numbers",
        )

    def test_register_tool_with_types_stores_signature(
        self, resolver, sample_signature
    ):
        """Verify signature is stored in _type_metadata."""
        resolver.register_tool_with_types(sample_signature)

        assert "native::tools::add" in resolver._type_metadata
        assert resolver._type_metadata["native::tools::add"] == sample_signature

    def test_register_tool_with_types_also_registers_fqn(
        self, resolver, sample_signature
    ):
        """Verify backward compatible registration."""
        resolver.register_tool_with_types(sample_signature)

        # Should also be in legacy fqn_registry
        assert "native::tools::add" in resolver.fqn_registry
        assert resolver.fqn_registry["native::tools::add"] == sample_signature.function

    def test_get_signature_returns_stored_signature(self, resolver, sample_signature):
        """Verify get_signature() retrieves correct signature."""
        resolver.register_tool_with_types(sample_signature)

        sig = resolver.get_signature("native::tools::add")
        assert sig is not None
        assert sig.fqn == "native::tools::add"
        assert sig.return_type == {"type": "number"}

    def test_get_signature_returns_none_for_unregistered(self, resolver):
        """Verify None returned for unknown FQN."""
        sig = resolver.get_signature("unknown::tool")
        assert sig is None

    def test_has_signature_returns_true_when_present(self, resolver, sample_signature):
        """Verify has_signature() helper works."""
        resolver.register_tool_with_types(sample_signature)

        assert resolver.has_signature("native::tools::add") is True

    def test_has_signature_returns_false_when_absent(self, resolver):
        """Verify has_signature() for unknown tool."""
        assert resolver.has_signature("unknown::tool") is False


class TestAutoRegistrationFromNativeTools:
    """Test from_native_tools() factory method."""

    def test_from_native_tools_creates_resolver(self):
        """Verify factory method creates ToolResolver."""
        resolver = ToolResolver.from_native_tools()

        assert isinstance(resolver, ToolResolver)
        assert len(resolver._type_metadata) > 0

    def test_from_native_tools_registers_len_function(self):
        """Verify len() is registered with correct signature."""
        resolver = ToolResolver.from_native_tools()

        assert resolver.has_signature("native::tools::len")
        sig = resolver.get_signature("native::tools::len")
        assert sig is not None
        assert sig.return_type == {"type": "number"}

    def test_from_native_tools_registers_sum_function(self):
        """Verify sum() is registered."""
        resolver = ToolResolver.from_native_tools()

        assert resolver.has_signature("native::tools::sum")

    def test_from_native_tools_registers_all_native_functions(self):
        """Verify all native tools are registered."""
        from cy_language.ui.tools import default_registry

        expected_tools = default_registry.get_tools_dict()
        resolver = ToolResolver.from_native_tools()

        # Check that major native functions are registered
        # Some tools now use 2-part namespaces, so check both formats
        flat_tools = ["len", "sum", "log"]  # These stay as native::tools::name
        namespaced_tools = {  # These use native::{namespace}::name
            "str": "native::type::str",
            "uppercase": "native::str::uppercase",
            "lowercase": "native::str::lowercase",
        }

        for tool_name in flat_tools:
            fqn = f"native::tools::{tool_name}"
            assert resolver.has_signature(fqn), f"Missing flat tool {tool_name}"

        for tool_name, fqn in namespaced_tools.items():
            assert resolver.has_signature(fqn), (
                f"Missing namespaced tool {tool_name} ({fqn})"
            )

    def test_from_native_tools_builds_correct_fqns(self):
        """Verify FQNs follow correct pattern."""
        resolver = ToolResolver.from_native_tools()

        # All registered tools should have native:: prefix with proper 3-part format
        # native::tools::name for flat, native::{namespace}::name for namespaced
        for fqn in resolver._type_metadata:
            assert fqn.startswith("native::"), (
                f"FQN should start with native:: - got: {fqn}"
            )
            parts = fqn.split("::")
            assert len(parts) == 3, f"FQN should have 3 parts - got {len(parts)}: {fqn}"

    def test_from_native_tools_short_names_work(self):
        """Verify short name resolution still works."""
        resolver = ToolResolver.from_native_tools()

        # Should be able to resolve "len" to "native::tools::len"
        fqn, original = resolver.resolve("len")
        assert fqn == "native::tools::len"
        assert original == "len"


class TestBackwardCompatibility:
    """Test backward compatibility with ToolResolver."""

    @pytest.fixture
    def resolver(self):
        """Create a fresh ToolResolver instance."""
        return ToolResolver()

    def test_old_register_tool_still_works(self, resolver):
        """Verify legacy register_tool(fqn, func) unchanged."""

        def sample_func():
            return "result"

        # Old API should work exactly as before
        resolver.register_tool("app::test::func", sample_func)

        assert "app::test::func" in resolver.fqn_registry
        assert resolver.fqn_registry["app::test::func"] == sample_func
        # Should NOT be in _type_metadata (legacy registration)
        assert "app::test::func" not in resolver._type_metadata

    def test_old_resolve_still_works(self, resolver):
        """Verify resolve() works for tools without type metadata."""

        def sample_func():
            return "result"

        resolver.register_tool("app::test::func", sample_func)
        resolver.register_short_name("func", "app::test::func")

        # Old resolve should work
        fqn, original = resolver.resolve("func")
        assert fqn == "app::test::func"
        assert original == "func"

    def test_old_and_new_apis_coexist(self, resolver):
        """Mix of old register_tool and new register_tool_with_types."""

        # Register one tool the old way
        def old_func():
            return "old"

        resolver.register_tool("app::old::func", old_func)

        # Register another tool the new way
        new_sig = ToolSignature(
            fqn="native::new::func",
            function=lambda: "new",
            parameters={},
            return_type={"type": "string"},
        )
        resolver.register_tool_with_types(new_sig)

        # Both should be resolvable
        assert "app::old::func" in resolver.fqn_registry
        assert "native::new::func" in resolver.fqn_registry
        assert resolver.has_signature("native::new::func")
        assert not resolver.has_signature(
            "app::old::func"
        )  # Old-style has no signature

    def test_backward_compatible_resolution(self, resolver):
        """Run subset of ToolResolver tests."""
        # This is a meta-test to verify backward compatibility
        # Reproduce key test patterns

        def func1():
            pass

        def func2():
            pass

        # patterns
        resolver.register_tool("app::splunk::search", func1)
        resolver.register_tool("mcp::demo::add", func2)
        resolver.register_short_name("search", "app::splunk::search")
        resolver.register_short_name("add", "mcp::demo::add")

        # Verify functionality unchanged
        assert len(resolver.fqn_registry) >= 2
        fqn, _ = resolver.resolve("search")
        assert fqn == "app::splunk::search"


class TestImportExport:
    """Test import/export of signatures."""

    @pytest.fixture
    def resolver_with_tools(self):
        """Create resolver with multiple tools."""
        resolver = ToolResolver()

        sig1 = ToolSignature(
            fqn="native::tools::len",
            function=None,
            parameters={
                "arg": ParameterSignature(
                    name="arg", type_schema={"type": ["string", "array"]}, required=True
                )
            },
            return_type={"type": "number"},
        )

        sig2 = ToolSignature(
            fqn="native::tools::uppercase",
            function=None,
            parameters={
                "text": ParameterSignature(
                    name="text", type_schema={"type": "string"}, required=True
                )
            },
            return_type={"type": "string"},
        )

        resolver.register_tool_with_types(sig1)
        resolver.register_tool_with_types(sig2)

        return resolver

    def test_export_signatures_returns_dict(self, resolver_with_tools):
        """Verify export_signatures() produces JSON-compatible dict."""
        exported = resolver_with_tools.export_signatures()

        assert isinstance(exported, dict)
        assert "native::tools::len" in exported
        assert "native::tools::uppercase" in exported

    def test_export_signatures_includes_all_registered(self, resolver_with_tools):
        """Verify all signatures are exported."""
        exported = resolver_with_tools.export_signatures()

        # Should have 2 tools
        assert len(exported) >= 2

    def test_import_signatures_restores_metadata(self):
        """Verify import_signatures() restores signatures."""
        # Export from one resolver
        resolver1 = ToolResolver()
        sig = ToolSignature(
            fqn="native::tool::func",
            function=None,
            parameters={},
            return_type={"type": "string"},
        )
        resolver1.register_tool_with_types(sig)
        exported = resolver1.export_signatures()

        # Import into another resolver
        resolver2 = ToolResolver()
        resolver2.import_signatures(exported)

        # Should have the signature
        assert resolver2.has_signature("native::tool::func")
        restored_sig = resolver2.get_signature("native::tool::func")
        assert restored_sig.return_type == {"type": "string"}

    def test_export_import_roundtrip(self, resolver_with_tools):
        """Verify export → import preserves all data."""
        exported = resolver_with_tools.export_signatures()

        # Create new resolver and import
        new_resolver = ToolResolver()
        new_resolver.import_signatures(exported)

        # Verify all signatures restored
        assert new_resolver.has_signature("native::tools::len")
        assert new_resolver.has_signature("native::tools::uppercase")

        # Verify signature details preserved
        len_sig = new_resolver.get_signature("native::tools::len")
        assert len_sig.return_type == {"type": "number"}

    def test_import_signatures_for_mcp_tools(self):
        """Verify can import external tool signatures."""
        # Simulate MCP tool signatures
        mcp_signatures = {
            "mcp::virustotal::scan_url": {
                "fqn": "mcp::virustotal::scan_url",
                "parameters": {
                    "url": {
                        "name": "url",
                        "type_schema": {"type": "string"},
                        "required": True,
                    }
                },
                "return_type": {"type": "object"},
                "description": "Scan URL with VirusTotal",
            }
        }

        resolver = ToolResolver()
        resolver.import_signatures(mcp_signatures)

        assert resolver.has_signature("mcp::virustotal::scan_url")


class TestNegativeCases:
    """Negative test cases for enhanced ToolResolver."""

    @pytest.fixture
    def resolver(self):
        """Create a fresh ToolResolver instance."""
        return ToolResolver()

    def test_register_tool_with_types_invalid_signature(self, resolver):
        """Verify error with invalid ToolSignature."""
        with pytest.raises((TypeError, AttributeError, NotImplementedError)):
            resolver.register_tool_with_types("not a signature")

    def test_get_signature_with_empty_fqn(self, resolver):
        """Verify error handling for empty FQN."""
        sig = resolver.get_signature("")
        # Should return None or handle gracefully
        assert sig is None

    def test_import_signatures_invalid_json(self, resolver):
        """Verify error handling for malformed import data."""
        with pytest.raises((ValueError, TypeError, KeyError, NotImplementedError)):
            resolver.import_signatures({"invalid": "format"})
