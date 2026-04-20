"""
Tests for node-level caching inside loops (async path).

Root bug: when _caching_enabled=True (triggered by hi_latency_tools), the
node-level cache uses static node_id keys.  Inside loops the same node_id
executes multiple times with different arguments, so iterations 2+ got
cache hits and skipped actual execution.

This file covers every variant of that bug pattern:
1. Any tool call inside a for loop (not just log)
2. Tool calls inside while loops
3. Tool calls inside nested loops
4. Assignments with tool call RHS inside loops
5. Conditional tool calls inside loops
6. Tool calls OUTSIDE loops still cache normally
7. HITL pause inside a loop (hi-latency tool in loop body)
"""

import pytest

from cy_language import Cy
from cy_language.errors import ExecutionPaused

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_call_tracker(name: str):
    """Return (tool_fn, call_log) where call_log records every invocation."""
    call_log = []

    def tool(*args, **kwargs):
        call_log.append({"args": args, "kwargs": kwargs})
        return f"{name}_result_{len(call_log)}"

    tool.__name__ = name
    return tool, call_log


def _make_hi_latency_dummy():
    """A hi_latency tool that exists only to enable _caching_enabled."""
    return {"fn": lambda: "noop", "hi_latency": True}


def _cy_with_caching(extra_tools=None, captured_logs=None):
    """Create a Cy interpreter with caching enabled via a hi_latency dummy tool."""
    tools = {"__hi_latency_dummy": _make_hi_latency_dummy()}
    if extra_tools:
        tools.update(extra_tools)
    return Cy(tools=tools, captured_logs=captured_logs)


# ===========================================================================
# 1. Any tool call inside a for loop
# ===========================================================================


class TestToolCallsInForLoop:
    """Tool calls inside for loops must execute every iteration."""

    @pytest.mark.asyncio
    async def test_custom_tool_called_every_iteration(self):
        """A non-log tool inside a for loop must be invoked N times."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        results = []
        for (i in [10, 20, 30]) {
            r = process(i)
            results = results + [r]
        }
        return results
        """
        result = await cy.run_native_async(program)
        assert len(call_log) == 3, f"Expected 3 calls, got {len(call_log)}"
        assert len(result) == 3
        # Each call should return a unique result (not a cached repeat)
        assert len(set(result)) == 3

    @pytest.mark.asyncio
    async def test_log_called_every_iteration(self):
        """log() inside a for loop must produce N log entries (original bug)."""
        logs = []
        cy = _cy_with_caching(captured_logs=logs)

        program = """
        for (x in ["a", "b", "c", "d"]) {
            log(x)
        }
        return "done"
        """
        result = await cy.run_native_async(program)
        assert result == "done"
        assert len(logs) == 4, (
            f"Expected 4 logs, got {len(logs)}: {[entry['message'] for entry in logs]}"
        )

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_in_loop_body(self):
        """Multiple different tool calls in the same loop body all execute every iteration."""
        fn_a, log_a = _make_call_tracker("tool_a")
        fn_b, log_b = _make_call_tracker("tool_b")
        cy = _cy_with_caching(extra_tools={"tool_a": fn_a, "tool_b": fn_b})

        program = """
        for (i in [1, 2, 3]) {
            a = tool_a(i)
            b = tool_b(i)
        }
        return "done"
        """
        await cy.run_native_async(program)
        assert len(log_a) == 3, f"tool_a: expected 3 calls, got {len(log_a)}"
        assert len(log_b) == 3, f"tool_b: expected 3 calls, got {len(log_b)}"


# ===========================================================================
# 2. Tool calls inside while loops
# ===========================================================================


class TestToolCallsInWhileLoop:
    """While loops (not desugared for-in) must also not cache across iterations."""

    @pytest.mark.asyncio
    async def test_tool_call_in_while_loop(self):
        """A tool call inside a plain while loop executes every iteration."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        i = 0
        results = []
        while (i < 4) {
            r = process(i)
            results = results + [r]
            i = i + 1
        }
        return results
        """
        result = await cy.run_native_async(program)
        assert len(call_log) == 4, f"Expected 4 calls, got {len(call_log)}"
        assert len(result) == 4
        assert len(set(result)) == 4


# ===========================================================================
# 3. Nested loops
# ===========================================================================


class TestToolCallsInNestedLoops:
    """Tool calls inside nested loops must execute for every inner iteration."""

    @pytest.mark.asyncio
    async def test_tool_in_doubly_nested_for_loop(self):
        """Tool inside inner loop of nested for loops runs M*N times."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        results = []
        for (i in [1, 2, 3]) {
            for (j in ["a", "b"]) {
                r = process("${i}-${j}")
                results = results + [r]
            }
        }
        return results
        """
        result = await cy.run_native_async(program)
        assert len(call_log) == 6, f"Expected 6 calls (3x2), got {len(call_log)}"
        assert len(result) == 6
        assert len(set(result)) == 6

    @pytest.mark.asyncio
    async def test_log_in_nested_loops(self):
        """log() in nested loops produces correct number of entries."""
        logs = []
        cy = _cy_with_caching(captured_logs=logs)

        program = """
        for (i in [1, 2]) {
            for (j in [1, 2, 3]) {
                log("${i}-${j}")
            }
        }
        return "done"
        """
        await cy.run_native_async(program)
        assert len(logs) == 6, f"Expected 6 logs (2x3), got {len(logs)}"


# ===========================================================================
# 4. Assignments with tool call RHS inside loops
# ===========================================================================


class TestAssignWithToolCallInLoop:
    """Assignment nodes whose RHS is a tool call must re-evaluate every iteration."""

    @pytest.mark.asyncio
    async def test_assign_tool_result_differs_each_iteration(self):
        """x = tool(i) must produce different values per iteration."""
        counter = {"n": 0}

        def incrementing_tool(*args, **kwargs):
            counter["n"] += 1
            return counter["n"]

        cy = _cy_with_caching(extra_tools={"next_id": incrementing_tool})

        program = """
        ids = []
        for (i in [1, 2, 3, 4, 5]) {
            id = next_id()
            ids = ids + [id]
        }
        return ids
        """
        result = await cy.run_native_async(program)
        assert result == [1, 2, 3, 4, 5], f"Expected [1,2,3,4,5], got {result}"


# ===========================================================================
# 5. Conditional tool calls inside loops
# ===========================================================================


class TestConditionalToolCallInLoop:
    """Tool calls guarded by if inside a loop must execute on every matching iteration."""

    @pytest.mark.asyncio
    async def test_conditional_tool_in_loop(self):
        """Tool inside if-branch within loop executes for matching iterations only."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        results = []
        for (i in [1, 2, 3, 4, 5, 6]) {
            if (i % 2 == 0) {
                r = process(i)
                results = results + [r]
            }
        }
        return results
        """
        result = await cy.run_native_async(program)
        # Even numbers: 2, 4, 6 → 3 calls
        assert len(call_log) == 3, f"Expected 3 calls (evens only), got {len(call_log)}"
        assert len(result) == 3
        assert len(set(result)) == 3


# ===========================================================================
# 5b. Tool calls inside list comprehensions
# ===========================================================================


class TestToolCallsInComprehensions:
    """List comprehensions are also iterative — tool calls must execute every iteration."""

    @pytest.mark.asyncio
    async def test_tool_in_list_comprehension(self):
        """A tool call inside a list comprehension element expression runs for each item."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        items = [1, 2, 3, 4]
        results = [process(i) for(i in items)]
        return results
        """
        result = await cy.run_native_async(program)
        assert len(call_log) == 4, f"Expected 4 calls, got {len(call_log)}"
        assert len(result) == 4
        assert len(set(result)) == 4

    @pytest.mark.asyncio
    async def test_tool_in_filtered_comprehension(self):
        """A tool call in a comprehension with a filter only runs for matching items."""
        process_fn, call_log = _make_call_tracker("process")
        cy = _cy_with_caching(extra_tools={"process": process_fn})

        program = """
        items = [1, 2, 3, 4, 5, 6]
        results = [process(i) for(i in items) if(i % 2 == 0)]
        return results
        """
        result = await cy.run_native_async(program)
        assert len(call_log) == 3, f"Expected 3 calls (evens), got {len(call_log)}"
        assert len(result) == 3
        assert len(set(result)) == 3


# ===========================================================================
# 6. Caching still works OUTSIDE loops
# ===========================================================================


class TestCachingOutsideLoopsPreserved:
    """Non-loop tool calls should still benefit from node-level caching."""

    @pytest.mark.asyncio
    async def test_tool_before_loop_is_cached_on_resume(self):
        """A tool call before a loop should be cached and not re-executed on resume.

        This verifies the fix doesn't break normal HITL caching.
        """
        call_log = []

        async def get_data(*args, **kwargs):
            call_log.append("get_data")
            return [1, 2, 3]

        async def ask_human(*args, **kwargs):
            call_log.append("ask_human")
            return "approved"

        tools = {
            "get_data": get_data,
            "ask_human": {"fn": ask_human, "hi_latency": True},
        }

        program = """
        data = get_data()
        decision = ask_human("approve?")
        return decision
        """

        # First run: should pause at ask_human
        cy1 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy1.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert "get_data" in call_log
        call_log.clear()

        # Resume: get_data should NOT be re-called (cached in checkpoint)
        checkpoint.pending_tool_result = "yes"
        cy2 = Cy(tools=tools)
        result = await cy2.run_native_async(program, checkpoint=checkpoint)
        assert "get_data" not in call_log, (
            "get_data should have been cached, not re-called"
        )


# ===========================================================================
# 7. HITL pause inside a loop
# ===========================================================================


class TestHITLPauseInsideLoop:
    """Hi-latency tools inside loops should still pause correctly."""

    @pytest.mark.asyncio
    async def test_hi_latency_tool_in_loop_pauses(self):
        """A hi_latency tool inside a for loop should raise ExecutionPaused."""

        async def review(item):
            return "approved"

        tools = {
            "review_item": {"fn": review, "hi_latency": True},
        }

        program = """
        items = ["a", "b", "c"]
        for (item in items) {
            verdict = review_item(item)
        }
        return "done"
        """

        cy = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert checkpoint.pending_tool_name == "review_item"

    @pytest.mark.asyncio
    async def test_hi_latency_tool_in_loop_resumes_without_infinite_pause(self):
        """HITL resume must work inside a loop — the checkpoint answer must not
        be skipped by the in-loop cache guard.

        Regression: the _loop_depth fix caused checkpoint cache entries to be
        ignored inside loops, creating an infinite ExecutionPaused loop.
        """
        call_log = []

        async def get_items():
            call_log.append("get_items")
            return ["item_a", "item_b"]

        async def review_item(item):
            call_log.append(f"review:{item}")
            return "approved"

        tools = {
            "get_items": get_items,
            "review_item": {"fn": review_item, "hi_latency": True},
        }

        program = """
        items = get_items()
        results = []
        for (item in items) {
            verdict = review_item(item)
            results = results + [verdict]
        }
        return results
        """

        # Step 1: First run pauses at first review_item
        cy1 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy1.run_native_async(program)

        cp1 = exc_info.value.checkpoint
        assert cp1.pending_tool_name == "review_item"
        call_log.clear()

        # Step 2: Resume with answer for iteration 0 — loop replays from
        # start, consumes the answer for iteration 0, then pauses at
        # iteration 1's review_item call.
        cp1.pending_tool_result = "approved_1"
        cy2 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info2:
            await cy2.run_native_async(program, checkpoint=cp1)

        cp2 = exc_info2.value.checkpoint
        assert cp2.pending_tool_name == "review_item"
