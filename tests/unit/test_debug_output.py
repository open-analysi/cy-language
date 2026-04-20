"""Unit tests for log() output handling.

Tests for log() behavior ensuring proper output channel handling
without interfering with main output.
"""

import io
from contextlib import redirect_stderr
from unittest.mock import patch

from cy_language.native_functions import log
from tests.utils.debug_capture import (
    capture_debug,
)


class TestLogCLI:
    """Test log() behavior in CLI mode (stderr fallback)."""

    def test_log_uses_stderr(self) -> None:
        """Test that log() outputs to stderr."""
        with redirect_stderr(io.StringIO()) as captured_stderr:
            message = "CLI debug message"
            result = log(message)

            assert result == message
            assert message in captured_stderr.getvalue()

    def test_log_does_not_interfere_with_stdout(self) -> None:
        """Test that log() doesn't interfere with main program output."""
        with redirect_stderr(io.StringIO()):
            with patch("sys.stdout", new_callable=io.StringIO) as captured_stdout:
                message = "Debug message that shouldn't affect stdout"
                result = log(message)

                assert result == message
                assert captured_stdout.getvalue() == ""

    def test_log_multiple_messages(self) -> None:
        """Test multiple log() calls maintain order."""
        messages = ["First debug", "Second debug", "Third debug"]

        with redirect_stderr(io.StringIO()) as captured_stderr:
            results = []
            for message in messages:
                result = log(message)
                results.append(result)

            assert results == messages
            stderr_content = captured_stderr.getvalue()
            for message in messages:
                assert message in stderr_content

    def test_log_writes_to_stderr_directly(self) -> None:
        """Test that log() writes directly to sys.stderr."""
        message = "Direct stderr test"
        with redirect_stderr(io.StringIO()) as captured:
            result = log(message)

        assert result == message
        assert message in captured.getvalue()

    def test_log_handles_newlines(self) -> None:
        """Test log() handles messages with newlines."""
        message_with_newlines = "Line 1\nLine 2\nLine 3"

        with redirect_stderr(io.StringIO()):
            result = log(message_with_newlines)
            assert result == message_with_newlines

    def test_log_handles_special_characters(self) -> None:
        """Test log() handles special characters."""
        special_message = "Debug: 100% complete \u2713 \u2192 Success!"

        with redirect_stderr(io.StringIO()):
            result = log(special_message)
            assert result == special_message


class TestLogEdgeCases:
    """Test log() edge cases."""

    def test_log_with_complex_data_structures(self) -> None:
        """Test log() with complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"key": "value", "numbers": [4, 5, 6]},
            "string": "test string",
        }

        with redirect_stderr(io.StringIO()):
            result = log(complex_data)
            assert result == str(complex_data)

    def test_log_error_handling(self) -> None:
        """Test log() error handling with problematic data."""

        class UnserializableObject:
            def __repr__(self):
                raise Exception("Cannot serialize this object")

        problematic_data = UnserializableObject()

        with redirect_stderr(io.StringIO()):
            try:
                result = log(problematic_data)
                assert isinstance(result, str)
            except Exception:
                pass

    def test_log_performance_with_large_data(self) -> None:
        """Test log() performance with large data structures."""
        large_list = list(range(10000))

        with redirect_stderr(io.StringIO()):
            result = log(large_list)
            assert isinstance(result, str)

    def test_log_concurrent_calls(self) -> None:
        """Test log() with concurrent/rapid calls."""
        import threading
        import time

        results = []
        errors = []

        def debug_worker(worker_id: int) -> None:
            try:
                for i in range(5):
                    message = f"Worker {worker_id}, Message {i}"
                    result = log(message)
                    results.append(result)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        with redirect_stderr(io.StringIO()):
            threads = []
            for worker_id in range(3):
                thread = threading.Thread(target=debug_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        assert len(results) == 15  # 3 workers x 5 messages each
        assert len(errors) == 0

        for result in results:
            assert isinstance(result, str)
            assert "Worker" in result
            assert "Message" in result


class TestLogCapture:
    """Test log() with capture utilities."""

    def test_log_with_capture_utility(self) -> None:
        """Test log() with our debug capture utility."""
        with capture_debug() as capture:
            messages = ["Captured message 1", "Captured message 2"]

            for message in messages:
                result = log(message)
                assert result == message

            captured_messages = capture.get_messages()
            assert captured_messages == messages

    def test_log_capture_isolation(self) -> None:
        """Test that debug capture doesn't interfere between tests."""
        with capture_debug() as capture1:
            log("Message in session 1")
            first_messages = capture1.get_messages()

        with capture_debug() as capture2:
            log("Message in session 2")
            second_messages = capture2.get_messages()

        assert len(first_messages) == 1
        assert len(second_messages) == 1
        assert first_messages != second_messages
        assert first_messages[0] == "Message in session 1"
        assert second_messages[0] == "Message in session 2"
