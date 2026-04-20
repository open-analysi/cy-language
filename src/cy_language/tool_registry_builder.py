"""
Tool registry building utilities - PHASE 27.

Provides export functions to convert various tool sources (native functions,
MCP managers, app managers, custom functions) into ToolRegistry format.
"""

from collections.abc import Callable
from typing import Any

from .tool_signature import (
    ParameterSignature,
    ToolRegistry,
    ToolSignature,
    extract_signature_from_function,
)


def build_tool_registry(
    include_native: bool = True,
    mcp_manager: Any | None = None,
    app_manager: Any | None = None,
    custom_tools: dict[str, Callable] | None = None,
) -> ToolRegistry:
    """
    Build complete validated ToolRegistry from all tool sources.

    Args:
        include_native: Include built-in native tools (len, str, etc.)
        mcp_manager: MCP manager with tools_cache attribute
        app_manager: App integration manager
        custom_tools: Dict of custom tool name -> function

    Returns:
        ToolRegistry with all tools from all sources
    """
    # Start with empty registry
    registry = ToolRegistry()

    # Add native tools if requested
    if include_native:
        native_registry = export_native_tools()
        registry.merge(native_registry)

    # Add MCP tools if manager provided
    if mcp_manager is not None:
        mcp_registry = export_mcp_tools(mcp_manager)
        registry.merge(mcp_registry)

    # Add app tools if manager provided
    if app_manager is not None:
        app_registry = export_app_tools(app_manager)
        registry.merge(app_registry)

    # Add custom tools if provided
    if custom_tools is not None:
        custom_registry = export_custom_tools(custom_tools)
        registry.merge(custom_registry)

    return registry


def export_native_tools() -> ToolRegistry:
    """
    Export native tools (len, str, etc.) with complete signatures.

    Extracts signatures from Python functions using inspect module.

    Returns:
        ToolRegistry with all native tools registered

    Note:
        - Flat tools (e.g., "len") get FQN: native::tools::len
        - Namespaced tools (e.g., "type::str") get FQN: native::type::str
        - This maintains the 3-part FQN format: namespace::category::name
    """
    from cy_language.ui.tools import default_registry

    registry = ToolRegistry()
    tools_dict = default_registry.get_tools_dict()

    for tool_name, tool_func in tools_dict.items():
        # Build FQN - handle 2-part namespaced names differently
        if "::" in tool_name:
            # Tool already has namespace (e.g., "type::str", "json::parse")
            # Use format: native::{namespace}::{name}
            fqn = f"native::{tool_name}"
        else:
            # Flat tool (e.g., "len", "sum")
            # Use format: native::tools::{name}
            fqn = f"native::tools::{tool_name}"

        # Extract signature from function using inspect
        signature = extract_signature_from_function(
            fqn=fqn, function=tool_func, description=""
        )

        # Add to registry
        registry.add_tool(signature)

    return registry


def export_mcp_tools(mcp_manager: Any) -> ToolRegistry:
    """
    Convert MCP tools from inputSchema/outputSchema format to ToolSignature.

    Args:
        mcp_manager: MCP manager with tools_cache attribute

    Returns:
        ToolRegistry with all MCP tools registered
    """
    registry = ToolRegistry()

    # MCP manager has tools_cache dict: mcp::server::tool -> metadata
    if not hasattr(mcp_manager, "tools_cache"):
        return registry

    for tool_fqn, tool_info in mcp_manager.tools_cache.items():
        # Extract schema information
        schema = tool_info.get("schema", {})
        input_schema = schema.get("inputSchema", {})
        output_schema = schema.get("outputSchema", {})

        # Convert inputSchema to parameters
        parameters = {}
        properties = input_schema.get("properties", {})
        required_params = input_schema.get("required", [])

        for param_name, param_schema in properties.items():
            parameters[param_name] = ParameterSignature(
                name=param_name,
                type_schema=param_schema,
                required=(param_name in required_params),
                default_value=None,
                description=param_schema.get("description", ""),
            )

        # Create tool signature
        signature = ToolSignature(
            fqn=tool_fqn,
            function=None,  # MCP tools don't have local functions
            parameters=parameters,
            return_type=output_schema if output_schema else {},
            description=tool_info.get("description", ""),
        )

        registry.add_tool(signature)

    return registry


def export_app_tools(app_manager: Any) -> ToolRegistry:
    """
    Extract signatures from application tool manager.

    Args:
        app_manager: App integration manager with get_all_tools() method

    Returns:
        ToolRegistry with all app tools registered
    """
    registry = ToolRegistry()

    if not hasattr(app_manager, "get_all_tools"):
        return registry

    # Get all tools from app manager (dict of FQN -> function)
    tools_dict = app_manager.get_all_tools()

    for tool_fqn, tool_func in tools_dict.items():
        # Extract signature from function using inspect
        signature = extract_signature_from_function(
            fqn=tool_fqn, function=tool_func, description=""
        )

        registry.add_tool(signature)

    return registry


def export_custom_tools(tools: dict[str, Callable]) -> ToolRegistry:
    """
    Extract signatures from custom Python functions using type hints.

    Args:
        tools: Dict mapping tool names (or FQNs) to Python functions
               - 3-part FQN (e.g., "native::tools::len"): use as-is
               - 2-part namespaced (e.g., "type::str"): prefix with "native::"
               - Simple name (e.g., "len"): prefix with "native::tools::"

    Returns:
        ToolRegistry with all custom tools registered
    """
    registry = ToolRegistry()

    for tool_name, tool_func in tools.items():
        # Count :: separators to determine structure
        parts = tool_name.split("::")
        num_parts = len(parts)

        if num_parts == 3:
            # Already a full 3-part FQN - use as-is
            fqn = tool_name
        elif num_parts == 2:
            # 2-part namespaced name (e.g., "type::str", "json::parse")
            # Convert to 3-part: native::type::str
            fqn = f"native::{tool_name}"
        else:
            # Simple name - add native::tools:: namespace
            fqn = f"native::tools::{tool_name}"

        # Extract signature from function using inspect
        signature = extract_signature_from_function(
            fqn=fqn, function=tool_func, description=""
        )

        registry.add_tool(signature)

    return registry
