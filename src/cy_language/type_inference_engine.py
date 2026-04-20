"""Type inference engine for Cy language.

This module provides the TypeInferenceEngine which walks ExecutionPlan nodes
and infers types for variables and expressions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from cy_language.tool_signature import ToolSignature

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
from cy_language.tool_resolver import ToolResolver
from cy_language.tool_signature import bind_arguments
from cy_language.type_environment import TypeEnvironment


class TypeInferenceEngine:
    """Type inference engine for Cy scripts.

    Walks an ExecutionPlan and infers types for all variables and expressions.
    Uses a TypeEnvironment to track variable types as assignments occur.
    """

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        tool_resolver: ToolResolver,
        input_schema: dict[str, Any] | None = None,
        check_types: bool = False,
        strict_input: bool = False,
    ):
        """Initialize type inference engine.

        Args:
            execution_plan: The compiled execution plan to infer types for
            tool_resolver: Tool resolver for looking up function signatures
            input_schema: Optional JSON Schema for the input variable
            check_types: If True, perform inline validation during inference
            strict_input: If True, validate that all input field accesses exist in input_schema
        """
        self.execution_plan = execution_plan
        self.tool_resolver = tool_resolver
        self.type_env = TypeEnvironment()
        self.check_types = check_types
        self.strict_input = strict_input
        self.input_schema = input_schema

        # Validate strict_input configuration
        if self.strict_input and input_schema is None:
            raise ValueError("strict_input requires input_schema to be provided")

        # Track return types for aggregation
        self.return_types: list[dict[str, Any]] = []

        # Track type errors during validation
        self.type_errors: list[str] = []

        # Bootstrap built-in variables (true, false, null)
        self.type_env.set_type("true", {"type": "boolean"})
        self.type_env.set_type("false", {"type": "boolean"})
        self.type_env.set_type("null", {"type": "null"})

        # Bootstrap input variable
        # If schema provided, use it; otherwise use Any type ({})
        if input_schema is not None:
            self.type_env.set_type("input", input_schema)
        else:
            self.type_env.set_type("input", {})

        # -------------------------------------------------------------------
        # Node inference dispatch table (bound methods).
        #
        # Maps concrete node type → inference handler.  Replaces the
        # isinstance if/elif chain with O(1) dict lookup and makes it
        # obvious which node types are covered.
        # -------------------------------------------------------------------
        self._node_inferrers: dict[type, Any] = {
            LiteralNode: self._infer_literal,
            VariableNode: self._infer_variable,
            AssignNode: self._infer_assignment,
            ArithmeticNode: self._infer_arithmetic,
            ComparisonNode: self._infer_comparison,
            BooleanOpNode: self._infer_boolean_op,
            UnaryOpNode: self._infer_unary_op,
            DictNode: self._infer_dict,
            ListNode: self._infer_list,
            ListComprehensionNode: self._infer_list_comprehension,
            FieldAccessNode: self._infer_field_access,
            IndexedAccessNode: self._infer_indexed_access,
            ToolCallNode: self._infer_tool_call,
            ConditionalNode: self._infer_conditional,
            WhileLoopNode: self._infer_while_loop,
            TryCatchNode: self._infer_try_catch,
            ReturnNode: self._infer_return,
            InterpolationNode: self._infer_interpolation,
            IndexedAssignNode: self._infer_indexed_assign,
            FieldAssignNode: self._infer_field_assign,
            BreakNode: self._infer_noop,
            ContinueNode: self._infer_noop,
        }

    def infer_types(self) -> TypeEnvironment:
        """Infer types for all nodes in the execution plan.

        Walks the execution plan nodes in order, inferring types for each node
        and updating the type environment as variables are assigned.

        If check_types=True, performs inline validation and collects errors.
        After processing all nodes, raises TypeError if any errors were found.

        Returns:
            TypeEnvironment containing inferred types for all variables

        Raises:
            TypeError: If check_types=True and validation errors were found
        """
        # Walk through all nodes in the execution plan
        for node in self.execution_plan.nodes:
            # Infer type for this node
            # This will update the type environment for assignments
            # If check_types=True, validation happens inline
            self.infer_node(node)

        # If check_types=True and errors were collected, raise TypeError
        if self.check_types and self.type_errors:
            error_message = "\n".join(self.type_errors)
            raise TypeError(f"Type validation failed:\n{error_message}")

        return self.type_env

    def infer_node(self, node: ExecutionNode) -> dict[str, Any]:
        """Infer type for a single execution node.

        Dispatches to the handler registered in ``self._node_inferrers``
        by the concrete Python type of *node*.

        Args:
            node: ExecutionNode to infer type for

        Returns:
            JSON Schema dict representing the inferred type

        Raises:
            ValueError: If node type is not supported
        """
        handler = self._node_inferrers.get(type(node))
        if handler is None:
            raise ValueError(
                f"Unsupported node type for type inference: {type(node).__name__}"
            )
        return handler(node)

    def _infer_noop(self, _node: ExecutionNode) -> dict[str, Any]:
        """Break/continue produce no value — return empty schema."""
        return {}

    def _infer_literal(self, node: LiteralNode) -> dict[str, Any]:
        """Infer type for a literal value.

        Args:
            node: LiteralNode containing the literal value

        Returns:
            JSON Schema: {"type": "number"} | {"type": "string"} |
                        {"type": "boolean"} | {"type": "null"}
        """
        value = node.value
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, (int, float)):
            return {"type": "number"}
        if isinstance(value, str):
            return {"type": "string"}
        # Unknown type - return Any
        return {}

    def _infer_variable(self, node: VariableNode) -> dict[str, Any]:
        """Infer type for a variable reference.

        Looks up the variable in the type environment.

        Args:
            node: VariableNode containing variable name

        Returns:
            JSON Schema for variable type, or {} (Any) if unknown
        """
        var_type = self.type_env.get_type(node.variable_name)
        if var_type is None:
            # Record undefined variable error if type checking is enabled
            if self.check_types:
                error_msg = f"Line {node.line_number}: Undefined variable '{node.variable_name}'"
                self.type_errors.append(error_msg)
            # Return Any to allow inference to continue
            return {}
        return var_type

    def _infer_assignment(self, node: AssignNode) -> dict[str, Any]:
        """Infer type for an assignment node.

        Infers the type of the right-hand side and stores it in the
        type environment for the variable.

        Args:
            node: AssignNode containing variable and value

        Returns:
            JSON Schema for the assigned value
        """
        # Infer type of the value being assigned
        value_type = self.infer_node(node.expression)

        # Store type in environment for the variable
        self.type_env.set_type(node.variable_name, value_type)

        return value_type

    def _infer_arithmetic(self, node: ArithmeticNode) -> dict[str, Any]:
        """Infer type for an arithmetic operation.

        Args:
            node: ArithmeticNode containing operator and operands

        Returns:
            JSON Schema for result type:
            - number + number → number
            - string + string → string
            - number op number → number (for -, *, /, %)
        """
        # Infer types of operands
        left_type = self.infer_node(node.left)
        right_type = self.infer_node(node.right)

        # Inline validation if check_types=True
        self._validate_arithmetic(node, left_type, right_type)

        # For + operator, check type of operands
        if node.operator == "+":
            if left_type.get("type") == "string" and right_type.get("type") == "string":
                return {"type": "string"}
            if left_type.get("type") == "number" and right_type.get("type") == "number":
                return {"type": "number"}
            if left_type.get("type") == "array" and right_type.get("type") == "array":
                # Array concatenation returns array
                # Try to preserve element type if both arrays have same element type
                left_elem = left_type.get("element_type", {})
                right_elem = right_type.get("element_type", {})
                if left_elem == right_elem and left_elem:
                    return {"type": "array", "element_type": left_elem}
                return {"type": "array"}
            # Type mismatch or unknown - return Any
            return {}

        # For -, *, /, % operators, result is number if both operands are numbers
        if node.operator in ["-", "*", "/", "%"]:
            if left_type.get("type") == "number" and right_type.get("type") == "number":
                return {"type": "number"}
            # Type mismatch or unknown - return Any
            return {}

        # Unknown operator - return Any
        return {}

    def _infer_comparison(self, node: ComparisonNode) -> dict[str, Any]:
        """Infer type for a comparison operation.

        All comparison operators return boolean.

        Args:
            node: ComparisonNode containing operator and operands

        Returns:
            JSON Schema: {"type": "boolean"}
        """
        # Infer operand types for validation
        left_type = self.infer_node(node.left)
        right_type = self.infer_node(node.right)

        # Inline validation if check_types=True
        self._validate_comparison(node, left_type, right_type)

        # Comparisons always return boolean
        return {"type": "boolean"}

    def _infer_boolean_op(self, node: BooleanOpNode) -> dict[str, Any]:
        """Infer type for a boolean operation (and, or, ??).

        Changed to return union of operand types instead of boolean,
        since 'or' and 'and' now return actual values (Python-like semantics).

        The '??' operator returns non-null types from operands, excluding null.

        Args:
            node: BooleanOpNode containing operator and operands

        Returns:
            JSON Schema: Union of all operand types (with null excluded for ??)
        """
        # Infer operand types for validation
        # Note: BooleanOpNode has operands list, not left/right
        operand_types = [self.infer_node(operand) for operand in node.operands]

        # Inline validation if check_types=True
        # Validate each pair of operands
        if self.check_types and len(operand_types) >= 2:
            for i in range(len(operand_types) - 1):
                self._validate_boolean_op(node, operand_types[i], operand_types[i + 1])

        # Null coalescing operator (??) returns non-null types
        # When left is (Any | null) and right is concrete type T, return T
        if node.operator == "??":
            # Helper to check if type is (Any | null)
            def is_nullable_any(typ: dict[str, Any]) -> bool:
                if "oneOf" not in typ:
                    return False
                variants = typ["oneOf"]
                if len(variants) != 2:
                    return False
                has_any = any(v == {} for v in variants)
                has_null = any(v.get("type") == "null" for v in variants)
                return has_any and has_null

            # Helper to check if type contains Any
            def contains_any(typ: dict[str, Any]) -> bool:
                if typ == {}:
                    return True
                if "oneOf" in typ:
                    return any(v == {} for v in typ["oneOf"])
                return False

            # Process operands from left to right, applying special rule
            # For chained ??: a ?? b ?? c becomes (a ?? b) ?? c
            result_type = operand_types[0]
            for i in range(1, len(operand_types)):
                right_type = operand_types[i]

                # Special case 1: (Any | null) ?? T → T (when T doesn't contain Any)
                if is_nullable_any(result_type) and not contains_any(right_type):
                    result_type = right_type
                # Special case 2: (Any | null) ?? (Any | null) → (Any | null)
                elif is_nullable_any(result_type) and is_nullable_any(right_type):
                    result_type = result_type  # Keep as (Any | null)
                else:
                    # Standard ?? logic: collect non-null types from both sides
                    non_null_types = []

                    # Extract non-null from result_type
                    if "oneOf" in result_type:
                        for variant in result_type["oneOf"]:
                            if (
                                variant.get("type") != "null"
                                and variant not in non_null_types
                            ):
                                non_null_types.append(variant)
                    elif (
                        result_type.get("type") != "null"
                        and result_type not in non_null_types
                    ):
                        non_null_types.append(result_type)

                    # Extract non-null from right_type
                    if "oneOf" in right_type:
                        for variant in right_type["oneOf"]:
                            if (
                                variant.get("type") != "null"
                                and variant not in non_null_types
                            ):
                                non_null_types.append(variant)
                    elif (
                        right_type.get("type") != "null"
                        and right_type not in non_null_types
                    ):
                        non_null_types.append(right_type)

                    # Update result_type
                    if not non_null_types:
                        result_type = {"type": "null"}
                    elif len(non_null_types) == 1:
                        result_type = non_null_types[0]
                    else:
                        result_type = {"oneOf": non_null_types}

            return result_type

        # Return union of operand types (or/and return values, not booleans)
        # If all operands have the same type, return that type
        if len(operand_types) == 1:
            return operand_types[0]

        first_type = operand_types[0]
        if all(t == first_type for t in operand_types):
            return first_type

        # Different types - create union with unique types
        unique_types = []
        for op_type in operand_types:
            if op_type not in unique_types:
                unique_types.append(op_type)

        return {"oneOf": unique_types}

    def _infer_unary_op(self, node: UnaryOpNode) -> dict[str, Any]:
        """Infer type for a unary operation (not, -).

        Args:
            node: UnaryOpNode containing operator and operand

        Returns:
            JSON Schema: {"type": "boolean"} for not, {"type": "number"} for -
        """
        # Infer the operand type (this also checks for undefined variables)
        self.infer_node(node.operand)

        if node.operator == "not":
            return {"type": "boolean"}
        if node.operator == "-":
            return {"type": "number"}
        # Unknown operator - return Any
        return {}

    def _infer_dict(self, node: DictNode) -> dict[str, Any]:
        """Infer type for a dictionary literal.

        Args:
            node: DictNode containing key-value pairs

        Returns:
            JSON Schema object type with properties or additionalProperties
        """
        # Empty dict - return basic object type
        if not node.pairs:
            return {"type": "object"}

        # Check if all keys are literal strings (static keys)
        all_static_keys = True
        properties = {}

        for key_node, value_node in node.pairs:
            # Check if key is a literal string
            if isinstance(key_node, LiteralNode) and isinstance(key_node.value, str):
                # Static key - add to properties
                key_name = key_node.value
                value_type = self.infer_node(value_node)
                properties[key_name] = value_type
            else:
                # Dynamic key (non-literal or non-string) - use additionalProperties
                all_static_keys = False
                break

        if all_static_keys:
            # All keys are static - return object with properties
            return {"type": "object", "properties": properties}
        # Has dynamic keys - use additionalProperties
        # Infer types of all values to determine additionalProperties schema
        value_types = [self.infer_node(value_node) for _, value_node in node.pairs]

        # Check if all values have the same type
        if len(value_types) == 1:
            return {"type": "object", "additionalProperties": value_types[0]}

        first_type = value_types[0]
        all_same = all(v_type == first_type for v_type in value_types)

        if all_same:
            return {"type": "object", "additionalProperties": first_type}
        # Mixed value types - use oneOf union
        unique_types = []
        for v_type in value_types:
            if v_type not in unique_types:
                unique_types.append(v_type)

        return {
            "type": "object",
            "additionalProperties": {"oneOf": unique_types},
        }

    def _infer_list(self, node: ListNode) -> dict[str, Any]:
        """Infer type for a list literal.

        Args:
            node: ListNode containing elements

        Returns:
            JSON Schema array type with items schema
        """
        # Empty list - return basic array type
        if not node.elements:
            return {"type": "array"}

        # Infer types for all elements
        element_types = [self.infer_node(elem) for elem in node.elements]

        # Check if all elements have the same type (homogeneous array)
        if len(element_types) == 1:
            # Single element - use its type
            return {"type": "array", "items": element_types[0]}

        # Check if all types are equal
        first_type = element_types[0]
        all_same = all(elem_type == first_type for elem_type in element_types)

        if all_same:
            # Homogeneous array - use single item type
            return {"type": "array", "items": first_type}
        # Heterogeneous array - use oneOf union
        # Collect unique types
        unique_types = []
        for elem_type in element_types:
            if elem_type not in unique_types:
                unique_types.append(elem_type)

        return {"type": "array", "items": {"oneOf": unique_types}}

    def _infer_field_access(self, node: FieldAccessNode) -> dict[str, Any]:
        """Infer type for field access operation.

        Field access can return null for missing keys, so we return
        a union type that includes null.

        Args:
            node: FieldAccessNode containing object and field name

        Returns:
            JSON Schema for the field type union with null, or {} (Any) if unknown
        """
        # Infer type of the object being accessed
        object_type = self.infer_node(node.object_node)

        # Inline validation if check_types=True
        self._validate_field_access(node, object_type)

        # If object could be null, field access returns null
        if object_type.get("type") == "null":
            return {"type": "null"}

        # Handle union types (e.g., from previous field access)
        if "oneOf" in object_type:
            # Extract the object variant (ignore null variant)
            object_variants = [
                v for v in object_type["oneOf"] if v.get("type") == "object"
            ]
            if not object_variants:
                # No object variant - return Any union with null
                return {"oneOf": [{}, {"type": "null"}]}
            # Use the object variant for field lookup
            object_type = object_variants[0]

        # If object type is unknown or not an object, return null
        # Safe navigation returns null for invalid field access
        # But we still validate above if check_types=True
        if not object_type or object_type.get("type") != "object":
            # Special case for Any type - return Any | null to preserve Any semantics
            # Any type should allow any operation, so field access should return nullable Any
            if self._is_any_type(object_type):
                return {"oneOf": [{}, {"type": "null"}]}
            # Return just null for other non-object types
            # This preserves type information so subsequent field access can still be validated
            return {"type": "null"}

        # Look up field in properties
        field_type = None
        if "properties" in object_type:
            properties = object_type["properties"]
            if node.field_name in properties:
                field_type = cast(dict[str, Any], properties[node.field_name])

        # Check additionalProperties if field not in properties
        if field_type is None and "additionalProperties" in object_type:
            field_type = cast(dict[str, Any], object_type["additionalProperties"])

        # strict_input mode exception - return base type, not union
        # When strict_input=True and accessing input variable, validation ensures
        # the field exists, so we can return the base type without null
        if self.strict_input and self._is_accessing_input(node.object_node):
            if field_type is None or not field_type:
                # Field doesn't exist - validation will have added error
                # Return Any for inference to continue
                return {}
            # Field exists - return base type (validation ensures it's safe)
            return field_type

        # Field access can return null for missing keys
        # Return union of field type with null
        if field_type is None or not field_type:
            # Unknown field - could be any type or null
            return {"oneOf": [{}, {"type": "null"}]}

        # Known field - return union with null
        # Special case: if field already includes null, don't duplicate
        if field_type.get("type") == "null":
            return field_type
        if "oneOf" in field_type:
            # Check if null already in union
            has_null = any(t.get("type") == "null" for t in field_type["oneOf"])
            if has_null:
                return field_type
            # Add null to union
            return {"oneOf": field_type["oneOf"] + [{"type": "null"}]}

        # Simple type - create union with null
        return {"oneOf": [field_type, {"type": "null"}]}

    def _infer_indexed_access(self, node: IndexedAccessNode) -> dict[str, Any]:
        """Infer type for indexed access operation.

        Indexed access can return null for missing keys (on objects),
        so we return a union type that includes null for object access.

        Args:
            node: IndexedAccessNode containing object and index

        Returns:
            JSON Schema for the element type union with null, or {} (Any) if unknown
        """
        # Infer type of the container being indexed
        container_type = self.infer_node(node.object_node)

        # Infer type of the index
        index_type = self.infer_node(node.index_node)

        # Inline validation if check_types=True
        self._validate_indexed_access(node, container_type, index_type)

        # If container could be null, indexed access returns null
        if container_type.get("type") == "null":
            return {"type": "null"}

        # Handle union types (e.g., from previous field/indexed access)
        if "oneOf" in container_type:
            # Extract non-null variants
            non_null_variants = [
                v for v in container_type["oneOf"] if v.get("type") != "null"
            ]
            if not non_null_variants:
                # Only null - return null
                return {"type": "null"}
            # Use first non-null variant for indexing
            container_type = non_null_variants[0]

        # If container type is unknown, return Any union with null
        if not container_type:
            return {"oneOf": [{}, {"type": "null"}]}

        # Handle array indexing
        # Note: Array indexing can also return null if index is out of bounds,
        # but we don't track array bounds in type system
        if container_type.get("type") == "array":
            # Return the items type
            if "items" in container_type:
                item_type = cast(dict[str, Any], container_type["items"])

                # Special case for for-in loops
                # When accessing __for_iterable_XXX variables (created by for-in loops),
                # the bounds are checked by the while condition, so we return the element
                # type directly without null. This allows loop variables to have the
                # correct non-nullable type for safe usage within the loop body.
                if isinstance(
                    node.object_node, VariableNode
                ) and node.object_node.variable_name.startswith("__for_iterable_"):
                    return item_type

                # Array access can return null for out of bounds
                # Return union with null
                if item_type.get("type") == "null":
                    return item_type
                if "oneOf" in item_type:
                    has_null = any(t.get("type") == "null" for t in item_type["oneOf"])
                    if has_null:
                        return item_type
                    return {"oneOf": item_type["oneOf"] + [{"type": "null"}]}
                return {"oneOf": [item_type, {"type": "null"}]}
            # Array with no items schema - return Any union with null
            return {"oneOf": [{}, {"type": "null"}]}

        # Handle object key access
        if container_type.get("type") == "object":
            # Check if index is a literal string (static key)
            element_type = None
            if isinstance(node.index_node, LiteralNode) and isinstance(
                node.index_node.value, str
            ):
                key_name = node.index_node.value
                # Look up in properties
                if "properties" in container_type:
                    properties = container_type["properties"]
                    if key_name in properties:
                        element_type = cast(dict[str, Any], properties[key_name])

            # Dynamic key or not found in properties - check additionalProperties
            if element_type is None and "additionalProperties" in container_type:
                element_type = cast(
                    dict[str, Any], container_type["additionalProperties"]
                )

            # strict_input mode exception - return base type, not union
            # When strict_input=True and accessing input variable, validation ensures
            # the field exists, so we can return the base type without null
            if self.strict_input and self._is_accessing_input(node.object_node):
                if element_type is None or not element_type:
                    # Field doesn't exist - validation will have added error
                    # Return Any for inference to continue
                    return {}
                # Field exists - return base type (validation ensures it's safe)
                return element_type

            # Object indexed access can return null for missing keys
            # Return union with null
            if element_type is None or not element_type:
                # Unknown key - could be any type or null
                return {"oneOf": [{}, {"type": "null"}]}

            # Known key - return union with null
            if element_type.get("type") == "null":
                return element_type
            if "oneOf" in element_type:
                has_null = any(t.get("type") == "null" for t in element_type["oneOf"])
                if has_null:
                    return element_type
                return {"oneOf": element_type["oneOf"] + [{"type": "null"}]}
            return {"oneOf": [element_type, {"type": "null"}]}

        # Unknown container or unsupported indexing - return Any
        return {}

    def _infer_tool_call(self, node: ToolCallNode) -> dict[str, Any]:
        """Infer type for a tool call.

        Args:
            node: ToolCallNode containing tool name and arguments

        Returns:
            JSON Schema for the tool's return type, or {} (Any) if unknown
        """
        # Query ToolResolver for the tool signature
        signature = self.tool_resolver.get_signature(node.tool_name)

        # Tool not found - return Any (conservative)
        if signature is None:
            return {}

        # Validate tool call arguments if check_types=True
        self._validate_tool_call(node, signature)

        # Special handling for __to_iterable to preserve element types
        # This function is used by for-in loops and must preserve type information
        if node.tool_name == "__to_iterable" and len(node.arguments) > 0:
            arg_type = self.infer_node(node.arguments[0])

            if arg_type.get("type") == "array":
                # Array → return same array (preserve element type)
                return arg_type
            if arg_type.get("type") == "object":
                # Dict → return array of strings (keys)
                return {"type": "array", "items": {"type": "string"}}
            if arg_type.get("type") == "string":
                # String → return array of strings (characters)
                return {"type": "array", "items": {"type": "string"}}
            # Fall through to default return type for other cases

        # Tool found - return its return type
        # If no return type specified in signature, return Any
        if signature.return_type is None or not signature.return_type:
            return {}

        return signature.return_type

    def _infer_conditional(self, node: ConditionalNode) -> dict[str, Any]:
        """Infer type for a conditional statement/expression.

        For conditional expressions (value-returning), returns union of
        branch types. For conditional statements (assignments in branches),
        merges variable types across branches to create unions where needed.

        Args:
            node: ConditionalNode containing condition, then_branch, else_branch

        Returns:
            JSON Schema for the conditional result (union of branches if different)
        """
        # Infer condition type (for completeness)
        self.infer_node(node.condition)

        # Save the current type environment before branches
        env_before_branches = self.type_env.copy()

        # Track variables assigned in each branch
        branch_envs = []

        # Collect return types from branches (for conditional expressions)
        branch_types = []

        # Process if branch
        if node.if_body:
            # Create a copy of the environment for this branch
            branch_env = env_before_branches.copy()

            # Temporarily use branch environment
            saved_env = self.type_env
            self.type_env = branch_env

            # Process all statements in if body
            for stmt in node.if_body:
                self.infer_node(stmt)

            # Last expression determines return type (for conditional expressions)
            if_type = self.infer_node(node.if_body[-1])
            branch_types.append(if_type)

            # Save branch environment for later merging
            branch_envs.append(self.type_env)

            # Restore original environment
            self.type_env = saved_env

        # Process elif branches
        for elif_body in node.elif_bodies:
            if elif_body:
                # Create a copy of the environment for this branch
                branch_env = env_before_branches.copy()

                # Temporarily use branch environment
                saved_env = self.type_env
                self.type_env = branch_env

                # Process all statements in elif body
                for stmt in elif_body:
                    self.infer_node(stmt)

                # Last expression determines return type (for conditional expressions)
                elif_type = self.infer_node(elif_body[-1])
                branch_types.append(elif_type)

                # Save branch environment for later merging
                branch_envs.append(self.type_env)

                # Restore original environment
                self.type_env = saved_env

        # Process else branch
        if node.else_body:
            # Create a copy of the environment for this branch
            branch_env = env_before_branches.copy()

            # Temporarily use branch environment
            saved_env = self.type_env
            self.type_env = branch_env

            # Process all statements in else body
            for stmt in node.else_body:
                self.infer_node(stmt)

            # Last expression determines return type (for conditional expressions)
            else_type = self.infer_node(node.else_body[-1])
            branch_types.append(else_type)

            # Save branch environment for later merging
            branch_envs.append(self.type_env)

            # Restore original environment
            self.type_env = saved_env

        # Merge all branch environments back into the main environment
        # Start with the environment before branches
        merged_env = env_before_branches.copy()

        # Merge each branch environment
        for branch_env in branch_envs:
            merged_env = merged_env.merge(branch_env)

        # Update the main environment with merged results
        self.type_env = merged_env

        # Calculate return type for conditional expressions
        # If no branches (shouldn't happen), return Any
        if not branch_types:
            return {}

        # If all types are the same, return that type (no union needed)
        first_type = branch_types[0]
        if all(t == first_type for t in branch_types):
            return first_type

        # Different types - create union type with unique types
        unique_types = []
        for branch_type in branch_types:
            if branch_type not in unique_types:
                unique_types.append(branch_type)

        return {"oneOf": unique_types}

    def _infer_while_loop(self, node: WhileLoopNode) -> dict[str, Any]:
        """Infer types for a while loop.

        Args:
            node: WhileLoopNode containing condition and body

        Returns:
            JSON Schema (while loops don't return values, returns {})
        """
        # Infer condition type (for completeness, though we don't use it)
        self.infer_node(node.condition)

        # Process loop body to infer variable types
        # Single-pass conservative inference - process body once
        for statement in node.body:
            self.infer_node(statement)

        # While loops don't have return values
        return {}

    def _infer_try_catch(self, node: TryCatchNode) -> dict[str, Any]:
        """Infer types for a try/catch/finally block.

        Args:
            node: TryCatchNode containing try_body, catch_clauses, and optional finally_body

        Returns:
            JSON Schema (try/catch blocks don't return values, returns {})
        """
        # Process try block
        for statement in node.try_body:
            self.infer_node(statement)

        # Process each catch clause
        for catch_clause in node.catch_clauses:
            # Register exception variable as string type (error messages are strings)
            # Note: In reality, exceptions could be any type, but for simplicity we use string
            self.type_env.set_type(catch_clause.exception_var, {"type": "string"})

            # Process catch body
            for statement in catch_clause.body:
                self.infer_node(statement)

        # Process finally block if present
        if node.finally_body:
            for statement in node.finally_body:
                self.infer_node(statement)

        # Try/catch blocks don't have return values
        return {}

    def _infer_return(self, node: ReturnNode) -> dict[str, Any]:
        """Infer type for a return statement.

        Args:
            node: ReturnNode containing optional return value

        Returns:
            JSON Schema for the return value type
        """
        # Bare return (no value) returns null
        if node.expression is None:
            return_type = {"type": "null"}
        else:
            # Return with value - infer the expression type
            return_type = self.infer_node(node.expression)

        # Track return type for aggregation
        self.return_types.append(return_type)

        return return_type

    def _infer_interpolation(self, node: InterpolationNode) -> dict[str, Any]:
        """Infer type for string interpolation.

        String interpolation (e.g., "Hello ${name}") always produces a string,
        regardless of the types of interpolated variables. However, we still
        infer the types of all interpolated expressions for:
        1. Type validation (if check_types=True)
        2. Tracking variable usage in type environment

        Args:
            node: InterpolationNode containing template and variable expressions

        Returns:
            JSON Schema for string type (always {"type": "string"})
        """
        # Infer types of all interpolated variables/expressions
        # This ensures:
        # - Variables are tracked in type environment
        # - Type checking validates the expressions (if enabled)
        # - Proper error messages if variables are undefined
        for var_node in node.variables:
            self.infer_node(var_node)

        # String interpolation always produces a string
        return {"type": "string"}

    def _infer_indexed_assign(self, node: IndexedAssignNode) -> dict[str, Any]:
        """Infer type for indexed assignment (e.g., dict[key] = value, list[0] = value).

        Infers the container and index sub-expressions individually, then
        the value.  Does NOT call ``infer_node(node.target)`` because that
        would route through ``_infer_indexed_access`` and trigger
        strict_input field-exists validation on what is actually a *write*.

        Args:
            node: IndexedAssignNode containing target (indexed access) and value

        Returns:
            Empty dict (indexed assignment doesn't produce a value)
        """
        # Infer sub-expressions individually — avoid _infer_indexed_access
        # which would trigger strict_input field-exists validation (issue #13).
        if isinstance(node.target, IndexedAccessNode):
            self.infer_node(node.target.object_node)
            self.infer_node(node.target.index_node)
        self.infer_node(node.value)

        # Note: Updating dict/list element types would require tracking
        # container element types in the type environment, which is complex.
        # For now, we just validate that the expressions are well-typed.

        # TODO (future): Track element type updates in containers
        # e.g., if dict: {"type": "object"} then after dict["key"] = "value",
        #       update properties: {"key": {"type": "string"}}

        # Indexed assignment doesn't produce a value (it's a statement)
        return {}

    def _infer_field_assign(self, node: FieldAssignNode) -> dict[str, Any]:
        """Infer type for field assignment (e.g., obj.field = value).

        Field assignment modifies an object in place.
        We infer the *object* sub-expression (to validate it exists) and
        the *value*, but skip the full target inference — ``_infer_field_access``
        would incorrectly flag a missing field in strict_input mode, even
        though the field is being *written*, not read.

        Args:
            node: FieldAssignNode containing target (field access) and value

        Returns:
            Empty dict (field assignment doesn't produce a value)
        """
        # Infer only the object being written to — avoid _infer_field_access
        # which would validate the field exists (wrong for writes).
        if isinstance(node.target, FieldAccessNode):
            self.infer_node(node.target.object_node)
        self.infer_node(node.value)
        return {}

    def _infer_list_comprehension(self, node: ListComprehensionNode) -> dict[str, Any]:
        """Infer type for list comprehension.

        Syntax: [element_expr for(iterator_var in iterable_expr)]
                [element_expr for(iterator_var in iterable_expr) if(filter_expr)]

        Sets the iterator variable type from the iterable's element type,
        then infers the element expression to determine the result array's
        item type.

        Args:
            node: ListComprehensionNode

        Returns:
            JSON Schema ``{"type": "array", "items": <element_type>}``
        """
        # Save any prior binding BEFORE evaluating the iterable expression.
        # A nested comprehension inside iterable_expr could leak a binding for
        # the same iterator variable name, corrupting the snapshot.
        prev_type = self.type_env.get_type(node.iterator_var)

        # Infer iterable type and extract element type for the iterator var
        iterable_type = self.infer_node(node.iterable_expr)
        element_type: dict[str, Any] = {}
        if iterable_type.get("type") == "array" and "items" in iterable_type:
            element_type = iterable_type["items"]

        # Bind iterator variable so element_expr inference can use it
        self.type_env.set_type(node.iterator_var, element_type)

        # Infer filter expression if present (validates well-typedness)
        if node.filter_expr is not None:
            self.infer_node(node.filter_expr)

        # Infer element expression type — this becomes the output array's item type
        item_type = self.infer_node(node.element_expr)

        # Restore prior binding (or remove if there was none)
        if prev_type is not None:
            self.type_env.set_type(node.iterator_var, prev_type)
        else:
            # Iterator var didn't exist before — keep it bound (matches runtime
            # semantics where the iterator variable leaks into outer scope).
            pass

        return {"type": "array", "items": item_type}

    def get_aggregated_return_type(self) -> dict[str, Any]:
        """Get aggregated type from all return statements.

        Aggregates all return types encountered during inference.
        Creates union type if multiple different types are returned.

        Returns:
            JSON Schema representing all possible return types:
            - {} if no returns
            - Single type if all returns are same type
            - {"oneOf": [...]} if multiple different types

        Examples:
            >>> # Script with single return type
            >>> engine.return_types = [{"type": "number"}, {"type": "number"}]
            >>> engine.get_aggregated_return_type()
            {"type": "number"}

            >>> # Script with multiple return types
            >>> engine.return_types = [{"type": "number"}, {"type": "string"}]
            >>> engine.get_aggregated_return_type()
            {"oneOf": [{"type": "number"}, {"type": "string"}]}
        """
        # No returns - return empty schema
        if not self.return_types:
            return {}

        # Single return type
        if len(self.return_types) == 1:
            return self.return_types[0]

        # Multiple returns - check if all same type
        first_type = self.return_types[0]
        if all(t == first_type for t in self.return_types):
            return first_type

        # Different types - create union with unique types
        unique_types: list[dict[str, Any]] = []
        for return_type in self.return_types:
            if return_type not in unique_types:
                unique_types.append(return_type)

        return {"oneOf": unique_types}

    # Type validation helper methods

    def _get_non_null_type(self, type_schema: dict[str, Any]) -> dict[str, Any] | None:
        """Extract non-null type from a type schema.

        Args:
            type_schema: JSON Schema that may be null or union with null

        Returns:
            Non-null type if exists, None if type is always null
        """
        if not type_schema:
            return None

        # Simple null type
        if type_schema.get("type") == "null":
            return None

        # Union type - extract non-null variant
        if "oneOf" in type_schema:
            non_null_variants = [
                v for v in type_schema["oneOf"] if v.get("type") != "null"
            ]
            if len(non_null_variants) == 1:
                return cast("dict[str, Any]", non_null_variants[0])
            if len(non_null_variants) > 1:
                # Multiple non-null types - return the union without null
                return {"oneOf": non_null_variants}
            return None  # All variants are null

        # Non-null simple type
        return type_schema

    def _are_types_compatible_for_coalesce(
        self, left_type: dict[str, Any], right_type: dict[str, Any]
    ) -> bool:
        """Check if two types are compatible for null-coalescing.

        Args:
            left_type: Non-null type from left operand
            right_type: Non-null type from right operand

        Returns:
            True if types are compatible, False otherwise
        """
        # Any type is compatible with anything
        if self._is_any_type(left_type) or self._is_any_type(right_type):
            return True

        left_t = left_type.get("type")
        right_t = right_type.get("type")

        # Same basic types are compatible
        if left_t == right_t:
            return True

        # Integer and number are compatible (integer is subtype of number)
        return (left_t == "integer" and right_t == "number") or (
            left_t == "number" and right_t == "integer"
        )

    def type_to_string(self, type_schema: dict[str, Any]) -> str:
        """Convert a type schema to a readable string.

        Args:
            type_schema: JSON Schema to convert

        Returns:
            Human-readable type description
        """
        if not type_schema:
            return "Any"

        if "oneOf" in type_schema:
            variants = [self.type_to_string(v) for v in type_schema["oneOf"]]
            return f"({' | '.join(variants)})"

        type_name = type_schema.get("type", "Any")
        if type_name == "object" and "properties" in type_schema:
            props = list(type_schema["properties"].keys())[:3]
            if len(props) < len(type_schema["properties"]):
                props.append("...")
            return f"object{{{', '.join(props)}}}"

        return cast(str, type_name)

    def _is_type_compatible(
        self, actual_type: dict[str, Any], expected_type: dict[str, Any]
    ) -> bool:
        """Check if actual_type is compatible with expected_type for tool parameters.

        Handles union types (oneOf) produced when a variable is assigned different
        object structures in if/else branches. When all non-null variants of a union
        share the same base type as expected, the union is compatible.

        Args:
            actual_type: Inferred type of the argument expression
            expected_type: Expected type from the tool parameter signature

        Returns:
            True if actual_type is compatible with expected_type
        """
        # Any type is compatible with everything
        if self._is_any_type(expected_type) or self._is_any_type(actual_type):
            return True

        # Exact match
        if actual_type == expected_type:
            return True

        # Same base type (e.g., both "object", both "string")
        actual_base = actual_type.get("type")
        expected_base = expected_type.get("type")
        if actual_base is not None and actual_base == expected_base:
            return True

        # Handle union types (oneOf) in actual: produced when if/else branches
        # assign objects with different property schemas (e.g., {"a":1} and {"b":2}).
        # Nullable unions (containing null) require ?? unwrapping first → not compatible.
        # Non-nullable unions are compatible only if ALL variants match the expected type.
        if "oneOf" in actual_type:
            has_null = any(v.get("type") == "null" for v in actual_type["oneOf"])
            if has_null:
                # Nullable type — caller must use ?? to unwrap null first
                return False
            return all(
                self._is_type_compatible(v, expected_type) for v in actual_type["oneOf"]
            )

        return False

    def _is_any_type(self, type_schema: dict[str, Any]) -> bool:
        """Check if a type schema represents Any type ({} or no type field).

        Args:
            type_schema: JSON Schema to check

        Returns:
            True if schema is Any type, False otherwise
        """
        # Empty schema is Any
        if not type_schema:
            return True

        # Union types (oneOf) are not Any
        if "oneOf" in type_schema:
            return False

        # Schema without type field is Any (unless it's a union)
        return "type" not in type_schema

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

        Nullable Any types should bypass strict null checking since
        Any type can handle any operation.

        Args:
            type_schema: Type schema to check

        Returns:
            True if type is a union of Any ({}) and null
        """
        # Not a union - cannot be nullable Any
        if "oneOf" not in type_schema:
            return False

        # Check if union contains both {} (Any) and null
        variants = type_schema["oneOf"]
        has_any = any(self._is_any_type(v) for v in variants)
        has_null = any(v.get("type") == "null" for v in variants)

        return has_any and has_null

    def _types_compatible(self, type1: dict[str, Any], type2: dict[str, Any]) -> bool:
        """Check if two types are compatible (same base type).

        Used for null coalescing operator validation - both sides must have
        compatible types so the union makes sense.

        Args:
            type1: First type schema
            type2: Second type schema

        Returns:
            True if types are compatible (same base type or both objects/arrays)
        """
        # Extract base types
        t1 = type1.get("type")
        t2 = type2.get("type")

        # Same base type - compatible
        if t1 == t2:
            return True

        # Both are objects - compatible (structural typing)
        if t1 == "object" and t2 == "object":
            return True

        # Both are arrays - compatible
        return t1 == "array" and t2 == "array"

    def _remove_null_from_type(self, type_schema: dict[str, Any]) -> dict[str, Any]:
        """Remove null variant from a type schema.

        If the type is a union containing null, return the union without null.
        If the type is just null, return null.
        Otherwise, return the type as-is.

        Args:
            type_schema: Type schema to process

        Returns:
            Type schema without null variant
        """
        # Not a union - return as-is
        if "oneOf" not in type_schema:
            return type_schema

        # Filter out null variants
        non_null_variants = [v for v in type_schema["oneOf"] if v.get("type") != "null"]

        # If no variants left after removing null, return null type
        if not non_null_variants:
            return {"type": "null"}

        # If only one variant left, unwrap the union
        if len(non_null_variants) == 1:
            return cast("dict[str, Any]", non_null_variants[0])

        # Multiple non-null variants - return as union
        return {"oneOf": non_null_variants}

    def _is_compatible(
        self,
        left_type: dict[str, Any],
        right_type: dict[str, Any],
        operation: str,
        _depth: int = 0,
    ) -> bool:
        """Check if two types are compatible for a given operation.

        For arithmetic/comparison operations, reject nullable types.
        Require explicit null handling with ?? operator before operations.

        Args:
            left_type: JSON Schema for left operand
            right_type: JSON Schema for right operand
            operation: Operation name (e.g., "add", "subtract", "compare")
            _depth: Internal parameter to prevent infinite recursion

        Returns:
            True if types are compatible, False otherwise
        """
        # Prevent infinite recursion
        if _depth > 5:
            return False

        # Any type is compatible with everything
        if self._is_any_type(left_type) or self._is_any_type(right_type):
            return True

        # Handle nullable Any types (Any | null union) - allow operations
        # This preserves Any semantics as an escape hatch from type checking
        # Must be checked BEFORE rejecting all nullable types
        if self._is_nullable_any_type(left_type) or self._is_nullable_any_type(
            right_type
        ):
            return True

        # Reject nullable types in arithmetic/comparison operations
        # This forces explicit null handling with ?? operator for typed nullables (e.g., string|null)
        if operation in [
            "add",
            "subtract",
            "multiply",
            "divide",
            "modulo",
            "compare",
        ] and (
            self._contains_null_variant(left_type)
            or self._contains_null_variant(right_type)
        ):
            return False  # Nullable types require explicit handling

        # Handle union types (oneOf) - if any variant is Any, allow operation
        # This supports safe navigation where fields return T | null unions
        for type_schema in [left_type, right_type]:
            if "oneOf" in type_schema:
                for variant in type_schema["oneOf"]:
                    if self._is_any_type(variant):
                        return True  # Union contains Any, so allow operation

        # Also check if either type is literally "unknown" (without union)
        # This handles cases where we don't have type information
        left_t = left_type.get("type")
        right_t = right_type.get("type")
        if left_t == "unknown" or right_t == "unknown":
            return True

        # Handle union types for operations
        # If either operand is a union, check if any variant is compatible
        # This supports safe navigation where fields return T | null
        if "oneOf" in left_type:
            # Check if any variant of left is compatible with right
            for variant in left_type["oneOf"]:
                if self._is_compatible(variant, right_type, operation, _depth + 1):
                    return True  # At least one variant is compatible

        if "oneOf" in right_type:
            # Check if left is compatible with any variant of right
            for variant in right_type["oneOf"]:
                if self._is_compatible(left_type, variant, operation, _depth + 1):
                    return True  # At least one variant is compatible

        # Helper: Check if both types are numeric (number or integer)
        def is_numeric(t: str | None) -> bool:
            return t in ["number", "integer"]

        # Arithmetic operations
        if operation == "add":
            # number/integer + number/integer or string + string or array + array
            return (
                (is_numeric(left_t) and is_numeric(right_t))
                or (left_t == "string" and right_t == "string")
                or (left_t == "array" and right_t == "array")
            )
        if operation in ["subtract", "multiply", "divide", "modulo"]:
            # Only number/integer - number/integer
            return is_numeric(left_t) and is_numeric(right_t)

        # Comparison operations
        if operation == "compare":
            # Must be same type (not mixing number < string)
            # But number and integer are compatible
            if is_numeric(left_t) and is_numeric(right_t):
                return True
            return left_t == right_t

        # Boolean operations
        if operation in ["and", "or"]:
            # Must both be boolean
            return left_t == "boolean" and right_t == "boolean"

        # Unknown operation - be conservative
        return False

    def _validate_arithmetic(
        self,
        node: ArithmeticNode,
        left_type: dict[str, Any],
        right_type: dict[str, Any],
    ) -> None:
        """Validate arithmetic operation types.

        Adds error to self.type_errors if validation fails.

        Args:
            node: ArithmeticNode being validated
            left_type: Inferred type of left operand
            right_type: Inferred type of right operand
        """
        if not self.check_types:
            return

        operation_name = {
            "+": "add",
            "-": "subtract",
            "*": "multiply",
            "/": "divide",
            "%": "modulo",
        }.get(node.operator, node.operator)

        if not self._is_compatible(left_type, right_type, operation_name):
            # Check if error is due to nullable types
            # Skip nullable error for nullable Any types (Any | null bypasses checking)
            left_is_nullable_any = self._is_nullable_any_type(left_type)
            right_is_nullable_any = self._is_nullable_any_type(right_type)

            if (
                self._contains_null_variant(left_type)
                or self._contains_null_variant(right_type)
            ) and not (left_is_nullable_any or right_is_nullable_any):
                # Provide helpful error message for nullable types
                error_msg = (
                    f"Line {node.line_number}: cannot {operation_name} nullable types. "
                    f"Use ?? operator for explicit null handling. "
                    f"Example: (obj.field ?? 0) {node.operator} 1"
                )
            else:
                # Original error message for type mismatches
                left_t = left_type.get("type", "unknown")
                right_t = right_type.get("type", "unknown")
                error_msg = (
                    f"Line {node.line_number}: cannot {operation_name} {left_t} and {right_t}. "
                    f"Operator '{node.operator}' requires compatible types."
                )
            self.type_errors.append(error_msg)

    def _validate_comparison(
        self,
        node: ComparisonNode,
        left_type: dict[str, Any],
        right_type: dict[str, Any],
    ) -> None:
        """Validate comparison operation types.

        Args:
            node: ComparisonNode being validated
            left_type: Inferred type of left operand
            right_type: Inferred type of right operand
        """
        if not self.check_types:
            return

        # Equality operators (== and !=) allow any types
        if node.operator in ["==", "!="]:
            return

        if node.operator == "in":
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
            type_desc = self.type_to_string(right_type)
            self.type_errors.append(
                f"Line {node.line_number}: 'in' requires a list, dictionary, "
                f"or string on the right side, got {type_desc}"
            )
            return

        # Other comparison operators require same types
        if not self._is_compatible(left_type, right_type, "compare"):
            # Check if error is due to nullable types
            # Skip nullable error for nullable Any types (Any | null bypasses checking)
            left_is_nullable_any = self._is_nullable_any_type(left_type)
            right_is_nullable_any = self._is_nullable_any_type(right_type)

            if (
                self._contains_null_variant(left_type)
                or self._contains_null_variant(right_type)
            ) and not (left_is_nullable_any or right_is_nullable_any):
                error_msg = (
                    f"Line {node.line_number}: cannot compare nullable types. "
                    f"Use ?? operator for explicit null handling. "
                    f"Example: (obj.field ?? 0) {node.operator} 5"
                )
            else:
                left_t = left_type.get("type", "unknown")
                right_t = right_type.get("type", "unknown")
                error_msg = (
                    f"Line {node.line_number}: cannot compare {left_t} with {right_t}. "
                    f"Comparison operator '{node.operator}' requires same types."
                )
            self.type_errors.append(error_msg)

    def _validate_boolean_op(
        self, node: BooleanOpNode, left_type: dict[str, Any], right_type: dict[str, Any]
    ) -> None:
        """Validate boolean operation types.

        'and'/'or' support truthy/falsy semantics for any type (like Python).
        '??' requires type compatibility between non-null types.

        Args:
            node: BooleanOpNode being validated
            left_type: Inferred type of left operand
            right_type: Inferred type of right operand
        """
        # For 'and'/'or', Python-like truthy/falsy semantics - allow any type
        if node.operator in ("and", "or"):
            return

        # For '??', allow any types - operator returns union of both types
        # The ?? operator has the semantics: if left is not null, return left, else return right
        # So the result type is a union of left's non-null type and right's type
        # No type validation needed for ??
        if node.operator == "??":
            # No validation needed - ?? accepts any combination of types
            return

    def _validate_field_access(
        self, node: FieldAccessNode, object_type: dict[str, Any]
    ) -> None:
        """Validate field access operation.

        Args:
            node: FieldAccessNode being validated
            object_type: Inferred type of object being accessed
        """
        if not self.check_types:
            return

        # Skip validation for Any type
        if self._is_any_type(object_type):
            return

        # Handle union types (oneOf)
        if "oneOf" in object_type:
            # Check each variant in the union
            non_null_variants = []
            has_null = False
            has_object = False
            object_variant = None

            for variant in object_type["oneOf"]:
                if self._is_any_type(variant):
                    return  # Any type allows field access
                if variant.get("type") == "null":
                    has_null = True
                elif variant.get("type") == "object":
                    has_object = True
                    object_variant = variant
                else:
                    non_null_variants.append(variant.get("type", "unknown"))

            # If no object variant and has non-null/non-object types, error
            if non_null_variants and not has_object:
                # Report error for the first non-null, non-object type
                obj_t = non_null_variants[0]
                error_msg = (
                    f"Line {node.line_number}: cannot access field '{node.field_name}' on {obj_t}. "
                    f"Field access requires an object."
                )
                self.type_errors.append(error_msg)
                return

            # If has object variant, continue validation with it
            if has_object and object_variant:
                object_type = object_variant
                # Fall through to regular object validation below

            # If only null variant, allow (safe navigation)
            elif has_null and not has_object and not non_null_variants:
                return

        # Allow field access on null (safe navigation)
        if object_type.get("type") == "null":
            return  # Field access on null is valid, returns null

        # Check if it's an object type
        if object_type.get("type") != "object":
            obj_t = object_type.get("type", "unknown")
            error_msg = (
                f"Line {node.line_number}: cannot access field '{node.field_name}' on {obj_t}. "
                f"Field access requires an object."
            )
            self.type_errors.append(error_msg)
            return

        # Strict input validation: Check if accessing input variable
        if self.strict_input and self._is_accessing_input(node.object_node):
            self._validate_strict_input_field(node, object_type, node.field_name)
            return

        # With safe navigation, missing fields are allowed and return null
        # We no longer error on missing fields - they will return null at runtime
        # This allows patterns like obj.missingField ?? defaultValue

        # Note: We could still warn about missing fields in strict mode,
        # but for now we allow them to support safe navigation patterns

    def _validate_indexed_access(
        self,
        node: IndexedAccessNode,
        container_type: dict[str, Any],
        index_type: dict[str, Any],
    ) -> None:
        """Validate indexed access operation.

        Args:
            node: IndexedAccessNode being validated
            container_type: Inferred type of container being indexed
            index_type: Inferred type of index expression
        """
        if not self.check_types:
            return

        # Skip validation for Any types
        if self._is_any_type(container_type) or self._is_any_type(index_type):
            return

        # Handle union types - extract non-null variants
        if "oneOf" in container_type:
            non_null_variants = [
                v for v in container_type["oneOf"] if v.get("type") != "null"
            ]
            if not non_null_variants:
                # Only null - error
                error_msg = (
                    f"Line {node.line_number}: cannot index null. "
                    f"Only arrays and objects support indexing."
                )
                self.type_errors.append(error_msg)
                return
            # Use first non-null variant for validation
            container_type = non_null_variants[0]

        container_t = container_type.get("type")
        index_t = index_type.get("type")

        # Strict input validation: Check if accessing input variable with string key
        if (
            self.strict_input
            and container_t == "object"
            and self._is_accessing_input(node.object_node)
        ):
            # For string literal keys, validate against input schema
            if isinstance(node.index_node, LiteralNode) and isinstance(
                node.index_node.value, str
            ):
                field_name = node.index_node.value
                self._validate_strict_input_field(node, container_type, field_name)
            # For nested accesses (input["a"]["b"]), check recursively
            elif isinstance(node.object_node, IndexedAccessNode):
                # Will be validated when we process the nested access
                pass

        # Array indexing requires number or integer index
        if container_t == "array":
            if index_t not in ["number", "integer"]:
                error_msg = f"Line {node.line_number}: array index must be a number, got {index_t}."
                self.type_errors.append(error_msg)

        # Object indexing requires string key
        elif container_t == "object":
            if index_t != "string":
                error_msg = f"Line {node.line_number}: object key must be a string, got {index_t}."
                self.type_errors.append(error_msg)

        # Other types cannot be indexed
        else:
            error_msg = (
                f"Line {node.line_number}: cannot index {container_t}. "
                f"Only arrays and objects support indexing."
            )
            self.type_errors.append(error_msg)

    def _is_accessing_input(self, node: ExecutionNode) -> bool:
        """Check if a node represents access to the input variable.

        Recursively checks if the base of a field/indexed access chain is the input variable.

        Args:
            node: ExecutionNode to check

        Returns:
            True if node accesses input variable, False otherwise
        """
        # Direct input variable reference
        if isinstance(node, VariableNode) and node.variable_name == "input":
            return True

        # Nested field access (e.g., input.address or input.address.city)
        if isinstance(node, FieldAccessNode):
            return self._is_accessing_input(node.object_node)

        # Nested indexed access (e.g., input["address"] or input["address"]["city"])
        if isinstance(node, IndexedAccessNode):
            return self._is_accessing_input(node.object_node)

        return False

    def _validate_strict_input_field(
        self, node: ExecutionNode, object_type: dict[str, Any], field_name: str
    ) -> None:
        """Validate that a field exists in the input schema (strict_input mode).

        Args:
            node: ExecutionNode being validated (FieldAccessNode or IndexedAccessNode)
            object_type: Inferred type of object being accessed
            field_name: Name of field being accessed
        """
        # Get properties from the schema
        properties = object_type.get("properties", {})

        # Check if field exists in properties
        if field_name not in properties:
            # Field doesn't exist - build helpful error message
            available_fields = list(properties.keys())

            if available_fields:
                available_str = ", ".join(available_fields)
                error_msg = (
                    f"Line {node.line_number}: field '{field_name}' not found in input schema. "
                    f"Available fields: {available_str}"
                )
            else:
                error_msg = (
                    f"Line {node.line_number}: field '{field_name}' not found in input schema. "
                    f"No fields available in schema."
                )

            self.type_errors.append(error_msg)

    def _validate_tool_call(self, node: ToolCallNode, signature: ToolSignature) -> None:
        """Validate tool call arguments match parameter types.

        Uses the canonical bind_arguments() to resolve positional+named args
        to parameter names, then type-checks each resolved binding.
        """
        if not self.check_types:
            return

        # Bind arguments to parameter names (the ONE algorithm)
        bound, binding_errors = bind_arguments(
            list(signature.parameters.keys()),
            {n for n, p in signature.parameters.items() if p.required},
            node.arguments,
            node.named_arguments,
        )

        for msg in binding_errors:
            self.type_errors.append(f"Line {node.line_number}: {msg}.")

        # Type-check each resolved binding
        for param_name, arg_node in bound.items():
            param_sig = signature.parameters[param_name]
            expected_type = param_sig.type_schema
            actual_type = self.infer_node(arg_node)

            if self._is_any_type(expected_type) or self._is_any_type(actual_type):
                continue

            if not self._is_type_compatible(actual_type, expected_type):
                self.type_errors.append(
                    f"Line {node.line_number}: parameter '{param_name}' expects "
                    f"{expected_type.get('type', 'unknown')}, got {actual_type.get('type', 'unknown')}."
                )
