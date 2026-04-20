"""
Integration tests for end-to-end execution plan workflow.
Tests the complete pipeline: AST -> Plan -> Execution -> Output
"""

from lark import Tree

from cy_language.compiler import compile_cy_program
from cy_language.execution_plan import ExecutionPlan
from cy_language.executor import _NO_RETURN, execute_plan


class TestEndToEndPlanExecution:
    """Test complete plan workflow from AST to output."""

    def test_empty_program_workflow(self):
        """Test complete workflow with empty program.

        Updated: empty programs return empty string instead of raising error.
        The validator (when enabled) would catch this at compile time.
        """
        # Create minimal AST
        ast_tree = Tree("start", [])

        # Compile to plan
        plan = compile_cy_program(ast_tree, "test.cy", validate_output=False)

        # Verify plan was created
        assert isinstance(plan, ExecutionPlan)
        assert plan.source_file == "test.cy"
        assert len(plan.nodes) == 0  # Empty program has no nodes

        # Empty plan returns _NO_RETURN sentinel (no output node)
        result = execute_plan(plan)
        assert result is _NO_RETURN

    def test_plan_serialization_roundtrip(self):
        """Test plan can be serialized and deserialized."""
        # Create a plan
        plan = ExecutionPlan(version="2.0", source_file="test.cy")

        # Serialize to JSON
        json_str = plan.to_json()
        assert isinstance(json_str, str)
        assert "2.0" in json_str
        assert "test.cy" in json_str

        # Deserialize back
        restored_plan = ExecutionPlan.from_json(json_str)
        assert restored_plan.version == plan.version
        assert restored_plan.source_file == plan.source_file

    def test_plan_validation_workflow(self):
        """Test plan validation in the workflow."""
        plan = ExecutionPlan()

        # Empty plan should have validation errors
        errors = plan.validate()
        assert len(errors) > 0
        assert "Execution plan has no nodes" in errors


class TestPlanExecutionWithMockData:
    """Test plan execution with mock data to verify interfaces."""

    def test_execution_with_tools_and_variables(self):
        """Test execution with external tools and variables.

        Updated: empty plan returns empty string.
        Variables are ignored unless accessed by nodes in the plan.
        """
        plan = ExecutionPlan()

        # Mock tools and variables
        tools = {"add": lambda a, b: a + b, "greet": lambda name: f"Hello, {name}!"}
        variables = {
            "name": "Alice",
            "output": "test_result",  # Not used by empty plan
        }

        result = execute_plan(
            plan, input_data="test_input", tools=tools, variables=variables
        )

        # Empty plan returns _NO_RETURN sentinel (no nodes to execute)
        assert result is _NO_RETURN

    def test_execution_with_different_interpolation_modes(self):
        """Test execution with different interpolation modes.

        Updated: empty plan returns empty string.
        Interpolation modes only matter when there are nodes to execute.
        """
        plan = ExecutionPlan()
        variables = {"output": "result"}

        # Test different interpolation modes
        for mode in ["markdown", "csv", "xml"]:
            result = execute_plan(
                plan, tools={}, variables=variables, interpolation_mode=mode
            )
            # Empty plan returns _NO_RETURN sentinel regardless of mode
            assert result is _NO_RETURN


class TestPlanWorkflowErrorHandling:
    """Test error handling throughout the plan workflow."""

    def test_compilation_error_handling(self):
        """Test compiler error handling."""
        # This will be expanded when actual compilation is implemented
        ast_tree = Tree("start", [])

        # Should not crash during compilation
        plan = compile_cy_program(ast_tree, validate_output=False)
        assert isinstance(plan, ExecutionPlan)

    def test_execution_error_handling(self):
        """Test executor error handling.

        Updated: empty plan returns empty string at runtime.
        The validator (when enabled) would catch missing output at compile time.
        """
        plan = ExecutionPlan()

        # Empty plan returns _NO_RETURN sentinel (runtime doesn't error)
        result = execute_plan(plan)
        assert result is _NO_RETURN

    def test_validation_error_handling(self):
        """Test plan validation error handling."""
        plan = ExecutionPlan()

        errors = plan.validate()
        assert isinstance(errors, list)


class TestPlanMetadataHandling:
    """Test handling of plan metadata throughout workflow."""

    def test_source_file_preservation(self):
        """Test source file information is preserved."""
        ast_tree = Tree("start", [])
        source_file = "my_script.cy"

        plan = compile_cy_program(ast_tree, source_file, validate_output=False)

        assert plan.source_file == source_file

    def test_version_information_handling(self):
        """Test version information is handled correctly."""
        plan = ExecutionPlan(version="2.0")

        json_str = plan.to_json()
        restored_plan = ExecutionPlan.from_json(json_str)

        assert restored_plan.version == "2.0"

    def test_metadata_preservation(self):
        """Test custom metadata is preserved."""
        plan = ExecutionPlan()
        plan.metadata["custom"] = "value"

        json_str = plan.to_json()
        restored_plan = ExecutionPlan.from_json(json_str)

        assert restored_plan.metadata.get("custom") == "value"


# Removed TestFuturePlanExecution class - it was just architectural placeholders
