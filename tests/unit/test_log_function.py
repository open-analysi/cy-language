"""Unit tests for the log() native function.

Tests for log() function with captured_logs parameter and stderr fallback.
Log entries are dicts with {"ts": epoch_float, "message": str}.
"""

import sys
from io import StringIO

import pytest

from cy_language.interpreter import Cy


def log_msg(entry):
    """Extract message string from a log entry dict."""
    return entry["message"]


def assert_log_has_ts(entry):
    """Assert a log entry has a valid epoch timestamp."""
    assert isinstance(entry, dict), f"Log entry should be a dict, got {type(entry)}"
    assert "ts" in entry, "Log entry should have 'ts' key"
    assert isinstance(entry["ts"], float), (
        f"ts should be float, got {type(entry['ts'])}"
    )
    assert entry["ts"] > 0, "ts should be a positive epoch value"


class TestLogFunctionBasic:
    """Basic tests for log() function."""

    def test_log_with_captured_logs(self):
        """Test log() captures messages to provided list."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        log("First message")
        log("Second message")
        output = "done"
        return output
        """

        result = cy.run(program)

        assert result == '"done"'
        assert len(logs) == 2
        assert log_msg(logs[0]) == "First message"
        assert log_msg(logs[1]) == "Second message"
        assert_log_has_ts(logs[0])
        assert_log_has_ts(logs[1])

    def test_log_without_captured_logs_goes_to_stderr(self):
        """Test log() writes to stderr when captured_logs not provided."""
        # Capture stderr
        stderr_capture = StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_capture

        try:
            cy = Cy()  # No captured_logs

            program = """
            log("Test stderr message")
            output = "done"
            return output
            """

            result = cy.run(program)

            assert result == '"done"'
            stderr_output = stderr_capture.getvalue()
            assert "LOG: Test stderr message" in stderr_output

        finally:
            sys.stderr = old_stderr

    def test_log_returns_message(self):
        """Test that log() returns the logged message."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        msg = log("Test message")
        output = msg
        return output
        """

        result = cy.run(program)

        assert result == '"Test message"'
        assert log_msg(logs[0]) == "Test message"

    def test_log_entry_format(self):
        """Test that log entries are dicts with ts (epoch) and message."""
        logs = []
        cy = Cy(captured_logs=logs)

        cy.run('log("hello")\nreturn "ok"')

        assert len(logs) == 1
        entry = logs[0]
        assert isinstance(entry, dict)
        assert set(entry.keys()) == {"ts", "message"}
        assert isinstance(entry["ts"], float)
        assert entry["ts"] > 1_700_000_000  # after 2023
        assert entry["message"] == "hello"


class TestLogFunctionWithData:
    """Test log() with different data types."""

    def test_log_with_string(self):
        """Test logging string values."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        message = "Hello, world!"
        log(message)
        output = "done"
        return output
        """

        cy.run(program)
        assert log_msg(logs[0]) == "Hello, world!"

    def test_log_with_number(self):
        """Test logging numeric values."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        count = 42
        log(count)
        output = "done"
        return output
        """

        cy.run(program)
        assert log_msg(logs[0]) == "42"

    def test_log_with_list(self):
        """Test logging list values."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        items = [1, 2, 3]
        log(items)
        output = "done"
        return output
        """

        cy.run(program)
        assert "[1, 2, 3]" in log_msg(logs[0])

    def test_log_with_dict(self):
        """Test logging dict values."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        data = {"key": "value"}
        log(data)
        output = "done"
        return output
        """

        cy.run(program)
        assert "key" in log_msg(logs[0])
        assert "value" in log_msg(logs[0])

    def test_log_with_interpolation(self):
        """Test logging with string interpolation."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        name = "Alice"
        age = 30
        log("User: ${name}, Age: ${age}")
        output = "done"
        return output
        """

        cy.run(program)
        assert log_msg(logs[0]) == "User: Alice, Age: 30"


class TestLogFunctionInControlFlow:
    """Test log() in control flow structures."""

    def test_log_in_if_statement(self):
        """Test log() inside if statement."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        x = 10
        if (x > 5) {
            log("x is greater than 5")
        } else {
            log("x is not greater than 5")
        }
        output = "done"
        return output
        """

        cy.run(program)
        assert len(logs) == 1
        assert log_msg(logs[0]) == "x is greater than 5"

    def test_log_in_loop(self):
        """Test log() inside loop."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        for (i in [1, 2, 3]) {
            log("Processing item: ${i}")
        }
        output = "done"
        return output
        """

        cy.run(program)
        assert len(logs) == 3
        assert log_msg(logs[0]) == "Processing item: 1"
        assert log_msg(logs[1]) == "Processing item: 2"
        assert log_msg(logs[2]) == "Processing item: 3"

    @pytest.mark.asyncio
    async def test_log_in_loop_with_caching_enabled(self):
        """Test log() inside loop when HITL caching is enabled (async path).

        Regression: when hi_latency_tools made _caching_enabled=True,
        the static node_id caused cache hits on iterations 2+, skipping
        actual log() calls.  Only 1 log appeared instead of N.
        """
        logs = []
        # Provide a hi_latency tool to trigger _caching_enabled=True
        dummy_tool = {"fn": lambda: "ok", "hi_latency": True}
        cy = Cy(captured_logs=logs, tools={"slow_tool": dummy_tool})

        program = """
        for (i in [1, 2, 3, 4, 5]) {
            log("item ${i}")
        }
        return "done"
        """

        result = await cy.run_async(program)
        assert result == '"done"'
        assert len(logs) == 5, (
            f"Expected 5 log entries, got {len(logs)}: {[log_msg(entry) for entry in logs]}"
        )
        for idx in range(5):
            assert log_msg(logs[idx]) == f"item {idx + 1}"

    def test_log_in_try_catch(self):
        """Test log() in try-catch block."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        try {
            log("In try block")
            x = 10 / 0
        } catch (e) {
            log("In catch block")
        }
        output = "done"
        return output
        """

        cy.run(program)
        assert len(logs) == 2
        assert log_msg(logs[0]) == "In try block"
        assert log_msg(logs[1]) == "In catch block"


class TestLogFunctionMultiplePrograms:
    """Test log() with multiple program executions."""

    def test_same_logs_list_multiple_runs(self):
        """Test using same logs list across multiple runs."""
        logs = []
        cy = Cy(captured_logs=logs)

        # First run
        cy.run('log("First run")\noutput = "done"\nreturn output')
        assert len(logs) == 1

        # Second run - should append to same list
        cy.run('log("Second run")\noutput = "done"\nreturn output')
        assert len(logs) == 2
        assert log_msg(logs[0]) == "First run"
        assert log_msg(logs[1]) == "Second run"

    def test_different_logs_lists(self):
        """Test using different logs lists for different interpreters."""
        logs1 = []
        logs2 = []

        cy1 = Cy(captured_logs=logs1)
        cy2 = Cy(captured_logs=logs2)

        cy1.run('log("From interpreter 1")\noutput = "done"\nreturn output')
        cy2.run('log("From interpreter 2")\noutput = "done"\nreturn output')

        assert len(logs1) == 1
        assert len(logs2) == 1
        assert log_msg(logs1[0]) == "From interpreter 1"
        assert log_msg(logs2[0]) == "From interpreter 2"


class TestLogFunctionRealWorld:
    """Real-world usage patterns for log()."""

    def test_debugging_workflow(self):
        """Test typical debugging workflow."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        data = [1, 2, 3, 4, 5]
        log("Starting processing...")

        total = sum(data)
        log("Calculated total: ${total}")

        result_value = total * 2
        log("Final result: ${result_value}")

        output = result_value
        return output
        """

        result = cy.run(program)

        assert result == "30"
        assert len(logs) == 3
        assert log_msg(logs[0]) == "Starting processing..."
        assert log_msg(logs[1]) == "Calculated total: 15"
        assert log_msg(logs[2]) == "Final result: 30"

    def test_conditional_logging(self):
        """Test conditional logging based on program state."""
        logs = []
        cy = Cy(captured_logs=logs)

        program = """
        value_list = [10, 20, 30]

        for (val in value_list) {
            if (val > 15) {
                log("Large value: ${val}")
            } else {
                log("Small value: ${val}")
            }
        }

        output = "done"
        return output
        """

        cy.run(program)

        assert len(logs) == 3
        assert log_msg(logs[0]) == "Small value: 10"
        assert log_msg(logs[1]) == "Large value: 20"
        assert log_msg(logs[2]) == "Large value: 30"

    def test_timestamps_are_monotonically_increasing(self):
        """Test that log timestamps increase across entries."""
        logs = []
        cy = Cy(captured_logs=logs)

        cy.run('log("a")\nlog("b")\nlog("c")\nreturn "ok"')

        assert len(logs) == 3
        assert logs[0]["ts"] <= logs[1]["ts"] <= logs[2]["ts"]


class TestLogFunctionMaxGuard:
    """Test log truncation guard."""

    def test_max_captured_logs_truncates(self):
        """Logs beyond max_captured_logs are silently dropped with a marker."""
        logs = []
        cy = Cy(captured_logs=logs, max_captured_logs=5)

        # Generate 10 log entries
        program = """
        for (i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
            log("entry ${i}")
        }
        return "done"
        """

        cy.run(program)

        # Should have 5 entries + 1 truncation marker = 6
        assert len(logs) == 6
        assert log_msg(logs[4]) == "entry 5"
        assert "TRUNCATED" in log_msg(logs[5])

    def test_default_max_is_1000(self):
        """Default max_captured_logs is 1000."""
        cy = Cy(captured_logs=[])
        assert cy.max_captured_logs == 1000
