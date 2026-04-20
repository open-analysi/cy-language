"""Argument validation and marshaling for unified function calling.

Validates arguments using the canonical bind_arguments() algorithm, then
marshals to the format each calling convention requires:
- MCP tools: bind + convert to all-named dict for the MCP protocol
- Everything else: validate, then pass through to Python (func(*args, **kwargs))
"""

import inspect
from collections.abc import Callable
from typing import Any

from .tool_signature import bind_arguments


class ArgumentAdapter:
    """Validates and marshals function arguments for different calling conventions."""

    def __init__(self, mcp_manager: Any | None = None):
        self._signature_cache: dict[int, inspect.Signature] = {}
        self.mcp_manager = mcp_manager

    def get_signature(self, func: Callable) -> inspect.Signature:
        """Get function signature with caching."""
        func_id = id(func)
        if func_id not in self._signature_cache:
            self._signature_cache[func_id] = inspect.signature(func)
        return self._signature_cache[func_id]

    def validate_native_call(
        self, func: Callable, args: list[Any], kwargs: dict[str, Any]
    ) -> None:
        """Validate arguments for a native/LLM Python function.

        After validation, the caller can safely do func(*args, **kwargs) —
        Python's call mechanism handles positional/named binding and defaults.

        Raises:
            ValueError: On binding errors (duplicate, unknown, too many, missing required)
        """
        sig = self.get_signature(func)
        params = sig.parameters

        # Skip validation for variadic or keyword-only functions — Python handles them.
        # VAR_POSITIONAL (*args), VAR_KEYWORD (**kwargs), and KEYWORD_ONLY (after *)
        # all have semantics that bind_arguments() doesn't model.
        if any(
            p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD, p.KEYWORD_ONLY)
            for p in params.values()
        ):
            return

        param_names = list(params.keys())
        required = {
            n for n, p in params.items() if p.default is inspect.Parameter.empty
        }

        _, errors = bind_arguments(param_names, required, args, kwargs)
        if errors:
            raise ValueError(errors[0])

    def normalize_mcp_call(
        self, func_name: str, args: list[Any], kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Bind and marshal arguments for an MCP function call.

        MCP protocol requires all-named arguments. This method resolves
        positional args to param names using the MCP schema, then returns
        a single dict suitable for mcp_manager.call_mcp_tool().

        Returns:
            Dict mapping parameter names to values.

        Raises:
            ValueError: On binding errors or missing schema for positional args.
        """
        param_names = self._get_mcp_param_names(func_name)

        if param_names is None:
            # No schema available — positional args can't be resolved
            if args:
                raise ValueError(
                    f"MCP tool '{func_name}' requires named arguments or schema information"
                )
            # Named-only without schema: pass through (server validates)
            return kwargs

        # Schema available — validate ALL calls through bind_arguments
        bound, errors = bind_arguments(param_names, set(param_names), args, kwargs)
        if errors:
            raise ValueError(errors[0])
        return bound

    def _get_mcp_param_names(self, func_name: str) -> list[str] | None:
        """Get parameter names from MCP manager schema."""
        if not self.mcp_manager:
            return None
        try:
            result = self.mcp_manager.get_tool_parameter_names(func_name)
            # Handle async MCP managers that we can't await here
            if inspect.iscoroutine(result):
                result.close()  # Prevent "coroutine never awaited" warning
                return None
            # Validate result is actually a list of strings (not a Mock or other junk)
            if not isinstance(result, list):
                return None
            return result
        except (AttributeError, KeyError, ValueError, TypeError):
            # AttributeError: MCP manager missing method
            # KeyError/ValueError: tool not found in schema
            # TypeError: unexpected schema structure
            return None

    # --- Legacy compatibility ---

    def normalize_arguments(
        self,
        _func_type: str,
        func: Callable | None,
        args: list[Any],
        kwargs: dict[str, Any],
        func_name: str | None = None,
    ) -> tuple[list[Any], dict[str, Any]]:
        """Legacy entry point — delegates to validate_native_call or normalize_mcp_call.

        Retained for backward compatibility with tests.  New code should call
        ``validate_native_call()`` or ``normalize_mcp_call()`` directly.

        Args:
            _func_type: Unused; kept for backward compatibility.
        """
        if func_name and func_name.startswith("mcp::"):
            bound = self.normalize_mcp_call(func_name, args, kwargs)
            return [], bound

        if func is not None:
            self.validate_native_call(func, args, kwargs)
        return args, kwargs
