"""
Tests for HITL (Human-in-the-Loop) resume inside loops.

Covers two tiers of fixes:
- Tier 1: __for_idx reset — loop resumes from the correct iteration, not 0
- Tier 2: Iteration-aware checkpoint keys — each loop iteration pauses
  independently with its own checkpoint key, so human answers are not
  mixed across iterations.

The full multi-step flow tested:
  run → pause(iter 0) → resume(answer_0) → pause(iter 1) → resume(answer_1) → complete
"""

import pytest

from cy_language import Cy
from cy_language.errors import ExecutionPaused

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_recording_tool(name: str, call_log: list):
    """Create an async tool that records calls and returns a unique result per call."""

    async def tool(*args, **kwargs):
        call_log.append({"name": name, "args": args, "kwargs": kwargs})
        return f"{name}_result_{len(call_log)}"

    tool.__name__ = name
    return tool


# ===========================================================================
# Tier 1: __for_idx reset on resume
# ===========================================================================


class TestLoopReplayOnResume:
    """On HITL resume, the loop replays from the start. Non-HITL tools
    re-execute (they're fast), and the HITL answer is consumed for the
    correct iteration via iteration-aware checkpoint keys."""

    @pytest.mark.asyncio
    async def test_resume_replays_loop_and_pauses_at_next_iteration(self):
        """After resuming with an answer for iteration 0, the loop replays
        from scratch. The HITL answer is consumed for iteration 0, then
        the loop pauses at iteration 1's HITL call."""
        call_log = []

        tools = {
            "process": _make_recording_tool("process", call_log),
            "review": {
                "fn": _make_recording_tool("review", call_log),
                "hi_latency": True,
            },
        }

        program = """
        items = ["a", "b", "c"]
        results = []
        for (item in items) {
            p = process(item)
            verdict = review(item)
            results = results + [verdict]
        }
        return results
        """

        # Step 1: First run — should pause at review("a") in iteration 0
        cy1 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy1.run_native_async(program)

        cp1 = exc_info.value.checkpoint
        assert cp1.pending_tool_name == "review"
        call_log.clear()

        # Step 2: Resume with answer for iteration 0 → pauses at iteration 1
        cp1.pending_tool_result = "approved_a"
        cy2 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info2:
            await cy2.run_native_async(program, checkpoint=cp1)

        cp2 = exc_info2.value.checkpoint
        assert cp2.pending_tool_name == "review"
        # The pending args should reference "b" (iteration 1)
        assert "b" in str(cp2.pending_tool_args)

    @pytest.mark.asyncio
    async def test_checkpoint_variables_include_loop_index(self):
        """The checkpoint's variables dict should contain the for-loop index."""
        tools = {
            "review": {"fn": _make_recording_tool("review", []), "hi_latency": True},
        }

        program = """
        items = ["x", "y", "z"]
        for (item in items) {
            verdict = review(item)
        }
        return "done"
        """

        cy = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy.run_native_async(program)

        cp = exc_info.value.checkpoint
        # Should have __for_idx_* variable
        for_idx_vars = {
            k: v for k, v in cp.variables.items() if k.startswith("__for_idx_")
        }
        assert len(for_idx_vars) == 1, (
            f"Expected one __for_idx var, got: {for_idx_vars}"
        )


# ===========================================================================
# Tier 2: Iteration-aware checkpoint keys
# ===========================================================================


class TestIterationAwareCheckpointKeys:
    """Each loop iteration should pause independently with its own checkpoint key."""

    @pytest.mark.asyncio
    async def test_full_multi_step_hitl_loop(self):
        """Complete flow: 3 items, pause at each, resume each with unique answer.

        run → pause(item_a) → resume("yes_a") → pause(item_b) → resume("yes_b")
            → pause(item_c) → resume("yes_c") → complete with ["yes_a", "yes_b", "yes_c"]
        """
        call_log = []

        tools = {
            "get_items": _make_recording_tool("get_items", call_log),
            "review": {
                "fn": _make_recording_tool("review", call_log),
                "hi_latency": True,
            },
        }

        # Override get_items to return a fixed list
        async def get_items():
            call_log.append({"name": "get_items", "args": (), "kwargs": {}})
            return ["item_a", "item_b", "item_c"]

        tools["get_items"] = get_items

        program = """
        items = get_items()
        results = []
        for (item in items) {
            verdict = review(item)
            results = results + [verdict]
        }
        return results
        """

        # Pause 1: at review("item_a")
        cy1 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await cy1.run_native_async(program)
        cp1 = exc_info.value.checkpoint
        assert cp1.pending_tool_name == "review"
        call_log.clear()

        # Resume 1 → Pause 2: at review("item_b")
        cp1.pending_tool_result = "yes_a"
        cy2 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info2:
            await cy2.run_native_async(program, checkpoint=cp1)
        cp2 = exc_info2.value.checkpoint
        assert cp2.pending_tool_name == "review"
        # The answer for item_a should be preserved in variables
        assert cp2.variables.get("verdict") == "yes_a"
        call_log.clear()

        # Resume 2 → Pause 3: at review("item_c")
        cp2.pending_tool_result = "yes_b"
        cy3 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info3:
            await cy3.run_native_async(program, checkpoint=cp2)
        cp3 = exc_info3.value.checkpoint
        assert cp3.pending_tool_name == "review"
        assert cp3.variables.get("verdict") == "yes_b"
        call_log.clear()

        # Resume 3 → Complete
        cp3.pending_tool_result = "yes_c"
        cy4 = Cy(tools=tools)
        result = await cy4.run_native_async(program, checkpoint=cp3)

        assert result == ["yes_a", "yes_b", "yes_c"]

    @pytest.mark.asyncio
    async def test_hitl_in_loop_applies_answer_to_correct_iteration(self):
        """The human's answer must be applied to the correct loop item,
        not to a re-executed earlier iteration."""
        call_log = []

        tools = {
            "review": {
                "fn": _make_recording_tool("review", call_log),
                "hi_latency": True,
            },
        }

        program = """
        items = ["alpha", "beta"]
        results = []
        for (item in items) {
            verdict = review(item)
            results = results + [verdict]
        }
        return results
        """

        # Pause at "alpha"
        cy1 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc:
            await cy1.run_native_async(program)
        cp1 = exc.value.checkpoint
        call_log.clear()

        # Resume → pause at "beta"
        cp1.pending_tool_result = "approved_alpha"
        cy2 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc2:
            await cy2.run_native_async(program, checkpoint=cp1)
        cp2 = exc2.value.checkpoint

        # The pending args should reference "beta", not "alpha"
        assert "beta" in str(cp2.pending_tool_args), (
            f"Expected pending args to reference 'beta', got: {cp2.pending_tool_args}"
        )

        # Resume → complete
        cp2.pending_tool_result = "approved_beta"
        cy3 = Cy(tools=tools)
        result = await cy3.run_native_async(program, checkpoint=cp2)

        assert result == ["approved_alpha", "approved_beta"]

    @pytest.mark.asyncio
    async def test_checkpoint_serialization_roundtrip_with_iteration_keys(self):
        """Checkpoint with iteration-aware data should survive JSON round-trip."""
        tools = {
            "review": {"fn": _make_recording_tool("review", []), "hi_latency": True},
        }

        program = """
        for (item in ["x", "y"]) {
            review(item)
        }
        return "done"
        """

        cy = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc:
            await cy.run_native_async(program)

        cp = exc.value.checkpoint

        # Round-trip through JSON
        json_str = cp.to_json()
        from cy_language.execution_plan import ExecutionCheckpoint

        cp_restored = ExecutionCheckpoint.from_json(json_str)

        assert cp_restored.pending_tool_name == cp.pending_tool_name
        assert cp_restored.pending_node_id == cp.pending_node_id
        assert cp_restored.variables == cp.variables
        assert cp_restored.node_results == cp.node_results
