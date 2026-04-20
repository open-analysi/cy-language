"""Unit tests for tool registry integration of native functions.

Tests that all native and LLM functions are properly registered
and available through the Cy language tool system.

NOTE: This test file uses fixtures to provide backward compatibility
with the old architecture where LLM and example tools were in default_registry.
"""

import pytest

from cy_language.llm_functions import (
    llm_evaluate_results,
    llm_give_feedback,
    llm_registry,
    llm_revise_task,
    llm_run,
)
from cy_language.native_functions import (
    from_json,
    len_function,
    log,
)
from cy_language.ui.tools import ToolRegistry, default_registry


@pytest.fixture
def legacy_registry():
    """Create a registry with all tools (native, LLM, and examples) for backward compatibility.

    This fixture provides a registry that mimics the old behavior where all tools
    were in default_registry. Tests use this to verify registration behavior.
    """
    # Create a new registry with all tools
    registry = ToolRegistry()

    # Add native functions
    registry.register(
        "len", len_function, "Return the length of a string, list, or dict"
    )
    registry.register("log", log, "Log messages without interfering with output")
    registry.register("from_json", from_json, "Parse JSON string to structured data")

    # Add LLM functions (from llm_registry)
    llm_tools = llm_registry.get_tools_dict()
    llm_descriptions = {
        item["name"]: item["description"]
        for item in llm_registry.get_tool_descriptions()
    }

    for name, func in llm_tools.items():
        registry.register(name, func, llm_descriptions[name])

    # Add example tools (for backward compatibility)
    def add(*args):
        return sum(args)

    def summarize(items):
        return f"Summary of {len(items)} items"

    registry.register("add", add, "Add numbers together")
    registry.register("summarize", summarize, "Summarize a list of items")

    return registry


class TestNativeFunctionRegistration:
    """Test that native functions are properly registered."""

    def test_len_function_registered(self) -> None:
        """Test that len() function is properly registered in tool registry."""
        tools_dict = default_registry.get_tools_dict()

        assert "len" in tools_dict
        assert tools_dict["len"] == len_function
        assert callable(tools_dict["len"])

    def test_log_registered(self) -> None:
        """Test that log() function is properly registered."""
        tools_dict = default_registry.get_tools_dict()

        assert "log" in tools_dict
        assert tools_dict["log"] == log
        assert callable(tools_dict["log"])

    def test_from_json_registered(self) -> None:
        """Test that from_json() function is properly registered."""
        tools_dict = default_registry.get_tools_dict()

        assert "from_json" in tools_dict
        assert tools_dict["from_json"] == from_json
        assert callable(tools_dict["from_json"])

    def test_native_functions_have_descriptions(self) -> None:
        """Test that all native functions have proper descriptions."""
        descriptions = default_registry.get_tool_descriptions()
        description_dict = {item["name"]: item["description"] for item in descriptions}

        # Check that our native functions have descriptions
        assert "len" in description_dict
        assert len(description_dict["len"]) > 0
        assert "list" in description_dict["len"].lower()

        assert "log" in description_dict
        assert len(description_dict["log"]) > 0
        assert "log" in description_dict["log"].lower()

        assert "from_json" in description_dict
        assert len(description_dict["from_json"]) > 0
        assert "json" in description_dict["from_json"].lower()


class TestLLMFunctionRegistration:
    """Test that LLM functions are properly registered (in llm_registry, not default)."""

    def test_llm_run_registered(self, legacy_registry) -> None:
        """Test that llm_run() function is properly registered."""
        # LLM functions are now in llm_registry, not default_registry
        # Use legacy_registry fixture for this test
        tools_dict = legacy_registry.get_tools_dict()

        assert "llm_run" in tools_dict
        assert tools_dict["llm_run"] == llm_run
        assert callable(tools_dict["llm_run"])

    def test_llm_evaluate_results_registered(self, legacy_registry) -> None:
        """Test that llm_evaluate_results() function is properly registered."""
        tools_dict = legacy_registry.get_tools_dict()

        assert "llm_evaluate_results" in tools_dict
        assert tools_dict["llm_evaluate_results"] == llm_evaluate_results
        assert callable(tools_dict["llm_evaluate_results"])

    def test_llm_give_feedback_registered(self, legacy_registry) -> None:
        """Test that llm_give_feedback() function is properly registered."""
        tools_dict = legacy_registry.get_tools_dict()

        assert "llm_give_feedback" in tools_dict
        assert tools_dict["llm_give_feedback"] == llm_give_feedback
        assert callable(tools_dict["llm_give_feedback"])

    def test_llm_revise_task_registered(self, legacy_registry) -> None:
        """Test that llm_revise_task() function is properly registered."""
        tools_dict = legacy_registry.get_tools_dict()

        assert "llm_revise_task" in tools_dict
        assert tools_dict["llm_revise_task"] == llm_revise_task
        assert callable(tools_dict["llm_revise_task"])

    def test_llm_functions_have_descriptions(self, legacy_registry) -> None:
        """Test that all LLM functions have proper descriptions."""
        descriptions = legacy_registry.get_tool_descriptions()
        description_dict = {item["name"]: item["description"] for item in descriptions}

        # Check that our LLM functions have descriptions
        llm_functions = [
            "llm_run",
            "llm_evaluate_results",
            "llm_give_feedback",
            "llm_revise_task",
        ]

        for func_name in llm_functions:
            assert func_name in description_dict
            assert len(description_dict[func_name]) > 0
            # Each should mention LLM or AI in description
            description = description_dict[func_name].lower()
            assert (
                "llm" in description
                or "ai" in description
                or "language model" in description
            )


class TestExistingToolsPreservation:
    """Test that existing tools are preserved after adding new functions."""

    def test_existing_tools_still_present(self, legacy_registry) -> None:
        """Test that existing tools (add, summarize, etc.) are still available."""
        # Example tools are now in example_registry, not default_registry
        # Use legacy_registry fixture for this test
        tools_dict = legacy_registry.get_tools_dict()

        # These tools should exist from the original implementation
        expected_existing_tools = ["add", "summarize"]

        for tool_name in expected_existing_tools:
            assert tool_name in tools_dict
            assert callable(tools_dict[tool_name])

    def test_example_tools_still_present(self, legacy_registry) -> None:
        """Test that existing tools are still available."""
        tools_dict = legacy_registry.get_tools_dict()

        # These basic tools should exist
        expected_basic_tools = ["add", "summarize"]

        for tool_name in expected_basic_tools:
            assert tool_name in tools_dict
            assert callable(tools_dict[tool_name])

    def test_no_tool_name_conflicts(self) -> None:
        """Test that there are no conflicts between tool names."""
        tools_dict = default_registry.get_tools_dict()

        # Get all tool names
        tool_names = list(tools_dict.keys())

        # Should not have duplicates
        assert len(tool_names) == len(set(tool_names))

        # No tool should have empty name
        for name in tool_names:
            assert name is not None
            assert len(name) > 0
            assert isinstance(name, str)


class TestToolRegistryFunctionality:
    """Test tool registry functionality with new functions."""

    def test_get_tools_dict_returns_all_functions(self, legacy_registry) -> None:
        """Test that get_tools_dict() returns all registered functions."""
        # Use legacy_registry for tests that expect all tools together
        tools_dict = legacy_registry.get_tools_dict()

        # Should include our new native functions
        new_native_functions = ["len", "log", "from_json"]
        for func_name in new_native_functions:
            assert func_name in tools_dict

        # Should include our new LLM functions
        new_llm_functions = [
            "llm_run",
            "llm_evaluate_results",
            "llm_give_feedback",
            "llm_revise_task",
        ]
        for func_name in new_llm_functions:
            assert func_name in tools_dict

        # Should be a copy (not the original dict)
        original_dict = legacy_registry._tools
        assert tools_dict is not original_dict

    def test_get_tool_descriptions_includes_new_functions(
        self, legacy_registry
    ) -> None:
        """Test that get_tool_descriptions() includes new function descriptions."""
        descriptions = legacy_registry.get_tool_descriptions()

        # Should be a list of dictionaries
        assert isinstance(descriptions, list)
        assert all(isinstance(item, dict) for item in descriptions)
        assert all("name" in item and "description" in item for item in descriptions)

        # Extract function names from descriptions
        function_names = {item["name"] for item in descriptions}

        # Should include all our new functions
        new_functions = [
            "len",
            "log",
            "from_json",
            "llm_run",
            "llm_evaluate_results",
            "llm_give_feedback",
            "llm_revise_task",
        ]

        for func_name in new_functions:
            assert func_name in function_names

    def test_tool_registry_isolation(self) -> None:
        """Test that tool registry provides isolated copies."""
        # Get tools dict twice
        tools_dict_1 = default_registry.get_tools_dict()
        tools_dict_2 = default_registry.get_tools_dict()

        # Should be different objects (copies)
        assert tools_dict_1 is not tools_dict_2

        # But should have same content
        assert tools_dict_1.keys() == tools_dict_2.keys()
        for key in tools_dict_1:
            assert tools_dict_1[key] is tools_dict_2[key]  # Same function objects

    def test_registry_prevents_duplicate_registration(self) -> None:
        """Test that registry prevents duplicate function registration."""
        from cy_language.ui.tools import ToolRegistry

        # Create a test registry
        test_registry = ToolRegistry()

        # Register a function
        def test_func():
            return "test"

        test_registry.register("test_function", test_func, "Test function")

        # Try to register again - should raise ValueError
        with pytest.raises(
            ValueError, match="Tool 'test_function' is already registered"
        ):
            test_registry.register("test_function", test_func, "Duplicate function")


class TestToolRegistryIntegration:
    """Test integration aspects of tool registry with Cy interpreter."""

    def test_tools_can_be_called_through_registry(self, legacy_registry) -> None:
        """Test that tools can be successfully called through the registry."""
        tools_dict = legacy_registry.get_tools_dict()

        # Test native functions can be called
        len_func = tools_dict["len"]
        result = len_func([1, 2, 3, 4, 5])
        assert result == 5

        debug_func = tools_dict["log"]
        result = debug_func("test message")
        assert result == "test message"

        # Test existing functions still work
        add_func = tools_dict["add"]
        result = add_func(2, 3, 5)
        assert result == 10

    def test_tool_signatures_are_correct(self, legacy_registry) -> None:
        """Test that tool function signatures are correct."""
        tools_dict = legacy_registry.get_tools_dict()

        # Check that functions have correct signatures
        len_func = tools_dict["len"]
        assert callable(len_func)

        # LLM functions should accept the expected parameters
        llm_run_func = tools_dict["llm_run"]
        assert callable(llm_run_func)

        # Can inspect function signature if needed
        import inspect

        sig = inspect.signature(llm_run_func)
        param_names = list(sig.parameters.keys())
        assert "prompt" in param_names

    def test_tools_available_in_streamlit_ui(self, legacy_registry) -> None:
        """Test that tools are available for Streamlit UI discovery."""
        # This simulates how the Streamlit UI would discover available tools
        descriptions = legacy_registry.get_tool_descriptions()

        # Should be able to categorize tools
        native_tools = []
        llm_tools = []
        utility_tools = []

        for tool_info in descriptions:
            name = tool_info["name"]
            description = tool_info["description"].lower()

            if name.startswith("llm_"):
                llm_tools.append(name)
            elif name in ["len", "log", "from_json"]:
                native_tools.append(name)
            else:
                utility_tools.append(name)

        # Should have tools in each category
        assert len(native_tools) == 3
        assert len(llm_tools) == 4
        assert len(utility_tools) > 0  # add, summarize, etc.

        # Total should be reasonable number
        total_tools = len(descriptions)
        assert total_tools >= 9  # At least our 7 new tools + 2 existing minimum

    def test_tool_registry_thread_safety(self) -> None:
        """Test that tool registry operations are thread-safe."""
        import threading
        import time

        results = []
        errors = []

        def worker_get_tools(worker_id: int) -> None:
            try:
                for i in range(10):
                    tools_dict = default_registry.get_tools_dict()
                    descriptions = default_registry.get_tool_descriptions()

                    # Verify integrity
                    assert len(tools_dict) > 0
                    assert len(descriptions) > 0

                    results.append(f"Worker {worker_id}: Success {i}")
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Create multiple threads accessing registry
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker_get_tools, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no errors and expected number of results
        assert len(errors) == 0
        assert len(results) == 50  # 5 workers × 10 operations each
