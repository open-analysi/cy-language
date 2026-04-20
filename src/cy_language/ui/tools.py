"""Tools system for Cy language UI.

This module provides a simple framework for managing tools within
the Cy language Streamlit UI.
"""

from collections.abc import Callable


class ToolRegistry:
    """Registry for tools used in the Cy language UI."""

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, Callable] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, func: Callable, description: str) -> None:
        """Register a tool in the registry.

        Args:
            name: The name of the tool (used in Cy programs)
            func: The function that implements the tool
            description: A short description of what the tool does

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = func
        self._descriptions[name] = description

    def get_tools_dict(self) -> dict[str, Callable]:
        """Get a dictionary of tools for use with the Cy interpreter.

        Returns:
            Dictionary mapping tool names to functions
        """
        return self._tools.copy()

    def get_tool_descriptions(self) -> list[dict[str, str]]:
        """Get a list of tools with their descriptions.

        Returns:
            List of dictionaries with tool information
        """
        return [
            {"name": name, "description": self._descriptions[name]}
            for name in self._tools
        ]


# Create the default registry
# Note: Only native functions from native_functions.py are registered by default
# Example tools like 'add' and 'summarize' have been removed
default_registry = ToolRegistry()

# Create a test-only registry for namespace demonstration tools
# These are NOT included in default_registry and won't be shipped to users
test_registry = ToolRegistry()


def register_tool(registry: ToolRegistry, name: str, description: str) -> Callable:
    """Decorator to register a function as a tool.

    Example:
        @register_tool(default_registry, "uppercase", "Convert a string to uppercase")
        def uppercase(text):
            return text.upper()

    Args:
        registry: The tool registry to register the tool in
        name: The name of the tool (used in Cy programs)
        description: A short description of what the tool does

    Returns:
        Decorator function that registers the tool
    """

    def decorator(func: Callable) -> Callable:
        registry.register(name, func, description)
        return func

    return decorator


def register_tool_with_alias(
    registry: ToolRegistry, old_name: str, new_name: str, description: str
) -> Callable:
    """Decorator to register a function under its new namespaced name only.

    Only the new namespaced name (e.g. "type::str") is stored in the registry.
    The old flat name (e.g. "str") resolves automatically as a short name via the
    ToolResolver, which extracts the last segment of the namespaced FQN.

    Registering both names was the original approach for backward compatibility,
    but it caused every aliased function to appear twice in the ToolResolver's
    short_name_index, making flat-name overrides via Cy(tools={...}) raise
    AmbiguousToolError.

    Example:
        @register_tool_with_alias(default_registry, "from_json", "json::parse", "Parse JSON")
        def from_json(json_str):
            return json.loads(json_str)
        # "json::parse" is in the registry; "from_json" resolves as short name.

    Args:
        registry: The tool registry to register the tool in
        old_name: The original flat name (kept for documentation; no longer registered)
        new_name: The new namespaced name (e.g., "json::parse") — the only one stored
        description: A short description of what the tool does

    Returns:
        Decorator function that registers the tool under the new name only
    """

    def decorator(func: Callable) -> Callable:
        # Only register the flat old_name when it differs from the last segment of
        # new_name.  When they are the same (e.g. old="str", new="type::str", last="str")
        # the flat name resolves automatically as a short-name of the namespaced FQN,
        # so registering it separately would create a duplicate short-name entry and
        # cause AmbiguousToolError when a user supplies Cy(tools={"str": custom_fn}).
        # When they differ (e.g. old="from_json", new="json::parse", last="parse")
        # the flat name is a genuine legacy alias that the resolver cannot derive on
        # its own, so it must still be registered.
        last_segment = new_name.split("::")[-1]
        if old_name != last_segment:
            registry.register(old_name, func, description)
        registry.register(new_name, func, description)
        return func

    return decorator


# Register namespaced test tools for demonstration
# NOTE: These are registered in test_registry, NOT default_registry
# They are for internal testing/demos only and won't be shipped to users
test_registry.register(
    "app::test::test1",
    lambda x: f"Test1 result: {x}",
    "Test tool - demonstrates app namespace (test1)",
)

test_registry.register(
    "app::test::test2",
    lambda x, y: f"Test2 result: {x} + {y} = {x + y}",
    "Test tool - demonstrates app namespace (test2)",
)

test_registry.register(
    "app::demo::greet",
    lambda name: f"Hello from app::demo, {name}!",
    "Demo tool - greeting function",
)

test_registry.register(
    "arc::example::analyze",
    lambda data: f"Archetype analyzed: {data}",
    "Archetype tool - demonstrates arc namespace",
)
