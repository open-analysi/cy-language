"""
Unit tests for tool registry builder export utilities.

Tests verify export functions that convert various tool sources (native, MCP, app, custom)
into ToolRegistry format.

These tests follow TDD - they will FAIL initially with NotImplementedError stubs,
and PASS once export utilities are implemented.
"""

from cy_language.tool_registry_builder import (
    build_tool_registry,
    export_app_tools,
    export_custom_tools,
    export_mcp_tools,
    export_native_tools,
)
from cy_language.tool_signature import ToolRegistry


class TestExportNativeTools:
    """Test export_native_tools() function."""

    def test_export_native_tools_returns_registry(self):
        """
        Verify function returns ToolRegistry instance.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """
        registry = export_native_tools()

        assert isinstance(registry, ToolRegistry)

    def test_export_native_tools_includes_len(self):
        """
        Verify native tools like len() are included.

        STUB TEST: Will FAIL until implemented.
        """
        registry = export_native_tools()

        # Should have len tool
        assert "native::tools::len" in registry.tools

    def test_export_native_tools_len_signature(self):
        """
        Verify len() has correct signature (parameter and return type).

        STUB TEST: Will FAIL until implemented.
        """
        registry = export_native_tools()

        len_tool = registry.tools.get("native::tools::len")
        assert len_tool is not None, "len tool not found in registry"

        # len() should return number type
        assert len_tool.return_type == {"type": "number"}

    def test_export_native_tools_str_signature(self):
        """
        Verify str() has correct signature.

        STUB TEST: Will FAIL until implemented.
        """
        registry = export_native_tools()

        str_tool = registry.tools.get("native::type::str")
        assert str_tool is not None, "str() should be registered as native::type::str"

        # str() should return string type
        assert str_tool.return_type == {"type": "string"}

    def test_export_native_tools_multiple_tools(self):
        """
        Verify multiple native tools are exported.

        STUB TEST: Will FAIL until implemented.
        """
        registry = export_native_tools()

        # Should have multiple tools
        assert len(registry.tools) > 0

        # Common native tools should be present
        # Note: str is registered as native::type::str (not native::tools::str)
        assert "native::tools::len" in registry.tools, "len not found in registry"
        assert "native::type::str" in registry.tools, "str not found in registry"
        assert "native::tools::sum" in registry.tools, "sum not found in registry"


class TestExportMCPTools:
    """Test export_mcp_tools() function."""

    def test_export_mcp_tools_empty_manager(self):
        """
        Verify empty MCP manager returns empty registry.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """

        # Mock MCP manager with empty tools_cache
        class MockMCPManager:
            tools_cache = {}

        registry = export_mcp_tools(MockMCPManager())

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0

    def test_export_mcp_tools_converts_input_schema(self):
        """
        Verify MCP inputSchema is converted to ParameterSignature.

        STUB TEST: Will FAIL until implemented.
        """

        # Mock MCP manager with tool
        class MockMCPManager:
            tools_cache = {
                "mcp::test::example": {
                    "schema": {
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ip": {"type": "string"},
                                "port": {"type": "number"},
                            },
                            "required": ["ip"],
                        },
                        "outputSchema": {"type": "object"},
                    },
                    "description": "Test tool",
                }
            }

        registry = export_mcp_tools(MockMCPManager())

        # Should have converted the tool
        assert "mcp::test::example" in registry.tools

        tool = registry.tools["mcp::test::example"]

        # Should have parameters from inputSchema
        assert "ip" in tool.parameters
        assert "port" in tool.parameters

    def test_export_mcp_tools_required_params(self):
        """
        Verify required array in inputSchema is respected.

        STUB TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {
                    "schema": {
                        "inputSchema": {
                            "properties": {
                                "required_param": {"type": "string"},
                                "optional_param": {"type": "number"},
                            },
                            "required": ["required_param"],
                        },
                        "outputSchema": {},
                    }
                }
            }

        registry = export_mcp_tools(MockMCPManager())
        tool = registry.tools["mcp::test::tool"]

        # required_param should be required
        assert tool.parameters["required_param"].required is True

        # optional_param should NOT be required
        assert tool.parameters["optional_param"].required is False

    def test_export_mcp_tools_output_schema(self):
        """
        Verify outputSchema becomes return_type.

        STUB TEST: Will FAIL until implemented.
        """
        output_schema = {
            "type": "object",
            "properties": {"score": {"type": "number"}, "verdict": {"type": "string"}},
        }

        class MockMCPManager:
            tools_cache = {
                "mcp::virustotal::ip_reputation": {
                    "schema": {"inputSchema": {}, "outputSchema": output_schema}
                }
            }

        registry = export_mcp_tools(MockMCPManager())
        tool = registry.tools["mcp::virustotal::ip_reputation"]

        # outputSchema should become return_type
        assert tool.return_type == output_schema

    def test_export_mcp_tools_preserves_fqn(self):
        """
        Verify MCP tool FQN is preserved from tools_cache key.

        STUB TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::custom_server::custom_tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {}}
                }
            }

        registry = export_mcp_tools(MockMCPManager())

        # FQN should be exactly the key from tools_cache
        assert "mcp::custom_server::custom_tool" in registry.tools

    def test_export_mcp_tools_manager_without_tools_cache(self):
        """
        Verify graceful handling of manager without tools_cache attribute.

        STUB TEST: Will FAIL until implemented.
        """

        class MockMCPManagerNoCache:
            pass  # No tools_cache attribute

        # Should not raise, should return empty registry
        registry = export_mcp_tools(MockMCPManagerNoCache())

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0


class TestExportAppTools:
    """Test export_app_tools() function."""

    def test_export_app_tools_empty_manager(self):
        """
        Verify empty app manager returns empty registry.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """

        class MockAppManager:
            def get_all_tools(self):
                return {}

        registry = export_app_tools(MockAppManager())

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0

    def test_export_app_tools_extracts_from_functions(self):
        """
        Verify signatures extracted from Python functions via introspection.

        STUB TEST: Will FAIL until implemented.
        """

        def sample_tool(ip: str, port: int = 80) -> bool:
            """Check if port is open."""
            return True

        class MockAppManager:
            def get_all_tools(self):
                return {"app::scanner::check_port": sample_tool}

        registry = export_app_tools(MockAppManager())

        assert "app::scanner::check_port" in registry.tools

        tool = registry.tools["app::scanner::check_port"]

        # Should have extracted parameters from type hints
        assert "ip" in tool.parameters
        assert "port" in tool.parameters

        # Should have extracted return type
        assert tool.return_type["type"] == "boolean"

    def test_export_app_tools_manager_without_get_all_tools(self):
        """
        Verify graceful handling of manager without get_all_tools() method.

        STUB TEST: Will FAIL until implemented.
        """

        class MockAppManagerNoMethod:
            pass  # No get_all_tools() method

        # Should not raise, should return empty registry
        registry = export_app_tools(MockAppManagerNoMethod())

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0


class TestExportCustomTools:
    """Test export_custom_tools() function."""

    def test_export_custom_tools_from_typed_function(self):
        """
        Verify custom function with type hints produces correct signature.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """

        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry = export_custom_tools({"add": add_numbers})

        # Should have tool with FQN
        fqn = "native::tools::add"
        assert fqn in registry.tools

        tool = registry.tools[fqn]

        # Should have parameters from function signature
        assert "a" in tool.parameters
        assert "b" in tool.parameters

        # Both should be required (no defaults)
        assert tool.parameters["a"].required is True
        assert tool.parameters["b"].required is True

        # Return type should be number
        assert tool.return_type["type"] == "number"

    def test_export_custom_tools_generates_fqn(self):
        """
        Verify custom tools get "native::tools::" FQN prefix.

        STUB TEST: Will FAIL until implemented.
        """

        def my_func(x: str) -> str:
            return x.upper()

        registry = export_custom_tools({"my_func": my_func})

        # FQN should be prefixed with native::tools::
        assert "native::tools::my_func" in registry.tools

    def test_export_custom_tools_multiple_functions(self):
        """
        Verify multiple custom functions are all exported.

        STUB TEST: Will FAIL until implemented.
        """

        def func1(x: int) -> int:
            return x * 2

        def func2(s: str) -> str:
            return s.lower()

        registry = export_custom_tools({"func1": func1, "func2": func2})

        assert len(registry.tools) == 2
        assert "native::tools::func1" in registry.tools
        assert "native::tools::func2" in registry.tools

    def test_export_custom_tools_empty_dict(self):
        """
        Verify empty tools dict returns empty registry.

        STUB TEST: Will FAIL until implemented.
        """
        registry = export_custom_tools({})

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0


class TestBuildToolRegistry:
    """Test build_tool_registry() main entry point."""

    def test_build_tool_registry_native_only(self):
        """
        Verify include_native=True includes native tools.

        STUB TEST: Will FAIL with NotImplementedError until implemented.
        """
        registry = build_tool_registry(include_native=True)

        assert isinstance(registry, ToolRegistry)

        # Should have native tools like len
        assert "native::tools::len" in registry.tools

    def test_build_tool_registry_mcp_only(self):
        """
        Verify MCP tools can be added without native.

        STUB TEST: Will FAIL until implemented.
        """

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {
                    "schema": {"inputSchema": {}, "outputSchema": {"type": "string"}}
                }
            }

        registry = build_tool_registry(
            include_native=False, mcp_manager=MockMCPManager()
        )

        # Should have MCP tool
        assert "mcp::test::tool" in registry.tools

        # Should NOT have native tools
        assert "native::tools::len" not in registry.tools

    def test_build_tool_registry_combines_all_sources(self):
        """
        Verify all sources (native, MCP, custom) combined.

        STUB TEST: Will FAIL until implemented.
        """

        def custom_func(x: int) -> int:
            return x

        class MockMCPManager:
            tools_cache = {
                "mcp::test::tool": {"schema": {"inputSchema": {}, "outputSchema": {}}}
            }

        registry = build_tool_registry(
            include_native=True,
            mcp_manager=MockMCPManager(),
            custom_tools={"custom": custom_func},
        )

        # Should have tools from all sources
        assert "native::tools::len" in registry.tools  # Native
        assert "mcp::test::tool" in registry.tools  # MCP
        assert "native::tools::custom" in registry.tools  # Custom

    def test_build_tool_registry_none_parameters(self):
        """
        Verify None parameters are handled gracefully.

        STUB TEST: Will FAIL until implemented.
        """
        # All optional parameters = None
        registry = build_tool_registry(
            include_native=False, mcp_manager=None, app_manager=None, custom_tools=None
        )

        assert isinstance(registry, ToolRegistry)
        assert len(registry.tools) == 0
