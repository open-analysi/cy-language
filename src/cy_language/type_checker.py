"""Type checking module for Cy language.

This module provides compile-time type checking to catch type errors
before execution. It leverages the type inference system to
validate type compatibility across operations.
"""

from dataclasses import dataclass
from typing import Any

from cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    ComparisonNode,
    ConditionalNode,
    ExecutionNode,
    ExecutionPlan,
    FieldAccessNode,
    FieldAssignNode,
    IndexedAccessNode,
    IndexedAssignNode,
    LiteralNode,
    ReturnNode,
    ToolCallNode,
    TryCatchNode,
    UnaryOpNode,
    WhileLoopNode,
)
from cy_language.tool_resolver import ToolResolver
from cy_language.tool_signature import bind_arguments
from cy_language.type_inference_engine import TypeInferenceEngine


@dataclass
class TypeError:
    """Represents a type error found during type checking.

    Attributes:
        message: Human-readable error message
        line: Line number where error occurred
        col: Column number where error occurred
        node_type: Type of node that caused the error (for debugging)
    """

    message: str
    line: int
    col: int
    node_type: str

    def __str__(self) -> str:
        """Format error message for display."""
        return f"Line {self.line}, Col {self.col}: {self.message}"


class TypeChecker:
    """Validates type compatibility in Cy execution plans.

    Uses type inference to determine expression types,
    then validates operations are type-safe.
    """

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        tool_resolver: ToolResolver | None = None,
    ):
        """Initialize type checker.

        Args:
            execution_plan: The execution plan to check
            tool_resolver: Optional tool resolver for validating tool calls
        """
        self.plan = execution_plan
        self.tool_resolver = tool_resolver
        self.errors: list[TypeError] = []

        # Initialize type inference engine to get type information
        self.type_engine = TypeInferenceEngine(
            execution_plan,
            tool_resolver if tool_resolver else ToolResolver(),
            input_schema=None,
        )
        # Run type inference to populate type environment
        self.type_env = self.type_engine.infer_types()

        # -------------------------------------------------------------------
        # Node type-check dispatch table (bound methods).
        #
        # Maps concrete node type → checker handler.  Replaces the
        # isinstance if/elif chain with O(1) dict lookup.  Node types
        # not in this dict are silently skipped (e.g. Literal, Variable)
        # because they have no type-compatibility rules to enforce.
        # -------------------------------------------------------------------
        self._node_checkers: dict[type, Any] = {
            ArithmeticNode: self._check_arithmetic,
            ComparisonNode: self._check_comparison,
            BooleanOpNode: self._check_boolean_op,
            UnaryOpNode: self._check_unary_op,
            ToolCallNode: self._check_tool_call,
            FieldAccessNode: self._check_field_access,
            IndexedAccessNode: self._check_indexed_access,
            ConditionalNode: self._check_conditional,
            WhileLoopNode: self._check_while_loop,
            TryCatchNode: self._check_try_catch,
            AssignNode: self._check_assign,
            IndexedAssignNode: self._check_indexed_assign,
            FieldAssignNode: self._check_field_assign,
            ReturnNode: self._check_return,
        }

    def check_types(self) -> list[TypeError]:
        """Run type checking on the execution plan.

        Returns:
            List of type errors found (empty if no errors)
        """
        # Clear any previous errors
        self.errors = []

        # Iterate through all nodes and check each one
        for node in self.plan.nodes:
            self._check_node(node)

        return self.errors

    def _check_node(self, node: ExecutionNode) -> None:
        """Dispatch node to appropriate type checker.

        Dispatches to the handler registered in ``self._node_checkers``
        by the concrete Python type of *node*.  Node types without an
        entry (Literal, Variable, Interpolation, etc.) are silently
        skipped — they have no type-compatibility rules to enforce.

        Args:
            node: Node to check
        """
        handler = self._node_checkers.get(type(node))
        if handler is not None:
            handler(node)

    def _check_assign(self, node: AssignNode) -> None:
        """Check assignment — recurse into the assigned expression."""
        self._check_node(node.expression)

    def _check_indexed_assign(self, node: IndexedAssignNode) -> None:
        """Check indexed assignment — recurse into sub-expressions.

        Checks the container, index, and value individually but does NOT
        route through ``_check_indexed_access`` (assignment is a write).
        """
        if isinstance(node.target, IndexedAccessNode):
            self._check_node(node.target.object_node)
            self._check_node(node.target.index_node)
        self._check_node(node.value)

    def _check_field_assign(self, node: FieldAssignNode) -> None:
        """Check field assignment — recurse into the value expression."""
        self._check_node(node.value)

    def _check_return(self, node: ReturnNode) -> None:
        """Check return statement — recurse into the returned expression."""
        if node.expression:
            self._check_node(node.expression)

    def _check_arithmetic(self, node: ArithmeticNode) -> None:
        """Check arithmetic operation for type compatibility.

        Rules:
        - `+`: both number OR both string
        - `-`, `*`, `/`, `%`: both must be number

        Args:
            node: ArithmeticNode to check
        """
        # Recursively check nested expressions
        self._check_node(node.left)
        self._check_node(node.right)

        # Get inferred types for operands
        left_type = self.type_engine.infer_node(node.left)
        right_type = self.type_engine.infer_node(node.right)

        # Skip checking if either operand is Any type
        if self._is_any_type(left_type) or self._is_any_type(right_type):
            return

        # Skip checking for nullable Any types (Any | null union)
        # This preserves Any semantics as an escape hatch from type checking
        # Must be checked BEFORE rejecting all nullable types
        if self._is_nullable_any_type(left_type) or self._is_nullable_any_type(
            right_type
        ):
            return

        # Reject nullable types in arithmetic operations
        # This forces explicit null handling with ?? operator for typed nullables
        if self._contains_null_variant(left_type) or self._contains_null_variant(
            right_type
        ):
            self.errors.append(
                TypeError(
                    message=f"Cannot {node.operator} nullable types. Use ?? operator for explicit null handling. Example: (obj.field ?? 0) {node.operator} 1",
                    line=node.line_number,
                    col=node.column,
                    node_type="ArithmeticNode",
                )
            )
            return

        left_type_name = left_type.get("type", "unknown")
        right_type_name = right_type.get("type", "unknown")

        # Check addition operation
        if node.operator == "+":
            # Both must be number OR both must be string
            if (left_type_name == "number" and right_type_name == "number") or (
                left_type_name == "string" and right_type_name == "string"
            ):
                return  # Valid
            # Type mismatch
            self.errors.append(
                TypeError(
                    message=f"Cannot add {left_type_name} and {right_type_name}",
                    line=node.line_number,
                    col=node.column,
                    node_type="ArithmeticNode",
                )
            )

        # Check other arithmetic operations
        elif node.operator in ["-", "*", "/", "%"]:
            # Both must be number
            if left_type_name == "number" and right_type_name == "number":
                return  # Valid
            op_names = {"-": "subtract", "*": "multiply", "/": "divide", "%": "modulo"}
            op_name = op_names.get(node.operator, "operate on")
            self.errors.append(
                TypeError(
                    message=f"Cannot {op_name} {left_type_name} and {right_type_name}",
                    line=node.line_number,
                    col=node.column,
                    node_type="ArithmeticNode",
                )
            )

    def _check_comparison(self, node: ComparisonNode) -> None:
        """Check comparison operation for type compatibility.

        Rules:
        - `<`, `>`, `<=`, `>=`: both number OR both string
        - `==`, `!=`: any types (always valid)
        - `in`: right side must be list, dictionary, or string

        Args:
            node: ComparisonNode to check
        """
        # Recursively check nested expressions
        self._check_node(node.left)
        self._check_node(node.right)

        # Equality operators accept any types
        if node.operator in ["==", "!="]:
            return  # Always valid

        if node.operator == "in":
            right_type = self.type_engine.infer_node(node.right)
            if self._is_any_type(right_type) or self._is_nullable_any_type(right_type):
                return
            if right_type.get("type") in ["array", "object", "string"]:
                return
            # Check nullable containers (e.g., array | null)
            if "oneOf" in right_type:
                non_null = [v for v in right_type["oneOf"] if v.get("type") != "null"]
                if non_null and all(
                    v.get("type") in ["array", "object", "string"] for v in non_null
                ):
                    return
            type_desc = self.type_engine.type_to_string(right_type)
            self.errors.append(
                TypeError(
                    message=f"'in' requires a list, dictionary, or string on the right side, got {type_desc}",
                    line=node.line_number,
                    col=node.column,
                    node_type="ComparisonNode",
                )
            )
            return

        # Get inferred types for operands
        left_type = self.type_engine.infer_node(node.left)
        right_type = self.type_engine.infer_node(node.right)

        # Skip checking if either operand is Any type
        if self._is_any_type(left_type) or self._is_any_type(right_type):
            return

        # Skip checking for nullable Any types (Any | null union)
        # This preserves Any semantics as an escape hatch from type checking
        # Must be checked BEFORE rejecting all nullable types
        if self._is_nullable_any_type(left_type) or self._is_nullable_any_type(
            right_type
        ):
            return

        # Reject nullable types in comparison operations
        # This forces explicit null handling with ?? operator for typed nullables
        if self._contains_null_variant(left_type) or self._contains_null_variant(
            right_type
        ):
            self.errors.append(
                TypeError(
                    message=f"Cannot compare nullable types. Use ?? operator for explicit null handling. Example: (obj.field ?? 0) {node.operator} 5",
                    line=node.line_number,
                    col=node.column,
                    node_type="ComparisonNode",
                )
            )
            return

        left_type_name = left_type.get("type", "unknown")
        right_type_name = right_type.get("type", "unknown")

        # For relational operators, both must be number OR both must be string
        if node.operator in ["<", ">", "<=", ">="]:
            if (left_type_name == "number" and right_type_name == "number") or (
                left_type_name == "string" and right_type_name == "string"
            ):
                return  # Valid
            # Type mismatch
            self.errors.append(
                TypeError(
                    message=f"Cannot compare {left_type_name} and {right_type_name}",
                    line=node.line_number,
                    col=node.column,
                    node_type="ComparisonNode",
                )
            )

    def _check_boolean_op(self, node: BooleanOpNode) -> None:
        """Check boolean operation for type compatibility.

        Changed to allow any types for 'and'/'or' (Python-like semantics).
        These operators now support truthy/falsy evaluation on any type.

        Rules:
        - `and`, `or`: accept any types (truthy/falsy semantics)

        Args:
            node: BooleanOpNode to check
        """
        # Recursively check nested expressions
        for operand in node.operands:
            self._check_node(operand)

        # No type validation needed for 'and'/'or'
        # Python-like truthy/falsy semantics allow any type
        # Type inference already handles creating union return types

    def _check_unary_op(self, node: UnaryOpNode) -> None:
        """Check unary operation for type compatibility.

        Rules:
        - `not`: operand must be boolean
        - `-`: operand must be number

        Args:
            node: UnaryOpNode to check
        """
        # Recursively check nested expression
        self._check_node(node.operand)

        # Get inferred type for operand
        operand_type = self.type_engine.infer_node(node.operand)

        # Skip checking if operand is Any type
        if self._is_any_type(operand_type):
            return

        operand_type_name = operand_type.get("type", "unknown")

        if node.operator == "not":
            # Operand must be boolean
            if operand_type_name != "boolean":
                self.errors.append(
                    TypeError(
                        message=f"Logical not requires boolean operand, got {operand_type_name}",
                        line=node.line_number,
                        col=node.column,
                        node_type="UnaryOpNode",
                    )
                )
        elif node.operator == "-" and operand_type_name != "number":
            self.errors.append(
                TypeError(
                    message=f"Unary negation requires number operand, got {operand_type_name}",
                    line=node.line_number,
                    col=node.column,
                    node_type="UnaryOpNode",
                )
            )

    def _check_tool_call(self, node: ToolCallNode) -> None:
        """Check tool call arguments match parameter types.

        Uses the canonical bind_arguments() to resolve positional+named args
        to parameter names, then type-checks each resolved binding.
        """
        if not self.tool_resolver:
            return

        signature = self.tool_resolver.get_signature(node.tool_name)
        if not signature:
            return

        # Recursively check all argument sub-expressions first
        for arg_node in node.arguments:
            self._check_node(arg_node)
        for arg_node in node.named_arguments.values():
            self._check_node(arg_node)

        # Bind arguments to parameter names (the ONE algorithm)
        bound, binding_errors = bind_arguments(
            list(signature.parameters.keys()),
            {n for n, p in signature.parameters.items() if p.required},
            node.arguments,
            node.named_arguments,
        )

        # Report binding errors
        for msg in binding_errors:
            self.errors.append(
                TypeError(
                    message=msg,
                    line=node.line_number,
                    col=node.column,
                    node_type="ToolCallNode",
                )
            )

        # Type-check each resolved binding
        for param_name, arg_node in bound.items():
            param_sig = signature.parameters[param_name]
            expected_type = param_sig.type_schema
            actual_type = self.type_engine.infer_node(arg_node)

            if self._is_any_type(expected_type) or self._is_any_type(actual_type):
                continue

            if not self._is_compatible(actual_type, expected_type):
                self.errors.append(
                    TypeError(
                        message=f"Parameter '{param_name}' expects "
                        f"{expected_type.get('type', 'unknown')}, "
                        f"got {actual_type.get('type', 'unknown')}",
                        line=node.line_number,
                        col=node.column,
                        node_type="ToolCallNode",
                    )
                )

    def _check_field_access(self, node: FieldAccessNode) -> None:
        """Check field access is valid.

        Rules:
        - Base must be object type
        - Field must exist in object schema
        - Mixed notation not supported (parser limitation)

        Args:
            node: FieldAccessNode to check
        """
        # Check for mixed notation (parser limitation)
        # Detect patterns like obj["key"].field or obj["key"]["key2"].field
        if isinstance(node.object_node, IndexedAccessNode):
            self.errors.append(
                TypeError(
                    message="Mixed bracket and dot notation is not supported. Use consistent notation: either all dot (obj.user.name) or all bracket (obj['user']['name'])",
                    line=node.line_number,
                    col=node.column,
                    node_type="FieldAccessNode",
                )
            )
            return

        # Recursively check nested expression
        self._check_node(node.object_node)

        # Get inferred type for object being accessed
        object_type = self.type_engine.infer_node(node.object_node)

        # Skip checking if object is Any type
        if self._is_any_type(object_type):
            return

        # Handle union types (e.g., from field access that can return null)
        if "oneOf" in object_type:
            # Check if union contains Any type (empty dict) - skip validation if so
            has_any = any(self._is_any_type(v) for v in object_type["oneOf"])
            if has_any:
                return  # Any type allows field access

            # Union type - check if any variant is an object type
            # Extract the object variant (ignore null variant)
            object_variants = [
                v for v in object_type["oneOf"] if v.get("type") == "object"
            ]
            if not object_variants:
                # No object variant in union - error
                self.errors.append(
                    TypeError(
                        message="Cannot access field on unknown type",
                        line=node.line_number,
                        col=node.column,
                        node_type="FieldAccessNode",
                    )
                )
                return
            # Use the object variant for further checking
            object_type = object_variants[0]

        # Check if object is actually an object type
        if object_type.get("type") != "object":
            object_type_name = object_type.get("type", "unknown")
            self.errors.append(
                TypeError(
                    message=f"Cannot access field on {object_type_name} type",
                    line=node.line_number,
                    col=node.column,
                    node_type="FieldAccessNode",
                )
            )
            return

        # Check if field exists in properties
        if "properties" in object_type:
            properties = object_type["properties"]
            if node.field_name not in properties:
                # Field not found in properties
                available_fields = list(properties.keys())
                self.errors.append(
                    TypeError(
                        message=f"Field '{node.field_name}' not found on object type. Available fields: {', '.join(available_fields) if available_fields else 'none'}",
                        line=node.line_number,
                        col=node.column,
                        node_type="FieldAccessNode",
                    )
                )
        # If object has additionalProperties, any field access is valid

    def _check_indexed_access(self, node: IndexedAccessNode) -> None:
        """Check indexed access is valid.

        Rules:
        - Base must be array, object, or string
        - Index type: number for array, string for object, number for string
        - Mixed notation not supported (parser limitation)

        Args:
            node: IndexedAccessNode to check
        """
        # Check for mixed notation (parser limitation)
        # Detect patterns like obj.field["key"] or obj.field1.field2["key"]
        if isinstance(node.object_node, FieldAccessNode):
            self.errors.append(
                TypeError(
                    message="Mixed dot and bracket notation is not supported. Use consistent notation: either all dot (obj.user.name) or all bracket (obj['user']['name'])",
                    line=node.line_number,
                    col=node.column,
                    node_type="IndexedAccessNode",
                )
            )
            return

        # Recursively check nested expressions
        self._check_node(node.object_node)
        self._check_node(node.index_node)

        # Get inferred types
        container_type = self.type_engine.infer_node(node.object_node)
        index_type = self.type_engine.infer_node(node.index_node)

        # Skip checking if container or index is Any type
        if self._is_any_type(container_type) or self._is_any_type(index_type):
            return

        # Handle union types for container (from field/indexed access returning null)
        if "oneOf" in container_type:
            # Check if union contains Any type (empty dict) - skip validation if so
            has_any = any(self._is_any_type(v) for v in container_type["oneOf"])
            if has_any:
                return  # Any type allows indexed access

            # Union type - extract non-null variant
            non_null_variants = [
                v for v in container_type["oneOf"] if v.get("type") != "null"
            ]
            if not non_null_variants:
                self.errors.append(
                    TypeError(
                        message="Cannot index null type",
                        line=node.line_number,
                        col=node.column,
                        node_type="IndexedAccessNode",
                    )
                )
                return
            # Use the first non-null variant for further checking
            container_type = non_null_variants[0]

        container_type_name = container_type.get("type", "unknown")
        index_type_name = index_type.get("type", "unknown")

        # Check based on container type
        if container_type_name == "array":
            # Arrays must be indexed with numbers
            if index_type_name != "number":
                self.errors.append(
                    TypeError(
                        message=f"Cannot index array with {index_type_name}, expected number",
                        line=node.line_number,
                        col=node.column,
                        node_type="IndexedAccessNode",
                    )
                )
        elif container_type_name == "object":
            # Objects must be indexed with strings
            if index_type_name != "string":
                self.errors.append(
                    TypeError(
                        message=f"Cannot index object with {index_type_name}, expected string",
                        line=node.line_number,
                        col=node.column,
                        node_type="IndexedAccessNode",
                    )
                )
            # If the index is a literal string, check if the key exists in properties
            elif isinstance(node.index_node, LiteralNode) and isinstance(
                node.index_node.value, str
            ):
                key_name = node.index_node.value
                if "properties" in container_type:
                    properties = container_type["properties"]
                    if key_name not in properties:
                        # Key not found in properties
                        available_fields = list(properties.keys())
                        self.errors.append(
                            TypeError(
                                message=f"Key '{key_name}' not found on object type. Available keys: {', '.join(available_fields) if available_fields else 'none'}",
                                line=node.line_number,
                                col=node.column,
                                node_type="IndexedAccessNode",
                            )
                        )
                # If object has additionalProperties, any key access is valid
        elif container_type_name == "string":
            # Strings must be indexed with numbers
            if index_type_name != "number":
                self.errors.append(
                    TypeError(
                        message=f"Cannot index string with {index_type_name}, expected number",
                        line=node.line_number,
                        col=node.column,
                        node_type="IndexedAccessNode",
                    )
                )
        else:
            # Cannot index this type
            self.errors.append(
                TypeError(
                    message=f"Cannot index {container_type_name} type",
                    line=node.line_number,
                    col=node.column,
                    node_type="IndexedAccessNode",
                )
            )

    def _check_conditional(self, node: ConditionalNode) -> None:
        """Check conditional statement.

        Rules:
        - Condition can be any type (Python-like truthy/falsy semantics)
        - Recursively check if/elif/else bodies

        Args:
            node: ConditionalNode to check
        """
        # Check condition expression (recursively validate nested operations)
        self._check_node(node.condition)

        # Note: We allow any type in conditions (truthy/falsy semantics like Python)
        # - null, 0, "", [], {} are falsy
        # - Everything else is truthy
        # So no type error is raised here

        # Recursively check if body
        if node.if_body:
            for stmt in node.if_body:
                self._check_node(stmt)

        # Recursively check elif conditions and bodies
        for elif_cond, elif_body in zip(
            node.elif_conditions, node.elif_bodies, strict=True
        ):
            self._check_node(elif_cond)
            for stmt in elif_body:
                self._check_node(stmt)

        # Recursively check else body
        if node.else_body:
            for stmt in node.else_body:
                self._check_node(stmt)

    def _check_while_loop(self, node: WhileLoopNode) -> None:
        """Check while loop.

        Rules:
        - Condition can be any type (Python-like truthy/falsy semantics)
        - Recursively check loop body

        Args:
            node: WhileLoopNode to check
        """
        # Check condition expression (recursively validate nested operations)
        self._check_node(node.condition)

        # Note: We allow any type in conditions (truthy/falsy semantics like Python)
        # - null, 0, "", [], {} are falsy
        # - Everything else is truthy
        # So no type error is raised here

        # Recursively check loop body
        for stmt in node.body:
            self._check_node(stmt)

    def _check_try_catch(self, node: TryCatchNode) -> None:
        """Check try/catch/finally — recurse into all sub-bodies."""
        for stmt in node.try_body:
            self._check_node(stmt)
        for clause in node.catch_clauses:
            for stmt in clause.body:
                self._check_node(stmt)
        if node.finally_body:
            for stmt in node.finally_body:
                self._check_node(stmt)

    def _is_compatible(self, type1: dict[str, Any], type2: dict[str, Any]) -> bool:
        """Check if two types are compatible.

        Args:
            type1: First type to compare
            type2: Second type to compare

        Returns:
            True if types are compatible
        """
        # Any type is compatible with everything
        if self._is_any_type(type1) or self._is_any_type(type2):
            return True

        # Exact type match
        if type1 == type2:
            return True

        # Check if types have same base type
        if type1.get("type") == type2.get("type"):
            return True

        # Union types - check if any variant matches
        if "oneOf" in type1:
            return any(
                self._is_compatible(variant, type2) for variant in type1["oneOf"]
            )
        if "oneOf" in type2:
            return any(
                self._is_compatible(type1, variant) for variant in type2["oneOf"]
            )

        return False

    def _is_any_type(self, type_info: dict[str, Any]) -> bool:
        """Check if type is Any (allows all operations).

        Args:
            type_info: Type to check

        Returns:
            True if type is Any
        """
        # Any type is represented as empty dict {}
        # or a dict without a "type" key
        if not type_info:
            return True
        return (
            "type" not in type_info
            and "oneOf" not in type_info
            and "properties" not in type_info
        )

    def _contains_null_variant(self, type_schema: dict[str, Any]) -> bool:
        """Check if a type schema is nullable (contains null variant).

        Used to enforce explicit null handling with ?? operator
        before operations on nullable types.

        Args:
            type_schema: Type schema to check

        Returns:
            True if type is null or union containing null
        """
        # Direct null type
        if type_schema.get("type") == "null":
            return True

        # Union type containing null
        if "oneOf" in type_schema:
            return any(v.get("type") == "null" for v in type_schema["oneOf"])

        return False

    def _is_nullable_any_type(self, type_schema: dict[str, Any]) -> bool:
        """Check if a type schema is a nullable Any type (Any | null union).

        Nullable Any types should bypass strict null checking
        to preserve Any semantics as an escape hatch from type checking.

        Args:
            type_schema: Type schema to check

        Returns:
            True if type is a union of Any ({}) and null
        """
        # Must be a union type
        if "oneOf" not in type_schema:
            return False

        variants = type_schema["oneOf"]

        # Check if union contains both Any and null
        has_any = any(self._is_any_type(v) for v in variants)
        has_null = any(v.get("type") == "null" for v in variants)

        return has_any and has_null
