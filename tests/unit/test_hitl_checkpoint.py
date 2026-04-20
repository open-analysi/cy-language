"""
Tests for Human-in-the-Loop (HITL) memoized replay in the Cy language.

Project Kalymnos, Cy Language — Memoized Replay (R1-R6)

Tests cover:
- R1: Hi-latency tool metadata detection
- R2: Node result cache (memoized replay on resume)
- R3: ExecutionPaused exception with checkpoint
- R4: ExecutionCheckpoint serialization (JSON round-trip)
- R5: Resume via checkpoint parameter on run_async/run_native_async
- R6: Control flow replay with cache (if/else, loops)
"""

import json

import pytest

from cy_language import Cy
from cy_language.errors import ExecutionPaused
from cy_language.execution_plan import ExecutionCheckpoint
from cy_language.executor import ExecutionContext, PlanExecutor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sync_tool(name: str, return_value):
    """Create a simple sync tool returning a fixed value."""

    def tool(*args, **kwargs):
        return return_value

    tool.__name__ = name
    return tool


def _make_async_tool(name: str, return_value):
    """Create an async tool returning a fixed value."""

    async def tool(*args, **kwargs):
        return return_value

    tool.__name__ = name
    return tool


def _make_recording_tool(name: str, return_value, call_log: list):
    """Create a tool that records calls and returns a fixed value."""

    async def tool(*args, **kwargs):
        call_log.append({"name": name, "args": args, "kwargs": kwargs})
        return return_value

    tool.__name__ = name
    return tool


# ===========================================================================
# R1: Hi-latency tool metadata
# ===========================================================================


class TestHiLatencyToolMetadata:
    """R1: Tools can be marked as hi_latency via metadata dict."""

    def test_tool_with_hi_latency_metadata_is_detected(self):
        """A tool registered with hi_latency=True metadata should be recognized."""

        async def slow_tool(question):
            return "answer"

        tools = {
            "ask_human": {
                "fn": slow_tool,
                "hi_latency": True,
            }
        }
        interpreter = Cy(tools=tools)
        # The interpreter should accept dict-style tool registration
        assert "ask_human" in interpreter.tools

    def test_tool_without_hi_latency_metadata_is_normal(self):
        """A tool registered as a plain callable should not be hi_latency."""
        tools = {"fast_tool": lambda x: x}
        interpreter = Cy(tools=tools)
        assert "fast_tool" in interpreter.tools

    def test_tool_with_explicit_hi_latency_false(self):
        """A tool with hi_latency=False should not be treated as hi_latency."""
        tools = {
            "regular_tool": {
                "fn": lambda x: x,
                "hi_latency": False,
            }
        }
        interpreter = Cy(tools=tools)
        assert "regular_tool" in interpreter.tools


# ===========================================================================
# R2: Node result cache (memoized replay)
# ===========================================================================


class TestNodeResultCache:
    """R2: PlanExecutor uses node_result_cache to skip re-execution."""

    @pytest.mark.asyncio
    async def test_cached_tool_call_returns_cached_value(self):
        """When a tool call node_id is in the cache, return cached result without calling the tool."""
        call_log = []
        tools = {
            "expensive_llm": _make_recording_tool(
                "expensive_llm", "llm_result", call_log
            ),
        }

        program = """
        result = expensive_llm("prompt")
        return result
        """

        # First run — tool should be called
        interpreter = Cy(tools=tools)
        result = await interpreter.run_native_async(program)
        assert result == "llm_result"
        assert len(call_log) == 1

        # Reset call log
        call_log.clear()

        # Second run with cache — tool should NOT be called
        interpreter2 = Cy(tools=tools)
        # We need to get the node_id for the tool call to build a cache.
        # For a simpler approach, we'll use the checkpoint-based resume path.
        # This test verifies the PlanExecutor-level cache directly.
        context = ExecutionContext(tools=tools)
        # Compile to get node IDs
        from cy_language.compiler import compile_cy_program

        ast_tree = interpreter2.parser.parse_only(program)
        plan = compile_cy_program(
            ast_tree,
            source_file="<test>",
            available_tools=interpreter2.tools,
            lark_parser=interpreter2.parser.lark_parser_no_transform,
        )

        # Find the tool call node
        tool_call_nodes = [
            n
            for n in plan.nodes
            if n.node_type.value == "tool_call"
            or (hasattr(n, "expression") and hasattr(n.expression, "tool_name"))
        ]
        # The tool call is inside an ASSIGN node
        assign_nodes = [n for n in plan.nodes if n.node_type.value == "assign"]
        assert len(assign_nodes) >= 1
        tool_node = assign_nodes[0].expression
        # Compiler prefixes native tools with "native::tools::"
        assert "expensive_llm" in tool_node.tool_name

        # Build cache with the tool call's node_id
        cache = {tool_node.node_id: "cached_llm_result"}

        executor = PlanExecutor(context, node_result_cache=cache)
        result2 = await executor.execute(plan)
        assert result2 == "cached_llm_result"
        assert len(call_log) == 0  # Tool was not called

    @pytest.mark.asyncio
    async def test_uncached_tool_call_executes_normally(self):
        """When a tool call node_id is NOT in the cache, execute normally."""
        call_log = []
        tools = {
            "my_tool": _make_recording_tool("my_tool", "fresh_result", call_log),
        }
        context = ExecutionContext(tools=tools)
        executor = PlanExecutor(context, node_result_cache={})

        program = """
        x = my_tool("arg")
        return x
        """
        interpreter = Cy(tools=tools)
        ast_tree = interpreter.parser.parse_only(program)
        from cy_language.compiler import compile_cy_program

        plan = compile_cy_program(
            ast_tree,
            source_file="<test>",
            available_tools=interpreter.tools,
            lark_parser=interpreter.parser.lark_parser_no_transform,
        )

        result = await executor.execute(plan)
        assert result == "fresh_result"
        assert len(call_log) == 1

    @pytest.mark.asyncio
    async def test_cache_records_new_results(self):
        """After executing a tool call, the result should be added to the cache."""
        call_log = []
        tools = {
            "record_me": _make_recording_tool("record_me", 42, call_log),
        }
        context = ExecutionContext(tools=tools)
        cache = {}
        executor = PlanExecutor(context, node_result_cache=cache)

        program = """
        val = record_me()
        return val
        """
        interpreter = Cy(tools=tools)
        ast_tree = interpreter.parser.parse_only(program)
        from cy_language.compiler import compile_cy_program

        plan = compile_cy_program(
            ast_tree,
            source_file="<test>",
            available_tools=interpreter.tools,
            lark_parser=interpreter.parser.lark_parser_no_transform,
        )

        result = await executor.execute(plan)
        assert result == 42
        assert len(cache) == 1  # One tool call result was cached


# ===========================================================================
# R3: ExecutionPaused exception with checkpoint
# ===========================================================================


class TestExecutionPaused:
    """R3: Hi-latency tool without cached result raises ExecutionPaused."""

    @pytest.mark.asyncio
    async def test_hi_latency_tool_pauses_when_no_cache(self):
        """A hi_latency tool with no cache entry should raise ExecutionPaused."""

        async def ask_human(question):
            return "should not reach here"

        tools = {
            "ask_human": {
                "fn": ask_human,
                "hi_latency": True,
            },
        }

        program = """
        answer = ask_human("Is this malicious?")
        return answer
        """

        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert isinstance(checkpoint, ExecutionCheckpoint)
        assert checkpoint.pending_tool_name == "ask_human"
        assert "Is this malicious?" in str(checkpoint.pending_tool_args)

    @pytest.mark.asyncio
    async def test_hi_latency_tool_with_cache_does_not_pause(self):
        """A hi_latency tool WITH a cache entry should NOT pause — it should use the cached value."""

        async def ask_human(question):
            return "should not be called"

        tools = {
            "ask_human": {
                "fn": ask_human,
                "hi_latency": True,
            },
        }

        program = """
        answer = ask_human("Is this malicious?")
        return answer
        """

        # Step 1: Pause to get a real checkpoint with correct node_id
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)
        checkpoint = exc_info.value.checkpoint

        # Step 2: Inject the human's answer into the checkpoint
        checkpoint.pending_tool_result = "Yes, it is malicious"

        # Step 3: Resume — should NOT pause again, should use the cached answer
        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert result == "Yes, it is malicious"

    @pytest.mark.asyncio
    async def test_paused_checkpoint_contains_prior_results(self):
        """When pausing, the checkpoint should contain results from nodes executed before the pause."""
        call_log = []
        tools = {
            "fast_lookup": _make_recording_tool(
                "fast_lookup", {"ip": "1.2.3.4", "threat": "high"}, call_log
            ),
            "ask_analyst": {
                "fn": _make_async_tool("ask_analyst", "approve"),
                "hi_latency": True,
            },
        }

        program = """
        threat_info = fast_lookup("192.168.1.1")
        decision = ask_analyst("Should we block ${threat_info.ip}?")
        return decision
        """

        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        # The fast_lookup result should be in node_results
        assert len(checkpoint.node_results) >= 1
        # Variables should contain threat_info
        assert "threat_info" in checkpoint.variables
        assert checkpoint.variables["threat_info"]["ip"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_normal_tool_does_not_pause(self):
        """A regular (non-hi_latency) tool should never pause, even without a cache."""
        tools = {
            "fast_tool": _make_async_tool("fast_tool", "result"),
        }

        program = """
        x = fast_tool()
        return x
        """

        interpreter = Cy(tools=tools)
        result = await interpreter.run_native_async(program)
        assert result == "result"  # No pause, runs to completion


# ===========================================================================
# R4: ExecutionCheckpoint serialization
# ===========================================================================


class TestCheckpointSerialization:
    """R4: ExecutionCheckpoint must be JSON-serializable for storage in PostgreSQL."""

    def test_checkpoint_to_json_and_back(self):
        """Checkpoint should round-trip through JSON without data loss."""
        checkpoint = ExecutionCheckpoint(
            node_results={
                "node_1": "lookup_result",
                "node_2": {"key": "value", "nested": [1, 2, 3]},
            },
            pending_node_id="node_3",
            pending_tool_name="slack::ask_question",
            pending_tool_args={"destination": "U123", "question": "Block IP?"},
            pending_tool_result=None,
            variables={
                "threat_info": {"ip": "10.0.0.1", "score": 95},
                "count": 5,
            },
            plan_version="2.0",
            captured_logs=[],
        )

        json_str = checkpoint.to_json()
        restored = ExecutionCheckpoint.from_json(json_str)

        assert restored.node_results == checkpoint.node_results
        assert restored.pending_node_id == checkpoint.pending_node_id
        assert restored.pending_tool_name == checkpoint.pending_tool_name
        assert restored.pending_tool_args == checkpoint.pending_tool_args
        assert restored.pending_tool_result is None
        assert restored.variables == checkpoint.variables
        assert restored.plan_version == checkpoint.plan_version

    def test_checkpoint_to_dict_and_back(self):
        """Checkpoint should round-trip through dict for DB storage."""
        checkpoint = ExecutionCheckpoint(
            node_results={"n1": 42},
            pending_node_id="n2",
            pending_tool_name="ask",
            pending_tool_args={"q": "yes?"},
            pending_tool_result="yes",
            variables={"x": 1},
            plan_version="2.0",
            captured_logs=[],
        )

        d = checkpoint.to_dict()
        assert isinstance(d, dict)

        restored = ExecutionCheckpoint.from_dict(d)
        assert restored.node_results == {"n1": 42}
        assert restored.pending_tool_result == "yes"

    def test_checkpoint_json_is_valid_json(self):
        """The JSON output should be parseable by standard json.loads."""
        checkpoint = ExecutionCheckpoint(
            node_results={},
            pending_node_id="n1",
            pending_tool_name="tool",
            pending_tool_args={},
            pending_tool_result=None,
            variables={},
            plan_version="2.0",
            captured_logs=[],
        )
        parsed = json.loads(checkpoint.to_json())
        assert "pending_tool_name" in parsed
        assert parsed["plan_version"] == "2.0"


# ===========================================================================
# R5: Resume via checkpoint on run_async / run_native_async
# ===========================================================================


class TestResumeViaCheckpoint:
    """R5: Interpreter accepts checkpoint param to resume paused execution."""

    @pytest.mark.asyncio
    async def test_resume_with_human_answer(self):
        """Full pause-resume cycle: first call pauses, second call resumes with answer."""
        call_log = []

        async def ask_human(question):
            # This should only be called on the first (pausing) run,
            # never on resume
            call_log.append("ask_human_called")
            return "should_not_reach"

        tools = {
            "ask_human": {
                "fn": ask_human,
                "hi_latency": True,
            },
        }

        program = """
        answer = ask_human("Approve remediation?")
        return answer
        """

        # Step 1: First run pauses
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert checkpoint.pending_tool_name == "ask_human"
        assert len(call_log) == 0  # The tool is NOT actually called on pause

        # Step 2: Human responds — inject answer into checkpoint
        checkpoint.pending_tool_result = "Approved"

        # Step 3: Resume with checkpoint
        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert result == "Approved"
        assert len(call_log) == 0  # Tool still not called — used cached result

    @pytest.mark.asyncio
    async def test_resume_skips_already_executed_tools(self):
        """On resume, tools that ran before the pause should use cached results (no re-execution)."""
        call_log = []

        tools = {
            "expensive_llm": _make_recording_tool(
                "expensive_llm", "llm_analysis", call_log
            ),
            "ask_analyst": {
                "fn": _make_async_tool("ask_analyst", "should_not_call"),
                "hi_latency": True,
            },
        }

        program = """
        analysis = expensive_llm("analyze this alert")
        decision = ask_analyst("Do you agree with: ${analysis}?")
        return decision
        """

        # Step 1: Run until pause
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert len(call_log) == 1  # expensive_llm was called
        assert call_log[0]["name"] == "expensive_llm"

        # Step 2: Resume with answer
        call_log.clear()
        checkpoint.pending_tool_result = "I agree, block it"

        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert result == "I agree, block it"
        assert len(call_log) == 0  # expensive_llm NOT re-called — used cache

    @pytest.mark.asyncio
    async def test_resume_run_async_returns_json(self):
        """run_async (not run_native_async) should also support checkpoint resume."""
        tools = {
            "ask": {
                "fn": _make_async_tool("ask", "unused"),
                "hi_latency": True,
            },
        }

        program = """
        answer = ask("question")
        return answer
        """

        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_async(program)

        checkpoint = exc_info.value.checkpoint
        checkpoint.pending_tool_result = "the_answer"

        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_async(program, checkpoint=checkpoint)
        # run_async returns JSON string
        assert json.loads(result) == "the_answer"


# ===========================================================================
# R6: Control flow replay with cache
# ===========================================================================


class TestControlFlowReplay:
    """R6: Memoized replay works correctly through control flow (if/else, loops)."""

    @pytest.mark.asyncio
    async def test_if_branch_replay_after_resume(self):
        """After resume, if/else should follow the same branch using cached variables."""
        call_log = []

        tools = {
            "check_threat": _make_recording_tool("check_threat", "high", call_log),
            "ask_human": {
                "fn": _make_async_tool("ask_human", "unused"),
                "hi_latency": True,
            },
            "block_ip": _make_recording_tool("block_ip", "blocked", call_log),
        }

        program = """
        severity = check_threat("192.168.1.1")
        if (severity == "high") {
            decision = ask_human("Block this high-severity threat?")
            if (decision == "yes") {
                result = block_ip("192.168.1.1")
                return result
            }
            return "skipped"
        }
        return "low severity"
        """

        # Step 1: Pauses at ask_human
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        call_log.clear()

        # Step 2: Resume with "yes" — should take the block_ip branch
        checkpoint.pending_tool_result = "yes"
        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert result == "blocked"
        # check_threat should NOT be re-called (cached)
        check_calls = [c for c in call_log if c["name"] == "check_threat"]
        assert len(check_calls) == 0
        # block_ip SHOULD be called (not cached, runs after resume)
        block_calls = [c for c in call_log if c["name"] == "block_ip"]
        assert len(block_calls) == 1

    @pytest.mark.asyncio
    async def test_multiple_hi_latency_tools_pause_at_first(self):
        """If a script has multiple hi_latency tools, it pauses at the first one encountered."""
        tools = {
            "ask_first": {
                "fn": _make_async_tool("ask_first", "unused"),
                "hi_latency": True,
            },
            "ask_second": {
                "fn": _make_async_tool("ask_second", "unused"),
                "hi_latency": True,
            },
        }

        program = """
        a = ask_first("Question 1")
        b = ask_second("Question 2")
        return "${a} and ${b}"
        """

        # First pause: at ask_first
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        cp1 = exc_info.value.checkpoint
        assert cp1.pending_tool_name == "ask_first"

        # Resume first, should pause at ask_second
        cp1.pending_tool_result = "Answer1"
        interpreter2 = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info2:
            await interpreter2.run_native_async(program, checkpoint=cp1)

        cp2 = exc_info2.value.checkpoint
        assert cp2.pending_tool_name == "ask_second"
        # ask_first's result should be in the cache
        assert "Answer1" in cp2.node_results.values()

        # Resume second, should complete
        cp2.pending_tool_result = "Answer2"
        interpreter3 = Cy(tools=tools)
        result = await interpreter3.run_native_async(program, checkpoint=cp2)
        assert "Answer1" in result
        assert "Answer2" in result

    @pytest.mark.asyncio
    async def test_loop_with_hi_latency_tool(self):
        """A hi_latency tool inside a loop should pause at the first iteration it encounters."""
        call_log = []
        tools = {
            "get_items": _make_recording_tool(
                "get_items", ["item_a", "item_b"], call_log
            ),
            "review_item": {
                "fn": _make_async_tool("review_item", "unused"),
                "hi_latency": True,
            },
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

        # Should pause at first review_item call
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert checkpoint.pending_tool_name == "review_item"


# ===========================================================================
# P1: Restore checkpoint variables on resume
# ===========================================================================


class TestCheckpointVariableRestore:
    """P1: Resumed execution must restore variables from the checkpoint."""

    @pytest.mark.asyncio
    async def test_resume_restores_variables_from_checkpoint(self):
        """Variables computed before the pause should be available after resume."""
        call_log = []
        tools = {
            "lookup": _make_recording_tool("lookup", "threat_data", call_log),
            "ask_human": {
                "fn": _make_async_tool("ask_human", "unused"),
                "hi_latency": True,
            },
        }

        program = """
        info = lookup("192.168.1.1")
        decision = ask_human("Review: ${info}")
        return "Decision: ${decision}, Info: ${info}"
        """

        # Step 1: Pause
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint
        assert "info" in checkpoint.variables
        call_log.clear()

        # Step 2: Resume — info should be available from checkpoint variables
        checkpoint.pending_tool_result = "approved"
        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert "threat_data" in result
        assert "approved" in result


# ===========================================================================
# P2: Null pending_tool_result must be distinguishable from "not set"
# ===========================================================================


class TestNullPendingToolResult:
    """P2: A human can legitimately respond with null/None."""

    @pytest.mark.asyncio
    async def test_resume_with_null_answer_completes(self):
        """Resuming with pending_tool_result=None (the human answered null) should complete."""
        tools = {
            "ask_human": {
                "fn": _make_async_tool("ask_human", "unused"),
                "hi_latency": True,
            },
        }

        program = """
        answer = ask_human("Any comments?")
        result = answer ?? "no comment"
        return result
        """

        # Step 1: Pause
        interpreter = Cy(tools=tools)
        with pytest.raises(ExecutionPaused) as exc_info:
            await interpreter.run_native_async(program)

        checkpoint = exc_info.value.checkpoint

        # Step 2: Human intentionally answers null
        checkpoint.pending_tool_result = None

        # Step 3: Resume — should NOT pause again, should complete with null answer
        interpreter2 = Cy(tools=tools)
        result = await interpreter2.run_native_async(program, checkpoint=checkpoint)
        assert result == "no comment"


# ===========================================================================
# P4: Non-JSON-serializable tool outputs in checkpoints
# ===========================================================================


class TestCheckpointNonJsonTypes:
    """P4: Checkpoint sanitizer must handle datetime, UUID, set, and custom objects."""

    def test_sanitize_datetime(self):
        """datetime objects should be converted to string."""
        import datetime

        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        result = PlanExecutor._sanitize_for_json(dt)
        assert isinstance(result, str)
        assert "2024" in result

    def test_sanitize_set(self):
        """set objects should be converted to a list."""
        s = {1, 2, 3}
        result = PlanExecutor._sanitize_for_json(s)
        assert isinstance(result, list)
        assert sorted(result) == [1, 2, 3]

    def test_sanitize_uuid(self):
        """UUID objects should be converted to string."""
        import uuid

        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = PlanExecutor._sanitize_for_json(u)
        assert isinstance(result, str)
        assert "12345678" in result

    def test_sanitize_custom_object(self):
        """Custom objects should be converted to string."""

        class MyModel:
            def __init__(self):
                self.name = "test"

            def __repr__(self):
                return "MyModel(name='test')"

        result = PlanExecutor._sanitize_for_json(MyModel())
        assert isinstance(result, str)

    def test_sanitize_nested_non_json_types(self):
        """Non-JSON types nested in dicts/lists should be sanitized."""
        import datetime

        data = {
            "timestamp": datetime.datetime(2024, 1, 1),
            "tags": {1, 2, 3},
            "items": [datetime.date(2024, 6, 15)],
        }
        result = PlanExecutor._sanitize_for_json(data)
        # Should be JSON-serializable now
        json.dumps(result)  # Should not raise
