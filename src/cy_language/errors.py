"""Error classes for the Cy language."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cy_language.execution_plan import ExecutionCheckpoint


class CyError(Exception):
    """Base class for all Cy language errors."""

    _from_cy_runtime: bool = False

    def __init__(
        self,
        message: str,
        line: int | None = None,
        col: int | None = None,
    ):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.formatted_message())

    def formatted_message(self) -> str:
        """Format the error message with line and column information."""
        if self.line is not None and self.col is not None:
            return f"Line {self.line}, Col {self.col}: {self.message}"
        return self.message

    def __str__(self) -> str:
        """String representation for use in catch blocks."""
        # Use enhanced format if available, but avoid recursion
        if (
            hasattr(self, "_context")
            and self._context
            and not getattr(self, "_formatting", False)
        ):
            self._formatting = True
            try:
                result = self._context.format_error(self)
                return str(result)
            finally:
                self._formatting = False
        return self.formatted_message()

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"{self.__class__.__name__}({self.message!r}, line={self.line}, col={self.col})"

    @property
    def type(self) -> str:
        """Get the error type name for error checking."""
        return self.__class__.__name__

    def to_dict(self) -> dict:
        """Convert the error to a dictionary format for UI display."""
        return {
            "type": self.__class__.__name__,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }


class CompilerError(CyError):
    """Error raised for compilation errors in the Cy language."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        col: int | None = None,
    ):
        super().__init__(message, line, col)

    @property
    def column(self) -> int | None:
        """Alias for col attribute for backward compatibility."""
        return self.col

    def formatted_message(self) -> str:
        """Format the error message with line and column information."""
        if self.line is not None and self.col is not None:
            return f"Line {self.line}, Column {self.col}: {self.message}"
        return self.message


class SyntaxError(CyError):
    """Error raised for syntax errors in the Cy language."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        col: int | None = None,
        text: str | None = None,
    ):
        self.text = text
        super().__init__(message, line, col)

    def to_dict(self) -> dict:
        """Convert the error to a dictionary format for UI display."""
        result = super().to_dict()
        if self.text is not None:
            result["text"] = self.text
        return result


class RuntimeError(CyError):
    """Error raised for runtime errors in the Cy language interpreter."""

    pass


class InterpolationError(CyError):
    """Error raised for string interpolation errors."""

    pass


class NameError(CyError):
    """Error raised for undefined variables or invalid names."""

    pass


class ToolError(CyError):
    """Error raised for errors related to tool invocation."""

    pass


class ToolNotFoundError(ToolError):
    """Error raised when a referenced tool is not found."""

    pass


class ToolInvocationError(ToolError):
    """Error raised when a tool invocation fails."""

    pass


class NotSupportedYetError(CyError):
    """Error raised for features that are reserved but not yet implemented."""

    pass


class AmbiguousToolError(CompilerError):
    """Tool short name matches multiple FQNs.

    Example:
        Line 5, Column 10: Ambiguous tool name 'lookup_ip'
        Matches multiple tools:
          - app::virustotal::lookup_ip
          - arc::threatintel::lookup_ip

        Please use the fully qualified name.
    """

    def __init__(
        self,
        tool_name: str,
        matches: list[str],
        line: int | None = None,
        col: int | None = None,
    ):
        """Initialize ambiguous tool error.

        Args:
            tool_name: The ambiguous short name
            matches: List of FQNs that match this short name
            line: Line number where error occurred
            col: Column number where error occurred
        """
        self.tool_name = tool_name
        self.matches = matches

        match_list = "\n  - ".join(matches)
        message = (
            f"Ambiguous tool name '{tool_name}'\n"
            f"Matches multiple tools:\n  - {match_list}\n\n"
            f"Please use the fully qualified name."
        )
        super().__init__(message, line, col)


class ToolResolutionError(CompilerError):
    """Tool cannot be resolved (not found).

    Example:
        Line 5, Column 10: Tool 'search_run' not found
        Did you mean:
          - app::splunk::search_run
          - app::elastic::search_run
    """

    def __init__(
        self,
        tool_name: str,
        suggestions: list[str] | None = None,
        line: int | None = None,
        col: int | None = None,
    ):
        """Initialize tool resolution error.

        Args:
            tool_name: The tool name that couldn't be resolved
            suggestions: Optional list of similar tool names
            line: Line number where error occurred
            col: Column number where error occurred
        """
        self.tool_name = tool_name
        self.suggestions = suggestions or []

        # Keep the message clean — suggestions are stored as data and
        # rendered by error_context.py's formatting layer instead.
        message = f"Tool '{tool_name}' not found"

        super().__init__(message, line, col)


class ExecutionPaused(Exception):
    """Raised when execution hits a hi-latency tool with no cached result.

    Carries an ExecutionCheckpoint that captures all state needed to resume
    execution later (memoized replay pattern — Project Kalymnos / HITL).
    """

    def __init__(self, checkpoint: ExecutionCheckpoint) -> None:
        self.checkpoint = checkpoint
        super().__init__(
            f"Execution paused at hi-latency tool '{checkpoint.pending_tool_name}'"
        )


class ReturnException(Exception):
    """Special exception used internally to handle return statements."""

    def __init__(self, value: Any) -> None:
        self.value = value
        super().__init__()


class BreakException(Exception):
    """Signal used internally to handle break statements in loops."""

    pass


class ContinueException(Exception):
    """Signal used internally to handle continue statements in loops."""

    pass
