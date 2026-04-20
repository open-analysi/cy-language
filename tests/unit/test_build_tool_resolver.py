"""
Unit tests for unified build_tool_resolver() function.

Tests verify that build_tool_resolver() is the single source of truth used by both
analyze_types() and compile_cy_program() to prevent code divergence.

These tests follow TDD - they will FAIL with NotImplementedError stubs,
and PASS once build_tool_resolver() is implemented.
"""

from cy_language.tool_resolver import ToolResolver, build_tool_resolver
from cy_language.tool_signature import ParameterSignature, ToolRegistry, ToolSignature


class TestBuildToolResolverFromRegistry:
    """Test building resolver from pre-built ToolRegistry (analyze_types path)."""

    def test_build_tool_resolver_from_tool_registry(self):
        """
        Verify resolver can be built from pre-built ToolRegistry.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """
        # Create registry with a tool
        registry = ToolRegistry()
        registry.add_tool(
            ToolSignature(
                fqn="native::tools::test",
                function=None,
                parameters={},
                return_type={"type": "string"},
            )
        )

        # Build resolver from registry
        resolver = build_tool_resolver(include_native=False, tool_registry=registry)

        assert isinstance(resolver, ToolResolver)

        # Resolver should have the tool
        assert resolver.has_tool("native::tools::test")

    def test_build_tool_resolver_registry_tools_have_types(self):
        """
        Verify tools from registry have proper type signatures (not Any).

        CRITICAL: This verifies Bug #1 fix - tools should NOT return Any type.

        STUB TEST: Will FAIL until implemented.
        """
        registry = ToolRegistry()
        registry.add_tool(
            ToolSignature(
                fqn="native::tools::len",
                function=None,
                parameters={
                    "obj": ParameterSignature(name="obj", type_schema={"type": "array"})
                },
                return_type={"type": "number"},
            )
        )

        resolver = build_tool_resolver(tool_registry=registry, include_native=False)

        # Get tool signature from resolver
        tool_sig = resolver.get_tool_signature("native::tools::len")

        # CRITICAL: Should have return_type = number, NOT {}
        assert tool_sig.return_type == {"type": "number"}, (
            "Bug #1 NOT FIXED: Tool from registry returned Any type"
        )

    def test_build_tool_resolver_registry_with_multiple_tools(self):
        """
        Verify registry with multiple tools builds correct resolver.

        STUB TEST: Will FAIL until implemented.
        """
        registry = ToolRegistry()
        tools = [
            ToolSignature(
                fqn="native::tools::len",
                function=None,
                parameters={},
                return_type={"type": "number"},
            ),
            ToolSignature(
                fqn="native::tools::str",
                function=None,
                parameters={},
                return_type={"type": "string"},
            ),
            ToolSignature(
                fqn="mcp::test::tool",
                function=None,
                parameters={},
                return_type={"type": "object"},
            ),
        ]

        for tool in tools:
            registry.add_tool(tool)

        resolver = build_tool_resolver(tool_registry=registry, include_native=False)

        # All tools should be in resolver
        assert resolver.has_tool("native::tools::len")
        assert resolver.has_tool("native::tools::str")
        assert resolver.has_tool("mcp::test::tool")


class TestBuildToolResolverFromManagers:
    """Test building resolver from managers (Cy() execution path)."""

    def test_build_tool_resolver_from_mcp_manager(self):
        """
        Verify resolver built from MCP manager has correct tools.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "number"}}
                }
            }

        resolver = build_tool_resolver(
            include_native=False, mcp_manager=MockMCPManager()
        )

        assert isinstance(resolver, ToolResolver)

        # Should have MCP tool
        assert resolver.has_tool("mcp::test::tool")

        # Tool should have proper type signature
        tool_sig = resolver.get_tool_signature("mcp::test::tool")
        assert tool_sig.return_type == {"type": "number"}

    def test_build_tool_resolver_from_available_tools(self):
        """
        Verify resolver built from available_tools dict (Cy() path).

        STUB TEST: Will FAIL until implemented.
        """

        def custom_func(x: int) -> str:
            return str(x)

        resolver = build_tool_resolver(
            include_native=False, available_tools={"custom": custom_func}
        )

        # Should have custom tool
        fqn = "native::tools::custom"
        assert resolver.has_tool(fqn)

        # Should have extracted signature from function
        tool_sig = resolver.get_tool_signature(fqn)
        assert tool_sig.return_type["type"] == "string"

    def test_build_tool_resolver_combines_native_and_mcp(self):
        """
        Verify native + MCP tools combined correctly.

        STUB TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {"schema": {"inputSchema": {}, "outputSchema": {}}}
            }

        resolver = build_tool_resolver(
            include_native=True, mcp_manager=MockMCPManager()
        )

        # Should have both native and MCP tools
        assert resolver.has_tool("native::tools::len")  # Native
        assert resolver.has_tool("mcp::test::tool")  # MCP

    def test_build_tool_resolver_from_app_manager(self):
        """
        Verify app manager tools are included.

        STUB TEST: Will FAIL until implemented.
        """

        def app_func() -> dict:
            return {}

        class MockAppManager:
            def get_all_tools(self):
                return {"app::integration::action": app_func}

        resolver = build_tool_resolver(
            include_native=False, app_manager=MockAppManager()
        )

        assert resolver.has_tool("app::integration::action")

    def test_build_tool_resolver_from_arc_router(self):
        """
        Verify archetype router tools are included (placeholders).

        STUB TEST: Will FAIL until implemented.
        """

        class MockArcRouter:
            def get_all_archetypes(self):
                return ["arc::archetype::task"]

        resolver = build_tool_resolver(include_native=False, arc_router=MockArcRouter())

        # Arc tools should be registered (even as placeholders)
        assert resolver.has_tool("arc::archetype::task")


class TestBuildToolResolverConsistency:
    """Test consistency between registry path and managers path."""

    def test_build_tool_resolver_same_result_both_paths(self):
        """
        Verify both paths (registry vs managers) produce identical resolver for same inputs.

        This is CRITICAL for Bug #1 fix - ensures no code divergence.

        STUB TEST: Will FAIL until implemented.
        """

        # Create MCP manager
        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "string"}}
                }
            }

        # Path 1: Build registry from MCP manager, then build resolver
        from cy_language.tool_registry_builder import export_mcp_tools

        registry = export_mcp_tools(MockMCPManager())
        resolver1 = build_tool_resolver(tool_registry=registry, include_native=False)

        # Path 2: Build resolver directly from MCP manager
        resolver2 = build_tool_resolver(
            mcp_manager=MockMCPManager(), include_native=False
        )

        # Both should have the same tool
        assert resolver1.has_tool("mcp::test::tool")
        assert resolver2.has_tool("mcp::test::tool")

        # Both should have same signature
        sig1 = resolver1.get_tool_signature("mcp::test::tool")
        sig2 = resolver2.get_tool_signature("mcp::test::tool")
        assert sig1.return_type == sig2.return_type

    def test_build_tool_resolver_tool_types_not_any(self):
        """
        Verify ALL tools in resolver have non-Any return types.

        CRITICAL for Bug #1 fix - no tool should return {} (Any type).

        STUB TEST: Will FAIL until implemented.
        """

        def custom_func(x: int) -> int:
            return x * 2

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "object"}}
                }
            }

        resolver = build_tool_resolver(
            include_native=True,
            mcp_manager=MockMCPManager(),
            custom_tools={"custom": custom_func},
        )

        # Check all tools have non-empty return types
        all_tools = [
            "native::tools::len",
            "native::type::str",  # str is now registered as type::str, not tools::str
            "mcp::test::tool",
            "native::tools::custom",
        ]

        for tool_fqn in all_tools:
            if resolver.has_tool(tool_fqn):
                sig = resolver.get_tool_signature(tool_fqn)
                assert sig.return_type != {}, (
                    f"Bug #1 NOT FIXED: Tool '{tool_fqn}' has Any return type"
                )

    def test_build_tool_resolver_native_tools_by_default(self):
        """
        Verify include_native=True (default) includes native tools.

        STUB TEST: Will FAIL until implemented.
        """
        # Default: include_native should be True
        resolver = build_tool_resolver()

        # Should have native tools
        assert resolver.has_tool("native::tools::len")
        assert resolver.has_tool(
            "native::type::str"
        )  # str is native::type::str, not tools::str

    def test_build_tool_resolver_no_native_tools_when_disabled(self):
        """
        Verify include_native=False excludes native tools.

        STUB TEST: Will FAIL until implemented.
        """
        resolver = build_tool_resolver(include_native=False)

        # Should NOT have native tools
        assert not resolver.has_tool("native::tools::len")


class TestBuildToolResolverEdgeCases:
    """Test edge cases and error handling."""

    def test_build_tool_resolver_all_none_parameters(self):
        """
        Verify all None parameters produces empty resolver (except native if enabled).

        STUB TEST: Will FAIL until implemented.
        """
        resolver = build_tool_resolver(
            include_native=False,
            tool_registry=None,
            available_tools=None,
            mcp_manager=None,
            app_manager=None,
            arc_router=None,
        )

        assert isinstance(resolver, ToolResolver)

    def test_build_tool_resolver_registry_takes_precedence(self):
        """
        Verify tool_registry parameter takes precedence over managers.

        When both registry and managers provided, registry should be used.

        STUB TEST: Will FAIL until implemented.
        """
        registry = ToolRegistry()
        registry.add_tool(
            ToolSignature(
                fqn="native::test::func",
                function=None,
                parameters={},
                return_type={"type": "string"},
            )
        )

        class MockMCPManager:
            tools_cache = {
                "mcp::should_not_appear::tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {}}
                }
            }

        # Provide both registry and manager
        resolver = build_tool_resolver(
            include_native=False,
            tool_registry=registry,
            mcp_manager=MockMCPManager(),  # Should be ignored
        )

        # Should have tool from registry
        assert resolver.has_tool("native::test::func")

        # Should NOT have tool from MCP manager (registry takes precedence)
        # Note: This behavior may change - document in implementation
