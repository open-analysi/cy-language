"""Enhanced error formatting utilities for Cy language.

This module provides utilities for formatting error messages with code context,
visual indicators, and helpful suggestions.
"""

from typing import Any


class ErrorFormatter:
    """Formats error messages with enhanced context and suggestions."""

    def __init__(self, use_color: bool = True):
        """Initialize error formatter.

        Args:
            use_color: Whether to use ANSI color codes for terminal output
        """
        self.use_color = use_color

    def format_with_context(
        self,
        source_code: str,
        line: int,
        col: int,
        message: str,
        suggestion: str | None = None,
        error_type: str = "Error",
    ) -> str:
        """Format error with source code context and visual indicators.

        Args:
            source_code: The full source code
            line: Line number (1-based)
            col: Column number (1-based)
            message: Error message
            suggestion: Optional fix suggestion
            error_type: Type of error (Syntax, Runtime, Type)

        Returns:
            Formatted error string with context
        """
        # Build the formatted error message
        parts = []

        # Error header with location
        header = f"{error_type} at line {line}, column {col}:"
        parts.append(self._colorize(header, "red"))
        parts.append("")

        # Get context lines
        context_lines = self._get_lines_around_error(source_code, line, context_lines=2)

        # Display context with line numbers
        for line_num, line_text in context_lines:
            line_prefix = f"{line_num:4} | "
            if line_num == line:
                # Highlight the error line
                parts.append(self._colorize(f"{line_prefix}{line_text}", "yellow"))
                # Add pointer line
                pointer_prefix = "     | "
                pointer = self._create_pointer_line(col)
                parts.append(self._colorize(f"{pointer_prefix}{pointer}", "red"))
            else:
                parts.append(f"{line_prefix}{line_text}")

        # Add error message
        parts.append("")
        parts.append(self._colorize(message, "red"))

        # Add suggestion if provided
        if suggestion:
            parts.append("")
            parts.append(self._colorize("Suggestion: ", "green") + suggestion)

        return "\n".join(parts)

    def _get_lines_around_error(
        self, source_code: str, line: int, context_lines: int = 2
    ) -> list[tuple[int, str]]:
        """Get lines around the error location.

        Args:
            source_code: Full source code
            line: Error line number (1-based)
            context_lines: Number of lines before/after to include

        Returns:
            List of (line_number, line_text) tuples
        """
        lines = source_code.split("\n")
        total_lines = len(lines)

        # Calculate range with bounds checking
        start_line = max(1, line - context_lines)
        end_line = min(total_lines, line + context_lines)

        result = []
        for line_num in range(start_line, end_line + 1):
            if line_num <= total_lines:
                # Line numbers are 1-indexed
                result.append((line_num, lines[line_num - 1]))

        return result

    def _create_pointer_line(self, col: int, length: int = 1) -> str:
        """Create a line pointing to the error location.

        Args:
            col: Column number (1-based)
            length: Length of the error span

        Returns:
            String with spaces and ^ characters pointing to error
        """
        # Create spaces leading up to the error position
        # Column is 1-based, so we need col-1 spaces
        spaces = " " * (col - 1)
        pointer = "^" * length
        return spaces + pointer

    def _colorize(self, text: str, color: str) -> str:
        """Add ANSI color codes to text if colors are enabled.

        Args:
            text: Text to colorize
            color: Color name (red, yellow, green, blue)

        Returns:
            Colorized text or original if colors disabled
        """
        if not self.use_color:
            return text

        # ANSI color codes
        colors = {
            "red": "\033[91m",
            "yellow": "\033[93m",
            "green": "\033[92m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }

        color_code = colors.get(color.lower(), "")
        reset_code = colors["reset"]

        if color_code:
            return f"{color_code}{text}{reset_code}"
        return text


# Common mistake patterns and their fixes
COMMON_MISTAKES: dict[str, dict[str, Any]] = {
    "lowercase_bool": {
        "pattern": r"\b(true|false)\b",
        "message": "'{match}' is not defined",
        "suggestion": "Did you mean '{fix}'? (Booleans are capitalized in Cy)",
        "fixes": {"true": "True", "false": "False"},
    },
    "symbol_operators": {
        "pattern": r"&&|\|\||!(?!=)",
        "message": "Unexpected operator '{match}'",
        "suggestion": "Use '{fix}' instead of '{match}' in Cy",
        "fixes": {"&&": "and", "||": "or", "!": "not"},
    },
    "range_function": {
        "pattern": r"(?<![_\w])range\s*\(",
        "message": "Tool 'range' not found",
        "suggestion": "range() is a native function in Cy. Syntax: range(stop) or range(start, stop)",
        "fixes": {},
    },
    # break/continue are now supported as loop control statements
}


def detect_common_mistake(
    error_message: str, source_line: str
) -> dict[str, Any] | None:
    """Detect if error is a common mistake and return suggestion.

    Args:
        error_message: The original error message
        source_line: The line of code with the error

    Returns:
        Dict with 'pattern', 'suggestion', and 'fix' if pattern detected, None otherwise
    """
    import re

    for pattern_name, pattern_config in COMMON_MISTAKES.items():
        pattern = pattern_config["pattern"]
        matches = re.search(pattern, source_line)

        if matches:
            matched_text = matches.group(0)

            # Check if this pattern is relevant to the error message
            if pattern_name == "lowercase_bool":
                if matched_text in ["true", "false"] and "not defined" in error_message:
                    fix = pattern_config["fixes"][matched_text]
                    suggestion = (
                        pattern_config["suggestion"]
                        .replace("{match}", matched_text)
                        .replace("{fix}", fix)
                    )
                    return {
                        "pattern": pattern_name,
                        "suggestion": suggestion,
                        "fix": fix,
                    }

            elif pattern_name == "symbol_operators":
                if matched_text in ["&&", "||", "!"]:
                    fix = pattern_config["fixes"][matched_text]
                    suggestion = (
                        pattern_config["suggestion"]
                        .replace("{match}", matched_text)
                        .replace("{fix}", fix)
                    )
                    return {
                        "pattern": pattern_name,
                        "suggestion": suggestion,
                        "fix": fix,
                    }

            elif pattern_name == "range_function":
                if "range" in error_message.lower():
                    return {
                        "pattern": pattern_name,
                        "suggestion": pattern_config["suggestion"],
                        "fix": None,
                    }

            elif pattern_name == "break_continue" and matched_text in error_message:
                suggestion = pattern_config["suggestion"].replace(
                    "{match}", matched_text
                )
                return {
                    "pattern": pattern_name,
                    "suggestion": suggestion,
                    "fix": None,
                }

    return None
