"""
Cy Language Compiler - converts AST to Task Execution Plans.

This module handles the compilation of parsed Cy programs into structured
execution plans that can be inspected, validated, and executed.
"""

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

from lark import Token, Tree

from .errors import CompilerError

if TYPE_CHECKING:
    from .tool_resolver import ToolResolver
from .execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    BreakNode,
    ComparisonNode,
    ConditionalNode,
    ContinueNode,
    DictNode,
    ExecutionNode,
    ExecutionPlan,
    FieldAccessNode,
    FieldAssignNode,
    IndexedAccessNode,
    IndexedAssignNode,
    InterpolationNode,
    ListComprehensionNode,
    ListNode,
    LiteralNode,
    ReturnNode,
    ToolCallNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)


class InterpolationExpressionParser:
    """Simple regex-based parser for interpolation expressions."""

    def __init__(self) -> None:
        """Initialize the interpolation expression parser."""
        pass

    def _find_matching_brace(self, text: str, start_pos: int) -> int:
        """Find the matching closing brace, handling quoted strings properly."""
        if start_pos >= len(text) or text[start_pos] != "{":
            return -1

        pos = start_pos + 1
        brace_count = 1
        in_single_quote = False
        in_double_quote = False

        while pos < len(text) and brace_count > 0:
            char = text[pos]

            # Handle quote state changes
            if char == "'" and not in_double_quote:
                if pos == 0 or text[pos - 1] != "\\":
                    in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                if pos == 0 or text[pos - 1] != "\\":
                    in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1

            pos += 1

        return pos - 1 if brace_count == 0 else -1

    def parse_interpolation_expression(
        self, template: str
    ) -> tuple[list[ExecutionNode], dict[str, str]]:
        """Parse interpolation expressions in template string using regex approach.

        Args:
            template: String with interpolation patterns like ${expr|format}

        Returns:
            Tuple of (variable_nodes, printer_hints)
        """

        variable_nodes = []
        printer_hints = {}

        # Find all interpolation patterns and process them by position to avoid overlaps
        all_matches = []

        # Pattern 1: ${expr|format} - most specific
        for match in re.finditer(r"\$\{([^}|]+)\|([^}]+)\}", template):
            all_matches.append((match.start(), match.end(), "hint", match))

        # Pattern 2: ${expr} - only if not already covered by hint pattern
        for match in re.finditer(r"\$\{([^}]+)\}", template):
            # Check if this match overlaps with any hint matches
            overlaps = any(
                start <= match.start() < end or start < match.end() <= end
                for start, end, pattern_type, _ in all_matches
                if pattern_type == "hint"
            )
            if not overlaps:
                all_matches.append((match.start(), match.end(), "braced", match))

        # Pattern 3: $var - simple variable
        for match in re.finditer(r"\$([a-zA-Z][a-zA-Z0-9_]*)", template):
            # Check if this match overlaps with any existing matches
            overlaps = any(
                start <= match.start() < end or start < match.end() <= end
                for start, end, _, _ in all_matches
            )
            if not overlaps:
                all_matches.append((match.start(), match.end(), "simple", match))

        # Sort by position and process
        all_matches.sort(key=lambda x: x[0])

        for start, _end, pattern_type, match in all_matches:
            # Calculate approximate line/column based on match position in template
            # This is a rough approximation since we don't have the original AST position
            line_in_template = template[:start].count("\n") + 1
            col_in_template = start - template.rfind("\n", 0, start)

            if pattern_type == "hint":
                # ${expr|format} pattern
                expr = match.group(1).strip()
                format_hint = match.group(2).strip()
                node = self._parse_expression_content(
                    expr, line_in_template, col_in_template
                )
                if node:
                    # Store the original expression text in the node for interpolation
                    if not isinstance(node, VariableNode):
                        node._interpolation_expr = expr  # type: ignore[attr-defined]
                    variable_nodes.append(node)
                    printer_hints[match.group(0)] = format_hint
            elif pattern_type == "braced":
                # ${expr} pattern
                expr = match.group(1).strip()
                node = self._parse_expression_content(
                    expr, line_in_template, col_in_template
                )
                if node:
                    # Store the original expression text in the node for interpolation
                    # This is needed so the executor knows what to replace in the template
                    if not isinstance(node, VariableNode):
                        # For non-variable nodes (like ArithmeticNode), store the expression
                        node._interpolation_expr = expr  # type: ignore[attr-defined]
                    variable_nodes.append(node)
            elif pattern_type == "simple":
                # $var pattern
                var_name = match.group(1)
                node = VariableNode(
                    var_name, line_in_template, col_in_template, f"var_{var_name}"
                )
                variable_nodes.append(node)

        return variable_nodes, printer_hints

    def _parse_expression_content(
        self, content: str, line: int = 1, column: int = 1
    ) -> ExecutionNode | None:
        """Parse the content inside ${...} into an ExecutionNode.

        Args:
            content: Expression content like 'obj.field', 'func(arg)', 'data[\'key\']'
            line: Line number for error reporting
            column: Column number for error reporting

        Returns:
            ExecutionNode representing the parsed expression
        """
        content = content.strip()
        if not content:
            return None

        # Check for different expression types

        # 1. Indexed access: arr[0], obj['key'], or chained: arr[0][1]
        if "[" in content and "]" in content:
            return self._parse_indexed_access(content)

        # 2. Field access: obj.field.subfield
        if "." in content and not self._has_function_call(content):
            return self._parse_field_access(content, line, column)

        # 3. Function call: func(args)
        if "(" in content and ")" in content:
            return self._parse_function_call(content)

        # 4. Simple variable: var_name
        if self._is_simple_identifier(content):
            return VariableNode(content, line, column, f"var_{content}")

        # 5. Complex expression: for now, treat as variable
        return VariableNode(content, line, column, f"expr_{content}")

    def _has_function_call(self, content: str) -> bool:
        """Check if content contains function call syntax."""
        return "(" in content and ")" in content

    def _is_simple_identifier(self, content: str) -> bool:
        """Check if content is a simple identifier."""
        if not content:
            return False
        if not (content[0].isalpha() or content[0] == "_"):
            return False
        return all(c.isalnum() or c == "_" for c in content)

    def _parse_field_access(
        self, content: str, line: int = 1, column: int = 1
    ) -> ExecutionNode:
        """Parse field access like 'obj.field.subfield' into FieldAccessNode chain."""
        parts = content.split(".")
        if len(parts) < 2:
            return VariableNode(content, line, column, f"var_{content}")

        # Start with the base variable
        base_var = parts[0]
        current_node: ExecutionNode = VariableNode(
            base_var, line, column, f"var_{base_var}"
        )

        # Chain field accesses
        for field_name in parts[1:]:
            current_node = FieldAccessNode(
                current_node, field_name, line, column, f"field_{field_name}"
            )

        return current_node

    def _find_matching_bracket(self, text: str, start_pos: int) -> int:
        """Find the matching closing bracket, handling quoted strings properly."""
        if start_pos >= len(text) or text[start_pos] != "[":
            return -1

        pos = start_pos + 1
        bracket_count = 1
        in_single_quote = False
        in_double_quote = False

        while pos < len(text) and bracket_count > 0:
            char = text[pos]

            # Handle quote state changes
            if char == "'" and not in_double_quote:
                # Check if it's escaped
                if pos == 0 or text[pos - 1] != "\\":
                    in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                # Check if it's escaped
                if pos == 0 or text[pos - 1] != "\\":
                    in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote:
                # Only count brackets when not inside quotes
                if char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1

            pos += 1

        # Return position of matching bracket, or -1 if not found
        return pos - 1 if bracket_count == 0 else -1

    def _parse_indexed_access(self, content: str) -> ExecutionNode:
        """Parse indexed access like 'arr[0]', 'obj[\'key\']', or chained."""
        # Improved parsing that handles quotes properly

        # Handle chained indexed access
        current_node = None
        remaining = content

        while "[" in remaining and "]" in remaining:
            bracket_start = remaining.find("[")
            if bracket_start == -1:
                break

            # Get the object part (before the first '[')
            obj_part = remaining[:bracket_start].strip()

            # Find the matching closing bracket (improved approach that handles quotes)
            bracket_end = self._find_matching_bracket(remaining, bracket_start)
            if bracket_end == -1:
                break

            # Get the index part (inside the brackets)
            index_part = remaining[bracket_start + 1 : bracket_end].strip()

            # Create the object node
            if current_node is None:
                # First iteration - create base object node
                if obj_part:
                    if "." in obj_part:
                        current_node = self._parse_field_access(obj_part)
                    elif self._is_simple_identifier(obj_part):
                        current_node = VariableNode(obj_part, 1, 1, f"var_{obj_part}")
                    else:
                        current_node = VariableNode(obj_part, 1, 1, f"expr_{obj_part}")
                else:
                    return VariableNode(content, 1, 1, f"var_{content}")

            # Create the index node
            index_node = self._parse_index_expression(index_part)

            # Create the IndexedAccessNode
            current_node = IndexedAccessNode(
                current_node, index_node, 1, 1, f"idx_{bracket_start}"
            )

            # Prepare for next iteration (handle chaining)
            remaining = remaining[bracket_end + 1 :].strip()
            if not remaining:
                break

            # If there's more content, it should start with another bracket
            if not remaining.startswith("["):
                break

        return (
            current_node
            if current_node
            else VariableNode(content, 1, 1, f"var_{content}")
        )

    def _parse_index_expression(self, index_content: str) -> ExecutionNode:
        """Parse the content inside brackets [index_content] into a node."""
        index_content = index_content.strip()

        # Check if it's a string literal with single quotes (our new approach)
        if index_content.startswith("'") and index_content.endswith("'"):
            value = index_content[1:-1]  # Remove quotes
            return LiteralNode(value, 1, 1, f"lit_{value}")

        # Check if it's a string literal with double quotes (compatibility)
        if index_content.startswith('"') and index_content.endswith('"'):
            value = index_content[1:-1]  # Remove quotes
            return LiteralNode(value, 1, 1, f"lit_{value}")

        # Check if it's a number
        try:
            num_value: float | int = (
                float(index_content) if "." in index_content else int(index_content)
            )
            return LiteralNode(num_value, 1, 1, f"lit_{num_value}")
        except ValueError:
            pass

        # Check if it's a variable reference (starts with $)
        if index_content.startswith("$") and len(index_content) > 1:
            var_name = index_content[1:]  # Remove the $ prefix
            if self._is_simple_identifier(var_name):
                return VariableNode(var_name, 1, 1, f"var_{var_name}")

        # Check if it's a simple variable (without $ prefix)
        if self._is_simple_identifier(index_content):
            return VariableNode(index_content, 1, 1, f"var_{index_content}")

        # For complex expressions inside brackets, recursively parse
        result = self._parse_expression_content(index_content)
        assert result is not None, f"Failed to parse index expression: {index_content}"
        return result

    def _parse_function_call(self, content: str) -> ExecutionNode:
        """Parse function call like 'func(arg1, arg2)' into ToolCallNode."""
        # Simple parsing - find function name and skip arguments for now
        paren_pos = content.find("(")
        if paren_pos == -1:
            return VariableNode(content, 1, 1, f"var_{content}")

        func_name = content[:paren_pos].strip()

        # For now, create a simple ToolCallNode without parsing arguments
        arguments: list[ExecutionNode] = []
        named_arguments: dict[str, ExecutionNode] = {}

        return ToolCallNode(
            func_name, arguments, named_arguments, 1, 1, f"call_{func_name}"
        )


class UnifiedInterpolationParser(InterpolationExpressionParser):
    """Unified interpolation parser that supports full expressions using the main Lark parser.

    This parser enhances interpolation to support function calls, arithmetic,
    and boolean expressions inside ${} patterns while maintaining backward compatibility.
    """

    def __init__(self, lark_parser: Any, compiler: "PlanCompiler") -> None:
        """Initialize with access to the main Lark parser and compiler.

        Args:
            lark_parser: The main Lark parser instance for parsing expressions
            compiler: The compiler instance for compiling parsed expressions
        """
        super().__init__()
        self.lark_parser = lark_parser
        self.compiler = compiler

    def _parse_expression_content(
        self, content: str, line: int = 1, column: int = 1
    ) -> ExecutionNode | None:
        """Parse the content inside ${...} into an ExecutionNode.

        Overrides parent method to support full expressions using Lark parser.
        """
        # Handle empty or whitespace-only content
        content = content.strip()
        if not content:
            return None

        # Check if we can use fast path for simple expressions
        if self._is_simple_expression(content):
            # Use parent's regex-based parsing for backward compatibility
            return super()._parse_expression_content(content, line, column)

        # Use full Lark parser for complex expressions
        return self._parse_with_lark(content, line, column)

    def _is_simple_expression(self, content: str) -> bool:
        """Determine if expression can use fast path (regex) or needs full parser.

        Returns True for simple variables, field access, and indexed access.
        Returns False for expressions with operators or function calls.
        """
        content = content.strip()

        # Check for operators that require full parsing
        operators = [
            " + ",
            " - ",
            " * ",
            " / ",
            " % ",
            " and ",
            " or ",
            " not ",
            " == ",
            " != ",
            " < ",
            " > ",
            " <= ",
            " >= ",
        ]
        for op in operators:
            if op in content:
                return False

        # Check for function calls (parentheses not in quotes)
        if self._has_unquoted_parens(content):
            return False

        # If it's a simple variable, field access, or indexed access, use fast path
        return (
            self._is_simple_variable(content)
            or self._is_simple_field_access(content)
            or self._is_simple_indexed_access(content)
        )

    def _parse_with_lark(
        self, content: str, line: int = 1, column: int = 1
    ) -> ExecutionNode:
        """Parse expression using the main Lark parser.

        Wraps the expression in a temporary assignment to leverage existing parser.
        """
        # Remove $ prefix from variables in the expression since the grammar expects plain identifiers
        # The $ is a Cy convention but the grammar uses IDENTIFIER without $
        content_for_parser = content.replace("$", "")

        # Create a temporary assignment statement to parse the expression
        # This leverages the existing parser's ability to parse complex expressions
        temp_program = f"tempExpr = {content_for_parser}"

        try:
            # Parse the temporary program
            ast_tree = self.lark_parser.parse(temp_program)

            # Extract the expression from the assignment
            # The AST should be: start -> statement -> assignment
            if ast_tree.data == "start" and ast_tree.children:
                statement = ast_tree.children[0]
                if (
                    hasattr(statement, "data")
                    and statement.data == "statement"
                    and statement.children
                    and hasattr(statement.children[0], "data")
                ):
                    assignment = statement.children[0]
                    if (
                        assignment.data == "assignment"
                        and len(assignment.children) >= 2
                    ):
                        # Assignment now has 3 children: [var, compound_op, expr]
                        # For temp interpolation assignments, compound_op will always be "="
                        # Extract expression from child[2] if 3 children, else child[1]
                        expr_tree = (
                            assignment.children[2]
                            if len(assignment.children) >= 3
                            else assignment.children[1]
                        )
                        # Compile the expression tree to an ExecutionNode
                        result = self.compiler._compile_expression(expr_tree)
                        if result is not None:
                            return result

            # Fallback: treat as simple variable if parsing fails
            return VariableNode(content, line, column, f"expr_{content}")

        except Exception as e:
            # Check if this looks like it should be a valid expression but has syntax errors
            # Look for indicators of function calls or operators
            if (
                "(" in content
                or ")" in content
                or any(
                    op in content
                    for op in ["+", "-", "*", "/", "**", "and", "or", "not"]
                )
            ):
                # This looks like an expression that failed to parse - likely a syntax error
                # Check for mixed notation pattern in interpolation
                # Patterns: obj.field["key"] or obj["key"].field
                import re

                from .errors import SyntaxError as CySyntaxError

                # Match patterns like: .field followed by [" or ["key"] followed by .field
                if re.search(r'\.\w+\s*\[[\'"]', content) or re.search(
                    r"\]\.\w+", content
                ):
                    raise CySyntaxError(
                        "Mixed dot and bracket notation is not supported in interpolations.\n"
                        "Use consistent notation:\n"
                        "  ✓ All dot: ${obj.user.data.name}\n"
                        "  ✓ All bracket: ${obj['user']['data']['name']}\n"
                        "  ✗ Mixed: ${obj.user['data'].name}",
                        line,
                        column,
                    )

                # Extract a more specific error message if possible
                error_msg = str(e)
                if "No terminal matches" in error_msg or "Expected" in error_msg:
                    raise CySyntaxError(
                        f"Invalid expression syntax: {content}", line, column
                    )
                raise CySyntaxError(
                    f"Failed to parse expression: {content}", line, column
                )
            # Otherwise, treat as a variable name (backward compatibility)
            return VariableNode(content, line, column, f"expr_{content}")

    def _is_simple_variable(self, content: str) -> bool:
        """Check if content is a simple variable like 'name' or '$name'."""
        content = content.strip()
        # Remove leading $ if present
        if content.startswith("$"):
            content = content[1:]
        # Check if it's a valid identifier
        if not content:
            return False
        if not (content[0].isalpha() or content[0] == "_"):
            return False
        return all(c.isalnum() or c == "_" for c in content)

    def _is_simple_field_access(self, content: str) -> bool:
        """Check if content is simple field access like 'user.email'."""
        content = content.strip()
        # Must have dots but no other operators
        if "." not in content:
            return False
        # No function calls
        if "(" in content or ")" in content:
            return False
        # No brackets (indexed access)
        if "[" in content or "]" in content:
            return False
        # Check each part is a valid identifier
        parts = content.split(".")
        for part in parts:
            part = part.strip()
            if part.startswith("$"):
                part = part[1:]
            if not part or not self._is_simple_identifier(part):
                return False
        return True

    def _is_simple_indexed_access(self, content: str) -> bool:
        """Check if content is simple indexed access like 'arr[0]' or 'data["key"]'."""
        content = content.strip()
        # Must have brackets
        if "[" not in content or "]" not in content:
            return False
        # No function calls (unless parens are inside quotes)
        if "(" in content and ")" in content and not self._parens_in_quotes(content):
            return False
        # No arithmetic/boolean operators outside of brackets
        # This is a simple heuristic - just check no operators before first bracket
        bracket_pos = content.find("[")
        before_bracket = content[:bracket_pos]
        operators = [" + ", " - ", " * ", " / ", " and ", " or ", " not "]
        return all(op not in before_bracket for op in operators)

    def _has_unquoted_parens(self, content: str) -> bool:
        """Check if content has parentheses that are not inside quotes."""
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(content):
            char = content[i]
            # Check for escaped characters
            if i > 0 and content[i - 1] == "\\":
                i += 1
                continue
            # Toggle quote states
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote and char in "()":
                return True
            i += 1
        return False

    def _parens_in_quotes(self, content: str) -> bool:
        """Check if all parentheses in content are inside quotes."""
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(content):
            char = content[i]
            # Check for escaped characters
            if i > 0 and content[i - 1] == "\\":
                i += 1
                continue
            # Toggle quote states
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote and char in "()":
                return False  # Found unquoted parens
            i += 1
        return True  # All parens are quoted

    def _is_simple_identifier(self, content: str) -> bool:
        """Check if content is a simple identifier."""
        if not content:
            return False
        if not (content[0].isalpha() or content[0] == "_"):
            return False
        return all(c.isalnum() or c == "_" for c in content)


class EnhancedInterpolationParser(InterpolationExpressionParser):
    """Enhanced interpolation parser for triple-quoted strings that supports double quotes in expressions."""

    def parse_interpolation_expression(
        self, template: str
    ) -> tuple[list[ExecutionNode], dict[str, str]]:
        """Parse interpolation expressions in triple-quoted template string with enhanced brace matching."""

        variable_nodes: list[ExecutionNode] = []
        printer_hints: dict[str, str] = {}
        all_matches: list[tuple[int, int, str, Any]] = []

        # Find ${...} patterns with proper brace matching (counter-based approach per web research)
        pos = 0
        while pos < len(template):
            dollar_pos = template.find("${", pos)
            if dollar_pos == -1:
                break

            # Find matching closing brace using counter-based approach
            close_pos = self._find_matching_brace(template, dollar_pos + 1)
            if close_pos == -1:
                pos = dollar_pos + 2
                continue

            full_expr = template[dollar_pos + 2 : close_pos]

            # Check for hint pattern (expr|format)
            if "|" in full_expr and full_expr.count("|") == 1:
                pipe_pos = full_expr.rfind("|")
                expr_part = full_expr[:pipe_pos]
                hint_part = full_expr[pipe_pos + 1 :]

                class MockHintMatch:
                    def __init__(
                        self,
                        start: int,
                        end: int,
                        full_match: str,
                        expr: str,
                        hint: str,
                    ) -> None:
                        self._start, self._end = start, end
                        self._full_match, self.expr, self.hint = full_match, expr, hint

                    def start(self) -> int:
                        return self._start

                    def end(self) -> int:
                        return self._end

                    def group(self, n: int) -> str:
                        return [self._full_match, self.expr, self.hint][n]

                full_match_text = template[dollar_pos : close_pos + 1]
                mock_match: Any = MockHintMatch(
                    dollar_pos, close_pos + 1, full_match_text, expr_part, hint_part
                )
                all_matches.append((dollar_pos, close_pos + 1, "hint", mock_match))
            else:

                class MockBracedMatch:
                    def __init__(
                        self, start: int, end: int, full_match: str, expr: str
                    ) -> None:
                        self._start, self._end = start, end
                        self._full_match, self.expr = full_match, expr

                    def start(self) -> int:
                        return self._start

                    def end(self) -> int:
                        return self._end

                    def group(self, n: int) -> str:
                        return [self._full_match, self.expr][n]

                full_match_text = template[dollar_pos : close_pos + 1]
                mock_match = MockBracedMatch(
                    dollar_pos, close_pos + 1, full_match_text, full_expr
                )
                all_matches.append((dollar_pos, close_pos + 1, "braced", mock_match))

            pos = close_pos + 1

        # Add simple variable patterns
        for match in re.finditer(r"\$([a-zA-Z][a-zA-Z0-9_]*)", template):
            overlaps = any(
                start <= match.start() < end or start < match.end() <= end
                for start, end, _, _ in all_matches
            )
            if not overlaps:
                all_matches.append((match.start(), match.end(), "simple", match))

        # Process matches
        all_matches.sort(key=lambda x: x[0])
        for start, _end, pattern_type, match in all_matches:
            line_in_template = template[:start].count("\n") + 1
            col_in_template = start - template.rfind("\n", 0, start)

            if pattern_type == "hint":
                expr = match.group(1).strip()
                format_hint = match.group(2).strip()
                node = self._parse_expression_content(
                    expr, line_in_template, col_in_template
                )
                if node:
                    variable_nodes.append(node)
                    printer_hints[match.group(0)] = format_hint
            elif pattern_type == "braced":
                expr = match.group(1).strip()
                node = self._parse_expression_content(
                    expr, line_in_template, col_in_template
                )
                if node:
                    variable_nodes.append(node)
            elif pattern_type == "simple":
                var_name = match.group(1)
                node = VariableNode(
                    var_name, line_in_template, col_in_template, f"var_{var_name}"
                )
                variable_nodes.append(node)

        return variable_nodes, printer_hints


class PlanCompiler:
    """Compiles Cy AST trees into execution plans."""

    def __init__(
        self,
        available_tools: dict[str, Any] | None = None,
        lark_parser: Any = None,
        tool_resolver: Optional["ToolResolver"] = None,
    ) -> None:
        self.node_counter = 0
        self.lark_parser = lark_parser  # For enhanced interpolation support
        # Use UnifiedInterpolationParser if we have a lark_parser, else create one
        if lark_parser is None:
            # Create a parser instance for interpolation support
            from .parser import Parser

            parser_instance = Parser()
            self.lark_parser = (
                parser_instance.lark_parser
            )  # Access the internal Lark parser
        # Use UnifiedInterpolationParser for full expression support in interpolation
        self.interpolation_parser = UnifiedInterpolationParser(self.lark_parser, self)
        self.available_tools = available_tools or {}
        self.tool_resolver = tool_resolver  # Namespace resolution
        self._loop_depth = 0  # Track nesting for break/continue validation
        self._in_finally = False  # Forbid break/continue in finally blocks

    @contextmanager
    def _loop_scope(self):
        """Enter a loop body scope: break/continue become valid, _in_finally is cleared.

        A loop inside a finally block is a fresh scope where break/continue
        target the inner loop, not the outer finally.
        """
        self._loop_depth += 1
        prev_in_finally = self._in_finally
        self._in_finally = False
        try:
            yield
        finally:
            self._in_finally = prev_in_finally
            self._loop_depth -= 1

    def compile(self, ast_tree: Tree, source_file: str | None = None) -> ExecutionPlan:
        """Compile AST tree to execution plan."""
        plan = ExecutionPlan(source_file=source_file)

        # No need to check for $output conflicts - only return statements are supported

        # Basic compilation - for now, just create a simple plan
        # This will be enhanced as we need more functionality

        if ast_tree.data == "start":
            # Process all children in the start node
            for child in ast_tree.children:
                node = self._compile_tree_node(child)
                if node:
                    # Handle for-in returning a list of nodes
                    if isinstance(node, list):
                        for n in node:
                            plan.add_node(n)
                    else:
                        plan.add_node(node)

        return plan

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self.node_counter += 1
        return f"node_{self.node_counter}"

    def _compile_assignment(self, tree: Tree) -> ExecutionNode:
        """Compile assignment statement."""
        # AST structure can be either:
        # 1. assignment -> VARIABLE compound_op expression  (traditional assignment)
        # 2. assignment -> indexed_assignment   (indexed assignment)
        # 3. assignment -> field_assignment     (field assignment)

        if len(tree.children) == 1:
            # This is either indexed_assignment or field_assignment
            child = tree.children[0]
            if child.data == "indexed_assignment":
                return self._compile_indexed_assignment(child)
            if child.data == "field_assignment":
                return self._compile_field_assignment(child)
            raise CompilerError(f"Unknown assignment type: {child.data}", 1, 1)
        if len(tree.children) == 3:
            # This is a traditional assignment
            # Extract variable name (handle both VARIABLE and IDENTIFIER tokens)
            var_token = tree.children[0]

            if isinstance(var_token, Token):
                if var_token.type == "VARIABLE":
                    # $name format - remove $ prefix and check for conflicts
                    variable_name = var_token.value
                    if variable_name.startswith("$"):
                        variable_name = variable_name[1:]

                    # Check reserved words and function conflicts
                    from .variable_normalizer import VariableNormalizer

                    # Check reserved literals first
                    if VariableNormalizer.is_reserved_literal(variable_name):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to reserved literal '{variable_name}'",
                            line,
                            col,
                        )

                    # Check reserved keywords (currently disabled)
                    if VariableNormalizer.is_reserved_keyword(variable_name):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to reserved keyword '{variable_name}'",
                            line,
                            col,
                        )

                    # Check if this conflicts with function names (after normalization)
                    if VariableNormalizer.is_reserved_function(
                        variable_name, self.available_tools
                    ):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to '{variable_name}': conflicts with function name",
                            line,
                            col,
                        )
                elif var_token.type == "IDENTIFIER":
                    # name format - check for conflicts
                    variable_name = var_token.value

                    # Check for special protected variables
                    if variable_name == "input":
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            "Cannot reassign the input variable",
                            line,
                            col,
                        )

                    # Check reserved words and function conflicts
                    from .variable_normalizer import VariableNormalizer

                    # Check reserved literals first
                    if VariableNormalizer.is_reserved_literal(variable_name):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to reserved literal '{variable_name}'",
                            line,
                            col,
                        )

                    # Check reserved keywords (currently disabled)
                    if VariableNormalizer.is_reserved_keyword(variable_name):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to reserved keyword '{variable_name}'",
                            line,
                            col,
                        )

                    # Check if this conflicts with function names
                    if VariableNormalizer.is_reserved_function(
                        variable_name, self.available_tools
                    ):
                        line, col = self._get_line_column(tree)
                        raise CompilerError(
                            f"Cannot assign to '{variable_name}': conflicts with function name",
                            line,
                            col,
                        )
                else:
                    raise CompilerError(
                        "Expected variable or identifier in assignment", 1, 1
                    )
            else:
                raise CompilerError(
                    "Expected variable or identifier in assignment", 1, 1
                )

            # Get the compound operator (child 1)
            compound_op_tree = tree.children[1]
            # Extract operator from either COMPOUND_ASSIGN_OP token or "=" literal
            if isinstance(compound_op_tree, Tree):
                if len(compound_op_tree.children) > 0:
                    operator = compound_op_tree.children[0].value  # type: ignore[union-attr]  # COMPOUND_ASSIGN_OP token
                else:
                    operator = "="  # String literal "=" produces empty Tree
            else:
                raise CompilerError("Failed to extract compound operator", 1, 1)

            # Compile the expression (child 2)
            expression_tree = tree.children[2]
            expression_node = self._compile_tree_node(expression_tree)

            if expression_node is None:
                raise CompilerError("Failed to compile expression in assignment", 1, 1)

            # Get line/column info from the variable token
            line, col = self._get_line_column(var_token)

            # Handle compound assignment operators
            # Desugar compound assignments: $x += 5 → $x = $x + 5
            if operator != "=":
                # Map compound operator to arithmetic operator
                op_map = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}
                arith_op = op_map.get(operator)

                if arith_op is None:
                    raise CompilerError(
                        f"Unknown compound operator: {operator}", line, col
                    )

                # Create variable reference for left side of arithmetic
                var_node = VariableNode(
                    variable_name, line, col, self._generate_node_id()
                )

                # Create arithmetic node: var <op> expression
                from .execution_plan import ArithmeticNode

                expression_node = ArithmeticNode(
                    arith_op,
                    var_node,
                    expression_node,
                    line,
                    col,
                    self._generate_node_id(),
                )

            return AssignNode(
                variable_name, expression_node, line, col, self._generate_node_id()
            )
        raise CompilerError("Invalid assignment syntax", 1, 1)

    def _compile_indexed_assignment(self, tree: Tree) -> IndexedAssignNode:
        """Compile indexed assignment statement like $dict[$key] = $value."""
        # AST structure: indexed_assignment -> indexed_access compound_op expression
        # Children: [Tree(indexed_access, [...]]), Tree(compound_op, [...]), Tree(expression, [...])]

        if len(tree.children) != 3:
            raise CompilerError("Invalid indexed assignment syntax", 1, 1)

        # Compile the target (indexed access)
        target_tree = tree.children[0]
        target_node = self._compile_tree_node(target_tree)

        if target_node is None:
            raise CompilerError("Failed to compile target in indexed assignment", 1, 1)

        # Get the compound operator (child 1)
        compound_op_tree = tree.children[1]
        # Extract operator from either COMPOUND_ASSIGN_OP token or "=" literal
        if isinstance(compound_op_tree, Tree):
            if len(compound_op_tree.children) > 0:
                operator = compound_op_tree.children[0].value  # type: ignore[union-attr]  # COMPOUND_ASSIGN_OP token
            else:
                operator = "="  # String literal "=" produces empty Tree
        else:
            raise CompilerError("Failed to extract compound operator", 1, 1)

        # Compile the value expression (child 2)
        value_tree = tree.children[2]
        value_node = self._compile_tree_node(value_tree)

        if value_node is None:
            raise CompilerError("Failed to compile value in indexed assignment", 1, 1)

        # Get line/column info
        line, col = self._get_line_column(tree)

        # Handle compound assignment operators
        # Desugar compound assignments: $list[0] += 5 → $list[0] = $list[0] + 5
        if operator != "=":
            # Map compound operator to arithmetic operator
            op_map = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}
            arith_op = op_map.get(operator)

            if arith_op is None:
                raise CompilerError(f"Unknown compound operator: {operator}", line, col)

            # Create a copy of the indexed access for the right side
            # We need to re-compile the target to get a fresh node
            target_node_rhs = self._compile_tree_node(target_tree)
            assert target_node_rhs is not None

            # Create arithmetic node: indexed_access <op> expression
            from .execution_plan import ArithmeticNode

            value_node = ArithmeticNode(
                arith_op,
                target_node_rhs,
                value_node,
                line,
                col,
                self._generate_node_id(),
            )

        return IndexedAssignNode(
            target_node, value_node, line, col, self._generate_node_id()
        )

    def _compile_field_assignment(self, tree: Tree) -> FieldAssignNode:
        """Compile field assignment statement like a.x = value.

        This is syntactic sugar for a["x"] = value.
        Tree structure: field_access compound_op expression
        """
        # AST structure: field_assignment -> field_access compound_op expression
        # Children: [Tree(field_access, [...]]), Tree(compound_op, [...]), Tree(expression, [...])]

        if len(tree.children) != 3:
            raise CompilerError("Invalid field assignment syntax", 1, 1)

        # Compile the target (field access)
        target_tree = tree.children[0]
        target_node = self._compile_tree_node(target_tree)

        if target_node is None:
            raise CompilerError("Failed to compile target in field assignment", 1, 1)

        # Get the compound operator (child 1)
        compound_op_tree = tree.children[1]
        # Extract operator from either COMPOUND_ASSIGN_OP token or "=" literal
        if isinstance(compound_op_tree, Tree):
            if len(compound_op_tree.children) > 0:
                operator = compound_op_tree.children[0].value  # type: ignore[union-attr]  # COMPOUND_ASSIGN_OP token
            else:
                operator = "="  # String literal "=" produces empty Tree
        else:
            raise CompilerError("Failed to extract compound operator", 1, 1)

        # Compile the value expression (child 2)
        value_tree = tree.children[2]
        value_node = self._compile_tree_node(value_tree)

        if value_node is None:
            raise CompilerError("Failed to compile value in field assignment", 1, 1)

        # Get line/column info
        line, col = self._get_line_column(tree)

        # Handle compound assignment operators
        # Desugar compound assignments: a.x += 5 → a.x = a.x + 5
        if operator != "=":
            # Map compound operator to arithmetic operator
            op_map = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}
            arith_op = op_map.get(operator)

            if arith_op is None:
                raise CompilerError(f"Unknown compound operator: {operator}", line, col)

            # Create a copy of the field access for the right side
            # We need to re-compile the target to get a fresh node
            target_node_rhs = self._compile_tree_node(target_tree)
            assert target_node_rhs is not None

            # Create arithmetic node: field_access <op> expression
            from .execution_plan import ArithmeticNode

            value_node = ArithmeticNode(
                arith_op,
                target_node_rhs,
                value_node,
                line,
                col,
                self._generate_node_id(),
            )

        return FieldAssignNode(
            target_node, value_node, line, col, self._generate_node_id()
        )

    def _compile_tool_call(self, tree: Tree) -> ToolCallNode:
        """Compile tool call."""
        # AST structure: function_call -> function_name "(" arguments? ")"
        # function_name -> IDENTIFIER | namespaced_identifier
        # arguments -> positional_args | named_args | mixed_args

        if len(tree.children) < 1:
            raise CompilerError("Invalid function call", 1, 1)

        # Extract tool name (should be a string from transformer)
        function_name_node = tree.children[0]

        if isinstance(function_name_node, str):
            # Transformer already converted to string
            tool_name = function_name_node
        elif (
            isinstance(function_name_node, Token)
            and function_name_node.type == "IDENTIFIER"
        ):
            # Legacy: Simple function name (when transformer wasn't used)
            tool_name = function_name_node.value
        elif (
            isinstance(function_name_node, Tree)
            and function_name_node.data == "function_name"
        ):
            # Legacy: function_name wrapper - get the actual identifier or namespaced_identifier
            inner_node = function_name_node.children[0]
            if isinstance(inner_node, Token) and inner_node.type == "IDENTIFIER":
                tool_name = inner_node.value
            elif (
                isinstance(inner_node, Tree)
                and inner_node.data == "namespaced_identifier"
            ):
                # namespaced_identifier: IDENTIFIER NAMESPACE_SEP IDENTIFIER NAMESPACE_SEP IDENTIFIER
                parts = []
                for child in inner_node.children:
                    if isinstance(child, Token) and child.type == "IDENTIFIER":
                        parts.append(child.value)
                tool_name = "::".join(parts)
            else:
                raise CompilerError("Expected function identifier", 1, 1)
        else:
            raise CompilerError("Expected function name", 1, 1)

        # Validate namespace format
        self._validate_namespace(tool_name)

        # Resolve tool name using ToolResolver
        original_name = tool_name  # Keep original for error messages
        if self.tool_resolver:
            from .errors import AmbiguousToolError, ToolResolutionError

            try:
                fqn, original_name = self.tool_resolver.resolve(tool_name)
                tool_name = fqn  # Use resolved FQN
            except AmbiguousToolError as e:
                # Re-raise with line/column info
                line, col = self._get_line_column(tree)
                raise AmbiguousToolError(e.tool_name, e.matches, line, col)
            except ToolResolutionError as e:
                # Re-raise with line/column info
                line, col = self._get_line_column(tree)
                raise ToolResolutionError(e.tool_name, e.suggestions, line, col)

        arguments: list[ExecutionNode] = []
        named_arguments: dict[str, ExecutionNode] = {}

        # Process arguments if present
        if len(tree.children) > 1:
            args_tree = tree.children[1]
            if isinstance(args_tree, Tree) and args_tree.data == "arguments":
                arguments, named_arguments = self._compile_arguments(args_tree)

        # Get line/column info
        line, col = self._get_line_column(tree)

        return ToolCallNode(
            tool_name,
            arguments,
            named_arguments,
            line,
            col,
            self._generate_node_id(),
            original_name=original_name,
        )

    def _compile_arguments(
        self, tree: Tree
    ) -> tuple[list[ExecutionNode], dict[str, ExecutionNode]]:
        """Compile function arguments."""
        arguments = []
        named_arguments = {}

        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "positional_args":
                    # positional_args -> expression ("," expression)*
                    for expr_child in child.children:
                        if isinstance(expr_child, Tree):
                            arg_node = self._compile_tree_node(expr_child)
                            if arg_node:
                                arguments.append(arg_node)

                elif child.data == "named_args":
                    # named_args -> named_arg ("," named_arg)*
                    for named_arg_child in child.children:
                        if (
                            isinstance(named_arg_child, Tree)
                            and named_arg_child.data == "named_arg"
                            and len(named_arg_child.children) >= 2
                        ):
                            name_token = named_arg_child.children[0]
                            expr_tree = named_arg_child.children[1]
                            if (
                                isinstance(name_token, Token)
                                and name_token.type == "IDENTIFIER"
                            ):
                                arg_node = self._compile_tree_node(expr_tree)
                                if arg_node:
                                    named_arguments[name_token.value] = arg_node

                elif child.data == "mixed_args":
                    # Handle mixed arguments (positional first, then named)
                    for mixed_child in child.children:
                        if (
                            isinstance(mixed_child, Tree)
                            and mixed_child.data == "mixed_args_pos_first"
                        ):
                            self._process_mixed_args_structure(
                                mixed_child, arguments, named_arguments
                            )

        return arguments, named_arguments

    def _process_mixed_args_structure(
        self, tree: Tree, arguments: list, named_arguments: dict
    ) -> None:
        """Process mixed arguments structure (both pos_first and named_first)."""
        # Both mixed_args_pos_first and mixed_args_named_first contain a mix of:
        # - expression nodes (positional args)
        # - named_arg nodes (named args)
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "named_arg":
                    # This is a named argument: name=value
                    if len(child.children) >= 2:
                        name_token = child.children[0]
                        expr_tree = child.children[1]
                        if (
                            isinstance(name_token, Token)
                            and name_token.type == "IDENTIFIER"
                        ):
                            arg_node = self._compile_tree_node(expr_tree)
                            if arg_node:
                                named_arguments[name_token.value] = arg_node
                else:
                    # This is a positional argument (expression)
                    arg_node = self._compile_tree_node(child)
                    if arg_node:
                        arguments.append(arg_node)
            elif isinstance(child, Token):
                # Skip tokens like commas
                continue

    def _compile_string_interpolation(self, tree: Tree) -> InterpolationNode:
        """Compile string interpolation."""
        # Stub implementation
        template = "stub_template"
        variables: list[ExecutionNode] = []
        printer_hints: dict[str, str] = {}
        return InterpolationNode(
            template, variables, printer_hints, 1, 1, self._generate_node_id()
        )

    def _compile_expression(self, tree: Tree) -> ExecutionNode | None:
        """Compile expression node."""
        # Expression nodes wrap other nodes, so compile their children
        for child in tree.children:
            node = self._compile_tree_node(child)
            if node:
                return node
        return None

    def _compile_string_literal(self, tree: Tree) -> ExecutionNode:
        """Compile string literal, detecting interpolation patterns."""
        # AST structure: string -> DOUBLE_QUOTED_STRING
        if len(tree.children) != 1:
            raise CompilerError("Invalid string literal", 1, 1)

        string_token = tree.children[0]
        if isinstance(string_token, Token):
            # Remove quotes from the string value
            value = string_token.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]  # Remove surrounding quotes

            # Check if string contains unescaped interpolation patterns
            if self._has_unescaped_interpolation(value):
                # Keep original value for interpolation (escapes handled in executor)
                return self._compile_interpolated_string(value, tree)
            # No interpolation, process escapes and return literal
            processed_value = self._process_escape_sequences(value)
            line, col = self._get_line_column(tree)
            return LiteralNode(processed_value, line, col, self._generate_node_id())
        raise CompilerError("Expected string token", 1, 1)

    def _compile_interpolated_multiline_string(
        self, template: str, tree: Tree
    ) -> InterpolationNode:
        """Compile a triple-quoted string with enhanced interpolation that supports double quotes."""
        # Use UnifiedInterpolationParser if lark_parser is available
        enhanced_parser: InterpolationExpressionParser
        if self.lark_parser:
            enhanced_parser = UnifiedInterpolationParser(self.lark_parser, self)
        else:
            # Use enhanced interpolation parser that can handle double quotes in expressions
            enhanced_parser = EnhancedInterpolationParser()
        (
            variable_nodes,
            printer_hints,
        ) = enhanced_parser.parse_interpolation_expression(template)

        # Get line/column info
        line, col = self._get_line_column(tree)

        # Variable nodes already have their line/column info set during parsing
        return InterpolationNode(
            template, variable_nodes, printer_hints, line, col, self._generate_node_id()
        )

    def _compile_single_quoted_string(self, tree: Tree) -> ExecutionNode:
        """Compile single quoted string literal (no interpolation support)."""
        # AST structure: single_quoted_string -> SINGLE_QUOTED_STRING
        if len(tree.children) != 1:
            raise CompilerError("Invalid single quoted string literal", 1, 1)

        string_token = tree.children[0]
        if isinstance(string_token, Token):
            # Remove quotes from the string value
            value = string_token.value
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]  # Remove surrounding quotes

            # Single quoted strings don't support interpolation - always return literal
            processed_value = self._process_escape_sequences(value)
            line, col = self._get_line_column(tree)
            return LiteralNode(processed_value, line, col, self._generate_node_id())
        raise CompilerError("Expected single quoted string token", 1, 1)

    def _has_interpolation(self, text: str) -> bool:
        """Check if a string contains variable interpolation patterns."""
        # Look for patterns like $variable, ${variable}, or ${variable|format}
        # But exclude escaped patterns (those with placeholder markers)
        patterns = [
            r"(?<!\x00ESCAPED_DOLLAR\x00)\$[a-zA-Z][a-zA-Z0-9_]*",  # $var (not escaped)
            r"(?<!\x00ESCAPED_DOLLAR\x00)\$\{[a-zA-Z][a-zA-Z0-9_.]*\}",  # ${var}
            r"(?<!\x00ESCAPED_DOLLAR\x00)\$\{[a-zA-Z][a-zA-Z0-9_.]*\|[^}]+\}",
        ]

        # First check if we have any placeholders (indicating escapes were processed)
        if "\x00ESCAPED_DOLLAR\x00" in text:
            # Text has been processed but not yet restored - check patterns
            # For now, if we have escaped dollars, we need to be more careful
            # Let's check if there are any unescaped $ patterns
            return any(
                re.search(
                    pattern.replace("(?<!\x00ESCAPED_DOLLAR\x00)", ""),
                    text.replace("\x00ESCAPED_DOLLAR\x00", "\x01"),
                )
                for pattern in patterns
            )
        # No escapes processed yet, use original logic
        simple_patterns = [
            r"\$[a-zA-Z][a-zA-Z0-9_]*",  # $var
            r"\$\{[a-zA-Z][a-zA-Z0-9_.]*\}",  # ${var} or ${obj.field}
            r"\$\{[a-zA-Z][a-zA-Z0-9_.]*\|[^}]+\}",  # ${var|format}
        ]
        return any(re.search(pattern, text) for pattern in simple_patterns)

    def _has_unescaped_interpolation(self, text: str) -> bool:
        """Check if string has interpolation patterns that are not escaped."""

        # Look for $var or ${...} patterns that are not preceded by backslash
        # Handle escaped quotes inside ${...} patterns from preprocessing
        patterns = [
            r"(?<!\\)\$[a-zA-Z][a-zA-Z0-9_]*",  # $var not escaped
            r"(?<!\\)\$\{([^}]|\\.)*\}",  # ${...} not escaped
        ]

        return any(re.search(pattern, text) for pattern in patterns)

    def _process_escape_sequences(self, text: str) -> str:
        """Process escape sequences in strings."""

        # Process escape sequences in order (most specific first)
        # Use a placeholder approach to avoid conflicts

        # First, protect double backslashes
        result = text.replace("\\\\", "\x00DOUBLE_BACKSLASH\x00")

        # Then process other escape sequences
        result = result.replace("\\$", "\x00ESCAPED_DOLLAR\x00")
        result = result.replace("\\{", "\x00ESCAPED_LBRACE\x00")
        result = result.replace("\\}", "\x00ESCAPED_RBRACE\x00")
        result = result.replace("\\n", "\n")
        result = result.replace("\\t", "\t")
        result = result.replace("\\r", "\r")
        result = result.replace('\\"', '"')

        # Finally, restore the placeholders
        result = result.replace("\x00DOUBLE_BACKSLASH\x00", "\\")
        result = result.replace("\x00ESCAPED_DOLLAR\x00", "$")
        result = result.replace("\x00ESCAPED_LBRACE\x00", "{")
        result = result.replace("\x00ESCAPED_RBRACE\x00", "}")

        return result

    def _compile_interpolated_string(
        self, template: str, tree: Tree
    ) -> InterpolationNode:
        """Compile a string with interpolation into an InterpolationNode."""
        # Use UnifiedInterpolationParser if lark_parser is available
        if self.lark_parser:
            parser = UnifiedInterpolationParser(self.lark_parser, self)
            (
                variable_nodes,
                printer_hints,
            ) = parser.parse_interpolation_expression(template)
        else:
            # Use the regular InterpolationExpressionParser
            (
                variable_nodes,
                printer_hints,
            ) = self.interpolation_parser.parse_interpolation_expression(template)

        # Get line/column info
        line, col = self._get_line_column(tree)

        # Update all nodes with proper line/column information from the tree
        updated_variables = []
        for node in variable_nodes:
            if hasattr(node, "line") and hasattr(node, "column"):
                # Update the node's location info
                node.line = line
                node.column = col
            updated_variables.append(node)

        # Create interpolation node with template, variables, and printer hints
        return InterpolationNode(
            template,
            updated_variables,
            printer_hints,
            line,
            col,
            self._generate_node_id(),
        )

    def _compile_variable_token(self, token: Token) -> VariableNode:
        """Compile a variable token to VariableNode."""
        variable_name = token.value
        if variable_name.startswith("$"):
            variable_name = variable_name[1:]  # Remove $ prefix

        # Get line/column info
        line, col = self._get_line_column(token)

        return VariableNode(variable_name, line, col, self._generate_node_id())

    def _compile_identifier_token(self, token: Token) -> VariableNode:
        """Compile an identifier token to VariableNode (for optional $ syntax)."""
        from .variable_normalizer import VariableNormalizer

        # Normalize the identifier name (handles both "name" and "$name" forms)
        variable_name = VariableNormalizer.normalize_name(token.value)

        # Get line/column info
        line, col = self._get_line_column(token)

        return VariableNode(variable_name, line, col, self._generate_node_id())

    def _compile_multiline_string(self, tree: Tree) -> ExecutionNode:
        """Compile multiline string literal, detecting interpolation patterns."""
        # AST structure: multiline_string -> TRIPLE_QUOTED_STRING
        if len(tree.children) != 1:
            raise CompilerError("Invalid multiline string literal", 1, 1)

        string_token = tree.children[0]
        if isinstance(string_token, Token):
            # Remove triple quotes from the string value
            value = string_token.value
            if value.startswith('"""') and value.endswith('"""'):
                value = value[3:-3]  # Remove surrounding triple quotes

            # Check if string contains unescaped interpolation patterns
            if self._has_unescaped_interpolation(value):
                # For triple-quoted strings, use enhanced interpolation that supports double quotes
                return self._compile_interpolated_multiline_string(value, tree)
            # No interpolation, process escapes and return literal
            processed_value = self._process_escape_sequences(value)
            line, col = self._get_line_column(tree)
            return LiteralNode(processed_value, line, col, self._generate_node_id())
        raise CompilerError("Expected multiline string token", 1, 1)

    def _compile_value(self, tree: Tree) -> LiteralNode:
        """Compile value literals (numbers, booleans, null)."""
        if len(tree.children) != 1:
            raise CompilerError("Invalid value literal", 1, 1)

        value_token = tree.children[0]
        if isinstance(value_token, Token):
            # Convert token value to appropriate Python type
            if value_token.type == "NUMBER":
                value = (
                    float(value_token.value)
                    if "." in value_token.value
                    else int(value_token.value)
                )
            elif value_token.value == "true":
                value = True
            elif value_token.value == "false":
                value = False
            elif value_token.value == "null":
                value = None
            else:
                value = value_token.value

            # Get line/column info
            line, col = self._get_line_column(tree)

            return LiteralNode(value, line, col, self._generate_node_id())
        raise CompilerError("Expected value token", 1, 1)

    def _compile_list(self, tree: Tree) -> ListNode:
        """Compile list literal."""
        # AST structure: list -> "[" list_items? "]"
        # list_items -> expression ("," expression)*

        elements = []

        # Find list_items child if it exists
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "list_items":
                # Compile each expression in the list
                for item_child in child.children:
                    if isinstance(item_child, Tree):
                        element_node = self._compile_tree_node(item_child)
                        if element_node:
                            elements.append(element_node)

        # Get line/column info
        line, col = self._get_line_column(tree)

        return ListNode(elements, line, col, self._generate_node_id())

    def _compile_list_comprehension(self, tree: Tree) -> ListComprehensionNode:
        """Compile list comprehension expression.

        Grammar: "[" expression FOR "(" IDENTIFIER "in" expression ")" "]"
               | "[" expression FOR "(" IDENTIFIER "in" expression ")" IF "(" expression ")" "]"
        """
        from cy_language.execution_plan import ListComprehensionNode

        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        element_expr = None
        iterator_var = None
        iterable_expr = None
        filter_expr = None

        # Parse children: first expression is element, IDENTIFIER is iterator,
        # second expression is iterable, optional third expression is filter
        expressions_found = 0
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "IDENTIFIER" and iterator_var is None:
                    iterator_var = child.value
            elif isinstance(child, Tree) and child.data == "expression":
                if expressions_found == 0:
                    element_expr = self._compile_tree_node(child)
                    expressions_found += 1
                elif expressions_found == 1:
                    iterable_expr = self._compile_tree_node(child)
                    expressions_found += 1
                elif expressions_found == 2:
                    filter_expr = self._compile_tree_node(child)
                    expressions_found += 1

        if not element_expr:
            raise CompilerError(
                "List comprehension missing element expression", line, column
            )
        if not iterator_var:
            raise CompilerError(
                "List comprehension missing iterator variable", line, column
            )
        if not iterable_expr:
            raise CompilerError(
                "List comprehension missing iterable expression", line, column
            )

        return ListComprehensionNode(
            element_expr,
            iterator_var,
            iterable_expr,
            filter_expr,
            line,
            column,
            node_id,
        )

    def _compile_dictionary(self, tree: Tree) -> DictNode:
        """Compile dictionary literal."""
        # AST structure: dictionary -> "{" dict_items? "}"
        # dict_items -> dict_item ("," dict_item)*
        # dict_item -> string ":" expression

        pairs = []

        # Find dict_items child if it exists
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "dict_items":
                # Compile each dict_item
                for item_child in child.children:
                    if (
                        isinstance(item_child, Tree)
                        and item_child.data == "dict_item"
                        and len(item_child.children) >= 2
                    ):
                        key_node = self._compile_tree_node(item_child.children[0])
                        value_node = self._compile_tree_node(item_child.children[1])
                        if key_node and value_node:
                            pairs.append((key_node, value_node))

        # Get line/column info
        line, col = self._get_line_column(tree)

        return DictNode(pairs, line, col, self._generate_node_id())

    def _compile_field_access(self, tree: Tree) -> FieldAccessNode:
        """Compile field access expressions like obj.field or func().field."""
        # AST structure: field_access -> (VARIABLE | function_call) "." field_path
        # field_path -> IDENTIFIER ("." IDENTIFIER)*

        if len(tree.children) != 2:
            raise CompilerError("Invalid field access structure", 1, 1)

        # First child: the object (variable or function call)
        object_tree = tree.children[0]
        object_node = self._compile_tree_node(object_tree)

        if object_node is None:
            raise CompilerError("Failed to compile object in field access", 1, 1)

        # Second child: the field path
        field_path_tree = tree.children[1]
        if (
            not isinstance(field_path_tree, Tree)
            or field_path_tree.data != "field_path"
        ):
            raise CompilerError("Expected field_path in field access", 1, 1)

        # Extract field names from the field path
        field_names = []
        for child in field_path_tree.children:
            if isinstance(child, Token) and child.type == "IDENTIFIER":
                field_names.append(child.value)

        if not field_names:
            raise CompilerError("No field names found in field path", 1, 1)

        # Build nested field access nodes for chained access like obj.a.b.c
        current_field_node: FieldAccessNode | None = None
        line, col = self._get_line_column(tree)

        current_base: ExecutionNode = object_node
        for field_name in field_names:
            current_field_node = FieldAccessNode(
                current_base, field_name, line, col, self._generate_node_id()
            )
            current_base = current_field_node

        assert current_field_node is not None  # field_names is non-empty
        return current_field_node

    def _compile_indexed_access(self, tree: Tree) -> IndexedAccessNode:
        """Compile indexed access expressions like obj['key'] or list[0]."""
        # AST structure: indexed_access -> object_node "[" index_expression "]"
        # Grammar: indexed_access: (VARIABLE | function_call | field_access) "[...]"

        if len(tree.children) != 2:
            raise CompilerError("Invalid indexed access structure", 1, 1)

        # First child: the object to be indexed
        object_tree = tree.children[0]
        object_node = self._compile_tree_node(object_tree)

        if object_node is None:
            raise CompilerError("Failed to compile object in indexed access", 1, 1)

        # Second child: the index expression
        index_tree = tree.children[1]
        index_node = self._compile_tree_node(index_tree)

        if index_node is None:
            raise CompilerError("Failed to compile index in indexed access", 1, 1)

        # Get line/column info
        line, col = self._get_line_column(tree)

        return IndexedAccessNode(
            object_node, index_node, line, col, self._generate_node_id()
        )

    def _compile_simple_expression(self, tree: Tree) -> ExecutionNode | None:
        """Compile simple_expression node (excludes concatenation)."""
        # Simple expression nodes wrap other nodes, so compile their children
        for child in tree.children:
            node = self._compile_tree_node(child)
            if node:
                return node
        return None

    def _compile_tree_node(self, tree_or_token: Any) -> ExecutionNode | None:
        """Compile a single AST node to execution plan node."""
        # Handle None nodes (empty statements)
        if tree_or_token is None:
            return None

        # Handle Token objects (terminals)
        if isinstance(tree_or_token, Token):
            if tree_or_token.type == "VARIABLE":
                return self._compile_variable_token(tree_or_token)
            if tree_or_token.type == "IDENTIFIER":
                return self._compile_identifier_token(tree_or_token)
            return None  # Other tokens are handled by their parent trees

        # Handle Tree objects (non-terminals)
        if not isinstance(tree_or_token, Tree):
            return None

        tree = tree_or_token

        # Route based on tree data (rule name)
        if tree.data == "statement":
            # Statements contain other nodes, compile their children
            for child in tree.children:
                node = self._compile_tree_node(child)
                if node:
                    return node
            return None

        if tree.data == "assignment":
            return self._compile_assignment(tree)

        if tree.data == "expression":
            return self._compile_expression(tree)

        if tree.data == "string":
            return self._compile_string_literal(tree)

        if tree.data == "single_quoted_string":
            return self._compile_single_quoted_string(tree)

        if tree.data == "function_call":
            return self._compile_tool_call(tree)

        if tree.data == "function_call_statement":
            # Standalone function call statement
            # Compile the function call and return it as a statement
            if tree.children:
                return self._compile_tree_node(tree.children[0])
            return None

        if tree.data == "multiline_string":
            return self._compile_multiline_string(tree)

        if tree.data == "value":
            return self._compile_value(tree)

        if tree.data == "true":
            line, col = self._get_line_column(tree)
            return LiteralNode(True, line, col, self._generate_node_id())

        if tree.data == "false":
            line, col = self._get_line_column(tree)
            return LiteralNode(False, line, col, self._generate_node_id())

        if tree.data == "null":
            line, col = self._get_line_column(tree)
            return LiteralNode(None, line, col, self._generate_node_id())

        if tree.data == "list":
            return self._compile_list(tree)

        if tree.data == "list_comprehension":
            return self._compile_list_comprehension(tree)

        if tree.data == "dictionary":
            return self._compile_dictionary(tree)

        if tree.data == "field_access":
            return self._compile_field_access(tree)

        if tree.data == "indexed_access":
            return self._compile_indexed_access(tree)

        if tree.data == "simple_expression":
            return self._compile_simple_expression(tree)

        # Mathematical and Boolean Operations
        # Null coalescing operator
        if tree.data == "null_coalesce":
            return self._compile_null_coalesce(tree)

        if tree.data == "boolean_or":
            return self._compile_boolean_or(tree)

        if tree.data == "boolean_and":
            return self._compile_boolean_and(tree)

        if tree.data == "boolean_not":
            return self._compile_boolean_not(tree)

        if tree.data == "comparison":
            return self._compile_comparison(tree)

        if tree.data == "arithmetic":
            return self._compile_arithmetic(tree)

        if tree.data == "term":
            return self._compile_term(tree)

        if tree.data == "multiplicative":
            return self._compile_multiplicative(tree)

        if tree.data == "factor":
            return self._compile_factor(tree)

        if tree.data == "atom":
            return self._compile_atom(tree)

        if tree.data == "primary":
            return self._compile_primary(tree)

        # Control flow statements
        if tree.data == "conditional_statement":
            return self._compile_conditional(tree)

        if tree.data == "conditional_expr":
            return self._compile_conditional_expr(tree)

        if tree.data == "while_loop_statement":
            return self._compile_while_loop(tree)

        if tree.data == "for_in_statement":
            return self._compile_for_in(tree)  # type: ignore[return-value]

        if tree.data == "try_catch_statement":
            return self._compile_try_catch(tree)

        if tree.data == "return_statement":
            return self._compile_return(tree)

        if tree.data == "break_statement":
            return self._compile_break(tree)

        if tree.data == "continue_statement":
            return self._compile_continue(tree)

        # Unknown node type - for now, return None
        # In production, we might want to log or raise an error
        return None

    # Mathematical and Boolean Operation Compilation Methods

    def _compile_null_coalesce(self, tree: Tree) -> ExecutionNode:
        """Compile null coalescing operation: boolean_or ("??" boolean_or)*

        The ?? operator returns the right operand when left is null,
        otherwise returns the left operand (even if falsy like 0, [], {}).
        """
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Multiple operands - create null coalesce operation node
        operands = []
        for child in tree.children:
            if isinstance(child, Tree):  # Skip "??" tokens
                operand = self._compile_tree_node(child)
                if operand:
                    operands.append(operand)

        if len(operands) == 1:
            return operands[0]

        line, col = self._get_line_column(tree)
        return BooleanOpNode("??", operands, line, col, self._generate_node_id())

    def _compile_boolean_or(self, tree: Tree) -> ExecutionNode:
        """Compile boolean OR operation: boolean_and ("or" boolean_and)*"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Multiple operands - create boolean operation node
        operands = []
        for child in tree.children:
            if isinstance(child, Tree):  # Skip "or" tokens
                operand = self._compile_tree_node(child)
                if operand:
                    operands.append(operand)

        if len(operands) == 1:
            return operands[0]

        line, col = self._get_line_column(tree)
        return BooleanOpNode("or", operands, line, col, self._generate_node_id())

    def _compile_boolean_and(self, tree: Tree) -> ExecutionNode:
        """Compile boolean AND operation: boolean_not ("and" boolean_not)*"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Multiple operands - create boolean operation node
        operands = []
        for child in tree.children:
            if isinstance(child, Tree):  # Skip "and" tokens
                operand = self._compile_tree_node(child)
                if operand:
                    operands.append(operand)

        if len(operands) == 1:
            return operands[0]

        line, col = self._get_line_column(tree)
        return BooleanOpNode("and", operands, line, col, self._generate_node_id())

    def _compile_boolean_not(self, tree: Tree) -> ExecutionNode:
        """Compile boolean NOT operation: "not" comparison | comparison"""
        if len(tree.children) == 1:
            # No "not" - just return the comparison
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result
        if len(tree.children) == 2:
            # "not" + comparison
            operand = self._compile_tree_node(tree.children[1])
            if operand:
                line, col = self._get_line_column(tree)
                return UnaryOpNode("not", operand, line, col, self._generate_node_id())

        raise CompilerError("Invalid boolean not expression", 1, 1)

    def _compile_comparison(self, tree: Tree) -> ExecutionNode:
        """Compile comparison operation: arithmetic (("==" | "!=" | ...) arithmetic)*"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Handle comparison operators
        left = self._compile_tree_node(tree.children[0])
        if not left:
            raise CompilerError("Invalid left operand in comparison", 1, 1)

        i = 1
        while i < len(tree.children) - 1:
            operator_token = tree.children[i]
            right_node = tree.children[i + 1]

            operator = (
                str(operator_token)
                if hasattr(operator_token, "__str__")
                else str(operator_token.value)  # type: ignore[union-attr]
            )
            right = self._compile_tree_node(right_node)

            if not right:
                raise CompilerError("Invalid right operand in comparison", 1, 1)

            line, col = self._get_line_column(tree)
            left = ComparisonNode(
                operator, left, right, line, col, self._generate_node_id()
            )
            i += 2

        return left

    def _compile_arithmetic(self, tree: Tree) -> ExecutionNode:
        """Compile arithmetic operation: just delegate to concatenation"""
        result = self._compile_tree_node(tree.children[0])
        assert result is not None
        return result

    def _compile_term(self, tree: Tree) -> ExecutionNode:
        """Compile term operation: multiplicative (("+" | "-") multiplicative)*"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Handle addition and subtraction (left-associative)
        left = self._compile_tree_node(tree.children[0])
        if not left:
            raise CompilerError("Invalid left operand in term", 1, 1)

        i = 1
        while i < len(tree.children) - 1:
            operator_token = tree.children[i]
            right_node = tree.children[i + 1]

            operator = (
                str(operator_token)
                if hasattr(operator_token, "__str__")
                else str(operator_token.value)  # type: ignore[union-attr]
            )
            right = self._compile_tree_node(right_node)

            if not right:
                raise CompilerError("Invalid right operand in term", 1, 1)

            line, col = self._get_line_column(tree)
            left = ArithmeticNode(
                operator, left, right, line, col, self._generate_node_id()
            )
            i += 2

        return left

    def _compile_multiplicative(self, tree: Tree) -> ExecutionNode:
        """Compile multiplicative operation: factor (("*" | "/") factor)*"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        # Handle multiplication and division (left-associative)
        left = self._compile_tree_node(tree.children[0])
        if not left:
            raise CompilerError("Invalid left operand in multiplicative", 1, 1)

        i = 1
        while i < len(tree.children) - 1:
            operator_token = tree.children[i]
            right_node = tree.children[i + 1]

            operator = (
                str(operator_token)
                if hasattr(operator_token, "__str__")
                else str(operator_token.value)  # type: ignore[union-attr]
            )
            right = self._compile_tree_node(right_node)

            if not right:
                raise CompilerError("Invalid right operand in multiplicative", 1, 1)

            line, col = self._get_line_column(tree)
            left = ArithmeticNode(
                operator, left, right, line, col, self._generate_node_id()
            )
            i += 2

        return left

    def _compile_factor(self, tree: Tree) -> ExecutionNode:
        """Compile factor operation: ("+" | "-") factor | atom"""
        if len(tree.children) == 1:
            # No unary operator - just return the atom
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result
        if len(tree.children) == 2:
            # Unary operator + factor/atom
            operator_token = tree.children[0]
            operand_node = tree.children[1]

            operator = (
                str(operator_token)
                if hasattr(operator_token, "__str__")
                else str(operator_token.value)  # type: ignore[union-attr]
            )
            operand = self._compile_tree_node(operand_node)

            if not operand:
                raise CompilerError("Invalid operand in unary operation", 1, 1)

            line, col = self._get_line_column(tree)
            return UnaryOpNode(operator, operand, line, col, self._generate_node_id())

        raise CompilerError("Invalid factor expression", 1, 1)

    def _compile_atom(self, tree: Tree) -> ExecutionNode:
        """Compile atom: concatenation | primary"""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result

        raise CompilerError("Invalid atom expression", 1, 1)

    def _compile_primary(self, tree: Tree) -> ExecutionNode:
        """Compile primary expressions including parenthesized expressions."""
        if len(tree.children) == 1:
            result = self._compile_tree_node(tree.children[0])
            assert result is not None
            return result
        if len(tree.children) == 3:
            # Parenthesized expression: "(" expression ")"
            result = self._compile_tree_node(tree.children[1])
            assert result is not None
            return result

        raise CompilerError("Invalid primary expression", 1, 1)

    def _validate_namespace(self, tool_name: str) -> None:
        """Validate namespace format for all supported prefixes.

        Supported formats:
        - 2-part (native function domains): json::parse, llm::run, str::lowercase
        - 3-part (integrations): app::integration::tool, mcp::server::tool,
          arc::archetype::tool, native::tools::function

        Args:
            tool_name: The tool name to validate

        Raises:
            CompilerError: If the namespace format is invalid
        """
        # Only validate if it looks like a namespace (contains ::)
        if "::" not in tool_name:
            return  # Native tool without prefix, no validation needed

        parts = tool_name.split("::")

        # Valid 2-part prefixes (native function domains)
        VALID_2PART_PREFIXES = {
            "json",
            "str",
            "list",
            "dict",
            "math",
            "time",
            "regex",
            "url",
            "ip",
            "llm",
            "type",
        }

        # Valid 3-part prefixes (integrations)
        VALID_3PART_PREFIXES = {"app", "mcp", "arc", "native"}

        prefix = parts[0]

        if len(parts) == 2:
            # 2-part namespace: prefix::function
            func_name = parts[1]

            if not func_name:
                raise CompilerError(
                    f"Invalid namespace '{tool_name}'. "
                    f"Function name must be non-empty.",
                    1,
                    1,
                )

            if prefix in VALID_3PART_PREFIXES:
                raise CompilerError(
                    f"Invalid namespace format '{tool_name}'. "
                    f"'{prefix}::' requires 3 parts: {prefix}::namespace::function",
                    1,
                    1,
                )

            if prefix not in VALID_2PART_PREFIXES:
                raise CompilerError(
                    f"Invalid 2-part namespace prefix '{prefix}' in '{tool_name}'. "
                    f"Valid 2-part prefixes: {', '.join(sorted(VALID_2PART_PREFIXES))}",
                    1,
                    1,
                )

        elif len(parts) == 3:
            # 3-part namespace: prefix::middle::name
            middle, name = parts[1], parts[2]

            if prefix not in VALID_3PART_PREFIXES:
                raise CompilerError(
                    f"Invalid namespace prefix '{prefix}' in '{tool_name}'. "
                    f"Supported 3-part prefixes: {', '.join(sorted(VALID_3PART_PREFIXES))}",
                    1,
                    1,
                )

            # Special validation for native:: - middle part must be "tools"
            if prefix == "native" and middle != "tools":
                raise CompilerError(
                    f"Invalid native namespace '{tool_name}'. "
                    f"Native functions must use format: native::tools::function_name",
                    1,
                    1,
                )

            # Check that middle and name are non-empty
            if not middle or not name:
                raise CompilerError(
                    f"Invalid namespace '{tool_name}'. "
                    f"Both namespace and function name must be non-empty.",
                    1,
                    1,
                )

        else:
            # Too many parts
            raise CompilerError(
                f"Invalid namespace format '{tool_name}'. "
                f"Expected 2 parts (prefix::function) or 3 parts (prefix::namespace::function)",
                1,
                1,
            )

    def _get_line_column(self, tree_or_token: Any) -> tuple[int, int]:
        """Extract line and column information from AST node."""
        # Try to extract line/column from Lark Tree/Token
        if hasattr(tree_or_token, "meta") and tree_or_token.meta:
            # Tree nodes have meta information
            meta = tree_or_token.meta
            line = getattr(meta, "line", 1)
            column = getattr(meta, "column", 1)
            return (line, column)
        if hasattr(tree_or_token, "line") and hasattr(tree_or_token, "column"):
            # Token nodes have line/column directly
            line = getattr(tree_or_token, "line", 1)
            column = getattr(tree_or_token, "column", 1)
            # Handle None values by using defaults
            line = line if line is not None else 1
            column = column if column is not None else 1
            return (line, column)
        if hasattr(tree_or_token, "children") and tree_or_token.children:
            # If this node doesn't have location info, try the first child
            for child in tree_or_token.children:
                if child is not None:
                    return self._get_line_column(child)
        # Fallback to default
        return (1, 1)

    def _compile_try_catch(self, tree: Tree) -> ExecutionNode:
        """Compile try/catch/finally statement."""
        from cy_language.execution_plan import CatchClause, TryCatchNode

        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse the AST structure:
        # try_catch_statement -> TRY "{" statement* "}" catch_clause+ [finally_clause]

        try_body = []
        catch_clauses = []
        finally_body = None

        # Process children of the try_catch_statement
        i = 0
        while i < len(tree.children):
            child = tree.children[i]

            if isinstance(child, Token) and child.type == "TRY":
                # Skip the TRY token
                i += 1
                continue

            if isinstance(child, Tree):
                if child.data == "statement":
                    # This is a statement in the try block
                    stmt_node = self._compile_tree_node(child)
                    if stmt_node:
                        try_body.append(stmt_node)

                elif child.data == "catch_clause":
                    # Process catch clause: CATCH "(" IDENTIFIER ")" "{" statement* "}"
                    exception_var = None
                    catch_body = []

                    for catch_child in child.children:
                        if (
                            isinstance(catch_child, Token)
                            and catch_child.type == "IDENTIFIER"
                        ):
                            # This is the exception variable name
                            exception_var = str(catch_child.value)
                        elif (
                            isinstance(catch_child, Tree)
                            and catch_child.data == "statement"
                        ):
                            # This is a statement in the catch block
                            stmt_node = self._compile_tree_node(catch_child)
                            if stmt_node:
                                catch_body.append(stmt_node)

                    if exception_var:
                        catch_clauses.append(CatchClause(exception_var, catch_body))

                elif child.data == "finally_clause":
                    # Process finally clause: FINALLY "{" statement* "}"
                    # break/continue inside finally would suppress in-flight
                    # control flow signals — forbid it at compile time.
                    finally_body = []
                    prev_in_finally = self._in_finally
                    self._in_finally = True

                    for finally_child in child.children:
                        if (
                            isinstance(finally_child, Tree)
                            and finally_child.data == "statement"
                        ):
                            stmt_node = self._compile_tree_node(finally_child)
                            if stmt_node:
                                finally_body.append(stmt_node)

                    self._in_finally = prev_in_finally
            i += 1

        # Ensure we have at least one catch clause (grammar should enforce this)
        if not catch_clauses:
            # This shouldn't happen with proper grammar, but add a default for safety
            catch_clauses.append(CatchClause("e", []))

        return TryCatchNode(
            try_body=try_body,
            catch_clauses=catch_clauses,
            finally_body=finally_body,
            line_number=line,
            column=column,
            node_id=node_id,
        )

    def _compile_conditional_expr(self, tree: Tree) -> ConditionalNode:
        """Compile conditional expression (ternary-like if/elif/else expression)."""
        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse: conditional_expr -> if (expr) { expr } [elif (expr) { expr }]* else { expr }
        condition_node: ExecutionNode | None = None
        if_body: list[ExecutionNode] = []
        elif_conditions: list[ExecutionNode] = []
        elif_bodies: list[list[ExecutionNode]] = []
        else_body: list[ExecutionNode] | None = None

        i = 0
        while i < len(tree.children):
            child = tree.children[i]
            if isinstance(child, Tree) and child.data == "expression":
                # First expression is the condition
                condition_node = self._compile_tree_node(child)
                i += 1
                # Next expression is the if body
                if (
                    i < len(tree.children)
                    and isinstance(tree.children[i], Tree)
                    and tree.children[i].data == "expression"
                ):
                    expr_node = self._compile_tree_node(tree.children[i])
                    if expr_node:
                        if_body.append(expr_node)
                    i += 1
                break
            i += 1

        # Process elif and else clauses
        while i < len(tree.children):
            child = tree.children[i]
            if isinstance(child, Tree):
                if child.data == "elif_expr_clause":
                    # elif (condition) { expression }
                    elif_cond: ExecutionNode | None = None
                    elif_expr: ExecutionNode | None = None
                    for elif_child in child.children:
                        if (
                            isinstance(elif_child, Tree)
                            and elif_child.data == "expression"
                        ):
                            if elif_cond is None:
                                elif_cond = self._compile_tree_node(elif_child)
                            else:
                                elif_expr = self._compile_tree_node(elif_child)
                    if elif_cond and elif_expr:
                        elif_conditions.append(elif_cond)
                        elif_bodies.append([elif_expr])
                elif child.data == "expression":
                    # This is the else expression (last one)
                    else_expr = self._compile_tree_node(child)
                    if else_expr:
                        else_body = [else_expr]
            i += 1

        if condition_node is None:
            condition_node = LiteralNode(True, line, column, f"{node_id}_cond")

        return ConditionalNode(
            condition_node,
            if_body,
            elif_conditions,
            elif_bodies,
            else_body,
            line,
            column,
            node_id,
        )

    def _compile_conditional(self, tree: Tree) -> ConditionalNode:
        """Compile if/elif/else conditional statement."""
        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse the AST structure:
        # conditional_statement -> if expression statement* [elif_clause* else_clause]

        # Extract the condition (should be the expression after 'if')
        condition_node = None
        if_body = []
        elif_conditions = []
        elif_bodies = []
        else_body = None

        # Find the condition expression and body statements
        i = 0
        while i < len(tree.children):
            child = tree.children[i]
            if isinstance(child, Tree) and child.data == "expression":
                # This is the condition
                condition_node = self._compile_tree_node(child)
                i += 1
                break
            i += 1

        # Collect the if body statements and process elif/else clauses
        while i < len(tree.children):
            child = tree.children[i]
            if child is None:
                i += 1
                continue
            if isinstance(child, Tree):
                if child.data == "statement":
                    stmt_node = self._compile_tree_node(child)
                    if stmt_node:
                        if_body.append(stmt_node)
                elif child.data == "elif_clause":
                    # Process elif clause: elif expression statement*
                    elif_condition = None
                    elif_body = []
                    for elif_child in child.children:
                        if isinstance(elif_child, Tree):
                            if elif_child.data == "expression":
                                elif_condition = self._compile_tree_node(elif_child)
                            elif elif_child.data == "statement":
                                stmt_node = self._compile_tree_node(elif_child)
                                if stmt_node:
                                    elif_body.append(stmt_node)
                    if elif_condition:
                        elif_conditions.append(elif_condition)
                        elif_bodies.append(elif_body)
                elif child.data == "else_clause":
                    # Process else clause: else statement*
                    else_body = []
                    for else_child in child.children:
                        if (
                            isinstance(else_child, Tree)
                            and else_child.data == "statement"
                        ):
                            stmt_node = self._compile_tree_node(else_child)
                            if stmt_node:
                                else_body.append(stmt_node)
                    break  # else clause is the last one
            i += 1

        if condition_node is None:
            condition_node = LiteralNode(True, line, column, f"{node_id}_cond")

        return ConditionalNode(
            condition_node,
            if_body,
            elif_conditions,
            elif_bodies,
            else_body,
            line,
            column,
            node_id,
        )

    def _compile_while_loop(self, tree: Tree) -> WhileLoopNode:
        """Compile while loop statement."""
        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse the AST structure:
        # while_loop_statement -> while expression statement*

        # Extract the condition (should be the expression after 'while')
        condition_node: ExecutionNode | None = None
        body: list[ExecutionNode] = []

        # Find the condition expression and body statements
        i = 0
        while i < len(tree.children):
            child = tree.children[i]
            if isinstance(child, Tree) and child.data == "expression":
                # This is the loop condition
                condition_node = self._compile_tree_node(child)
                i += 1
                break
            i += 1

        # Collect the loop body statements within a loop scope
        with self._loop_scope():
            while i < len(tree.children):
                child = tree.children[i]
                if child is None:
                    i += 1
                    continue
                if isinstance(child, Tree) and child.data == "statement":
                    stmt_node = self._compile_tree_node(child)
                    if stmt_node:
                        if isinstance(stmt_node, list):
                            body.extend(stmt_node)
                        else:
                            body.append(stmt_node)
                i += 1

        if condition_node is None:
            condition_node = LiteralNode(False, line, column, f"{node_id}_cond")

        return WhileLoopNode(condition_node, body, line, column, node_id)

    def _compile_for_in(self, tree: Tree) -> list[ExecutionNode]:
        """Compile for-in loop statement by transforming to while loop.

        Transform: for (item in items) { body }
        Into:
            __idx = 0
            while (__idx < len(items)) {
                item = items[__idx]
                __idx = __idx + 1   # before body so `continue` still advances
                body
            }
        """
        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse the AST structure: for_in_statement -> FOR "(" IDENTIFIER "in" expression ")" "{" statement* "}"
        iterator_var: str | None = None
        iterable_expr: ExecutionNode | None = None
        body_statements: list[ExecutionNode] = []

        # Extract components from the parse tree within a loop scope
        with self._loop_scope():
            i = 0
            while i < len(tree.children):
                child = tree.children[i]

                if isinstance(child, Token):
                    if child.type == "IDENTIFIER" and iterator_var is None:
                        iterator_var = child.value
                    elif child.value == "in":
                        i += 1
                        if i < len(tree.children):
                            next_child = tree.children[i]
                            if (
                                isinstance(next_child, Tree)
                                and next_child.data == "expression"
                            ):
                                iterable_expr = self._compile_tree_node(next_child)
                elif isinstance(child, Tree):
                    if child.data == "expression" and iterable_expr is None:
                        iterable_expr = self._compile_tree_node(child)
                    elif child.data == "statement":
                        stmt_node = self._compile_tree_node(child)
                        if stmt_node:
                            if isinstance(stmt_node, list):
                                body_statements.extend(stmt_node)
                            else:
                                body_statements.append(stmt_node)
                i += 1

        if not iterator_var:
            from .errors import SyntaxError as CySyntaxError

            raise CySyntaxError("For-in loop missing iterator variable", line, column)
        if not iterable_expr:
            from .errors import SyntaxError as CySyntaxError

            raise CySyntaxError("For-in loop missing iterable expression", line, column)

        # Generate unique variables to avoid conflicts
        idx_var = f"__for_idx_{node_id}"
        iterable_var = f"__for_iterable_{node_id}"

        # Create nodes for the transformation
        from cy_language.execution_plan import (
            ArithmeticNode,
            AssignNode,
            ComparisonNode,
            IndexedAccessNode,
            LiteralNode,
            ToolCallNode,
            VariableNode,
            WhileLoopNode,
        )

        # Create the equivalent while loop nodes
        nodes: list[ExecutionNode] = []

        # 0. Convert collection to iterable: __iterable = __to_iterable(collection)
        # This converts dicts to list of keys, strings to list of chars, arrays stay as-is
        to_iterable_call = ToolCallNode(
            "__to_iterable",
            [iterable_expr],
            {},
            line,
            column,
            f"{node_id}_to_iterable",
        )
        iterable_init = AssignNode(
            iterable_var,
            to_iterable_call,
            line,
            column,
            f"{node_id}_iterable_init",
        )
        nodes.append(iterable_init)

        # 1. Initialize index: __idx = 0
        idx_init = AssignNode(
            idx_var,
            LiteralNode(0, line, column, f"{node_id}_init"),
            line,
            column,
            f"{node_id}_idx_init",
        )
        nodes.append(idx_init)

        # 2. Create while condition: __idx < len(__iterable)
        iterable_var_node = VariableNode(
            iterable_var, line, column, f"{node_id}_iterable_var"
        )
        len_call = ToolCallNode(
            "len", [iterable_var_node], {}, line, column, f"{node_id}_len"
        )
        idx_var_node = VariableNode(idx_var, line, column, f"{node_id}_idx_var")
        condition = ComparisonNode(
            "<", idx_var_node, len_call, line, column, f"{node_id}_cond"
        )

        # 3. Create loop body
        loop_body: list[ExecutionNode] = []

        # 3a. Assign iterator: item = __iterable[__idx]
        indexed_access = IndexedAccessNode(
            VariableNode(iterable_var, line, column, f"{node_id}_iterable_access"),
            VariableNode(idx_var, line, column, f"{node_id}_idx_access"),
            line,
            column,
            f"{node_id}_indexed",
        )
        iterator_assign = AssignNode(
            iterator_var, indexed_access, line, column, f"{node_id}_iter_assign"
        )
        loop_body.append(iterator_assign)

        # 3b. Increment index BEFORE user body: __idx = __idx + 1
        # This ordering is critical: `continue` skips the remaining user
        # body but the index must still advance to avoid an infinite loop.
        idx_increment = AssignNode(
            idx_var,
            ArithmeticNode(
                "+",
                VariableNode(idx_var, line, column, f"{node_id}_idx_inc_var"),
                LiteralNode(1, line, column, f"{node_id}_one"),
                line,
                column,
                f"{node_id}_inc",
            ),
            line,
            column,
            f"{node_id}_idx_inc_assign",
        )
        loop_body.append(idx_increment)

        # 3c. Add original body statements
        loop_body.extend(body_statements)

        # 4. Create the while loop
        while_loop = WhileLoopNode(
            condition, loop_body, line, column, f"{node_id}_while"
        )
        nodes.append(while_loop)

        # Return as a list of nodes to be inserted into the program
        return nodes

    def _compile_return(self, tree: Tree) -> ReturnNode:
        """Compile return statement."""
        line, column = self._get_line_column(tree)
        node_id = self._generate_node_id()

        # Parse the AST structure:
        # return_statement -> return expression

        # Extract the expression to return
        expression_node = None

        # Find the expression to return
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "expression":
                expression_node = self._compile_tree_node(child)
                break

        if expression_node is None:
            # Default to empty string if no expression found
            expression_node = LiteralNode("", line, column, f"{node_id}_expr")

        return ReturnNode(expression_node, line, column, node_id)

    def _compile_loop_control(
        self, tree: Tree, keyword: str, node_cls: type[ExecutionNode]
    ) -> ExecutionNode:
        """Compile break/continue (only valid inside a loop, not in finally)."""
        line, column = self._get_line_column(tree)
        if self._loop_depth <= 0:
            raise CompilerError(
                f"'{keyword}' can only be used inside a loop", line, column
            )
        if self._in_finally:
            raise CompilerError(
                f"'{keyword}' cannot be used inside a finally block", line, column
            )
        return node_cls(line, column, self._generate_node_id())

    def _compile_break(self, tree: Tree) -> ExecutionNode:
        return self._compile_loop_control(tree, "break", BreakNode)

    def _compile_continue(self, tree: Tree) -> ExecutionNode:
        return self._compile_loop_control(tree, "continue", ContinueNode)


def compile_cy_program(
    ast_tree: Tree,
    source_file: str | None = None,
    available_tools: dict[str, Any] | None = None,
    lark_parser: Any = None,  # Optional parser for enhanced interpolation
    tool_resolver: Optional["ToolResolver"] = None,  # Namespace resolution
    mcp_manager: Any | None = None,  # MCP manager for tool registration
    app_manager: Any | None = None,  # App manager for tool registration
    arc_router: Any | None = None,  # Archetype router for tool registration
    validate_output: bool = True,  # Whether to validate output coverage
    check_types: bool = False,  # Whether to perform type checking
    input_schema: dict[str, Any] | None = None,  # Input schema for type checking
) -> ExecutionPlan:
    """Convenience function to compile a Cy program.

    Args:
        ast_tree: The parsed AST tree
        source_file: Optional source file name
        available_tools: Dictionary of available tools (legacy)
        lark_parser: Parser instance for interpolation support
        tool_resolver: Optional ToolResolver for namespace resolution
        mcp_manager: Optional MCP manager with tools_cache
        app_manager: Optional App integration manager
        arc_router: Optional Archetype router
        validate_output: Whether to validate output coverage
        check_types: Whether to perform compile-time type checking
        input_schema: Optional input schema for type checking

    Returns:
        ExecutionPlan ready for execution

    Raises:
        TypeError: If type checking is enabled and type errors are found
    """
    # Build tool resolver if not provided
    # Use unified build_tool_resolver() to ensure type signatures are properly extracted
    if tool_resolver is None:
        from .tool_resolver import build_tool_resolver

        # Build resolver with type signatures from all sources
        tool_resolver = build_tool_resolver(
            include_native=True,
            available_tools=available_tools,
            mcp_manager=mcp_manager,
            app_manager=app_manager,
            arc_router=arc_router,
        )

    compiler = PlanCompiler(available_tools, lark_parser, tool_resolver)
    plan = compiler.compile(ast_tree, source_file)

    # Validate the execution plan if requested
    if validate_output:
        from .plan_validator import validate_plan

        validate_plan(plan)

    # Type check the execution plan if requested
    if check_types:
        from .type_inference_engine import TypeInferenceEngine

        # Create type inference engine with check_types=True
        engine = TypeInferenceEngine(
            plan, tool_resolver, input_schema=input_schema, check_types=True
        )

        # Run type inference with validation
        # This will raise TypeError if validation fails
        try:
            engine.infer_types()
        except TypeError:
            # Re-raise TypeError as-is (validation failures)
            raise

    return plan
