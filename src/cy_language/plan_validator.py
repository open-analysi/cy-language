"""Execution plan validator for Cy language.

This module validates that execution plans have proper output handling,
ensuring all code paths have a return statement.
"""

from cy_language.execution_plan import (
    ConditionalNode,
    ExecutionNode,
    ExecutionPlan,
    ReturnNode,
    TryCatchNode,
    WhileLoopNode,
)

from .errors import CompilerError


class PlanValidator:
    """Validates execution plans for correctness."""

    def __init__(self, plan: ExecutionPlan):
        """Initialize validator with an execution plan.

        Args:
            plan: The execution plan to validate
        """
        self.plan = plan

    def validate(self) -> None:
        """Validate the execution plan.

        Raises:
            CompilerError: If validation fails
        """
        self._validate_output_coverage()

    def _validate_output_coverage(self) -> None:
        """Validate that all code paths have a return statement.

        Scripts must use return statements for output.
        The $output variable is no longer supported for script output.

        Raises:
            CompilerError: If no return statement is found
        """
        # Check if there are any return statements
        has_return = self._has_return(self.plan.nodes)

        # If no return, that's an error
        if not has_return:
            raise CompilerError(
                "No return statement found in the program. "
                "All Cy scripts must use a return statement to produce output.",
                line=0,
                col=0,
            )

        # If using conditionals, validate all paths have return
        if self._has_conditionals(self.plan.nodes):
            self._validate_conditional_paths(self.plan.nodes)

    def _has_return(self, nodes: list[ExecutionNode] | None) -> bool:
        """Check if any node is a return statement.

        Args:
            nodes: List of execution nodes to check (can be None)

        Returns:
            True if any node is a return statement
        """
        if nodes is None:
            return False

        for node in nodes:
            if isinstance(node, ReturnNode):
                return True

            # Check conditional branches
            if isinstance(node, ConditionalNode):
                if self._has_return(node.if_body):
                    return True
                if self._has_return(node.else_body):
                    return True

            # Check while loop body
            if isinstance(node, WhileLoopNode) and self._has_return(node.body):
                return True

            # Check try-catch-finally blocks
            if isinstance(node, TryCatchNode):
                if self._has_return(node.try_body):
                    return True
                for catch_clause in node.catch_clauses:
                    if self._has_return(catch_clause.body):
                        return True
                if self._has_return(node.finally_body):
                    return True

        return False

    def _has_conditionals(self, nodes: list[ExecutionNode]) -> bool:
        """Check if there are any conditional nodes.

        Args:
            nodes: List of execution nodes to check

        Returns:
            True if any conditional nodes exist
        """
        return any(isinstance(node, ConditionalNode) for node in nodes)

    def _validate_conditional_paths(self, nodes: list[ExecutionNode] | None) -> None:
        """Validate that all conditional paths have return statements.

        This ensures that if a script uses conditionals, ALL branches
        have a return statement.

        Args:
            nodes: List of execution nodes to validate (can be None)

        Raises:
            CompilerError: If any conditional path lacks return statement
        """
        if nodes is None:
            return

        for node in nodes:
            if isinstance(node, ConditionalNode):
                # Check if if-branch has return
                if_has_return = self._path_has_return(node.if_body)

                # Check if else-branch has return
                else_has_return = self._path_has_return(node.else_body)

                # If one branch has return but the other doesn't, that's an error
                # UNLESS there's a fallthrough return after the conditional
                if if_has_return and not else_has_return:
                    # Check if there's a return after this conditional
                    # that would be reached by the else branch
                    after_conditional = self._nodes_after(nodes, node)
                    if not self._has_return(after_conditional):
                        raise CompilerError(
                            "Conditional branch lacks return statement. "
                            "All branches must use return to produce output.",
                            line=0,
                            col=0,
                        )

                elif else_has_return and not if_has_return:
                    # Check if there's a return after this conditional
                    after_conditional = self._nodes_after(nodes, node)
                    if not self._has_return(after_conditional):
                        raise CompilerError(
                            "Conditional branch lacks return statement. "
                            "All branches must use return to produce output.",
                            line=0,
                            col=0,
                        )

                # Recursively validate nested conditionals
                self._validate_conditional_paths(node.if_body)
                self._validate_conditional_paths(node.else_body)

    def _path_has_return(self, nodes: list[ExecutionNode] | None) -> bool:
        """Check if a code path has a return statement.

        Args:
            nodes: List of execution nodes representing a code path (can be None)

        Returns:
            True if path has a return statement
        """
        if nodes is None:
            return False
        return self._has_return(nodes)

    def _nodes_after(
        self, nodes: list[ExecutionNode], target_node: ExecutionNode
    ) -> list[ExecutionNode]:
        """Get all nodes that come after a target node.

        Args:
            nodes: List of all nodes
            target_node: The node to find

        Returns:
            List of nodes that come after target_node
        """
        try:
            index = nodes.index(target_node)
            return nodes[index + 1 :]
        except ValueError:
            return []


def validate_plan(plan: ExecutionPlan) -> None:
    """Validate an execution plan.

    This is the main entry point for plan validation.

    Args:
        plan: The execution plan to validate

    Raises:
        CompileError: If validation fails
    """
    validator = PlanValidator(plan)
    validator.validate()
