"""Tests for the Cy language error classes."""

from cy_language.errors import (
    CyError,
    InterpolationError,
    NameError,
    NotSupportedYetError,
    RuntimeError,
    SyntaxError,
    ToolError,
    ToolInvocationError,
    ToolNotFoundError,
)


def test_cy_error_basic():
    """Test basic CyError functionality."""
    error = CyError("Test error message")
    assert "Test error message" in str(error)
    assert error.line is None
    assert error.col is None


def test_cy_error_with_line_col():
    """Test CyError with line and column information."""
    error = CyError("Test error message", line=5, col=10)
    assert "Line 5, Col 10: Test error message" in str(error)
    assert error.line == 5
    assert error.col == 10


def test_cy_error_to_dict():
    """Test CyError to_dict method."""
    error = CyError("Test error message", line=5, col=10)
    error_dict = error.to_dict()

    assert error_dict["type"] == "CyError"
    assert error_dict["line"] == 5
    assert error_dict["col"] == 10
    assert error_dict["message"] == "Test error message"


def test_error_subclasses():
    """Test error subclasses."""
    errors = [
        SyntaxError("Syntax error"),
        RuntimeError("Runtime error"),
        InterpolationError("Interpolation error"),
        NameError("Name error"),
        ToolError("Tool error"),
        ToolNotFoundError("Tool not found"),
        ToolInvocationError("Tool invocation error"),
        NotSupportedYetError("Not supported yet"),
    ]

    for error in errors:
        assert isinstance(error, CyError)
        assert error.__class__.__name__ in str(error.to_dict()["type"])
