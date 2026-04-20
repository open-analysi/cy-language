"""
Dependency analyzer for Cy execution plans.

This module analyzes execution nodes to determine dependencies and identify
opportunities for parallel execution.
"""

import logging
from typing import Any

from cy_language.execution_plan import ExecutionNode, NodeType

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes execution nodes to determine dependencies between them."""

    def __init__(
        self,
        tools: dict[str, Any] | None = None,
        debug: bool = False,
        assume_unregistered_async: bool = True,
    ):
        """Initialize the dependency analyzer.

        Args:
            tools: Available tools for analysis context
            debug: If True, enable debug logging of analysis
            assume_unregistered_async: If True, treat tools not in the registry
                as async. This is the correct default for Cy's ecosystem where
                unregistered tools are almost always MCP/integration tools
                (async HTTP calls). Set to False to require explicit registration.
        """
        self.tools = tools or {}
        self.debug = debug
        self.assume_unregistered_async = assume_unregistered_async

    def analyze_node_dependencies(
        self, nodes: list[ExecutionNode]
    ) -> dict[int, set[int]]:
        """Build a dependency graph from execution nodes.

        Analyzes reads and writes to determine which nodes depend on others.

        Args:
            nodes: List of execution nodes to analyze

        Returns:
            Dictionary mapping node index to set of indices it depends on
        """
        dependencies: dict[int, set[int]] = {i: set() for i in range(len(nodes))}

        # Track last writer for each variable (for RAW and WAW dependencies)
        last_writer: dict[str, int] = {}
        # Track all readers since last write (for WAR dependencies)
        readers_since_write: dict[str, set[int]] = {}

        for i, node in enumerate(nodes):
            # Collect reads and writes for this node
            reads = self._collect_reads(node)
            writes = self._collect_writes(node)
            if self.debug and writes:
                logger.debug(f"Node {i}: writes={writes}")

            # Handle control flow nodes - they create barriers
            if self._is_control_flow_node(node):
                # Control flow depends on all previous nodes
                if i > 0:
                    dependencies[i] = set(range(i))
                # All subsequent nodes depend on control flow
                for j in range(i + 1, len(nodes)):
                    dependencies[j].add(i)
                continue

            # RAW (Read-After-Write) dependencies
            for var in reads:
                if var in last_writer:
                    # This node reads a variable written by a previous node
                    dependencies[i].add(last_writer[var])
                # Also check if this is a base object read that depends on field writes
                for written_var in last_writer:
                    if written_var.startswith(var + ".") or written_var.startswith(
                        var + "["
                    ):
                        # Reading obj depends on writes to obj.field or obj[index]
                        dependencies[i].add(last_writer[written_var])

            # WAR (Write-After-Read) dependencies
            for var in writes:
                if var in readers_since_write:
                    # This node writes to a variable read by previous nodes
                    for reader_idx in readers_since_write[var]:
                        dependencies[i].add(reader_idx)
                # Check if writing to a field/index that was read as part of base
                for read_var in readers_since_write:
                    if var.startswith(read_var + ".") or var.startswith(read_var + "["):
                        # Writing to obj.field after reading obj
                        for reader_idx in readers_since_write[read_var]:
                            dependencies[i].add(reader_idx)

            # WAW (Write-After-Write) dependencies
            for var in writes:
                if var in last_writer:
                    # Exact same variable - definite dependency
                    dependencies[i].add(last_writer[var])
                else:
                    # Check for overlapping writes (e.g., obj vs obj.field)
                    # but NOT obj.field1 vs obj.field2 (different fields)
                    for written_var in list(last_writer.keys()):
                        if self._writes_overlap(var, written_var):
                            dependencies[i].add(last_writer[written_var])

            # Update tracking structures
            for var in reads:
                if var not in readers_since_write:
                    readers_since_write[var] = set()
                readers_since_write[var].add(i)

            for var in writes:
                last_writer[var] = i
                # Clear readers since we have a new write
                readers_since_write[var] = set()

            # Handle nodes with side effects
            if self._has_side_effects(node):
                # Side-effect nodes should maintain order with other side-effect nodes
                for j in range(i):
                    if self._has_side_effects(nodes[j]):
                        dependencies[i].add(j)

        if self.debug:
            logger.debug(f"Dependency analysis for {len(nodes)} nodes:")
            for i, deps in dependencies.items():
                if deps:
                    logger.debug(f"  Node {i} depends on: {sorted(deps)}")

        return dependencies

    def find_parallel_groups(
        self, dependencies: dict[int, set[int]]
    ) -> list[list[int]]:
        """Group nodes that can execute in parallel.

        Uses topological sort to find groups of nodes with satisfied dependencies.

        Args:
            dependencies: Dependency graph from analyze_node_dependencies

        Returns:
            List of groups, where each group contains node indices that can run in parallel
        """
        if not dependencies:
            return []

        # Create a copy of dependencies to modify
        remaining_deps = {i: deps.copy() for i, deps in dependencies.items()}
        groups = []

        # Keep processing until all nodes are grouped
        while remaining_deps:
            # Find nodes with no remaining dependencies
            ready = []
            for node_idx, deps in remaining_deps.items():
                if not deps:  # No dependencies
                    ready.append(node_idx)

            if not ready:
                # Circular dependency or error - fall back to sequential
                if self.debug:
                    logger.debug(
                        "Warning: Circular dependency detected, "
                        "falling back to sequential execution"
                    )
                # Return remaining nodes each in their own group
                for node_idx in sorted(remaining_deps.keys()):
                    groups.append([node_idx])
                break

            # Add ready nodes as a parallel group
            groups.append(sorted(ready))

            # Remove processed nodes from dependencies
            for node_idx in ready:
                del remaining_deps[node_idx]

            # Update remaining dependencies
            for node_idx in remaining_deps:
                remaining_deps[node_idx] -= set(ready)

        if self.debug:
            logger.debug(f"Parallel groups identified: {groups}")

        return groups

    def _collect_reads(self, node: ExecutionNode) -> set[str]:
        """Recursively collect all variables read by this node.

        Organized into three tiers:
        1. Leaf nodes (no recursion needed)
        2. Access nodes (need ``_get_access_path`` for path-aware tracking)
        3. Container nodes (recurse into children)

        Args:
            node: The execution node to analyze

        Returns:
            Set of variable names read by this node and its children
        """
        from cy_language.execution_plan import (
            ArithmeticNode,
            AssignNode,
            BooleanOpNode,
            ComparisonNode,
            ConditionalNode,
            DictNode,
            FieldAccessNode,
            IndexedAccessNode,
            IndexedAssignNode,
            InterpolationNode,
            ListNode,
            LiteralNode,
            ReturnNode,
            ToolCallNode,
            TryCatchNode,
            UnaryOpNode,
            VariableNode,
            WhileLoopNode,
        )

        # -- Tier 1: leaf nodes (no recursion) --
        if isinstance(node, LiteralNode):
            return set()
        if isinstance(node, VariableNode):
            return {node.variable_name}
        if isinstance(node, TryCatchNode):
            return set()  # body handled separately by caller

        # -- Tier 2: access nodes (path-aware tracking) --
        if isinstance(node, FieldAccessNode):
            reads: set[str] = set()
            base_path = self._get_access_path(node.object_node)
            if base_path:
                reads.add(f"{base_path}.{node.field_name}")
            reads.update(self._collect_reads(node.object_node))
            return reads

        if isinstance(node, IndexedAccessNode):
            reads = set()
            base_path = self._get_access_path(node.object_node)
            if base_path and isinstance(node.index_node, LiteralNode):
                reads.add(f"{base_path}[{node.index_node.value}]")
            reads.update(self._collect_reads(node.object_node))
            reads.update(self._collect_reads(node.index_node))
            return reads

        # -- Tier 3: container nodes (recurse into children) --
        if isinstance(node, ToolCallNode):
            return self._collect_child_reads(
                *node.arguments, *node.named_arguments.values()
            )
        if isinstance(node, InterpolationNode):
            return self._collect_child_reads(*node.variables)
        if isinstance(node, ListNode):
            return self._collect_child_reads(*node.elements)
        if isinstance(node, DictNode):
            reads = set()
            for key, value in node.pairs:
                reads.update(self._collect_reads(key))
                reads.update(self._collect_reads(value))
            return reads
        if isinstance(node, (ArithmeticNode, ComparisonNode)):
            return self._collect_child_reads(node.left, node.right)
        if isinstance(node, BooleanOpNode):
            return self._collect_child_reads(*node.operands)
        if isinstance(node, UnaryOpNode):
            return self._collect_reads(node.operand)
        if isinstance(node, ConditionalNode):
            reads = self._collect_reads(node.condition)
            for cond in node.elif_conditions:
                reads.update(self._collect_reads(cond))
            return reads
        if isinstance(node, WhileLoopNode):
            return self._collect_reads(node.condition)
        if isinstance(node, AssignNode):
            return self._collect_reads(node.expression)
        if isinstance(node, IndexedAssignNode):
            reads = self._collect_assignment_target_reads(node.target)
            reads.update(self._collect_reads(node.value))
            return reads
        if isinstance(node, ReturnNode):
            return self._collect_reads(node.expression) if node.expression else set()

        return set()

    def _collect_child_reads(self, *children: ExecutionNode) -> set[str]:
        """Collect reads from multiple child nodes (DRY helper)."""
        reads: set[str] = set()
        for child in children:
            reads.update(self._collect_reads(child))
        return reads

    def _collect_assignment_target_reads(self, node: ExecutionNode) -> set[str]:
        """Collect reads from assignment targets (only index expressions, not base objects).

        For assignment targets, we don't want to create read dependencies on the base object
        being assigned to, but we do need to read any index expressions.

        Examples:
        - obj.field = value -> reads nothing (field assignment doesn't read base)
        - arr[i] = value -> reads i (index expression)
        - obj[key] = value -> reads key (index expression)
        """
        from cy_language.execution_plan import (
            FieldAccessNode,
            IndexedAccessNode,
            VariableNode,
        )

        reads = set()

        if isinstance(node, FieldAccessNode):
            # Field assignment doesn't read the base object
            # obj.field = value -> no reads needed
            pass

        elif isinstance(node, IndexedAccessNode):
            # For indexed assignment, we need to read the index expression
            # but not the base object being assigned to
            # arr[i] = value -> reads i, but not arr
            reads.update(self._collect_reads(node.index_node))

        elif isinstance(node, VariableNode):
            # Simple variable assignment doesn't read anything
            # x = value -> no reads
            pass

        return reads

    def _collect_writes(self, node: ExecutionNode) -> set[str]:
        """Collect all variables written by this node.

        Args:
            node: The execution node to analyze

        Returns:
            Set of variable names written by this node
        """
        from cy_language.execution_plan import (
            AssignNode,
            FieldAccessNode,
            IndexedAccessNode,
            IndexedAssignNode,
        )

        writes = set()

        if isinstance(node, AssignNode):
            # Simple assignment writes to the variable
            writes.add(node.variable_name)

        elif isinstance(node, IndexedAssignNode):
            # Indexed assignment - track specific field/index if possible
            target = node.target

            if isinstance(target, FieldAccessNode):
                # obj.field = value - track as "obj.field"
                path = self._get_access_path(target)
                if path:
                    writes.add(path)
            elif isinstance(target, IndexedAccessNode):
                # arr[index] = value - track as "arr[index]" if index is literal
                path = self._get_access_path(target)
                if path:
                    writes.add(path)

        return writes

    def _writes_overlap(self, var1: str, var2: str) -> bool:
        """Check if two write paths overlap.

        Examples:
        - "obj" and "obj.field" -> True (writing to obj overwrites field)
        - "obj.field" and "obj" -> True (writing to obj overwrites field)
        - "obj.field1" and "obj.field2" -> False (different fields)
        - "arr[0]" and "arr[1]" -> False (different indices)
        - "arr" and "arr[0]" -> True (writing to arr overwrites element)
        """
        # Check if one is a prefix of the other
        # but with proper boundary checking (. or [)
        if var1 == var2:
            return True

        # Check if var1 is base of var2 (e.g., "obj" vs "obj.field")
        if var2.startswith(var1 + ".") or var2.startswith(var1 + "["):
            return True

        # Check if var2 is base of var1 (e.g., "obj.field" vs "obj")
        return var1.startswith(var2 + ".") or var1.startswith(var2 + "[")

    def _get_access_path(self, node: ExecutionNode) -> str | None:
        """Get the full access path for a field or index access.

        Returns path like "obj.field" or "arr[0]" for specific tracking,
        or just "obj" if we can't determine the specific field/index.
        """
        from cy_language.execution_plan import (
            FieldAccessNode,
            IndexedAccessNode,
            LiteralNode,
            VariableNode,
        )

        if isinstance(node, VariableNode):
            return node.variable_name
        if isinstance(node, FieldAccessNode):
            base_path = self._get_access_path(node.object_node)
            if base_path:
                return f"{base_path}.{node.field_name}"
        elif isinstance(node, IndexedAccessNode):
            base_path = self._get_access_path(node.object_node)
            if base_path and isinstance(node.index_node, LiteralNode):
                # Only track literal indices
                return f"{base_path}[{node.index_node.value}]"
            if base_path:
                # Non-literal index - track base only
                return base_path

        return None

    def _is_control_flow_node(self, node: ExecutionNode) -> bool:
        """Check if node is a control flow node that affects execution order.

        Args:
            node: The execution node to check

        Returns:
            True if node affects control flow
        """
        return node.node_type in [
            NodeType.CONDITIONAL,
            NodeType.WHILE_LOOP,
            NodeType.TRY_CATCH,
            NodeType.RETURN,
            NodeType.BREAK,
            NodeType.CONTINUE,
        ]

    def _has_side_effects(self, node: ExecutionNode) -> bool:
        """Check if node has side effects that prevent reordering.

        Args:
            node: The execution node to check

        Returns:
            True if node has side effects
        """
        return node.node_type == NodeType.TOOL_CALL

    def can_parallelize_nodes(
        self, node1_idx: int, node2_idx: int, dependencies: dict[int, set[int]]
    ) -> bool:
        """Check if two specific nodes can run in parallel.

        Args:
            node1_idx: Index of first node
            node2_idx: Index of second node
            dependencies: Dependency graph

        Returns:
            True if nodes can safely run in parallel
        """
        # They can run in parallel if neither depends on the other
        return (
            node2_idx not in dependencies[node1_idx]
            and node1_idx not in dependencies[node2_idx]
        )

    # ===== For-In Loop Parallelization Stubs =====

    def can_parallelize_for_in(
        self, for_node: ExecutionNode
    ) -> tuple[bool, str | None]:
        """Analyze if a for-in loop can be parallelized using async concurrency.

        In Python's async model (single-threaded event loop):
        - Multiple async operations can be started without waiting
        - Only one piece of code runs at a time (no race conditions)
        - Accumulators are safe because updates happen sequentially
        - The benefit comes from concurrent I/O waiting, not parallel computation

        Args:
            for_node: The for-in loop node (or transformed while loop) to analyze

        Returns:
            Tuple of (can_parallelize, reason_if_not)
            - True, None if loop can be parallelized
            - False, "reason" if loop cannot be parallelized
        """
        from cy_language.execution_plan import (
            BreakNode,
            ContinueNode,
            ReturnNode,
            TryCatchNode,
            WhileLoopNode,
        )

        # Non-loop nodes are considered parallelizable
        if not isinstance(for_node, WhileLoopNode):
            return True, None

        # Get loop body
        loop_body = for_node.body if hasattr(for_node, "body") else []

        # Empty body - parallelizable (no work to do)
        if not loop_body:
            return True, None

        # Check for patterns that prevent async parallelization.
        # Must be recursive — break/continue/return can appear inside
        # conditionals or try/catch within the loop body.
        from cy_language.execution_plan import ConditionalNode

        def _find_blocker(nodes: list[ExecutionNode]) -> str | None:
            for node in nodes:
                if isinstance(node, ReturnNode):
                    return "Loop contains return statement"
                if isinstance(node, BreakNode):
                    return "Loop contains break statement"
                if isinstance(node, ContinueNode):
                    return "Loop contains continue statement"
                if isinstance(node, TryCatchNode):
                    return "Loop contains try-catch blocks that may need sequential handling"
                # Recurse into conditional branches
                if isinstance(node, ConditionalNode):
                    for branch_body in [
                        node.if_body,
                        *(node.elif_bodies or []),
                        node.else_body or [],
                    ]:
                        reason = _find_blocker(branch_body)
                        if reason:
                            return reason
                # Recurse into nested loops (break/continue there is
                # scoped to the inner loop and does NOT block the outer)
                # — so we intentionally do NOT recurse into WhileLoopNode.
            return None

        blocker = _find_blocker(loop_body)
        if blocker:
            return False, blocker

        # Check if there are async operations to benefit from
        if not self._has_async_operations_in_loop(loop_body):
            # No async operations = no benefit from concurrent execution
            return False, "Loop has no async operations to parallelize"

        # Check for file/database operations that might need ordering
        if self._has_shared_resources(loop_body):
            return False, "Loop accesses shared resources (files/database)"

        # Check if async operations depend on loop-modified variables
        if self._async_depends_on_loop_state(loop_body):
            return False, "Async operations depend on loop-modified state"

        # All checks passed - safe to parallelize with async
        return True, None

    def detect_loop_dependencies(
        self, loop_body: list[ExecutionNode]
    ) -> dict[str, set[str]]:
        """Detect dependencies within a loop body.

        Args:
            loop_body: List of nodes in the loop body

        Returns:
            Dictionary of variable dependencies within the loop
        """
        dependencies: dict[str, set[str]] = {}

        for node in loop_body:
            # Get reads and writes for this node
            reads = self._collect_reads(node)
            writes = self._collect_writes(node)

            # Build dependency map
            for write_var in writes:
                if write_var not in dependencies:
                    dependencies[write_var] = set()
                # Variable depends on what it reads
                dependencies[write_var].update(reads)

        return dependencies

    def has_side_effects(self, node: ExecutionNode) -> bool:
        """Check if a node has side effects that prevent parallelization.

        Args:
            node: The node to check

        Returns:
            True if node has side effects
        """
        from cy_language.execution_plan import (
            AssignNode,
            BreakNode,
            ContinueNode,
            IndexedAssignNode,
            ReturnNode,
            ToolCallNode,
        )

        # Tool calls usually have side effects
        if isinstance(node, ToolCallNode):
            return True

        # Control flow signals affect execution order
        if isinstance(node, (ReturnNode, BreakNode, ContinueNode)):
            return True

        # Assignments can have side effects if they modify external state
        if isinstance(node, (AssignNode, IndexedAssignNode)):
            # For now, consider all assignments as having side effects
            # This is conservative but safe
            return True

        # Recursively check children
        if hasattr(node, "children"):
            for child in node.children:
                if self.has_side_effects(child):
                    return True

        return False

    def estimate_parallelization_benefit(
        self, loop_body: list[ExecutionNode], num_iterations: int
    ) -> float:
        """Estimate the performance benefit of parallelizing a loop.

        Args:
            loop_body: The loop body nodes
            num_iterations: Number of loop iterations

        Returns:
            Estimated speedup factor (1.0 = no benefit, 2.0 = 2x faster, etc.)
        """
        from cy_language.execution_plan import ToolCallNode

        if num_iterations < 2:
            return 1.0  # No benefit for single iteration

        # Count I/O operations (tool calls) vs CPU operations
        io_ops = 0
        cpu_ops = 0

        for node in loop_body:
            if isinstance(node, ToolCallNode):
                io_ops += 1
            else:
                cpu_ops += 1

        # Async I/O model: asyncio.gather runs on a single thread, so
        # the benefit comes from concurrent I/O waiting, not CPU cores.
        # All I/O operations can overlap regardless of CPU count.
        if io_ops > 0:
            io_ratio = io_ops / (io_ops + cpu_ops) if (io_ops + cpu_ops) > 0 else 0
            # With async, all num_iterations can wait concurrently on I/O.
            # The speedup scales with the number of iterations times the I/O ratio.
            potential_speedup = num_iterations * io_ratio
            return max(1.0, potential_speedup)

        # CPU-bound operations have no benefit from async concurrency
        return 1.0

    def _find_external_modifications(self, loop_body: list[ExecutionNode]) -> set[str]:
        """Find variables modified in the loop that might be external.

        NOTE: This method is deprecated for async parallelization.
        In single-threaded async, variable modifications are safe.
        Keeping for potential future multi-threaded support.

        Args:
            loop_body: The loop body nodes

        Returns:
            Empty set (async doesn't have race conditions for variables)
        """
        # In async concurrency, all variable modifications are safe
        # because only one coroutine runs at a time
        return set()

    def has_async_operations_in_expression(self, expr: ExecutionNode) -> bool:
        """Check if a single expression contains async operations.

        Thin wrapper around _has_async_operations_in_loop for checking
        a single expression tree (e.g., list comprehension element_expr).
        """
        return self._has_async_operations_in_loop([expr])

    def _has_async_operations_in_loop(self, loop_body: list[ExecutionNode]) -> bool:
        """Check if loop contains async operations that benefit from parallelization.

        Args:
            loop_body: The loop body nodes

        Returns:
            True if loop has async operations (tool calls, etc.)
        """
        import inspect

        from cy_language.execution_plan import (
            AssignNode,
            ConditionalNode,
            IndexedAssignNode,
            ToolCallNode,
        )

        if self.debug:
            logger.debug(
                f"[DEBUG] Checking {len(loop_body)} nodes for async operations"
            )
            for i, node in enumerate(loop_body):
                logger.debug(f"[DEBUG]   Node {i}: {type(node).__name__}")

        def check_node_recursive(node: ExecutionNode) -> bool:
            """Recursively check a node and all its children for async operations."""
            if node is None:
                return False

            if self.debug:
                logger.debug(
                    f"[DEBUG] Recursively checking node: {type(node).__name__}"
                )

            # Check if this is a tool call
            if isinstance(node, ToolCallNode) and hasattr(node, "tool_name"):
                tool_name = node.tool_name
                # Use original_name for tool lookups since tool_name may be FQN
                lookup_name = getattr(node, "original_name", tool_name)

                if self.debug:
                    logger.debug(
                        f"[DEBUG] Found ToolCallNode with tool_name: {tool_name}"
                    )
                    logger.debug(f"[DEBUG] Lookup name: {lookup_name}")
                    logger.debug(
                        f"[DEBUG] Tool in registry: {lookup_name in self.tools}"
                    )

                # Only trust inspect.iscoroutinefunction — no heuristic name matching
                if lookup_name in self.tools:
                    tool = self.tools[lookup_name]
                    is_async = inspect.iscoroutinefunction(tool)
                    if self.debug:
                        logger.debug(f"[DEBUG] Tool {lookup_name} is async: {is_async}")
                    if is_async:
                        return True
                else:
                    # Tool not in local registry (e.g., MCP/integration tool).
                    # These are almost always async HTTP calls.
                    if self.assume_unregistered_async:
                        if self.debug:
                            logger.debug(
                                f"[DEBUG] Tool {lookup_name} not in registry, "
                                f"assuming async"
                            )
                        return True

            # Check assignment values recursively
            if isinstance(node, AssignNode):
                if hasattr(node, "value") and check_node_recursive(node.value):
                    return True
                if hasattr(node, "expression") and check_node_recursive(
                    node.expression
                ):
                    return True

            # Check indexed assignment values recursively (e.g., ioc["result"] = task_run(...))
            if (
                isinstance(node, IndexedAssignNode)
                and hasattr(node, "value")
                and check_node_recursive(node.value)
            ):
                return True

            # Check conditional branches recursively
            if isinstance(node, ConditionalNode):
                if self.debug:
                    logger.debug("[DEBUG] Checking ConditionalNode branches")
                    if hasattr(node, "if_body") and node.if_body:
                        logger.debug(f"[DEBUG]   If body has {len(node.if_body)} nodes")
                    if hasattr(node, "elif_bodies") and node.elif_bodies:
                        logger.debug(f"[DEBUG]   Elif bodies: {len(node.elif_bodies)}")
                    if hasattr(node, "else_body") and node.else_body:
                        logger.debug(
                            f"[DEBUG]   Else body has {len(node.else_body)} nodes"
                        )

                # Check if branch
                if hasattr(node, "if_body") and node.if_body:
                    for if_node in node.if_body:
                        if check_node_recursive(if_node):
                            return True

                # Check elif branches
                if hasattr(node, "elif_bodies") and node.elif_bodies:
                    # elif_bodies is a list of bodies, elif_conditions is a list of conditions
                    for elif_body in node.elif_bodies:
                        for elif_node in elif_body:
                            if check_node_recursive(elif_node):
                                return True

                # Check else branch
                if hasattr(node, "else_body") and node.else_body:
                    for else_node in node.else_body:
                        if check_node_recursive(else_node):
                            return True

            # Check other composite nodes (you can add more node types here)
            # For example: WhileLoopNode, TryCatchNode, etc.

            return False

        # Check each node in the loop body recursively
        return any(check_node_recursive(node) for node in loop_body)

    def _has_shared_resources(self, loop_body: list[ExecutionNode]) -> bool:
        """Check if loop accesses shared resources that need ordering.

        Only file I/O and database operations need ordering.
        Regular API calls (fetch, get, etc.) are safe to parallelize.

        Uses word-boundary matching: the tool name is split into segments
        (on underscores) and each segment is checked against unsafe patterns.
        This avoids false positives like 'query_virustotal' matching 'query'
        when the tool is a safe read-only API call.

        Args:
            loop_body: The loop body nodes

        Returns:
            True if loop accesses shared resources that need ordering
        """
        from cy_language.execution_plan import ToolCallNode

        # Compound patterns that indicate genuinely unsafe operations.
        # Each pattern is a tuple of words that must ALL appear as segments
        # in the tool name for a match.
        UNSAFE_COMPOUND_PATTERNS = [
            ("file", "write"),
            ("file", "save"),
            ("file", "append"),
            ("file", "delete"),
            ("db", "write"),
            ("db", "insert"),
            ("db", "delete"),
            ("db", "update"),
            ("db", "query"),
            ("sql", "query"),
            ("sql", "insert"),
            ("sql", "delete"),
            ("sql", "update"),
            ("database",),
            ("transaction",),
            ("commit",),
            ("rollback",),
            ("lock",),
            ("mutex",),
            ("semaphore",),
        ]

        for node in loop_body:
            if isinstance(node, ToolCallNode) and hasattr(node, "tool_name"):
                # Split on both _ and :: to handle FQN names like
                # native::tools::file_write or app::db::query
                import re

                segments = set(re.split(r"_|::", node.tool_name.lower()))
                segments.discard("")  # Remove empty segments from leading ::
                for pattern in UNSAFE_COMPOUND_PATTERNS:
                    if all(word in segments for word in pattern):
                        return True
        return False

    def _async_depends_on_loop_state(self, loop_body: list[ExecutionNode]) -> bool:
        """Check if async operations depend on cross-iteration state (including transitive).

        We need to detect patterns where async operations use values that
        accumulate or carry over between iterations, including transitive dependencies.

        Safe patterns (can parallelize):
        - temp = await fetch(item); result = await process(temp)
          (temp is local to each iteration)

        Unsafe patterns (must run sequentially):
        - sum = sum + item; result = await process(sum)
          (sum carries state across iterations)
        - sum = sum + item; a = sum * 2; result = await process(a)
          (a transitively depends on sum which is cross-iteration)

        Args:
            loop_body: The loop body nodes

        Returns:
            True if async operations depend on cross-iteration state
        """
        from cy_language.execution_plan import ArithmeticNode, AssignNode, ToolCallNode

        # Step 1: Identify variables that carry state across iterations
        cross_iteration_vars = set()

        # First, collect all variables that are read and written in the loop
        variables_read = set()
        variables_written = set()
        read_before_write: dict[
            str, tuple[int | None, int | None]
        ] = {}  # Track order: var -> (first_read_idx, first_write_idx)

        for idx, node in enumerate(loop_body):
            # Collect reads from this node
            node_reads = self._collect_reads(node)
            for var in node_reads:
                if var not in read_before_write:
                    read_before_write[var] = (idx, None)  # First read at this index
                variables_read.add(var)

            # Check if this node writes a variable
            if isinstance(node, AssignNode) and hasattr(node, "variable_name"):
                var_name = node.variable_name

                # Update write index if this is the first write
                if (
                    var_name in read_before_write
                    and read_before_write[var_name][1] is None
                ):
                    read_before_write[var_name] = (read_before_write[var_name][0], idx)
                elif var_name not in read_before_write:
                    read_before_write[var_name] = (
                        None,
                        idx,
                    )  # Written but not read yet

                variables_written.add(var_name)

                # Skip loop index variables (they're expected to increment)
                if var_name.startswith("__for_idx_"):
                    continue

                # Check both value and expression for accumulator patterns
                value_to_check = getattr(
                    node, "expression", getattr(node, "value", None)
                )

                # Check if this assignment reads its own variable (accumulator pattern)
                # This covers both arithmetic accumulators (sum = sum + x) and
                # concatenation accumulators (results = results + [x])
                if value_to_check and isinstance(value_to_check, ArithmeticNode):
                    reads = self._collect_reads(value_to_check)
                    if var_name in reads:
                        cross_iteration_vars.add(var_name)

        # Add variables that are read before they're written (carry state from previous iteration)
        # BUT exclude:
        # 1. Loop index variables
        # 2. Variables only used in safe concatenation patterns
        # 3. Variables never written (likely loop variables or external constants)
        for var, (read_idx, write_idx) in read_before_write.items():
            if var.startswith("__for_idx_"):
                continue

            # Skip variables that are never written in the loop body
            # These are likely loop variables (item) or external constants
            if write_idx is None:
                continue

            # If variable is read before it's written, it carries state
            if read_idx is not None and read_idx < write_idx:
                # Check if this variable is only used in safe concatenation patterns
                is_safe_concat = False
                write_node = loop_body[write_idx]
                if isinstance(write_node, AssignNode):
                    value = getattr(
                        write_node, "expression", getattr(write_node, "value", None)
                    )
                    if isinstance(value, ArithmeticNode) and value.operator == "+":
                        # This is a concatenation - safe for async
                        is_safe_concat = True

                if not is_safe_concat:
                    cross_iteration_vars.add(var)

        # Step 2: Build dependency graph to find transitive dependencies
        dependencies = {}  # var -> set of vars it depends on

        for node in loop_body:
            if isinstance(node, AssignNode) and hasattr(node, "variable_name"):
                var_name = node.variable_name

                # Skip loop index variables
                if var_name.startswith("__for_idx_"):
                    continue

                # Check both value and expression
                value_to_check = getattr(
                    node, "expression", getattr(node, "value", None)
                )
                if value_to_check:
                    reads = self._collect_reads(value_to_check)
                    # Filter out loop index variables from reads too
                    filtered_reads = {
                        r for r in reads if not r.startswith("__for_idx_")
                    }
                    dependencies[var_name] = filtered_reads

        # Step 3: Find all variables that transitively depend on cross-iteration vars
        tainted_vars = cross_iteration_vars.copy()
        changed = True

        while changed:
            changed = False
            for var, deps in dependencies.items():
                if var not in tainted_vars and deps.intersection(tainted_vars):
                    # This variable depends on a tainted variable
                    tainted_vars.add(var)
                    changed = True

        # Step 4: Check if any async operations use tainted variables
        for node in loop_body:
            # Check both direct ToolCallNodes and those inside assignments
            nodes_to_check = []

            if isinstance(node, ToolCallNode):
                nodes_to_check.append(node)
            elif isinstance(node, AssignNode):
                # Check both value and expression for tool calls
                if hasattr(node, "value") and isinstance(node.value, ToolCallNode):
                    nodes_to_check.append(node.value)
                if hasattr(node, "expression") and isinstance(
                    node.expression, ToolCallNode
                ):
                    nodes_to_check.append(node.expression)

            for tool_node in nodes_to_check:
                # Collect all variables read by the async operation
                async_reads = self._collect_reads(tool_node)

                # If async reads any tainted variables, it must run sequentially
                if async_reads.intersection(tainted_vars):
                    return True

        return False
