"""Tool signature definitions for Cy language type inference.

This module provides data structures for storing complete function signatures
including parameter types and return types. Also contains the canonical
bind_arguments() algorithm used by every layer of the argument pipeline.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, field_validator


def bind_arguments(
    param_names: list[str],
    required: set[str],
    args: list,
    kwargs: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Canonical argument binding: maps positional+named args to parameter names.

    This is the ONE algorithm for resolving which parameter each argument fills.
    Used by the type checker (compile-time), type inference engine (compile-time),
    and argument adapter (runtime).

    Args:
        param_names: Parameter names in definition order.
        required: Set of required parameter names (no default value).
        args: Positional arguments (values or AST nodes).
        kwargs: Named arguments (values or AST nodes).

    Returns:
        (bound, errors) where:
        - bound: dict mapping param_name -> value for each resolved argument
        - errors: list of error message strings (empty if binding succeeded)
    """
    bound: dict[str, Any] = {}
    errors: list[str] = []

    param_set = set(param_names)

    # 1. Too many positional?
    if len(args) > len(param_names):
        errors.append(
            f"Too many positional arguments: got {len(args)}, "
            f"expected at most {len(param_names)}"
        )
        return bound, errors

    # 2. Map positional args to param names by order
    for i, value in enumerate(args):
        bound[param_names[i]] = value

    # 3. Add named args (with duplicate + unknown checks)
    for name, value in kwargs.items():
        if name not in param_set:
            errors.append(f"Unknown parameter '{name}'")
            continue
        if name in bound:
            errors.append(f"Parameter '{name}' specified both positionally and by name")
            continue
        bound[name] = value

    # 4. Check required params are provided
    for name in required:
        if name not in bound:
            errors.append(f"Missing required parameter '{name}'")

    return bound, errors


class ParameterSignature(BaseModel):
    """Signature for a single function parameter."""

    name: str
    type_schema: dict[str, Any]  # JSON Schema
    required: bool = True
    default_value: Any = None
    description: str = ""

    model_config = {"arbitrary_types_allowed": True}


class ToolSignature(BaseModel):
    """Complete signature for a Cy tool/function."""

    fqn: str  # Fully qualified name (e.g., "native::tools::len")
    function: Callable | None = None  # The actual Python function
    parameters: dict[str, ParameterSignature] = {}  # param_name -> signature
    return_type: dict[str, Any] = {}  # JSON Schema for return value
    description: str = ""

    @field_validator("fqn")
    @classmethod
    def validate_fqn(cls, v: str) -> str:
        """Validate FQN format: namespace::category::name."""
        if not v:
            raise ValueError("FQN cannot be empty")

        parts = v.split("::")
        if len(parts) != 3:
            raise ValueError(
                f"FQN must have exactly 3 parts (namespace::category::name), got {len(parts)}: {v}"
            )

        namespace, category, name = parts
        valid_namespaces = {"native", "mcp", "app", "arc", "custom", "test"}
        if namespace not in valid_namespaces:
            raise ValueError(
                f"Invalid namespace '{namespace}'. Valid namespaces are: {', '.join(sorted(valid_namespaces))}"
            )

        return v

    model_config = {"arbitrary_types_allowed": True}

    def validate_call(self, arguments: dict[str, Any]) -> list[str]:
        """Validate named-only arguments against signature (legacy convenience).

        Args:
            arguments: Dict of argument_name -> value

        Returns:
            List of error messages (empty if valid)
        """
        _, errors = self.bind([], arguments)
        return errors

    def bind(
        self, args: list, kwargs: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """Bind positional+named arguments to parameters using the canonical algorithm.

        Args:
            args: Positional arguments
            kwargs: Named arguments

        Returns:
            (bound, errors) — see bind_arguments() for details.
        """
        param_names = list(self.parameters.keys())
        required = {n for n, p in self.parameters.items() if p.required}
        return bind_arguments(param_names, required, args, kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return self.model_dump(exclude={"function"})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolSignature":
        """Create from dict deserialization (function is always None)."""
        return cls.model_validate({**data, "function": None})


def extract_signature_from_function(
    fqn: str, function: Callable, description: str = ""
) -> ToolSignature:
    """Extract tool signature from Python function using inspect module.

    Uses inspect.signature() and get_type_hints() to automatically
    extract parameter types and return type from function annotations.

    Args:
        fqn: Fully qualified name for the tool
        function: Python function to extract signature from
        description: Optional description of the function

    Returns:
        ToolSignature with complete type information

    Example:
        >>> def add(a: int, b: int) -> int:
        ...     return a + b
        >>> sig = extract_signature_from_function("native::tools::add", add)
        >>> sig.return_type
        {"type": "number"}
    """
    import inspect
    from typing import get_type_hints

    from cy_language.type_system import python_type_to_json_schema

    # Get function signature and type hints
    sig = inspect.signature(function)
    try:
        type_hints = get_type_hints(function)
    except (TypeError, NameError, AttributeError):
        # TypeError: non-module object (e.g., lambda, Mock)
        # NameError: unresolvable forward references
        # AttributeError: unusual callable without __globals__
        type_hints = getattr(function, "__annotations__", {})

    # Ensure type_hints is not None (can happen with Mock objects)
    if type_hints is None:
        type_hints = {}

    # Extract parameters
    parameters: dict[str, ParameterSignature] = {}
    for param_name, param in sig.parameters.items():
        # Get type hint for this parameter
        if param_name in type_hints:
            param_type = type_hints[param_name]
            type_schema = python_type_to_json_schema(param_type)
        else:
            # No type hint - use Any
            type_schema = {}

        # Determine if required (no default value)
        required = param.default is inspect.Parameter.empty

        # Get default value
        default_value = (
            None if param.default is inspect.Parameter.empty else param.default
        )

        parameters[param_name] = ParameterSignature(
            name=param_name,
            type_schema=type_schema,
            required=required,
            default_value=default_value,
            description="",
        )

    # Extract return type
    if "return" in type_hints:
        return_type = python_type_to_json_schema(type_hints["return"])
    else:
        # No return type hint - use Any
        return_type = {}

    return ToolSignature(
        fqn=fqn,
        function=function,
        parameters=parameters,
        return_type=return_type,
        description=description,
    )


# PHASE 27: ToolRegistry class (Pydantic)
class ToolRegistry(BaseModel):
    """
    Collection of tool signatures with merge and export capabilities.

    Pydantic model with validation.
    """

    tools: dict[str, ToolSignature] = {}

    model_config = {"arbitrary_types_allowed": True}

    def add_tool(self, signature: ToolSignature) -> None:
        """Register a tool signature."""
        self.tools[signature.fqn] = signature

    def merge(self, other: "ToolRegistry") -> "ToolRegistry":
        """Merge another registry into this one."""
        for fqn, signature in other.tools.items():
            self.tools[fqn] = signature
        return self

    def export_for_analyze_types(self) -> dict[str, Any]:
        """
        Export to dict format expected by analyze_types().

        Returns:
            Dict in format:
            {
                "fqn": {
                    "parameters": {"param_name": {"type": "..."}},
                    "return_type": {"type": "..."}
                },
                ...
            }
        """
        result = {}
        for fqn, signature in self.tools.items():
            result[fqn] = {
                "parameters": {
                    name: param.type_schema
                    for name, param in signature.parameters.items()
                },
                "return_type": signature.return_type,
            }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolRegistry":
        """
        Create ToolRegistry from legacy dict format (backward compatibility).

        Args:
            data: Dict in format {"fqn": {"parameters": {...}, "required": [...], "return_type": {...}}}

        Returns:
            ToolRegistry instance
        """
        registry = cls()
        for fqn, metadata in data.items():
            params = {}
            # Get list of required parameters (default to all if not specified)
            required_params = metadata.get(
                "required", list(metadata.get("parameters", {}).keys())
            )

            for param_name, param_schema in metadata.get("parameters", {}).items():
                params[param_name] = ParameterSignature(
                    name=param_name,
                    type_schema=param_schema,
                    required=param_name
                    in required_params,  # Check if param is in required list
                )

            signature = ToolSignature(
                fqn=fqn,
                function=None,  # No function in serialized format
                parameters=params,
                return_type=metadata.get("return_type", {}),
                description="",
            )
            registry.add_tool(signature)

        return registry
