"""Tests for non-UI functions in the Streamlit app.py module."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cy_language.ui.app import init_session_state, load_example, run_cy_program


class MockSessionState(dict):
    """Dict subclass that supports attribute access (mimics st.session_state)."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(f"'MockSessionState' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


@pytest.fixture
def mock_st() -> Any:
    """Fixture that patches ``streamlit`` inside ``cy_language.ui.app``."""
    with patch("cy_language.ui.app.st") as patched:
        patched.session_state = MockSessionState()
        yield patched


# ── init_session_state ─────────────────────────────────────────────────


def test_init_session_state(mock_st: Any) -> None:
    """All expected keys are initialised with correct defaults."""
    init_session_state()

    ss = mock_st.session_state

    # Keys must exist
    for key in (
        "cy_code",
        "cy_input",
        "cy_output",
        "example_source",
        "interpolation_mode",
        "item_tag",
        "parallel_enabled",
        "parallel_threshold",
        "last_run_ms",
    ):
        assert key in ss, f"Missing session-state key: {key}"

    # Default program must contain key phrases (regression guard)
    assert "namespaced functions" in ss.cy_code
    assert "len" in ss.cy_code
    assert "str::uppercase" in ss.cy_code

    # Scalar defaults
    assert ss.cy_input == ""
    assert ss.cy_output == ""
    assert ss.example_source == ""
    assert ss.interpolation_mode == "markdown"
    assert ss.item_tag == "item"
    assert ss.parallel_enabled is False
    assert ss.parallel_threshold == 2
    assert ss.last_run_ms is None


def test_init_session_state_has_logs_and_error_flag(mock_st: Any) -> None:
    """Session state includes cy_logs (list) and cy_is_error (bool)."""
    init_session_state()
    ss = mock_st.session_state

    assert "cy_logs" in ss, "Missing session-state key: cy_logs"
    assert ss.cy_logs == []
    assert "cy_is_error" in ss, "Missing session-state key: cy_is_error"
    assert ss.cy_is_error is False


# ── load_example ───────────────────────────────────────────────────────


def test_load_example(mock_st: Any) -> None:
    """Built-in examples load the expected source code."""
    mock_st.session_state.cy_code = "// placeholder"

    load_example("basic")
    assert "Hello, $name!" in mock_st.session_state.cy_code

    load_example("list")
    assert "fruits" in mock_st.session_state.cy_code.lower()
    assert "apple" in mock_st.session_state.cy_code

    load_example("struct")
    assert "User #${user.id}" in mock_st.session_state.cy_code


def test_load_example_invalid_key_keeps_previous_code(mock_st: Any) -> None:
    """An invalid key does not overwrite the current editor content."""
    mock_st.session_state.cy_code = "keep me"
    load_example("nonexistent")
    assert mock_st.session_state.cy_code == "keep me"


# ── run_cy_program ─────────────────────────────────────────────────────

_COMMON_STATE = {
    "cy_input": "",
    "cy_output": "",
    "cy_logs": [],
    "cy_is_error": False,
    "interpolation_mode": "markdown",
    "item_tag": "item",
    "parallel_enabled": False,
    "parallel_threshold": 2,
    "last_run_ms": None,
}


def _prepare_run_state(mock_st: Any, code: str, **overrides: Any) -> None:
    """Populate session state for a ``run_cy_program`` call."""
    mock_st.session_state.cy_code = code
    for k, v in {**_COMMON_STATE, **overrides}.items():
        mock_st.session_state[k] = v


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_success(mock_cy_class: Any, mock_st: Any) -> None:
    """A successful run stores the interpreter result in session state."""
    _prepare_run_state(mock_st, '$output = "Test output"')

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value="Test output")
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_output == "Test output"
    assert isinstance(mock_st.session_state.last_run_ms, int)


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_success_clears_error_flag(
    mock_cy_class: Any, mock_st: Any
) -> None:
    """A successful run sets cy_is_error to False."""
    _prepare_run_state(mock_st, 'return "ok"', cy_is_error=True)

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value='"ok"')
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_is_error is False


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_captures_logs(mock_cy_class: Any, mock_st: Any) -> None:
    """Captured logs are stored in session state after execution."""
    _prepare_run_state(mock_st, 'log("hello")\nreturn "done"')

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value='"done"')
    # Simulate the interpreter populating captured_logs
    interpreter.captured_logs = [
        {"ts": 1700000000.0, "message": "hello"},
    ]
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_logs == [
        {"ts": 1700000000.0, "message": "hello"},
    ]


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_passes_captured_logs(mock_cy_class: Any, mock_st: Any) -> None:
    """create_async is called with a captured_logs list."""
    _prepare_run_state(mock_st, 'return "ok"')

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value='"ok"')
    interpreter.captured_logs = []
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    _, kwargs = mock_cy_class.create_async.call_args
    assert "captured_logs" in kwargs
    assert isinstance(kwargs["captured_logs"], list)


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_with_json_input(mock_cy_class: Any, mock_st: Any) -> None:
    """JSON input is parsed before being passed to the interpreter."""
    _prepare_run_state(
        mock_st,
        '$output = "Hello, ${input.name}!"',
        cy_input='{"name": "Alice"}',
    )

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value="Hello, Alice!")
    interpreter.captured_logs = []
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_output == "Hello, Alice!"


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_with_error(mock_cy_class: Any, mock_st: Any) -> None:
    """Runtime errors are captured into session state."""
    _prepare_run_state(mock_st, "Invalid code")

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(side_effect=Exception("Test error"))
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert "Test error" in mock_st.session_state.cy_output


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_error_sets_flag(mock_cy_class: Any, mock_st: Any) -> None:
    """Runtime errors set cy_is_error to True."""
    _prepare_run_state(mock_st, "Invalid code")

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(side_effect=Exception("Test error"))
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_is_error is True


@patch("cy_language.ui.app.Cy")
def test_run_cy_program_with_invalid_json(mock_cy_class: Any, mock_st: Any) -> None:
    """Invalid JSON input falls back to raw string without crashing."""
    _prepare_run_state(
        mock_st,
        '$output = "Process input"',
        cy_input="{ invalid json",
    )

    interpreter = MagicMock()
    interpreter.run_async = AsyncMock(return_value="Process input")
    interpreter.captured_logs = []
    mock_cy_class.create_async = AsyncMock(return_value=interpreter)

    run_cy_program()

    assert mock_st.session_state.cy_output == "Process input"


# ── _render_output ─────────────────────────────────────────────────────


class TestRenderOutput:
    """Verify _render_output handles all output types correctly."""

    def _setup_state(self, mock_st: Any, output: str, is_error: bool = False) -> None:
        mock_st.session_state.cy_output = output
        mock_st.session_state.cy_is_error = is_error
        mock_st.session_state.last_run_ms = 42

    def test_never_run_shows_info(self, mock_st: Any) -> None:
        """When program has never been run, show an info hint."""
        from cy_language.ui.app import _render_output

        mock_st.session_state.cy_output = ""
        mock_st.session_state.cy_is_error = False
        mock_st.session_state.last_run_ms = None

        _render_output()

        mock_st.info.assert_called_once()

    def test_empty_output_shows_success(self, mock_st: Any) -> None:
        """Empty output after a run shows success message."""
        from cy_language.ui.app import _render_output

        self._setup_state(mock_st, "")
        _render_output()
        mock_st.success.assert_called_once()

    def test_json_object_uses_st_json(self, mock_st: Any) -> None:
        """JSON objects are rendered with st.json() for interactivity."""
        from cy_language.ui.app import _render_output

        self._setup_state(mock_st, '{"key": "value"}')
        _render_output()
        mock_st.json.assert_called_once()
        mock_st.code.assert_not_called()

    def test_json_array_uses_st_json(self, mock_st: Any) -> None:
        """JSON arrays are rendered with st.json()."""
        from cy_language.ui.app import _render_output

        self._setup_state(mock_st, "[1, 2, 3]")
        _render_output()
        mock_st.json.assert_called_once()

    def test_plain_string_uses_st_code(self, mock_st: Any) -> None:
        """JSON-encoded string is decoded and rendered with st.code()."""
        from cy_language.ui.app import _render_output

        self._setup_state(mock_st, '"Hello, world!"')
        _render_output()
        mock_st.code.assert_called_once_with("Hello, world!", language=None)
        mock_st.json.assert_not_called()

    def test_string_with_newlines_decoded(self, mock_st: Any) -> None:
        r"""JSON-encoded \\n sequences become real newlines in display."""
        from cy_language.ui.app import _render_output

        # This is what run_async() returns for a multi-line string result
        self._setup_state(mock_st, '"line 1\\nline 2"')
        _render_output()
        mock_st.code.assert_called_once_with("line 1\nline 2", language=None)

    def test_error_uses_is_error_flag(self, mock_st: Any) -> None:
        """Error rendering uses cy_is_error flag, not substring match."""
        from cy_language.ui.app import _render_output

        # A successful return value that contains "Error" in the text
        self._setup_state(mock_st, '{"status": "Error loading complete"}')
        _render_output()
        # Should use json rendering (success path), not error path
        mock_st.json.assert_called_once()
        mock_st.error.assert_not_called()

    def test_error_output_renders_error_block(self, mock_st: Any) -> None:
        """Error output is rendered with st.error()."""
        from cy_language.ui.app import _render_output

        self._setup_state(
            mock_st, "Line 5, Col 3: Variable 'x' is not defined", is_error=True
        )
        _render_output()
        mock_st.error.assert_called()

    def test_error_with_suggestion_renders_separately(self, mock_st: Any) -> None:
        """Errors with 'Suggestion:' split the suggestion into st.info()."""
        from cy_language.ui.app import _render_output

        error_msg = (
            "Line 3, Col 5: Unexpected operator '&&'\n\n"
            "Suggestion: Use 'and' instead of '&&' in Cy"
        )
        self._setup_state(mock_st, error_msg, is_error=True)
        _render_output()
        mock_st.info.assert_called()
        # Verify suggestion text is in the info call
        info_text = mock_st.info.call_args[0][0]
        assert "and" in info_text

    def test_error_with_ansi_codes_strips_them(self, mock_st: Any) -> None:
        """ANSI color codes are stripped from error output."""
        from cy_language.ui.app import _render_output

        ansi_error = "\x1b[91mError at line 1:\x1b[0m bad stuff"
        self._setup_state(mock_st, ansi_error, is_error=True)
        _render_output()
        # The error call should have clean text (no ANSI codes)
        error_text = mock_st.error.call_args[0][0]
        assert "\x1b[" not in error_text

    def test_error_with_source_context_renders_code_block(self, mock_st: Any) -> None:
        """Errors with source context (line numbers + pointer) render
        the context in a code block separate from the error message."""
        from cy_language.ui.app import _render_output

        error_msg = (
            "CompilerError at line 3, column 5:\n"
            "\n"
            "   1 | data = [1, 2, 3]\n"
            "   2 | x = 10\n"
            "   3 | y = x && 5\n"
            "     |     ^\n"
            "\n"
            "Unexpected operator '&&'\n"
            "\n"
            "Suggestion: Use 'and' instead of '&&' in Cy"
        )
        self._setup_state(mock_st, error_msg, is_error=True)
        _render_output()
        # Should render code context separately
        mock_st.code.assert_called()
        # Suggestion should appear in an info box
        mock_st.info.assert_called()


# ── _parse_enhanced_error ──────────────────────────────────────────────


class TestParseEnhancedError:
    """Verify structured parsing of enhanced error messages."""

    def test_simple_error(self) -> None:
        """Plain error without source context."""
        from cy_language.ui.app import _parse_enhanced_error

        parts = _parse_enhanced_error("Variable 'x' is not defined")
        assert parts["message"] == "Variable 'x' is not defined"
        assert parts["header"] is None
        assert parts["context"] is None
        assert parts["suggestion"] is None

    def test_error_with_suggestion(self) -> None:
        """Error with Suggestion: marker."""
        from cy_language.ui.app import _parse_enhanced_error

        text = "Unexpected operator '&&'\n\nSuggestion: Use 'and' instead"
        parts = _parse_enhanced_error(text)
        assert parts["message"] == "Unexpected operator '&&'"
        assert parts["suggestion"] == "Use 'and' instead"

    def test_full_enhanced_error(self) -> None:
        """Full enhanced error with header, context, message, suggestion."""
        from cy_language.ui.app import _parse_enhanced_error

        text = (
            "CompilerError at line 3, column 5:\n"
            "\n"
            "   1 | data = [1, 2, 3]\n"
            "   2 | x = 10\n"
            "   3 | y = x && 5\n"
            "     |     ^\n"
            "\n"
            "Unexpected operator '&&'\n"
            "\n"
            "Suggestion: Use 'and' instead of '&&' in Cy"
        )
        parts = _parse_enhanced_error(text)
        assert parts["header"] is not None
        assert "CompilerError" in parts["header"]
        assert parts["context"] is not None
        assert "   3 | y = x && 5" in parts["context"]
        assert "^" in parts["context"]
        assert parts["message"] == "Unexpected operator '&&'"
        assert parts["suggestion"] == "Use 'and' instead of '&&' in Cy"

    def test_error_no_suggestion(self) -> None:
        """Enhanced error without suggestion."""
        from cy_language.ui.app import _parse_enhanced_error

        text = (
            "RuntimeError at line 5, column 1:\n"
            "\n"
            "   5 | result = bad_call()\n"
            "     | ^\n"
            "\n"
            "Tool 'bad_call' not found"
        )
        parts = _parse_enhanced_error(text)
        assert parts["header"] is not None
        assert parts["context"] is not None
        assert parts["suggestion"] is None
        assert "bad_call" in (parts["message"] or "")


# ── _render_logs ───────────────────────────────────────────────────────


class TestRenderLogs:
    """Verify log output rendering."""

    def test_no_logs_shows_hint(self, mock_st: Any) -> None:
        """When there are no logs, show an info message."""
        from cy_language.ui.app import _render_logs

        mock_st.session_state.cy_logs = []
        mock_st.session_state.last_run_ms = None

        _render_logs()

        mock_st.caption.assert_called()

    def test_logs_render_entries(self, mock_st: Any) -> None:
        """Log entries are rendered as text elements with timestamps."""
        from cy_language.ui.app import _render_logs

        mock_st.session_state.cy_logs = [
            {"ts": 1700000000.0, "message": "Processing 3 items"},
            {"ts": 1700000001.0, "message": "First item uppercase: APPLE"},
        ]
        mock_st.session_state.last_run_ms = 42

        _render_logs()

        # Should render each log entry via st.text
        assert mock_st.text.call_count == 2

        # Each call should include the message and a timestamp
        first_call = mock_st.text.call_args_list[0][0][0]
        second_call = mock_st.text.call_args_list[1][0][0]

        assert "Processing 3 items" in first_call
        assert "+0ms" in first_call  # first entry is the baseline
        assert "First item uppercase: APPLE" in second_call
        assert "+1000ms" in second_call  # 1 second after baseline
