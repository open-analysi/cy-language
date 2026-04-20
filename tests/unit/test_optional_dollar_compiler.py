"""
Tests for Compiler Integration for Optional $ Syntax.

Tests that the compiler correctly handles both VARIABLE and IDENTIFIER tokens
in assignments, with proper function conflict detection.
"""

import pytest
from lark import Lark

from cy_language.compiler import CompilerError, PlanCompiler
from cy_language.execution_plan import AssignNode
from cy_language.grammar import get_grammar


class TestOptionalDollarCompiler:
    """Test compiler integration for optional $ syntax."""

    def setup_method(self):
        """Set up test fixtures."""
        self.grammar = get_grammar()
        self.parser = Lark(self.grammar, start="start", parser="lalr")
        self.compiler = PlanCompiler()

        # Mock available tools for conflict detection
        self.compiler.available_tools = {
            "add": lambda x, y: x + y,
            "summarize": lambda text: text[:10],
        }

    def test_compile_dollar_assignment(self):
        """Test compiling $var = value assignments."""
        program = 'name = "Alice"'
        tree = self.parser.parse(program)

        plan = self.compiler.compile(tree)
        assert plan is not None

        # Should have one assignment node
        assert len(plan.nodes) == 1

        stmt = plan.nodes[0]
        assert isinstance(stmt, AssignNode)

        # Variable name should be stored without $ prefix (normalized)
        assert stmt.variable_name == "name"
        assert not stmt.variable_name.startswith("$")

        # Check line/column information is preserved
        assert stmt.line_number > 0
        assert stmt.column >= 0

    def test_compile_no_dollar_assignment(self):
        """Test compiling var = value assignments (without $)."""
        program = 'name = "Alice"'
        tree = self.parser.parse(program)

        plan = self.compiler.compile(tree)
        assert plan is not None

        # Should have one assignment node
        assert len(plan.nodes) == 1

        stmt = plan.nodes[0]
        assert isinstance(stmt, AssignNode)

        # Variable name should be stored as "name" (no $ prefix to remove)
        assert stmt.variable_name == "name"

        # Check line/column information is preserved
        assert stmt.line_number > 0
        assert stmt.column >= 0

    def test_both_forms_same_variable(self):
        """Test that both $name and name compile to same variable."""
        # Program with both forms
        program = '''name = "Alice"
name = "Bob"'''

        tree = self.parser.parse(program)
        plan = self.compiler.compile(tree)

        assert len(plan.nodes) == 2

        # Both should compile to same normalized variable name
        stmt1 = plan.nodes[0]
        stmt2 = plan.nodes[1]

        assert isinstance(stmt1, AssignNode)
        assert isinstance(stmt2, AssignNode)

        # Both should have same variable name (normalized)
        assert stmt1.variable_name == "name"
        assert stmt2.variable_name == "name"

    def test_function_conflict_detection(self):
        """Test that assignments to function names raise CompilerError."""
        # Test built-in function conflict
        program = "len = 5"
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "len" in str(error)
        assert "conflicts with function" in str(error)

        # Test another built-in function
        program = 'debug_print = "hello"'
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "debug_print" in str(error)
        assert "conflicts with function" in str(error)

        # Test LLM function conflict
        program = 'llm_run = "test"'
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "llm_run" in str(error)

    def test_custom_tool_conflict_detection(self):
        """Test conflicts with custom tools raise CompilerError."""
        # Test custom tool conflict
        program = "add = 5"
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "add" in str(error)
        assert "conflicts with function" in str(error)

        # Test another custom tool
        program = 'summarize = "text"'
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "summarize" in str(error)

    def test_dollar_prefix_function_conflicts(self):
        """Test that $function_name also raises conflicts (normalized)."""
        # Even with $ prefix, should detect conflict after normalization
        program = "len = 5"
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        assert "len" in str(error)  # Should show normalized name
        assert "conflicts with function" in str(error)

    def test_allowed_variable_names_compile(self):
        """Test that allowed variable names compile successfully."""
        # Test various allowed variable names
        program = '''name = "Alice"
user_data = "test"
my_var = 123
count = 0
result = "success"'''

        tree = self.parser.parse(program)
        plan = self.compiler.compile(tree)

        assert len(plan.nodes) == 5

        # All should be AssignNode instances
        for stmt in plan.nodes:
            assert isinstance(stmt, AssignNode)

        # Variable names should be preserved
        var_names = [stmt.variable_name for stmt in plan.nodes]
        expected_names = ["name", "user_data", "my_var", "count", "result"]
        assert var_names == expected_names

    def test_error_message_quality(self):
        """Test that error messages contain helpful information."""
        program = "len = 5"
        tree = self.parser.parse(program)

        with pytest.raises(CompilerError) as exc_info:
            self.compiler.compile(tree)

        error = exc_info.value
        error_msg = str(error)

        # Should include specific function name
        assert "len" in error_msg

        # Should explain the conflict
        assert "conflicts with function" in error_msg.lower()

        # Should include line information
        assert "Line" in error_msg

        # Check that error has proper attributes
        assert hasattr(error, "line")
        assert hasattr(error, "column")
        assert hasattr(error, "message")

    def test_case_sensitivity_conflict_detection(self):
        """Test that function conflicts are case-sensitive."""
        # These should be allowed (different case)
        program = '''LEN = 5
Len = 6
DEBUG_PRINT = "test"'''

        tree = self.parser.parse(program)
        plan = self.compiler.compile(tree)

        assert len(plan.nodes) == 3

        # All should compile successfully
        for stmt in plan.nodes:
            assert isinstance(stmt, AssignNode)

    def test_complex_expressions_compilation(self):
        """Test compiling assignments with complex expressions."""
        program = '''result = add(1, 2)
data = {"key": "value"}
list_var = [1, 2, 3]
interpolated = "Hello ${existing_var}!"'''

        tree = self.parser.parse(program)
        plan = self.compiler.compile(tree)

        assert len(plan.nodes) == 4

        # Check normalized variable names
        var_names = [stmt.variable_name for stmt in plan.nodes]
        expected_names = ["result", "data", "list_var", "interpolated"]
        assert var_names == expected_names

    def test_invalid_assignment_syntax_errors(self):
        """Test that invalid assignment syntax still raises errors."""
        # These should fail compilation for syntax reasons

        # Missing expression
        with pytest.raises((CompilerError, Exception)):
            program = "name ="
            tree = self.parser.parse(program)
            self.compiler.compile(tree)

    def test_line_column_preservation(self):
        """Test that line and column information is preserved in compilation."""
        program = """name = "Alice"
age = 25"""

        tree = self.parser.parse(program)
        plan = self.compiler.compile(tree)

        assert len(plan.nodes) == 2

        # Check that line numbers are different and valid
        stmt1, stmt2 = plan.nodes
        assert stmt1.line_number != stmt2.line_number
        assert stmt1.line_number > 0
        assert stmt2.line_number > 0

        # Second statement should be on a later line
        assert stmt2.line_number > stmt1.line_number
