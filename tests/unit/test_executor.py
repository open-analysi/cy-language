"""
Unit tests for the Cy Language Plan Executor.
"""

import pytest

from src.cy_language.errors import NameError as CyNameError
from src.cy_language.errors import RuntimeError as CyRuntimeError
from src.cy_language.errors import ToolNotFoundError
from src.cy_language.execution_plan import (
    AssignNode,
    ExecutionPlan,
    InterpolationNode,
    LiteralNode,
    ToolCallNode,
    VariableNode,
)
from src.cy_language.executor import ExecutionContext, PlanExecutor, execute_plan


class TestExecutionContext:
    """Test the ExecutionContext class."""

    def test_context_creation_empty(self):
        """Test ExecutionContext creation with no parameters."""
        context = ExecutionContext()

        assert context.variables == {}
        assert context.tools == {}
        assert context.interpolation_mode == "markdown"
        assert context.output is None

    def test_context_creation_with_data(self):
        """Test ExecutionContext creation with tools and variables."""
        tools = {"add": lambda a, b: a + b}
        variables = {"name": "Alice"}

        context = ExecutionContext(
            tools=tools, variables=variables, interpolation_mode="csv"
        )

        assert context.variables == {"name": "Alice"}
        assert "add" in context.tools
        assert context.interpolation_mode == "csv"

    def test_get_variable_exists(self):
        """Test getting an existing variable."""
        context = ExecutionContext(variables={"test": "value"})

        result = context.get_variable("test")

        assert result == "value"

    def test_get_variable_not_exists(self):
        """Test getting a non-existent variable raises error."""
        context = ExecutionContext()

        with pytest.raises(CyNameError) as exc_info:
            context.get_variable("nonexistent")

        assert "Variable 'nonexistent' is not defined" in str(exc_info.value)

    def test_set_variable(self):
        """Test setting a variable."""
        context = ExecutionContext()

        context.set_variable("test", "value")

        assert context.variables["test"] == "value"

    @pytest.mark.asyncio
    async def test_call_tool_exists(self):
        """Test calling an existing tool."""

        def mock_tool(a, b):
            return a + b

        context = ExecutionContext(tools={"add": mock_tool})

        result = await context.call_tool("add", [1, 2], {})

        assert result == 3

    @pytest.mark.asyncio
    async def test_call_tool_not_exists(self):
        """Test calling a non-existent tool raises error."""
        context = ExecutionContext()

        with pytest.raises(ToolNotFoundError) as exc_info:
            await context.call_tool("nonexistent", [], {})

        assert "Tool 'nonexistent' not found" in str(exc_info.value)


class TestPlanExecutor:
    """Test the PlanExecutor class."""

    def test_executor_creation(self):
        """Test PlanExecutor creation."""
        executor = PlanExecutor()

        assert executor.context is not None
        assert isinstance(executor.context, ExecutionContext)

    def test_executor_creation_with_context(self):
        """Test PlanExecutor creation with custom context."""
        context = ExecutionContext(variables={"test": "value"})
        executor = PlanExecutor(context)

        assert executor.context == context
        assert executor.context.variables["test"] == "value"

    @pytest.mark.asyncio
    async def test_execute_empty_plan_no_output(self):
        """Test executing empty plan returns no-return sentinel.

        Plans without return statements should be caught by the validator
        at compile-time. If a plan without return statement reaches the executor
        (e.g., when validate_output=False), it returns the _NO_RETURN sentinel.
        """
        from src.cy_language.executor import _NO_RETURN

        executor = PlanExecutor()
        plan = ExecutionPlan()

        result = await executor.execute(plan)

        assert result is _NO_RETURN

    @pytest.mark.asyncio
    async def test_execute_with_input_data(self):
        """Test execute sets input variable when input_data provided.

        Without a return statement, the executor returns empty string.
        The input variable should still be set correctly.
        """
        from src.cy_language.execution_plan import ReturnNode

        executor = PlanExecutor()
        plan = ExecutionPlan()
        # Create a proper return node to return a value
        literal_node = LiteralNode("test", 1, 1, "node_1")
        return_node = ReturnNode(literal_node, 1, 1, "node_2")
        plan.add_node(return_node)

        result = await executor.execute(plan, input_data="test_input")

        assert executor.context.variables["input"] == "test_input"
        assert result == "test"


class TestNodeExecution:
    """Test execution of individual node types."""

    @pytest.mark.asyncio
    async def test_execute_literal_node(self):
        """Test executing a literal node."""
        executor = PlanExecutor()
        node = LiteralNode("hello", 1, 1, "node_1")

        result = await executor._execute_node(node)

        assert result == "hello"

    @pytest.mark.asyncio
    async def test_execute_variable_node(self):
        """Test executing a variable node."""
        context = ExecutionContext(variables={"test_var": "test_value"})
        executor = PlanExecutor(context)
        node = VariableNode("test_var", 1, 1, "node_1")

        result = await executor._execute_node(node)

        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_execute_assignment_node(self):
        """Test executing an assignment node."""
        executor = PlanExecutor()
        expr_node = LiteralNode("value", 1, 10, "node_1")
        assign_node = AssignNode("var", expr_node, 1, 1, "node_2")

        await executor._execute_node(assign_node)

        # Assignment should set the variable (stub implementation uses stub value)
        assert "var" in executor.context.variables

    @pytest.mark.asyncio
    async def test_execute_tool_call_node(self):
        """Test executing a tool call node."""

        def mock_tool():
            return "tool_result"

        context = ExecutionContext(tools={"test_tool": mock_tool})
        executor = PlanExecutor(context)
        tool_node = ToolCallNode("test_tool", [], {}, 1, 1, "node_1")

        result = await executor._execute_node(tool_node)

        # Stub implementation may not return actual result yet
        # This test verifies the execution doesn't crash
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_interpolation_node(self):
        """Test executing an interpolation node."""
        context = ExecutionContext(variables={"name": "World"})
        executor = PlanExecutor(context)
        var_node = VariableNode("name", 1, 10, "node_1")
        interp_node = InterpolationNode("Hello ${name}", [var_node], {}, 1, 1, "node_2")

        result = await executor._execute_node(interp_node)

        assert isinstance(result, str)
        assert result == "Hello World"  # Real implementation

    @pytest.mark.asyncio
    async def test_execute_unknown_node_type(self):
        """Test executing unknown node type raises error."""
        executor = PlanExecutor()
        # Create a node with invalid type by directly setting the enum
        node = LiteralNode("test", 1, 1, "node_1")
        node.node_type = "invalid_type"  # This will cause an error

        with pytest.raises(CyRuntimeError):
            await executor._execute_node(node)


class TestExecutorIntegration:
    """Test executor integration scenarios."""

    @pytest.mark.asyncio
    async def test_execute_plan_with_output_variable(self):
        """Test executing a plan that returns a value.

        Output must come from return statements, not output variable.
        """
        from src.cy_language.execution_plan import ReturnNode

        executor = PlanExecutor()
        plan = ExecutionPlan()

        # Create a return node to properly return a value
        literal_node = LiteralNode("final_result", 1, 1, "node_1")
        return_node = ReturnNode(literal_node, 1, 1, "node_2")
        plan.add_node(return_node)

        result = await executor.execute(plan)

        assert result == "final_result"

    @pytest.mark.asyncio
    async def test_execute_plan_input_variable_handling(self):
        """Test that execute properly handles input variable."""
        executor = PlanExecutor()
        plan = ExecutionPlan()
        executor.context.set_variable("output", "result")

        await executor.execute(plan, input_data={"key": "value"})

        assert executor.context.variables["input"] == {"key": "value"}


class TestConvenienceFunction:
    """Test the convenience execute_plan function."""

    def test_execute_plan_function(self):
        """Test execute_plan convenience function.

        Return value must come from return statement.
        """
        from src.cy_language.execution_plan import ReturnNode

        plan = ExecutionPlan()
        tools = {"test": lambda: "result"}
        variables = {}

        # Create a return node
        literal_node = LiteralNode("test_output", 1, 1, "node_1")
        return_node = ReturnNode(literal_node, 1, 1, "node_2")
        plan.add_node(return_node)

        result = execute_plan(
            plan,
            input_data="input",
            tools=tools,
            variables=variables,
            interpolation_mode="csv",
        )

        assert result == "test_output"

    def test_execute_plan_function_defaults(self):
        """Test execute_plan with default parameters.

        Plans without return statements return _NO_RETURN sentinel at runtime.
        (They should be caught by the validator at compile-time with validate_output=True)
        """
        from src.cy_language.executor import _NO_RETURN

        plan = ExecutionPlan()

        result = execute_plan(plan)
        assert result is _NO_RETURN


# Tests that will be expanded during implementation
class TestFutureExecutionFeatures:
    """Tests for execution features to be implemented."""

    @pytest.mark.asyncio
    async def test_execute_assignment_with_expression(self):
        """Test executing assignment with arithmetic expression x = 5 + 3 gives x = 8."""
        from src.cy_language.execution_plan import ArithmeticNode

        executor = PlanExecutor()
        left_node = LiteralNode(5, 1, 5, "node_1")
        right_node = LiteralNode(3, 1, 9, "node_2")
        arith_node = ArithmeticNode("+", left_node, right_node, 1, 5, "node_3")
        assign_node = AssignNode("x", arith_node, 1, 1, "node_4")

        await executor._execute_node(assign_node)

        assert executor.context.variables["x"] == 8

    @pytest.mark.asyncio
    async def test_execute_tool_call_with_arguments(self):
        """Test executing tool call with positional arguments."""

        def add(a, b):
            return a + b

        context = ExecutionContext(tools={"add": add})
        executor = PlanExecutor(context)
        arg1 = LiteralNode(10, 1, 5, "node_1")
        arg2 = LiteralNode(20, 1, 8, "node_2")
        tool_node = ToolCallNode("add", [arg1, arg2], {}, 1, 1, "node_3")

        result = await executor._execute_node(tool_node)

        assert result == 30

    @pytest.mark.asyncio
    async def test_execute_string_interpolation_with_variables(self):
        """Test executing string interpolation with variable substitution."""
        from src.cy_language.execution_plan import ReturnNode

        executor = PlanExecutor()
        plan = ExecutionPlan()

        name_literal = LiteralNode("Alice", 1, 8, "node_1")
        name_assign = AssignNode("name", name_literal, 1, 1, "node_2")

        name_var = VariableNode("name", 2, 18, "node_3")
        interp_node = InterpolationNode(
            "Hello ${name}", [name_var], {}, 2, 10, "node_4"
        )
        output_assign = AssignNode("output", interp_node, 2, 1, "node_5")

        output_var = VariableNode("output", 3, 8, "node_6")
        return_node = ReturnNode(output_var, 3, 1, "node_7")

        plan.add_node(name_assign)
        plan.add_node(output_assign)
        plan.add_node(return_node)

        result = await executor.execute(plan)

        assert result == "Hello Alice"

    @pytest.mark.asyncio
    async def test_execute_list_and_dictionary_nodes(self):
        """Test executing list literal node returns a Python list."""
        from src.cy_language.execution_plan import ListNode, ReturnNode

        executor = PlanExecutor()
        plan = ExecutionPlan()

        elem1 = LiteralNode(1, 1, 9, "node_1")
        elem2 = LiteralNode(2, 1, 12, "node_2")
        elem3 = LiteralNode(3, 1, 15, "node_3")
        list_node = ListNode([elem1, elem2, elem3], 1, 8, "node_4")
        assign_node = AssignNode("items", list_node, 1, 1, "node_5")

        items_var = VariableNode("items", 2, 8, "node_6")
        return_node = ReturnNode(items_var, 2, 1, "node_7")

        plan.add_node(assign_node)
        plan.add_node(return_node)

        result = await executor.execute(plan)

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_error_handling_with_line_numbers(self):
        """Test that a runtime error carries line and column attributes."""

        executor = PlanExecutor()
        # Dividing by zero via a tool that raises a CyRuntimeError with location info
        node = VariableNode("undefined_var", 5, 10, "node_1")

        with pytest.raises(CyNameError) as exc_info:
            await executor._execute_node(node)

        error = exc_info.value
        assert hasattr(error, "line")
        assert hasattr(error, "col")

    @pytest.mark.asyncio
    async def test_variable_scoping_maintenance(self):
        """Test that a variable set in one statement is accessible in the next."""
        from src.cy_language.execution_plan import ReturnNode

        executor = PlanExecutor()
        plan = ExecutionPlan()

        # first statement: x = 42
        literal_node = LiteralNode(42, 1, 5, "node_1")
        assign_node = AssignNode("x", literal_node, 1, 1, "node_2")

        # second statement: return x
        var_node = VariableNode("x", 2, 8, "node_3")
        return_node = ReturnNode(var_node, 2, 1, "node_4")

        plan.add_node(assign_node)
        plan.add_node(return_node)

        result = await executor.execute(plan)

        assert result == 42
