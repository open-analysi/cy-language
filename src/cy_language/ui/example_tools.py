"""Example tools for the Cy language UI.

This module demonstrates how to add custom tools to the Cy language
using the tools registry system.

NOTE: These are EXAMPLE tools for demonstration purposes only.
They are NOT registered with default_registry and are NOT available
to end users by default. They show how to create custom tools.
"""

from typing import Any, Union

from cy_language.ui.tools import ToolRegistry, register_tool

# Create a separate registry for example tools (not loaded by default)
example_registry = ToolRegistry()


# Example of registering a tool directly with the decorator
@register_tool(example_registry, "uppercase", "Convert a string to uppercase")
def uppercase(text: str) -> str:
    """Convert a string to uppercase.

    Args:
        text: The string to convert

    Returns:
        The uppercase version of the string
    """
    return str(text).upper()


@register_tool(example_registry, "lowercase", "Convert a string to lowercase")
def lowercase(text: str) -> str:
    """Convert a string to lowercase.

    Args:
        text: The string to convert

    Returns:
        The lowercase version of the string
    """
    return str(text).lower()


@register_tool(example_registry, "join", "Join a list of items with a separator")
def join(items: list[Any], separator: str = ", ") -> str:
    """Join a list of items with a separator.

    Args:
        items: The list of items to join
        separator: The separator to use (default: ", ")

    Returns:
        The joined string
    """
    return separator.join(str(item) for item in items)


# Example of registering a tool with the registry method
def multiply(*args: Union[int, float]) -> float:
    """Multiply all arguments together."""
    if not args:
        return 0.0

    result = 1.0
    for arg in args:
        result *= arg
    return result


# Register the multiply function
example_registry.register("multiply", multiply, "Multiply two or more numbers together")
