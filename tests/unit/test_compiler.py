"""
Unit tests for the Cy Language Compiler (AST to Execution Plan conversion).
"""

from lark import Token, Tree

from src.cy_language.compiler import CompilerError, PlanCompiler, compile_cy_program
from src.cy_language.execution_plan import ExecutionPlan, NodeType


class TestPlanCompiler:
    """Test the PlanCompiler class."""

    def test_compiler_creation(self):
        """Test PlanCompiler can be created."""
        compiler = PlanCompiler()
        assert compiler is not None
        assert compiler.node_counter == 0

    def test_compile_empty_ast(self):
        """Test compiling an empty AST tree."""
        compiler = PlanCompiler()
        empty_tree = Tree("start", [])

        plan = compiler.compile(empty_tree, "test.cy")

        assert isinstance(plan, ExecutionPlan)
        assert plan.source_file == "test.cy"

    def test_generate_node_id(self):
        """Test node ID generation."""
        compiler = PlanCompiler()

        id1 = compiler._generate_node_id()
        id2 = compiler._generate_node_id()

        assert id1 != id2
        assert id1 == "node_1"
        assert id2 == "node_2"

    def test_get_line_column_stub(self):
        """Test _get_line_column returns valid coordinates."""
        compiler = PlanCompiler()

        # Test with mock tree/token
        line, column = compiler._get_line_column(None)

        assert isinstance(line, int)
        assert isinstance(column, int)
        assert line >= 1
        assert column >= 1


class TestAssignmentCompilation:
    """Test compilation of assignment statements."""

    def test_compile_assignment_stub(self):
        """Test _compile_assignment creates AssignNode."""
        compiler = PlanCompiler()
        # Create proper AST structure: assignment -> VARIABLE compound_op expression
        var_token = Token("VARIABLE", "$test")
        compound_op_tree = Tree("compound_op", [])  # Empty tree for "=" literal
        expr_tree = Tree(
            "expression", [Tree("string", [Token("DOUBLE_QUOTED_STRING", '"value"')])]
        )
        mock_tree = Tree("assignment", [var_token, compound_op_tree, expr_tree])

        node = compiler._compile_assignment(mock_tree)

        assert node.node_type == NodeType.ASSIGN
        assert node.variable_name == "test"
        assert node.expression is not None
        assert node.line_number >= 1
        assert node.column >= 1
        assert node.node_id.startswith("node_")


class TestToolCallCompilation:
    """Test compilation of tool/function calls."""

    def test_compile_tool_call_stub(self):
        """Test _compile_tool_call creates ToolCallNode."""
        from lark import Token

        compiler = PlanCompiler()
        # Create proper tree structure: function_call -> IDENTIFIER
        tool_name_token = Token("IDENTIFIER", "test_tool")
        mock_tree = Tree("tool_call", [tool_name_token])

        node = compiler._compile_tool_call(mock_tree)

        assert node.node_type == NodeType.TOOL_CALL
        assert node.tool_name == "test_tool"
        assert node.arguments == []
        assert node.named_arguments == {}
        assert node.line_number >= 1
        assert node.column >= 1
        assert node.node_id.startswith("node_")


class TestStringInterpolationCompilation:
    """Test compilation of string interpolation."""

    def test_compile_string_interpolation_stub(self):
        """Test _compile_string_interpolation creates InterpolationNode."""
        compiler = PlanCompiler()
        mock_tree = Tree("interpolation", [])

        node = compiler._compile_string_interpolation(mock_tree)

        assert node.node_type == NodeType.INTERPOLATION
        assert node.template == "stub_template"
        assert node.variables == []
        assert node.printer_hints == {}
        assert node.line_number >= 1
        assert node.column >= 1
        assert node.node_id.startswith("node_")


class TestCompilerErrorHandling:
    """Test compiler error handling."""

    def test_compiler_error_creation(self):
        """Test CompilerError can be created with proper info."""
        error = CompilerError("Test message", 5, 10)

        assert error.message == "Test message"
        assert error.line == 5
        assert error.column == 10
        assert "Line 5, Column 10: Test message" in str(error)


class TestConvenienceFunction:
    """Test the convenience compile function."""

    def test_compile_cy_program_function(self):
        """Test compile_cy_program convenience function."""
        mock_tree = Tree("start", [])

        plan = compile_cy_program(mock_tree, "test.cy", validate_output=False)

        assert isinstance(plan, ExecutionPlan)
        assert plan.source_file == "test.cy"


class TestCompilerIntegration:
    """Test compiler integration scenarios."""

    def test_compile_maintains_source_file(self):
        """Test compiler maintains source file information."""
        compiler = PlanCompiler()
        mock_tree = Tree("start", [])

        plan = compiler.compile(mock_tree, "my_script.cy")

        assert plan.source_file == "my_script.cy"

    def test_compile_without_source_file(self):
        """Test compiler works without source file."""
        compiler = PlanCompiler()
        mock_tree = Tree("start", [])

        plan = compiler.compile(mock_tree)

        assert plan.source_file is None

    def test_multiple_compilations_unique_ids(self):
        """Test multiple compilations generate unique node IDs."""
        compiler = PlanCompiler()
        # Create proper AST structures with compound_op
        var_token1 = Token("VARIABLE", "$test1")
        compound_op_tree1 = Tree("compound_op", [])  # Empty tree for "=" literal
        expr_tree1 = Tree(
            "expression", [Tree("string", [Token("DOUBLE_QUOTED_STRING", '"value1"')])]
        )
        mock_tree1 = Tree("assignment", [var_token1, compound_op_tree1, expr_tree1])

        var_token2 = Token("VARIABLE", "$test2")
        compound_op_tree2 = Tree("compound_op", [])  # Empty tree for "=" literal
        expr_tree2 = Tree(
            "expression", [Tree("string", [Token("DOUBLE_QUOTED_STRING", '"value2"')])]
        )
        mock_tree2 = Tree("assignment", [var_token2, compound_op_tree2, expr_tree2])

        node1 = compiler._compile_assignment(mock_tree1)
        node2 = compiler._compile_assignment(mock_tree2)

        assert node1.node_id != node2.node_id


# Tests that will be expanded during implementation
class TestFutureCompilationFeatures:
    """Tests for compilation features to be implemented."""

    def test_simple_assignment_compilation(self):
        """Test compiling x = 'hello' to plan."""
        from cy_language.parser import Parser

        compiler = PlanCompiler()
        program = 'x = "hello"\nreturn x'
        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        assert len(plan.nodes) >= 1
        assign_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "x":
                assign_node = node
                break
        assert assign_node is not None, "Should have x assignment node"

    def test_variable_reference_compilation(self):
        """Test compiling x = 5 / y = x to plan."""
        from cy_language.parser import Parser

        compiler = PlanCompiler()
        program = "x = 5\ny = x\nreturn y"
        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        assert len(plan.nodes) >= 2
        x_node = None
        y_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "x":
                x_node = node
            if node.node_type == NodeType.ASSIGN and node.variable_name == "y":
                y_node = node
        assert x_node is not None, "Should have x assignment node"
        assert y_node is not None, "Should have y assignment node"
        assert y_node.expression.node_type == NodeType.VARIABLE

    def test_string_literal_compilation(self):
        """Test compiling string literals to plan nodes."""
        from cy_language.parser import Parser

        compiler = PlanCompiler()
        program = 'x = "hello"\nreturn x'
        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        assign_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "x":
                assign_node = node
                break
        assert assign_node is not None, "Should have x assignment node"
        assert assign_node.expression is not None
        assert assign_node.expression.node_type == NodeType.LITERAL

    def test_list_compilation(self):
        """Test compiling items = ['a', 'b', 'c'] to plan."""
        from cy_language.parser import Parser

        compiler = PlanCompiler()
        program = 'items = ["a", "b", "c"]\nreturn items'
        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        items_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "items":
                items_node = node
                break
        assert items_node is not None, "Should have items assignment node"
        assert items_node.expression.node_type == NodeType.LIST

    def test_dictionary_compilation(self):
        """Test compiling obj = {'key': 'value'} to plan."""
        from cy_language.parser import Parser

        compiler = PlanCompiler()
        program = 'obj = {"key": "value"}\nreturn obj'
        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        obj_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "obj":
                obj_node = node
                break
        assert obj_node is not None, "Should have obj assignment node"
        assert obj_node.expression.node_type == NodeType.DICT

    def test_tool_call_with_args_compilation(self):
        """Test compiling result = add(1, 2) to plan - will be implemented.

        Updated: removed $ prefix from assignment.
        """
        # This will test actual compilation rather than being a placeholder
        compiler = PlanCompiler()

        # Test a simple tool call compilation
        program = "result = add(1, 2)\noutput = result\nreturn output"
        from cy_language.parser import Parser

        parser = Parser()
        ast_tree = parser.parse_only(program)

        plan = compiler.compile(ast_tree, "<test>")

        # Should have multiple nodes: result = add(1, 2), output = result, return output
        assert len(plan.nodes) >= 1

        # The first assignment node should be result = add(1, 2)
        result_node = None
        for node in plan.nodes:
            if node.node_type == NodeType.ASSIGN and node.variable_name == "result":
                result_node = node
                break

        assert result_node is not None, "Should have result assignment node"
        assert result_node.expression.node_type == NodeType.TOOL_CALL

        tool_call_node = result_node.expression
        assert tool_call_node.tool_name == "add"
        assert len(tool_call_node.arguments) == 2
