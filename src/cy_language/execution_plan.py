"""
Task Execution Plan data structures and schema for Cy language.

This module defines the core data structures that represent compiled Cy programs
as structured execution plans.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class NodeType(Enum):
    """Types of nodes in an execution plan.

    ``EXPRESSION`` and ``FOR_IN`` are defined for enum completeness but have
    no corresponding node subclass:

    * ``EXPRESSION`` — never implemented; all expressions are represented by
      their concrete types (Literal, Arithmetic, etc.).
    * ``FOR_IN`` — for-in loops are desugared to WhileLoop nodes by the
      compiler, so a dedicated ForInNode was never needed.

    Neither value has a deserializer entry in ``_NODE_DESERIALIZERS``.
    """

    ASSIGN = "assign"
    INDEXED_ASSIGN = "indexed_assign"
    FIELD_ASSIGN = "field_assign"
    EXPRESSION = "expression"  # Dead — see docstring above
    LITERAL = "literal"
    VARIABLE = "variable"
    TOOL_CALL = "tool_call"
    INTERPOLATION = "interpolation"
    LIST = "list"
    DICT = "dict"
    FIELD_ACCESS = "field_access"
    INDEXED_ACCESS = "indexed_access"
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    BOOLEAN_OP = "boolean_op"
    UNARY_OP = "unary_op"
    CONDITIONAL = "conditional"
    WHILE_LOOP = "while_loop"
    FOR_IN = "for_in"  # Dead — for-in is desugared to WhileLoop
    LIST_COMPREHENSION = "list_comprehension"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    TRY_CATCH = "try_catch"


@dataclass
class ExecutionNode:
    """Base class for all execution plan nodes."""

    node_type: NodeType
    line_number: int
    column: int
    node_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary for JSON serialization."""
        return {
            "type": self.node_type.value,
            "line": self.line_number,
            "column": self.column,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionNode":
        """Create node from a serialized dictionary.

        Uses a dispatch registry (``_NODE_DESERIALIZERS``) that maps each
        ``NodeType`` to the corresponding subclass's ``_from_dict_fields``
        classmethod — O(1) lookup instead of a long if/elif chain.

        New node types only need to:
        1. Implement ``_from_dict_fields(cls, data)`` on their subclass.
        2. Add an entry in the ``_NODE_DESERIALIZERS`` dict at module level.
        """
        node_type = NodeType(data["type"])
        deserializer = _NODE_DESERIALIZERS.get(node_type)
        if deserializer is None:
            raise ValueError(f"Unknown node type: {node_type}")
        return deserializer(data)


@dataclass
class AssignNode(ExecutionNode):
    """Node representing variable assignment."""

    variable_name: str
    expression: ExecutionNode

    def __init__(
        self,
        variable_name: str,
        expression: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.ASSIGN, line_number, column, node_id)
        self.variable_name = variable_name
        self.expression = expression

    def to_dict(self) -> dict[str, Any]:
        """Convert assign node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "variable_name": self.variable_name,
                "expression": self.expression.to_dict(),
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "AssignNode":
        expression = ExecutionNode.from_dict(data["expression"])
        return cls(
            data["variable_name"],
            expression,
            data["line"],
            data["column"],
            data["node_id"],
        )


@dataclass
class IndexedAssignNode(ExecutionNode):
    """Node representing indexed assignment like $dict[$key] = $value."""

    target: ExecutionNode  # The indexed access expression ($dict[$key])
    value: ExecutionNode  # The value being assigned

    def __init__(
        self,
        target: ExecutionNode,
        value: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.INDEXED_ASSIGN, line_number, column, node_id)
        self.target = target
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        """Convert indexed assign node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "target": self.target.to_dict(),
                "value": self.value.to_dict(),
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "IndexedAssignNode":
        target = ExecutionNode.from_dict(data["target"])
        value = ExecutionNode.from_dict(data["value"])
        return cls(target, value, data["line"], data["column"], data["node_id"])


class FieldAssignNode(ExecutionNode):
    """Node representing field assignment like a.x = value.

    This is syntactic sugar for a["x"] = value.
    """

    target: ExecutionNode  # The field access expression (a.x)
    value: ExecutionNode  # The value being assigned

    def __init__(
        self,
        target: ExecutionNode,
        value: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.FIELD_ASSIGN, line_number, column, node_id)
        self.target = target
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        """Convert field assign node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "target": self.target.to_dict(),
                "value": self.value.to_dict(),
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "FieldAssignNode":
        target = ExecutionNode.from_dict(data["target"])
        value = ExecutionNode.from_dict(data["value"])
        return cls(target, value, data["line"], data["column"], data["node_id"])


@dataclass
class LiteralNode(ExecutionNode):
    """Node representing literal values."""

    value: Any

    def __init__(self, value: Any, line_number: int, column: int, node_id: str):
        super().__init__(NodeType.LITERAL, line_number, column, node_id)
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        """Convert literal node to dictionary."""
        result = super().to_dict()
        result["value"] = self.value
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "LiteralNode":
        return cls(data["value"], data["line"], data["column"], data["node_id"])


@dataclass
class VariableNode(ExecutionNode):
    """Node representing variable references."""

    variable_name: str

    def __init__(self, variable_name: str, line_number: int, column: int, node_id: str):
        super().__init__(NodeType.VARIABLE, line_number, column, node_id)
        self.variable_name = variable_name

    def to_dict(self) -> dict[str, Any]:
        """Convert variable node to dictionary."""
        result = super().to_dict()
        result["variable_name"] = self.variable_name
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "VariableNode":
        return cls(data["variable_name"], data["line"], data["column"], data["node_id"])


@dataclass
class ToolCallNode(ExecutionNode):
    """Node representing tool/function calls."""

    tool_name: str
    arguments: list[ExecutionNode]
    named_arguments: dict[str, ExecutionNode]
    original_name: str  # The name as written in source code

    def __init__(
        self,
        tool_name: str,
        arguments: list[ExecutionNode],
        named_arguments: dict[str, ExecutionNode],
        line_number: int,
        column: int,
        node_id: str,
        original_name: str | None = None,
    ):
        super().__init__(NodeType.TOOL_CALL, line_number, column, node_id)
        self.tool_name = tool_name
        self.arguments = arguments
        self.named_arguments = named_arguments
        self.original_name = original_name or tool_name

    def to_dict(self) -> dict[str, Any]:
        """Convert tool call node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "tool_name": self.tool_name,
                "original_name": self.original_name,
                "arguments": [arg.to_dict() for arg in self.arguments],
                "named_arguments": {
                    k: v.to_dict() for k, v in self.named_arguments.items()
                },
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ToolCallNode":
        arguments = [ExecutionNode.from_dict(arg) for arg in data["arguments"]]
        named_args = {
            k: ExecutionNode.from_dict(v) for k, v in data["named_arguments"].items()
        }
        return cls(
            data["tool_name"],
            arguments,
            named_args,
            data["line"],
            data["column"],
            data["node_id"],
            original_name=data.get("original_name"),
        )


@dataclass
class InterpolationNode(ExecutionNode):
    """Node representing string interpolation."""

    template: str
    variables: list[ExecutionNode]
    printer_hints: dict[str, str]

    def __init__(
        self,
        template: str,
        variables: list[ExecutionNode],
        printer_hints: dict[str, str],
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.INTERPOLATION, line_number, column, node_id)
        self.template = template
        self.variables = variables
        self.printer_hints = printer_hints

    def to_dict(self) -> dict[str, Any]:
        """Convert interpolation node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "template": self.template,
                "variables": [var.to_dict() for var in self.variables],
                "printer_hints": self.printer_hints,
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "InterpolationNode":
        variables = [ExecutionNode.from_dict(var) for var in data["variables"]]
        return cls(
            data["template"],
            variables,
            data["printer_hints"],
            data["line"],
            data["column"],
            data["node_id"],
        )


@dataclass
class ListNode(ExecutionNode):
    """Node representing list literals."""

    elements: list[ExecutionNode]

    def __init__(
        self, elements: list[ExecutionNode], line_number: int, column: int, node_id: str
    ):
        super().__init__(NodeType.LIST, line_number, column, node_id)
        self.elements = elements

    def to_dict(self) -> dict[str, Any]:
        """Convert list node to dictionary."""
        result = super().to_dict()
        result["elements"] = [elem.to_dict() for elem in self.elements]
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ListNode":
        elements = [ExecutionNode.from_dict(elem) for elem in data["elements"]]
        return cls(elements, data["line"], data["column"], data["node_id"])


class ListComprehensionNode(ExecutionNode):
    """Node representing list comprehension expressions.

    Syntax: [element_expr for(iterator_var in iterable_expr)]
            [element_expr for(iterator_var in iterable_expr) if(filter_expr)]
    """

    element_expr: ExecutionNode
    iterator_var: str
    iterable_expr: ExecutionNode
    filter_expr: ExecutionNode | None

    def __init__(
        self,
        element_expr: ExecutionNode,
        iterator_var: str,
        iterable_expr: ExecutionNode,
        filter_expr: ExecutionNode | None,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.LIST_COMPREHENSION, line_number, column, node_id)
        self.element_expr = element_expr
        self.iterator_var = iterator_var
        self.iterable_expr = iterable_expr
        self.filter_expr = filter_expr

    def to_dict(self) -> dict[str, Any]:
        """Convert list comprehension node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "element_expr": self.element_expr.to_dict(),
                "iterator_var": self.iterator_var,
                "iterable_expr": self.iterable_expr.to_dict(),
                "filter_expr": self.filter_expr.to_dict() if self.filter_expr else None,
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ListComprehensionNode":
        element_expr = ExecutionNode.from_dict(data["element_expr"])
        iterable_expr = ExecutionNode.from_dict(data["iterable_expr"])
        filter_expr = (
            ExecutionNode.from_dict(data["filter_expr"])
            if data.get("filter_expr")
            else None
        )
        return cls(
            element_expr,
            data["iterator_var"],
            iterable_expr,
            filter_expr,
            data["line"],
            data["column"],
            data["node_id"],
        )


@dataclass
class DictNode(ExecutionNode):
    """Node representing dictionary literals."""

    pairs: list[tuple[ExecutionNode, ExecutionNode]]  # List of (key, value) pairs

    def __init__(
        self,
        pairs: list[tuple[ExecutionNode, ExecutionNode]],
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.DICT, line_number, column, node_id)
        self.pairs = pairs

    def to_dict(self) -> dict[str, Any]:
        """Convert dict node to dictionary."""
        result = super().to_dict()
        result["pairs"] = [
            [key.to_dict(), value.to_dict()] for key, value in self.pairs
        ]
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "DictNode":
        pairs = [
            (ExecutionNode.from_dict(pair[0]), ExecutionNode.from_dict(pair[1]))
            for pair in data["pairs"]
        ]
        return cls(pairs, data["line"], data["column"], data["node_id"])


@dataclass
class FieldAccessNode(ExecutionNode):
    """Node representing field access like obj.field."""

    object_node: ExecutionNode
    field_name: str

    def __init__(
        self,
        object_node: ExecutionNode,
        field_name: str,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.FIELD_ACCESS, line_number, column, node_id)
        self.object_node = object_node
        self.field_name = field_name

    def to_dict(self) -> dict[str, Any]:
        """Convert field access node to dictionary."""
        result = super().to_dict()
        result.update(
            {"object": self.object_node.to_dict(), "field_name": self.field_name}
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "FieldAccessNode":
        object_node = ExecutionNode.from_dict(data["object"])
        return cls(
            object_node,
            data["field_name"],
            data["line"],
            data["column"],
            data["node_id"],
        )


@dataclass
class IndexedAccessNode(ExecutionNode):
    """Node representing indexed access like obj[index] or list[0]."""

    object_node: ExecutionNode
    index_node: ExecutionNode

    def __init__(
        self,
        object_node: ExecutionNode,
        index_node: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.INDEXED_ACCESS, line_number, column, node_id)
        self.object_node = object_node
        self.index_node = index_node

    def to_dict(self) -> dict[str, Any]:
        """Convert indexed access node to dictionary."""
        result = super().to_dict()
        result.update(
            {"object": self.object_node.to_dict(), "index": self.index_node.to_dict()}
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "IndexedAccessNode":
        object_node = ExecutionNode.from_dict(data["object"])
        index_node = ExecutionNode.from_dict(data["index"])
        return cls(
            object_node,
            index_node,
            data["line"],
            data["column"],
            data["node_id"],
        )


class ArithmeticNode(ExecutionNode):
    """Node representing arithmetic operations (+, -, *, /)."""

    operator: str
    left: ExecutionNode
    right: ExecutionNode

    def __init__(
        self,
        operator: str,
        left: ExecutionNode,
        right: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.ARITHMETIC, line_number, column, node_id)
        self.operator = operator
        self.left = left
        self.right = right

    def to_dict(self) -> dict[str, Any]:
        """Convert arithmetic node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "operator": self.operator,
                "left": self.left.to_dict(),
                "right": self.right.to_dict(),
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ArithmeticNode":
        left = ExecutionNode.from_dict(data["left"])
        right = ExecutionNode.from_dict(data["right"])
        return cls(
            data["operator"],
            left,
            right,
            data["line"],
            data["column"],
            data["node_id"],
        )


class ComparisonNode(ExecutionNode):
    """Node representing comparison operations (==, !=, <, >, <=, >=, in)."""

    operator: str
    left: ExecutionNode
    right: ExecutionNode

    def __init__(
        self,
        operator: str,
        left: ExecutionNode,
        right: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.COMPARISON, line_number, column, node_id)
        self.operator = operator
        self.left = left
        self.right = right

    def to_dict(self) -> dict[str, Any]:
        """Convert comparison node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "operator": self.operator,
                "left": self.left.to_dict(),
                "right": self.right.to_dict(),
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ComparisonNode":
        left = ExecutionNode.from_dict(data["left"])
        right = ExecutionNode.from_dict(data["right"])
        return cls(
            data["operator"],
            left,
            right,
            data["line"],
            data["column"],
            data["node_id"],
        )


class BooleanOpNode(ExecutionNode):
    """Node representing boolean operations (and, or)."""

    operator: str
    operands: list[ExecutionNode]

    def __init__(
        self,
        operator: str,
        operands: list[ExecutionNode],
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.BOOLEAN_OP, line_number, column, node_id)
        self.operator = operator
        self.operands = operands

    def to_dict(self) -> dict[str, Any]:
        """Convert boolean operation node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "operator": self.operator,
                "operands": [operand.to_dict() for operand in self.operands],
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "BooleanOpNode":
        operands = [ExecutionNode.from_dict(op) for op in data["operands"]]
        return cls(
            data["operator"],
            operands,
            data["line"],
            data["column"],
            data["node_id"],
        )


class UnaryOpNode(ExecutionNode):
    """Node representing unary operations (not, -, +)."""

    operator: str
    operand: ExecutionNode

    def __init__(
        self,
        operator: str,
        operand: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.UNARY_OP, line_number, column, node_id)
        self.operator = operator
        self.operand = operand

    def to_dict(self) -> dict[str, Any]:
        """Convert unary operation node to dictionary."""
        result = super().to_dict()
        result.update({"operator": self.operator, "operand": self.operand.to_dict()})
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "UnaryOpNode":
        operand = ExecutionNode.from_dict(data["operand"])
        return cls(
            data["operator"],
            operand,
            data["line"],
            data["column"],
            data["node_id"],
        )


class ConditionalNode(ExecutionNode):
    """Node representing if/elif/else conditional statements."""

    condition: ExecutionNode
    if_body: list[ExecutionNode]
    elif_conditions: list[ExecutionNode]
    elif_bodies: list[list[ExecutionNode]]
    else_body: list[ExecutionNode] | None

    def __init__(
        self,
        condition: ExecutionNode,
        if_body: list[ExecutionNode],
        elif_conditions: list[ExecutionNode],
        elif_bodies: list[list[ExecutionNode]],
        else_body: list[ExecutionNode] | None,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.CONDITIONAL, line_number, column, node_id)
        self.condition = condition
        self.if_body = if_body
        self.elif_conditions = elif_conditions
        self.elif_bodies = elif_bodies
        self.else_body = else_body

    def to_dict(self) -> dict[str, Any]:
        """Convert conditional node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "condition": self.condition.to_dict(),
                "if_body": [node.to_dict() for node in self.if_body],
                "elif_conditions": [cond.to_dict() for cond in self.elif_conditions],
                "elif_bodies": [
                    [node.to_dict() for node in body] for body in self.elif_bodies
                ],
                "else_body": [node.to_dict() for node in self.else_body]
                if self.else_body
                else None,
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ConditionalNode":
        condition = ExecutionNode.from_dict(data["condition"])
        if_body = [ExecutionNode.from_dict(n) for n in data["if_body"]]
        elif_conditions = [ExecutionNode.from_dict(c) for c in data["elif_conditions"]]
        elif_bodies = [
            [ExecutionNode.from_dict(n) for n in body] for body in data["elif_bodies"]
        ]
        else_body = (
            [ExecutionNode.from_dict(n) for n in data["else_body"]]
            if data["else_body"]
            else None
        )
        return cls(
            condition,
            if_body,
            elif_conditions,
            elif_bodies,
            else_body,
            data["line"],
            data["column"],
            data["node_id"],
        )


class WhileLoopNode(ExecutionNode):
    """Node representing while loop statements."""

    condition: ExecutionNode
    body: list[ExecutionNode]

    def __init__(
        self,
        condition: ExecutionNode,
        body: list[ExecutionNode],
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.WHILE_LOOP, line_number, column, node_id)
        self.condition = condition
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        """Convert while loop node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "condition": self.condition.to_dict(),
                "body": [node.to_dict() for node in self.body],
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "WhileLoopNode":
        condition = ExecutionNode.from_dict(data["condition"])
        body = [ExecutionNode.from_dict(n) for n in data["body"]]
        return cls(condition, body, data["line"], data["column"], data["node_id"])


class ReturnNode(ExecutionNode):
    """Node representing return statements."""

    expression: ExecutionNode

    def __init__(
        self,
        expression: ExecutionNode,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.RETURN, line_number, column, node_id)
        self.expression = expression

    def to_dict(self) -> dict[str, Any]:
        """Convert return node to dictionary."""
        result = super().to_dict()
        result.update({"expression": self.expression.to_dict()})
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ReturnNode":
        expression = ExecutionNode.from_dict(data["expression"])
        return cls(expression, data["line"], data["column"], data["node_id"])


class BreakNode(ExecutionNode):
    """Node representing a break statement inside a loop."""

    def __init__(self, line_number: int, column: int, node_id: str):
        super().__init__(NodeType.BREAK, line_number, column, node_id)

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "BreakNode":
        return cls(data["line"], data["column"], data["node_id"])


class ContinueNode(ExecutionNode):
    """Node representing a continue statement inside a loop."""

    def __init__(self, line_number: int, column: int, node_id: str):
        super().__init__(NodeType.CONTINUE, line_number, column, node_id)

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "ContinueNode":
        return cls(data["line"], data["column"], data["node_id"])


@dataclass
class CatchClause:
    """Represents a catch clause with exception variable and body."""

    exception_var: str
    body: list[ExecutionNode]

    def to_dict(self) -> dict[str, Any]:
        """Convert catch clause to dictionary."""
        return {
            "exception_var": self.exception_var,
            "body": [stmt.to_dict() for stmt in self.body],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatchClause":
        """Create catch clause from dictionary."""
        body = [ExecutionNode.from_dict(node) for node in data["body"]]
        return cls(exception_var=data["exception_var"], body=body)


@dataclass
class TryCatchNode(ExecutionNode):
    """Node representing try/catch/finally statements."""

    try_body: list[ExecutionNode]
    catch_clauses: list[CatchClause]
    finally_body: list[ExecutionNode] | None

    def __init__(
        self,
        try_body: list[ExecutionNode],
        catch_clauses: list[CatchClause],
        finally_body: list[ExecutionNode] | None,
        line_number: int,
        column: int,
        node_id: str,
    ):
        super().__init__(NodeType.TRY_CATCH, line_number, column, node_id)
        self.try_body = try_body
        self.catch_clauses = catch_clauses
        self.finally_body = finally_body

    def to_dict(self) -> dict[str, Any]:
        """Convert try/catch node to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "try_body": [stmt.to_dict() for stmt in self.try_body],
                "catch_clauses": [clause.to_dict() for clause in self.catch_clauses],
                "finally_body": [stmt.to_dict() for stmt in self.finally_body]
                if self.finally_body
                else None,
            }
        )
        return result

    @classmethod
    def _from_dict_fields(cls, data: dict[str, Any]) -> "TryCatchNode":
        try_body = [ExecutionNode.from_dict(n) for n in data["try_body"]]
        catch_clauses = [
            CatchClause.from_dict(clause) for clause in data["catch_clauses"]
        ]
        finally_body = (
            [ExecutionNode.from_dict(n) for n in data["finally_body"]]
            if data.get("finally_body")
            else None
        )
        return cls(
            try_body,
            catch_clauses,
            finally_body,
            data["line"],
            data["column"],
            data["node_id"],
        )


@dataclass
class ExecutionPlan:
    """Complete execution plan for a Cy program."""

    version: str
    source_file: str | None
    nodes: list[ExecutionNode]
    metadata: dict[str, Any]

    def __init__(self, version: str = "2.0", source_file: str | None = None):
        self.version = version
        self.source_file = source_file
        self.nodes = []
        self.metadata = {}

    def add_node(self, node: ExecutionNode) -> None:
        """Add a node to the execution plan."""
        self.nodes.append(node)

    def to_json(self) -> str:
        """Serialize execution plan to JSON."""
        return json.dumps(
            {
                "version": self.version,
                "source_file": self.source_file,
                "nodes": [node.to_dict() for node in self.nodes],
                "metadata": self.metadata,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        """Deserialize execution plan from JSON."""
        data = json.loads(json_str)
        plan = cls(
            version=data.get("version", "2.0"), source_file=data.get("source_file")
        )
        plan.metadata = data.get("metadata", {})

        # Deserialize nodes
        for node_data in data.get("nodes", []):
            node = ExecutionNode.from_dict(node_data)
            plan.add_node(node)

        return plan

    def validate(self) -> list[str]:
        """Validate the execution plan structure."""
        errors = []

        # Check for empty plan
        if not self.nodes:
            errors.append("Execution plan has no nodes")
            return errors

        # Check for duplicate node IDs
        node_ids = set()
        for node in self.nodes:
            if node.node_id in node_ids:
                errors.append(f"Duplicate node ID: {node.node_id}")
            node_ids.add(node.node_id)

        # Check for valid line numbers
        for node in self.nodes:
            if node.line_number < 1:
                errors.append(
                    f"Invalid line number {node.line_number} for node {node.node_id}"
                )
            if node.column < 1:
                errors.append(
                    f"Invalid column number {node.column} for node {node.node_id}"
                )

        # Check for return statement instead of $output assignment
        has_return = False
        for node in self.nodes:
            if isinstance(node, ReturnNode):
                has_return = True
                break

        if not has_return:
            errors.append("Execution plan must have a return statement")

        return errors


# Sentinel to distinguish "human hasn't answered yet" from "human answered null"
_PENDING = object()


@dataclass
class ExecutionCheckpoint:
    """Serializable snapshot of execution state for pause/resume (HITL).

    When a hi-latency tool is encountered without a cached result, the executor
    raises ExecutionPaused carrying this checkpoint.  The backend stores it in
    PostgreSQL.  When the human responds, the backend loads the checkpoint,
    injects the answer into ``pending_tool_result``, and passes it back to the
    interpreter so execution can resume via memoized replay.

    Project Kalymnos (R3, R4, R6).
    """

    node_results: dict[str, Any]
    """Map of node_id → result for every tool call executed so far."""

    pending_node_id: str
    """node_id of the hi-latency tool call that caused the pause."""

    pending_tool_name: str
    """Fully-qualified name of the hi-latency tool (e.g. ``app::slack::ask_question``)."""

    pending_tool_args: dict[str, Any]
    """Arguments that were going to be passed to the hi-latency tool."""

    pending_tool_result: Any
    """The human's answer — ``_PENDING`` on initial pause, set before resume.

    Can be any value including ``None`` (a legitimate null response).
    Use ``is _PENDING`` to check whether the human has answered.
    """

    variables: dict[str, Any]
    """Snapshot of all execution context variables at the moment of pause."""

    plan_version: str
    """Version of the ExecutionPlan to detect stale checkpoints."""

    captured_logs: list
    """Log entries captured before the pause (preserved across resume)."""

    # -- serialization helpers ------------------------------------------------

    _PENDING_JSON_SENTINEL = "__PENDING__"

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain dict (suitable for JSONB column storage)."""
        # Serialize _PENDING sentinel as a JSON-safe string marker
        ptr = (
            self._PENDING_JSON_SENTINEL
            if self.pending_tool_result is _PENDING
            else self.pending_tool_result
        )
        return {
            "node_results": self.node_results,
            "pending_node_id": self.pending_node_id,
            "pending_tool_name": self.pending_tool_name,
            "pending_tool_args": self.pending_tool_args,
            "pending_tool_result": ptr,
            "variables": self.variables,
            "plan_version": self.plan_version,
            "captured_logs": self.captured_logs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionCheckpoint":
        """Create from a plain dict."""
        ptr = data.get("pending_tool_result", cls._PENDING_JSON_SENTINEL)
        if ptr == cls._PENDING_JSON_SENTINEL:
            ptr = _PENDING
        return cls(
            node_results=data["node_results"],
            pending_node_id=data["pending_node_id"],
            pending_tool_name=data["pending_tool_name"],
            pending_tool_args=data["pending_tool_args"],
            pending_tool_result=ptr,
            variables=data["variables"],
            plan_version=data["plan_version"],
            captured_logs=data.get("captured_logs", []),
        )

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionCheckpoint":
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))


# ---------------------------------------------------------------------------
# Dispatch registry for ExecutionNode.from_dict()
#
# Maps each NodeType to the corresponding subclass's ``_from_dict_fields``
# classmethod.  Defined here (module-level) so every subclass is in scope.
# New node types only need to add an entry + implement ``_from_dict_fields``.
# ---------------------------------------------------------------------------
_NODE_DESERIALIZERS: dict[NodeType, Any] = {
    NodeType.LITERAL: LiteralNode._from_dict_fields,
    NodeType.VARIABLE: VariableNode._from_dict_fields,
    NodeType.ASSIGN: AssignNode._from_dict_fields,
    NodeType.INDEXED_ASSIGN: IndexedAssignNode._from_dict_fields,
    NodeType.FIELD_ASSIGN: FieldAssignNode._from_dict_fields,
    NodeType.TOOL_CALL: ToolCallNode._from_dict_fields,
    NodeType.INTERPOLATION: InterpolationNode._from_dict_fields,
    NodeType.LIST: ListNode._from_dict_fields,
    NodeType.LIST_COMPREHENSION: ListComprehensionNode._from_dict_fields,
    NodeType.DICT: DictNode._from_dict_fields,
    NodeType.FIELD_ACCESS: FieldAccessNode._from_dict_fields,
    NodeType.INDEXED_ACCESS: IndexedAccessNode._from_dict_fields,
    NodeType.ARITHMETIC: ArithmeticNode._from_dict_fields,
    NodeType.COMPARISON: ComparisonNode._from_dict_fields,
    NodeType.BOOLEAN_OP: BooleanOpNode._from_dict_fields,
    NodeType.UNARY_OP: UnaryOpNode._from_dict_fields,
    NodeType.CONDITIONAL: ConditionalNode._from_dict_fields,
    NodeType.WHILE_LOOP: WhileLoopNode._from_dict_fields,
    NodeType.RETURN: ReturnNode._from_dict_fields,
    NodeType.BREAK: BreakNode._from_dict_fields,
    NodeType.CONTINUE: ContinueNode._from_dict_fields,
    NodeType.TRY_CATCH: TryCatchNode._from_dict_fields,
}


def create_execution_plan_from_ast(ast_tree: Any) -> ExecutionPlan:
    """Create execution plan from AST tree."""
    # Import here to avoid circular imports
    from .compiler import compile_cy_program

    return compile_cy_program(ast_tree)
