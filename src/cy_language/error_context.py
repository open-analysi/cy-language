"""Error context management for enhanced error messages."""

import re
from dataclasses import dataclass
from typing import Any

from .error_formatter import ErrorFormatter, detect_common_mistake
from .errors import CyError, ToolError
from .errors import SyntaxError as CySyntaxError
from .suggestion_engine import SuggestionEngine
from .ui.tools import default_registry

# Bracket pairs for syntax error detection: (open, close, missing_msg, extra_msg)
_BRACKET_PAIRS = [
    ("(", ")", "parenthesis ')'", "parenthesis ')' or missing opening '('"),
    ("[", "]", "bracket ']'", "bracket ']' or missing opening '['"),
    ("{", "}", "brace '}'", "brace '}' or missing opening '{'"),
]


@dataclass
class ErrorContext:
    """Carries context information for enhanced error formatting."""

    source_code: str
    filename: str | None = None
    tool_registry: dict[str, Any] | None = None
    show_enhanced: bool = True
    use_color: bool = True

    def __post_init__(self) -> None:
        """Initialize formatter and suggestion engine."""
        self.formatter = ErrorFormatter(use_color=self.use_color)
        self.suggestion_engine = SuggestionEngine(self.tool_registry or {})

    def enhance_error(self, error: Exception) -> CyError:
        """Enhance any error with context information.

        Args:
            error: The original error (CyError or parse exception)

        Returns:
            Enhanced CyError with source_code attached
        """
        # Check if it's a CyError from either import path
        # Handle both src.cy_language.errors and cy_language.errors
        is_cy_error = False
        if isinstance(error, CyError):
            is_cy_error = True
        else:
            # Check with alternative import path
            try:
                from cy_language.errors import CyError as AltCyError

                if isinstance(error, AltCyError):
                    is_cy_error = True
            except ImportError:
                pass

        # If it's already a CyError, just add source
        if is_cy_error:
            error.source_code = self.source_code  # type: ignore[attr-defined]
            error._context = self  # type: ignore[attr-defined]

            # Runtime errors (ToolError subclasses) should not get
            # syntax-level suggestions like bracket checks
            is_runtime_error = isinstance(error, ToolError)

            # If it's a SyntaxError from a parse error, ensure cleaned message
            # Only clean message for actual SyntaxErrors, not other error types
            # Check both import paths
            is_syntax_error = isinstance(error, CySyntaxError)
            if not is_syntax_error:
                try:
                    from cy_language.errors import SyntaxError as AltCySyntaxError

                    is_syntax_error = isinstance(error, AltCySyntaxError)
                except ImportError:
                    pass

            if is_syntax_error and not hasattr(error, "_cleaned_message"):
                # Only clean parse errors, not explicit SyntaxErrors with good messages
                # Check if error has a descriptive message already
                has_good_message = (
                    hasattr(error, "message")
                    and error.message
                    and error.message != "SyntaxError"
                    and not error.message.startswith("No terminal matches")
                    and not error.message.startswith("Unexpected token Token(")
                )

                if not has_good_message:
                    # This is a parse error that needs cleaning
                    error_str = str(error)
                    error._cleaned_message = self._clean_error_message(error_str)  # type: ignore[attr-defined]
                    if not hasattr(error, "_suggestion"):
                        error._suggestion = self._get_suggestion_for_error(  # type: ignore[attr-defined]
                            error_str, error.line if hasattr(error, "line") else None
                        )
                elif not hasattr(error, "_suggestion"):
                    # Has good message, just check for suggestions
                    error_str = str(error)
                    error._suggestion = self._get_suggestion_for_error(  # type: ignore[attr-defined]
                        error_str, error.line if hasattr(error, "line") else None
                    )
            # Check for suggestions for all error types (including NameError)
            elif not hasattr(error, "_suggestion"):
                error_str = str(error)
                suggestion = self._get_suggestion_for_error(
                    error_str,
                    error.line if hasattr(error, "line") else None,
                    is_runtime=is_runtime_error,
                )
                # Fallback: use resolver suggestions from ToolResolutionError
                if (
                    not suggestion
                    and hasattr(error, "suggestions")
                    and error.suggestions
                ):
                    suggestion = f"Did you mean: {', '.join(error.suggestions[:3])}"
                if suggestion:
                    error._suggestion = suggestion  # type: ignore[attr-defined]
            return error  # type: ignore[return-value]

        # Convert parse errors to CySyntaxError
        error_str = str(error)

        # Try to extract line/column from error message
        line, col = self._extract_location(error_str)

        # Detect common patterns and get suggestion
        suggestion = self._get_suggestion_for_error(error_str, line)

        # Get cleaned message
        cleaned_message = self._clean_error_message(error_str)

        # Create enhanced CySyntaxError
        enhanced = CySyntaxError(message=cleaned_message, line=line, col=col)
        enhanced.source_code = self.source_code  # type: ignore[attr-defined]
        enhanced._context = self  # type: ignore[attr-defined]
        enhanced._suggestion = suggestion  # type: ignore[attr-defined]
        # Store both cleaned and original messages
        enhanced._cleaned_message = cleaned_message  # type: ignore[attr-defined]
        enhanced._original_message = error_str  # type: ignore[attr-defined]

        return enhanced

    def _extract_location(self, error_str: str) -> tuple[int | None, int | None]:
        """Extract line and column from error string."""
        # Pattern: "at line X col Y" or "Line X, Col Y"
        patterns = [
            r"at line (\d+) col (\d+)",
            r"Line (\d+), Col(?:umn)? (\d+)",
            r"line (\d+):(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                line = int(match.group(1))
                col = int(match.group(2))
                # For && and || operators, adjust column to point to the operator
                if "&&" in error_str or "||" in error_str:
                    # Column is usually at the first &/| character
                    pass  # Keep original column
                return line, col

        # If no patterns match, try to find just line number
        line_match = re.search(r"line (\d+)", error_str, re.IGNORECASE)
        if line_match:
            # Try to find column separately
            col_match = re.search(r"col(?:umn)? (\d+)", error_str, re.IGNORECASE)
            col = int(col_match.group(1)) if col_match else 1
            return int(line_match.group(1)), col

        return None, None

    def _get_suggestion_for_error(
        self, error_str: str, line: int | None, is_runtime: bool = False
    ) -> str | None:
        """Get a user-facing suggestion based on error pattern, or None.

        Args:
            error_str: The error message string
            line: Line number where the error occurred
            is_runtime: If True, skip syntax-level heuristics (bracket checks,
                keyword detection, etc.) to avoid false positives on tool errors.
        """
        source_line = self._get_source_line(line)
        error_lower = error_str.lower()

        # Phase 1: operator & casing checks (always run)
        result = self._check_operator_errors(error_str, error_lower, source_line)
        if result:
            return result

        # Phase 2: undefined-variable heuristics (always run)
        result = self._check_undefined_variable(error_str)
        if result:
            return result

        # --- Remaining phases are syntax-level and skipped for runtime errors ---
        # Runtime errors (ToolError subclasses) parsed fine; keyword/bracket
        # checks would false-positive on tool error messages.
        if not is_runtime:
            result = self._check_syntax_keywords(error_str, error_lower, source_line)
            if result:
                return result

            result = self._check_bracket_and_string_errors(source_line)
            if result:
                return result

            result = self._check_tool_not_found(error_str, error_lower)
            if result:
                return result

            if source_line:
                pattern = detect_common_mistake(error_str, source_line)
                if pattern:
                    return pattern.get("suggestion")

        return None

    def _get_source_line(self, line: int | None) -> str:
        """Extract the source line for the given 1-based line number."""
        if line and line > 0:
            lines = self.source_code.split("\n")
            if line <= len(lines):
                return lines[line - 1]
        return ""

    # -- Phase 1: operator & literal-casing checks --

    @staticmethod
    def _check_operator_errors(
        error_str: str, error_lower: str, source_line: str
    ) -> str | None:
        """Check for C/JS-style operators and Python-style literal casing."""
        # Operator substitution checks (need the operator in source to avoid
        # suggesting on unrelated parse errors)
        if source_line:
            if (
                "No terminal matches '&'" in error_str or "'&&'" in error_str
            ) and "&" in source_line:
                return "Use 'and' instead of '&&' in Cy"
            if (
                "No terminal matches '|'" in error_str or "'||'" in error_str
            ) and "|" in source_line:
                return "Use 'or' instead of '||' in Cy"
            if (
                "No terminal matches '!'" in error_str
                and "!=" not in error_str
                and "!" in source_line
            ):
                return "Use 'not' instead of '!' in Cy"

        # Python/JS-style boolean and null literals
        if "not defined" in error_str:
            if "'true'" in error_lower:
                return "Did you mean 'True'? (Booleans are capitalized in Cy)"
            if "'false'" in error_lower:
                return "Did you mean 'False'? (Booleans are capitalized in Cy)"
            if "'none'" in error_lower:
                return (
                    "Did you mean 'null'? In Cy, use 'null' instead of Python's 'None'"
                )
        return None

    # -- Phase 2: undefined variable checks --

    def _check_undefined_variable(self, error_str: str) -> str | None:
        """Check if an undefined variable is actually a native function name."""
        if "not defined" not in error_str:
            return None
        match = re.search(r"Variable '([^']+)' is not defined", error_str)
        if match:
            var_name = match.group(1)
            native_functions = default_registry.get_tools_dict()
            if var_name in native_functions:
                return (
                    f"Did you forget to call the function? "
                    f"Use '{var_name}()' instead of '{var_name}'"
                )
        return None

    # -- Phase 3: syntax keyword checks --

    @staticmethod
    def _check_syntax_keywords(
        error_str: str, error_lower: str, source_line: str
    ) -> str | None:
        """Check for unsupported keywords and source-line patterns.

        Skipped for runtime errors and for undefined-variable errors (names
        like ``should_continue`` contain keyword substrings).
        """
        is_undefined_var = "not defined" in error_str

        # Keyword checks — only when NOT an undefined-variable error
        if not is_undefined_var and re.search(r"(?<![_\w])range\s*\(", error_str):
            return (
                "range() is a native function in Cy. "
                "Syntax: range(stop) or range(start, stop)"
            )

        # 'print' check intentionally handles "not defined" (user wrote print())
        if "'print'" in error_str and ("not found" in error_lower or is_undefined_var):
            return (
                "print() is not available in Cy. "
                "Use 'return' to produce output from your script"
            )

        # Source-line pattern checks
        if source_line:
            if re.search(r"\[\s*\w+[^]]*\s+for\s+\w+\s+in\s+", source_line):
                return (
                    "Cy list comprehensions require parentheses: "
                    "[expr for(x in items)] or [expr for(x in items) if(cond)]"
                )
            if "else if" in source_line:
                return (
                    "Use 'elif' instead of 'else if' in Cy. "
                    "Syntax: } elif (condition) {"
                )
            if re.search(r"if\s*\([^)]*\s=\s", source_line):
                return (
                    "Use '==' for comparison, not '='. "
                    "Assignment in conditions is not allowed"
                )
            if source_line.rstrip().endswith(";"):
                return (
                    "Semicolons are not needed in Cy. "
                    "Remove the ';' at the end of the line"
                )
            if re.search(r"\b[a-zA-Z_]\s+[a-zA-Z_]", source_line) and not (
                '"' in source_line[: source_line.find(" ")]
                if " " in source_line
                else False
            ):
                return (
                    "Variable names cannot contain spaces. "
                    "Did you mean to write it as one word?"
                )

        return None

    # -- Phase 4: bracket / string / delimiter checks --

    @staticmethod
    def _check_bracket_and_string_errors(source_line: str) -> str | None:
        """Detect mismatched brackets, unclosed strings, and missing delimiters.

        Only for syntax/parse errors — runtime errors on multiline calls
        would falsely trigger these (e.g. "llm_run(" on one line is valid).
        """
        if not source_line:
            return None

        for open_ch, close_ch, missing_msg, extra_msg in _BRACKET_PAIRS:
            opens = source_line.count(open_ch)
            closes = source_line.count(close_ch)
            if opens > closes:
                return f"Missing closing {missing_msg}"
            if closes > opens:
                return f"Extra closing {extra_msg}"

        # Unclosed string checks
        if source_line.count('"') % 2 != 0:
            return "Unclosed string - missing closing double quote"
        if source_line.count("'") % 2 != 0:
            return "Unclosed string - missing closing single quote"

        # Missing colon in dict literal (check BEFORE missing comma)
        if (
            "{" in source_line
            and '"' in source_line
            and re.search(r'"\s+"', source_line)
            and ":" not in source_line
        ):
            return "Missing colon ':' between dictionary key and value"

        # Missing commas in list/dict literals
        if "[" in source_line or "{" in source_line:
            if re.search(r"\d\s+\d", source_line):
                return "Missing comma between elements"
            if re.search(r'"\s+"', source_line) and ":" in source_line:
                return "Missing comma between elements"

        return None

    # -- Phase 5: tool-not-found fuzzy matching --

    def _check_tool_not_found(self, error_str: str, error_lower: str) -> str | None:
        """Suggest similar tool names when a tool is not found.

        Skipped for runtime errors — the tool was found and ran but its
        output contains "not found" (e.g. HTTP 404).
        """
        if "not found" not in error_lower or not self.tool_registry:
            return None
        match = re.search(r"Tool '([^']+)'", error_str)
        if match:
            tool_name = match.group(1)
            suggestions = self.suggestion_engine.suggest_similar_tools(tool_name)
            if suggestions:
                return f"Did you mean: {', '.join(suggestions[:2])}"
        return None

    def _clean_error_message(self, error_str: str) -> str:
        """Clean up parser error messages."""
        # Check for specific patterns first
        if "No terminal matches '&'" in error_str:
            # Check if it's actually &&
            if "&&" in self.source_code:
                return "Unexpected operator '&&'"
            return "Unexpected operator '&'"
        if "No terminal matches '|'" in error_str:
            # Check if it's actually ||
            if "||" in self.source_code:
                return "Unexpected operator '||'"
            return "Unexpected operator '|'"
        if "No terminal matches '!'" in error_str and "!=" not in error_str:
            return "Unexpected operator '!'"

        # For SyntaxError, extract just the core message
        if "SyntaxError at line" in error_str:
            # Already formatted, just return the message part
            lines = error_str.split("\n")
            for line in lines:
                if line and not line.strip().startswith("|") and "at line" not in line:
                    return line.strip()

        # Remove parser internals for other errors
        clean = error_str.split("\n")[0]  # Take first line
        clean = re.sub(r"at line \d+ col \d+", "", clean)
        clean = re.sub(r"No terminal matches", "Unexpected token", clean)
        clean = clean.strip()

        # If we get just "SyntaxError" or similar, return a more descriptive message
        if clean == "SyntaxError" or clean == "":
            return "Syntax error in expression"

        return clean

    def format_error(self, error: CyError) -> str:
        """Format error with enhanced display."""
        if not self.show_enhanced or not hasattr(error, "source_code"):
            return str(error)

        suggestion = getattr(error, "_suggestion", None)

        # For parse errors, use the cleaned message if available
        if hasattr(error, "_cleaned_message"):
            message = error._cleaned_message
        elif hasattr(error, "message"):
            message = error.message
        else:
            # Use formatted_message to avoid recursion through __str__
            message = (
                error.formatted_message()
                if hasattr(error, "formatted_message")
                else str(error)
            )

        # Determine column value
        col_value = (
            error.col
            if error.col
            else (error.column if hasattr(error, "column") else 1)
        )

        return str(
            self.formatter.format_with_context(
                source_code=error.source_code,
                line=error.line or 1,
                col=col_value,
                message=message,
                suggestion=suggestion,
                error_type=error.__class__.__name__,
            )
        )
