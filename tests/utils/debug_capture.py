"""Debug output capture system for testing log() functionality.

This module provides utilities to capture and verify debug output from
the log() function.
"""

import io
import sys
from collections.abc import Generator
from contextlib import contextmanager


class DebugCapture:
    """Capture debug output for testing purposes."""

    def __init__(self) -> None:
        """Initialize debug capture system."""
        self.captured_messages: list[str] = []
        self.stderr_capture: io.StringIO | None = None
        self.original_stderr = None

    def clear(self) -> None:
        """Clear all captured messages."""
        self.captured_messages.clear()
        if self.stderr_capture:
            self.stderr_capture.seek(0)
            self.stderr_capture.truncate(0)

    def get_messages(self) -> list[str]:
        """Get all captured debug messages.

        Returns:
            List of captured debug messages
        """
        if self.stderr_capture:
            stderr_content = self.stderr_capture.getvalue()
            if stderr_content:
                # Extract log messages (they start with "LOG: ")
                lines = stderr_content.strip().split("\n")
                messages = []
                for line in lines:
                    if line.startswith("LOG: "):
                        messages.append(line[5:])  # Remove "LOG: " prefix
                return messages
        return self.captured_messages

    def get_last_message(self) -> str | None:
        """Get the last captured debug message.

        Returns:
            Last debug message or None if no messages captured
        """
        messages = self.get_messages()
        return messages[-1] if messages else None


@contextmanager
def capture_debug() -> Generator[DebugCapture, None, None]:
    """Context manager to capture debug output during testing.

    Usage:
        with capture_debug() as capture:
            log("test message")
            assert "test message" in capture.get_messages()

    Yields:
        DebugCapture instance for inspecting captured output
    """
    capture = DebugCapture()
    capture.original_stderr = sys.stderr
    capture.stderr_capture = io.StringIO()

    # Redirect stderr to our capture buffer
    sys.stderr = capture.stderr_capture

    try:
        yield capture
    finally:
        # Restore original stderr
        sys.stderr = capture.original_stderr


@contextmanager
def capture_stderr() -> Generator[io.StringIO, None, None]:
    """Context manager to capture stderr output.

    Yields:
        StringIO object containing captured stderr
    """
    original_stderr = sys.stderr
    captured_stderr = io.StringIO()
    try:
        sys.stderr = captured_stderr
        yield captured_stderr
    finally:
        sys.stderr = original_stderr
