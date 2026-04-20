"""Parser for the Cy language."""

import re
from typing import Any

from lark import Lark, ParseError, Token, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from cy_language.grammar import get_grammar

from .errors import (
    SyntaxError,
)


def _detect_python_style_syntax(source: str, line_num: int) -> str | None:
    """Detect Python-style syntax and return a helpful error message.

    Users coming from Python commonly use colons and skip parentheses for
    control flow statements.  Also detects other Python idioms that are not
    valid in Cy.

    Organized into three phases:
    1. Simple regex patterns (no trailing colon required)
    2. ``pass`` lookback heuristic (special case)
    3. Colon-terminated block starters (if/elif/while/for/else/with/except)
    """
    if not source or not line_num:
        return None

    lines = source.split("\n")
    if line_num < 1 or line_num > len(lines):
        return None

    stripped = lines[line_num - 1].strip()

    # ----------------------------------------------------------------
    # Phase 1: Simple regex → message patterns (no trailing colon needed)
    # ----------------------------------------------------------------
    for pattern, message in _SIMPLE_PYTHON_PATTERNS:
        if pattern.search(stripped):
            return message

    # Ternary expression needs an extra negative guard (not starting with "if")
    if re.search(r"^\S.+\s+if\s+\S.+\s+else\s+\S", stripped) and not re.match(
        r"^if\s", stripped
    ):
        return (
            "Python ternary expression 'x if cond else y' is not supported in Cy.\n"
            "Use a Cy conditional expression instead:\n"
            "  Python: result = x if x > 0 else 0\n"
            "  Cy:     result = if (x > 0) { x } else { 0 }"
        )

    # ----------------------------------------------------------------
    # Phase 2: ``pass`` lookback (error may be reported on the following line)
    # ----------------------------------------------------------------
    if stripped == "pass":
        return (
            "Python 'pass' is not needed in Cy.\n"
            "Remove it — Cy blocks can be empty, or just remove the block entirely."
        )
    for prev_idx in range(line_num - 2, max(line_num - 4, -1), -1):
        if lines[prev_idx].strip() == "pass":
            return (
                f"Python 'pass' is not needed in Cy (line {prev_idx + 1}).\n"
                "Remove it — Cy blocks can be empty, or just remove the block entirely."
            )
        if lines[prev_idx].strip():  # Stop at the first non-empty line
            break

    # ----------------------------------------------------------------
    # Phase 3: Colon-terminated block starters
    # ----------------------------------------------------------------
    if not stripped.endswith(":"):
        return None

    # Strip trailing colon and optional leading "}" (e.g. "} else:")
    inner = stripped[:-1].rstrip()
    inner_key = inner.lstrip("}").strip()

    # Python-style for: "for x in items:" (with or without outer parens)
    m = re.match(r"^for\s+\(?(\w+)\s+in\s+(.+?)\)?\s*$", inner_key)
    if m:
        var, iterable = m.group(1), m.group(2).strip()
        return (
            "Python-style for loop detected. In Cy, use parentheses and curly braces:\n"
            f"  Python: for {var} in {iterable}:\n"
            f"  Cy:     for ({var} in {iterable}) {{"
        )

    # Shared logic for if / elif / while (identical structure, different names)
    result = _check_colon_block_keyword(inner_key)
    if result:
        return result

    # Python-style else
    if re.match(r"^else\s*$", inner_key):
        return (
            "Python-style else detected. In Cy, use curly braces instead of ':':\n"
            "  Python: else:\n"
            "  Cy:     } else {"
        )

    # Remaining colon patterns: with, except
    for pattern, message in _COLON_SIMPLE_PATTERNS:
        if pattern.match(inner_key):
            return message

    return None


# ---------------------------------------------------------------------------
# Pattern tables for _detect_python_style_syntax()
#
# Each entry: (compiled_regex, message_string)
# Compiled once at import time for efficiency.
# ---------------------------------------------------------------------------

_SIMPLE_PYTHON_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^def\s+\w+\s*\("),
        "Python function definition is not supported in Cy.\n"
        "Write your logic directly in the script without defining functions.",
    ),
    (
        re.compile(r"^class\s+\w+"),
        "Python class definition is not supported in Cy.\n"
        "Cy is a scripting language — write your logic directly as a script.",
    ),
    (
        re.compile(r"^import\s+\w+"),
        "Python import statement is not supported in Cy.\n"
        "Cy scripts interact with the world through tools — "
        "check available tools with your Cy instance.",
    ),
    (
        re.compile(r"^from\s+\S+\s+import\s+"),
        "Python 'from ... import' statement is not supported in Cy.\n"
        "Cy scripts interact with the world through tools — "
        "check available tools with your Cy instance.",
    ),
    (
        re.compile(r"^raise\s+"),
        "Python 'raise' is not supported in Cy.\n"
        "Use try/catch to handle errors:\n"
        "  try {\n"
        "      ...\n"
        "  } catch (e) {\n"
        "      ...\n"
        "  }",
    ),
    (
        re.compile(r"^assert\s+"),
        "Python 'assert' is not supported in Cy.\n"
        "Use an if statement for validation:\n"
        '  if (x != 2) { return "validation failed" }',
    ),
    (
        re.compile(r"^.*\blambda\s+\w"),
        "Python lambda functions are not supported in Cy.\n"
        "Write the logic inline or use a for loop:\n"
        "  Python: fn = lambda x: x + 1\n"
        "  Cy:     result = x + 1  (inline)",
    ),
    (
        re.compile(r'(?<!["\'])f["\']'),
        "Python f-strings are not supported in Cy.\n"
        "Use Cy string interpolation with ${} inside double quotes:\n"
        '  Python: f"Hello {name}"\n'
        '  Cy:     "Hello ${name}"',
    ),
    (
        re.compile(r"\*\*"),
        "Python exponentiation operator ** is not supported in Cy.\n"
        "Use the pow() tool if available, or multiply explicitly:\n"
        "  Python: x ** 2\n"
        "  Cy:     x * x  (for square)",
    ),
    (
        re.compile(r"//"),
        "Python floor division operator // is not supported in Cy.\n"
        "Use regular division with integer conversion if needed:\n"
        "  Python: x // 3\n"
        "  Cy:     int(x / 3)",
    ),
    (
        re.compile(r"^(\w+\s*,\s*)+\w+\s*="),
        "Python tuple unpacking is not supported in Cy.\n"
        "Assign each variable on its own line:\n"
        "  Python: a, b = 1, 2\n"
        "  Cy:     a = 1\n"
        "          b = 2",
    ),
]

# Colon-terminated simple patterns (with, except) — no capture groups needed
_COLON_SIMPLE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^with\s+"),
        "Python 'with' statement is not supported in Cy.\n"
        "Cy scripts interact with external resources through tools.",
    ),
    (
        re.compile(r"^except\b"),
        "Python 'except' is not valid Cy syntax.\n"
        "Use 'catch' instead:\n"
        "  Python: except Exception as e:\n"
        "  Cy:     } catch (e) {",
    ),
]

# -- if / elif / while share identical structure: detect and suggest braces --
_COLON_BLOCK_KEYWORDS: list[tuple[str, re.Pattern[str], str, str]] = [
    # (keyword, regex, label_text, closing_prefix)
    (
        "if",
        re.compile(r"^if\s+(.+)$"),
        "if statement",
        "if",
    ),
    (
        "elif",
        re.compile(r"^elif\s+(.+)$"),
        "elif",
        "} elif",
    ),
    (
        "while",
        re.compile(r"^while\s+(.+)$"),
        "while loop",
        "while",
    ),
]


def _check_colon_block_keyword(inner_key: str) -> str | None:
    """Check for Python-style if/elif/while with colon.

    Shared logic: if condition already has parens → suggest replacing colon
    with brace; otherwise → wrap condition in parens too.
    """
    for _kw, pattern, label, cy_prefix in _COLON_BLOCK_KEYWORDS:
        m = pattern.match(inner_key)
        if not m:
            continue
        cond = m.group(1).strip()
        if cond.startswith("(") and cond.endswith(")"):
            return (
                f"Python-style {label} detected. In Cy, use '{{' instead of ':':\n"
                f"  Python: {_kw} {cond}:\n"
                f"  Cy:     {cy_prefix} {cond} {{"
            )
        return (
            f"Python-style {label} detected. In Cy, wrap the condition "
            f"and use curly braces:\n"
            f"  Python: {_kw} {cond}:\n"
            f"  Cy:     {cy_prefix} ({cond}) {{"
        )
    return None


# Module-level cache for compiled Lark parsers to avoid recompilation
# Note: These are set to None to force recompilation after grammar changes
_compiled_parser_cache = None
_compiled_parser_no_transform_cache = None


def _get_cached_parser() -> Lark:
    """Get cached Lark parser with transformer support."""
    global _compiled_parser_cache
    if _compiled_parser_cache is None:
        grammar = get_grammar()
        _compiled_parser_cache = Lark(grammar, parser="lalr", propagate_positions=True)
    return _compiled_parser_cache


def _get_cached_parser_no_transform() -> Lark:
    """Get cached Lark parser without transformer."""
    global _compiled_parser_no_transform_cache
    if _compiled_parser_no_transform_cache is None:
        grammar = get_grammar()
        _compiled_parser_no_transform_cache = Lark(
            grammar, parser="lalr", propagate_positions=True
        )
    return _compiled_parser_no_transform_cache


class Parser:
    """Parser for the Cy language."""

    def __init__(
        self,
        tools: dict[str, Any] | None = None,
        interpolation_mode: str = "markdown",
        item_tag: str = "item",
    ):
        """Initialize the parser.

        Args:
            tools: Unused (kept for backward compatibility)
            interpolation_mode: Unused (kept for backward compatibility)
            item_tag: Unused (kept for backward compatibility)
        """
        self.grammar = get_grammar()
        # Use cached parsers to avoid recompilation overhead
        self.lark_parser = _get_cached_parser()
        self.lark_parser_no_transform = _get_cached_parser_no_transform()

    def parse_only(self, code: str) -> Tree[Token]:
        """Parse a Cy program and return the AST without transformation.

        Args:
            code: The Cy program code

        Returns:
            The parsed AST tree

        Raises:
            SyntaxError: If the code has syntax errors
        """
        try:
            # Parse the code without transformation
            return self.lark_parser_no_transform.parse(code)
        except UnexpectedCharacters as e:
            # Check if the error is due to $ in variable assignment
            error_msg = str(e)
            if "'$'" in error_msg or "No terminal matches '$'" in error_msg:
                line, col = getattr(e, "line", 0), getattr(e, "column", 0)
                custom_msg = (
                    "Dollar signs ($) are only allowed inside string interpolations.\n"
                    "Use simple variable names like 'x = 5' instead of '$x = 5'.\n"
                    'For string interpolation, use ${variable} syntax: "Hello ${name}!"'
                )
                raise SyntaxError(custom_msg, line, col, text=code) from e
            line, col = getattr(e, "line", 0), getattr(e, "column", 0)
            python_msg = _detect_python_style_syntax(code, line)
            if python_msg:
                raise SyntaxError(python_msg, line, col, text=code) from e
            raise SyntaxError(str(e), line, col, text=code) from e
        except (ParseError, UnexpectedToken) as e:
            error_msg = str(e)
            line, col = getattr(e, "line", 0), getattr(e, "column", 0)
            # Check for Python-style syntax first (highest priority)
            python_msg = _detect_python_style_syntax(code, line)
            if python_msg:
                raise SyntaxError(python_msg, line, col, text=code) from e
            # Check for mixed notation pattern (parser limitation)
            if (
                "Unexpected token Token('DOT', '.')" in error_msg
                and "Previous tokens: [Token('RSQB', ']')]" in error_msg
            ):
                custom_msg = (
                    "Mixed bracket and dot notation is not supported.\n"
                    "Use consistent notation throughout:\n"
                    "  ✓ All dot notation: obj.user.data.name\n"
                    "  ✓ All bracket notation: obj['user']['data']['name']\n"
                    "  ✗ Mixed notation: obj.user['data'].name or obj['user'].data['name']"
                )
                raise SyntaxError(custom_msg, line, col, text=code) from e
            if "Unexpected token Token('LSQB', '[')" in error_msg:
                custom_msg = (
                    "Mixed dot and bracket notation is not supported.\n"
                    "Use consistent notation throughout:\n"
                    "  ✓ All dot notation: obj.user.data.name\n"
                    "  ✓ All bracket notation: obj['user']['data']['name']\n"
                    "  ✗ Mixed notation: obj.user['data'].name or obj['user'].data['name']"
                )
                raise SyntaxError(custom_msg, line, col, text=code) from e
            raise SyntaxError(str(e), line, col, text=code) from e
        except Exception as e:
            # Catch other Lark exceptions and convert them to SyntaxError
            raise SyntaxError(str(e)) from e
