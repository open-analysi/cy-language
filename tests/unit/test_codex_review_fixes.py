"""
TDD tests for issues found by Codex code review.

R1: Child executors in parallel comprehensions don't inherit parent settings
R2: Comprehension parallelization skips _has_shared_resources check
R3: _has_shared_resources doesn't handle FQN tool names (:: separator)
"""

import asyncio
import json
from unittest.mock import Mock

import pytest

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import ToolCallNode
from cy_language.interpreter import Cy
from cy_language.native_functions import default_registry


# ────────────────────────────────────────────────────────────
# R1: Child executors must inherit parent settings
# ────────────────────────────────────────────────────────────
class TestR1ChildExecutorInheritance:
    """Parallel comprehension child executors must inherit interpolation_mode,
    item_tag, enable_parallel, parallel_threshold, hi_latency_tools, and
    node_result_cache from the parent."""

    @pytest.mark.asyncio
    async def test_child_inherits_interpolation_mode(self):
        """Child executor must use the parent's interpolation_mode, not default."""

        async def async_format(x):
            return {"key": x}

        tools = default_registry.get_tools_dict()
        tools["async_format"] = async_format

        # Use xml mode — if child resets to default "markdown", output differs
        cy = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=2,
            interpolation_mode="xml",
        )

        code_parallel = """
        items = [1, 2, 3]
        results = [async_format(x) for(x in items)]
        return results
        """

        cy_seq = await Cy.create_async(
            tools=tools,
            enable_parallel=False,
            interpolation_mode="xml",
        )

        result_parallel = json.loads(await cy.run_async(code_parallel))
        result_sequential = json.loads(await cy_seq.run_async(code_parallel))

        # Both should produce the same result regardless of parallel execution
        assert result_parallel == result_sequential, (
            f"Parallel result {result_parallel} differs from sequential {result_sequential} "
            f"— child executor likely reset interpolation_mode"
        )


# ────────────────────────────────────────────────────────────
# R2: Comprehension must check shared resources before parallelizing
# ────────────────────────────────────────────────────────────
class TestR2ComprehensionSharedResourceCheck:
    """Comprehensions with shared-resource tools (file_write, sql_query)
    must NOT be parallelized, even if the tool is async."""

    @pytest.mark.asyncio
    async def test_file_write_comprehension_stays_sequential(self):
        """[file_write(path, x) for(x in items)] must run sequentially."""
        concurrent_count = 0
        max_concurrent = 0

        async def file_write(path, data):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.02)
            concurrent_count -= 1
            return data

        tools = default_registry.get_tools_dict()
        tools["file_write"] = file_write

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        items = [1, 2, 3]
        results = [file_write("out.txt", x) for(x in items)]
        return results
        """

        result = json.loads(await cy.run_async(code))
        assert result == [1, 2, 3]
        assert max_concurrent == 1, (
            f"file_write should run sequentially, but max_concurrent was {max_concurrent}"
        )


# ────────────────────────────────────────────────────────────
# R3: _has_shared_resources must handle FQN tool names
# ────────────────────────────────────────────────────────────
class TestR3FQNSharedResources:
    """_has_shared_resources must recognize FQN tool names like
    native::tools::file_write and app::db::query as shared resources."""

    def test_fqn_file_write_detected(self):
        """native::tools::file_write should be detected as shared resource."""
        analyzer = DependencyAnalyzer(tools={})

        node = Mock(spec=ToolCallNode)
        node.tool_name = "native::tools::file_write"

        assert analyzer._has_shared_resources([node]) is True, (
            "FQN tool native::tools::file_write should be detected as shared resource"
        )

    def test_fqn_db_query_detected(self):
        """app::db::query should be detected as shared resource."""
        analyzer = DependencyAnalyzer(tools={})

        node = Mock(spec=ToolCallNode)
        node.tool_name = "app::db::query"

        assert analyzer._has_shared_resources([node]) is True

    def test_fqn_sql_query_detected(self):
        """app::postgres::sql_query should be detected as shared resource."""
        analyzer = DependencyAnalyzer(tools={})

        node = Mock(spec=ToolCallNode)
        node.tool_name = "app::postgres::sql_query"

        assert analyzer._has_shared_resources([node]) is True

    def test_fqn_safe_tool_not_blocked(self):
        """app::virustotal::ip_reputation should NOT be detected as shared resource."""
        analyzer = DependencyAnalyzer(tools={})

        node = Mock(spec=ToolCallNode)
        node.tool_name = "app::virustotal::ip_reputation"

        assert analyzer._has_shared_resources([node]) is False
