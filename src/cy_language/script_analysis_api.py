"""Public API for static analysis of Cy scripts.

Extracts tools used and externally-injected variables referenced by a script
without executing it. Used by Backend-Y and workflow builder to understand
task dependencies.

"""

from typing import Any

from cy_language.compiler import compile_cy_program
from cy_language.execution_plan import (
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
    TryCatchNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_analysis_api import _parse_tool_registry


def analyze_script(
    code: str,
    tool_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Analyze a Cy script to extract tools used and external variables referenced.

    Performs static analysis on compiled execution plan nodes to find:
    - All tool calls made by the script (by FQN)
    - All externally-injected variables (read but never assigned within the script)

    External variables are those injected via ``Cy(variables={"my_table": ...})``
    and ``input_data``. At the ExecutionPlan level they appear as VariableNode
    reads with no corresponding AssignNode within the script.

    Args:
        code: Cy language source code to analyze
        tool_registry: Optional dictionary of tool definitions (same format as
                      ``infer_output_schema``). Used to resolve custom tools
                      during compilation.

    Returns:
        Dictionary with sorted lists::

            {
                "tools_used": ["app::virustotal::ip_reputation", ...],
                "external_variables": ["config", "input", ...]
            }

    Raises:
        SyntaxError: If the Cy code cannot be parsed
    """
    if not code or code.strip() == "":
        return {"tools_used": [], "external_variables": []}

    # Step 1: Parse
    try:
        parser = Parser()
        ast = parser.parse_only(code)
    except Exception as e:
        raise SyntaxError(f"Failed to parse Cy code: {e}") from e

    # Step 2: Build tool resolver
    tool_resolver = ToolResolver.from_native_tools()
    if tool_registry:
        custom_tools = _parse_tool_registry(tool_registry)
        for tool_sig in custom_tools:
            tool_resolver.register_tool_with_types(tool_sig)

    # Step 3: Compile (with unknown-tool fallback loop)
    execution_plan = _compile_with_fallback(ast, tool_resolver)

    # Step 4: Walk all nodes to collect tools, reads, assigns
    tools: set[str] = set()
    reads: set[str] = set()
    assigns: set[str] = set()

    for node in execution_plan.nodes:
        _walk_node(node, tools, reads, assigns)

    # Step 5: Compute external variables and filter compiler internals
    external = reads - assigns
    external = {
        v
        for v in external
        if not v.startswith("__for_idx_") and not v.startswith("__for_iterable_")
    }

    return {
        "tools_used": sorted(tools),
        "external_variables": sorted(external),
    }


def _compile_with_fallback(
    ast: Any,
    tool_resolver: ToolResolver,
) -> ExecutionPlan:
    """Compile AST to ExecutionPlan, registering unknown tools as placeholders."""
    from cy_language.errors import ToolResolutionError

    max_retries = 20  # safety limit for scripts with many unknown tools
    for _ in range(max_retries):
        try:
            return compile_cy_program(
                ast,
                source_file="<api>",
                tool_resolver=tool_resolver,
                validate_output=False,
            )
        except (ToolResolutionError, Exception) as e:
            tool_error = None
            if isinstance(e, ToolResolutionError):
                tool_error = e
            elif isinstance(e.__cause__, ToolResolutionError):
                tool_error = e.__cause__

            if tool_error is None:
                raise SyntaxError(f"Failed to compile Cy code: {e}") from e

            unknown_tool = tool_error.tool_name
            tool_resolver.register_tool(unknown_tool, None)
            if "::" not in unknown_tool:
                tool_resolver.register_short_name(unknown_tool, unknown_tool)

    raise SyntaxError("Too many unknown tools in script")  # pragma: no cover


def _walk_node(
    node: ExecutionNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    """Recursively walk an execution plan node, collecting tools, reads, and assigns.

    Dispatches to ``_NODE_WALKERS`` by node type.  Each walker receives the
    concrete node and the three accumulator sets, and is responsible for
    recursing into its children via ``_walk_node``.
    """
    # The compiler may emit a raw list of nodes (e.g., for-in loop expansion
    # inside an if/elif/else/while/try body). Flatten by walking each element.
    if isinstance(node, list):
        for child in node:
            _walk_node(child, tools, reads, assigns)
        return

    walker = _NODE_WALKERS.get(type(node))
    if walker is None:
        raise ValueError(f"Unknown execution plan node type: {type(node).__name__}")
    walker(node, tools, reads, assigns)


# ---------------------------------------------------------------------------
# Per-node-type walker functions
#
# Each function handles one (or a small family of) node type(s).
# They are referenced by the ``_NODE_WALKERS`` dispatch dict at module end.
# ---------------------------------------------------------------------------


def _walk_noop(
    _node: ExecutionNode,
    _tools: set[str],
    _reads: set[str],
    _assigns: set[str],
) -> None:
    """No-op walker for leaf nodes (literal, break, continue)."""


def _walk_variable(
    node: VariableNode,
    _tools: set[str],
    reads: set[str],
    _assigns: set[str],
) -> None:
    reads.add(node.variable_name)


def _walk_assign(
    node: AssignNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    assigns.add(node.variable_name)
    _walk_node(node.expression, tools, reads, assigns)


def _walk_indexed_or_field_assign(
    node: IndexedAssignNode | FieldAssignNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.target, tools, reads, assigns)
    _walk_node(node.value, tools, reads, assigns)


def _walk_tool_call(
    node: ToolCallNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    tools.add(node.tool_name)
    for arg in node.arguments:
        _walk_node(arg, tools, reads, assigns)
    for arg in node.named_arguments.values():
        _walk_node(arg, tools, reads, assigns)


def _walk_interpolation(
    node: InterpolationNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    for var in node.variables:
        _walk_node(var, tools, reads, assigns)


def _walk_list(
    node: ListNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    for elem in node.elements:
        _walk_node(elem, tools, reads, assigns)


def _walk_dict(
    node: DictNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    for key, value in node.pairs:
        _walk_node(key, tools, reads, assigns)
        _walk_node(value, tools, reads, assigns)


def _walk_field_access(
    node: FieldAccessNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.object_node, tools, reads, assigns)


def _walk_indexed_access(
    node: IndexedAccessNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.object_node, tools, reads, assigns)
    _walk_node(node.index_node, tools, reads, assigns)


def _walk_binary_op(
    node: ArithmeticNode | ComparisonNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    """Arithmetic and Comparison nodes share the same left/right structure."""
    _walk_node(node.left, tools, reads, assigns)
    _walk_node(node.right, tools, reads, assigns)


def _walk_boolean_op(
    node: BooleanOpNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    for operand in node.operands:
        _walk_node(operand, tools, reads, assigns)


def _walk_unary_op(
    node: UnaryOpNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.operand, tools, reads, assigns)


def _walk_conditional(
    node: ConditionalNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.condition, tools, reads, assigns)
    for stmt in node.if_body:
        _walk_node(stmt, tools, reads, assigns)
    for cond in node.elif_conditions:
        _walk_node(cond, tools, reads, assigns)
    for body in node.elif_bodies:
        for stmt in body:
            _walk_node(stmt, tools, reads, assigns)
    if node.else_body:
        for stmt in node.else_body:
            _walk_node(stmt, tools, reads, assigns)


def _walk_while_loop(
    node: WhileLoopNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.condition, tools, reads, assigns)
    for stmt in node.body:
        _walk_node(stmt, tools, reads, assigns)


def _walk_try_catch(
    node: TryCatchNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    for stmt in node.try_body:
        _walk_node(stmt, tools, reads, assigns)
    for clause in node.catch_clauses:
        assigns.add(clause.exception_var)
        for stmt in clause.body:
            _walk_node(stmt, tools, reads, assigns)
    if node.finally_body:
        for stmt in node.finally_body:
            _walk_node(stmt, tools, reads, assigns)


def _walk_return(
    node: ReturnNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    _walk_node(node.expression, tools, reads, assigns)


def _walk_list_comprehension(
    node: ListComprehensionNode,
    tools: set[str],
    reads: set[str],
    assigns: set[str],
) -> None:
    """Walk list comprehension — collects from iterable, element, and filter."""
    _walk_node(node.iterable_expr, tools, reads, assigns)
    assigns.add(node.iterator_var)
    if node.filter_expr is not None:
        _walk_node(node.filter_expr, tools, reads, assigns)
    _walk_node(node.element_expr, tools, reads, assigns)


# ---------------------------------------------------------------------------
# Dispatch registry — maps concrete node type → walker function.
# ---------------------------------------------------------------------------
_NODE_WALKERS: dict[type, Any] = {
    LiteralNode: _walk_noop,
    VariableNode: _walk_variable,
    AssignNode: _walk_assign,
    IndexedAssignNode: _walk_indexed_or_field_assign,
    FieldAssignNode: _walk_indexed_or_field_assign,
    ToolCallNode: _walk_tool_call,
    InterpolationNode: _walk_interpolation,
    ListNode: _walk_list,
    ListComprehensionNode: _walk_list_comprehension,
    DictNode: _walk_dict,
    FieldAccessNode: _walk_field_access,
    IndexedAccessNode: _walk_indexed_access,
    ArithmeticNode: _walk_binary_op,
    ComparisonNode: _walk_binary_op,
    BooleanOpNode: _walk_boolean_op,
    UnaryOpNode: _walk_unary_op,
    ConditionalNode: _walk_conditional,
    WhileLoopNode: _walk_while_loop,
    TryCatchNode: _walk_try_catch,
    ReturnNode: _walk_return,
    BreakNode: _walk_noop,
    ContinueNode: _walk_noop,
}
