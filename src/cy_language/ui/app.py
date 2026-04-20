"""Cy Language Editor — interactive playground for the Cy scripting language.

A Streamlit-based web UI for writing, running, and debugging Cy programs.
This is strictly a development tool; the Cy language works independently
as a Python library.
"""

import contextlib
import json
import re
import time
from datetime import UTC

import streamlit as st

# Type stub missing for streamlit_ace
from streamlit_ace import st_ace  # type: ignore

# Side-effect imports: register native functions into the global registry
import cy_language.native_functions
import cy_language.ui.example_tools  # noqa: F401
from cy_language import Cy
from cy_language.ui.examples import EXAMPLES, get_test_examples
from cy_language.ui.styles import CUSTOM_CSS
from cy_language.ui.tools import default_registry, test_registry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_PROGRAM = """\
# Cy Language — namespaced functions example

data = ["apple", "banana", "cherry"]
count = len(data)
log("Processing ${count} items")

# String namespace
upper_first = str::uppercase(data[0])
log("First item uppercase: ${upper_first}")

# JSON namespace
json_str = json::stringify(data, 2)

# Math namespace
value = math::abs(-42)

result = "Items (${count}): ${json_str}"
return result
"""

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


def init_session_state() -> None:
    """Initialise Streamlit session state with sensible defaults."""
    defaults: dict = {
        "cy_code": _DEFAULT_PROGRAM,
        "cy_input": "",
        "cy_output": "",
        "cy_logs": [],
        "cy_is_error": False,
        "example_source": "",
        "interpolation_mode": "markdown",
        "item_tag": "item",
        "parallel_enabled": False,
        "parallel_threshold": 2,
        "last_run_ms": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Example loading
# ---------------------------------------------------------------------------


def load_example(example_key: str) -> None:
    """Load a built-in example program into the editor."""
    test_examples = get_test_examples()

    if example_key not in test_examples:
        return

    st.session_state.cy_code = test_examples[example_key]
    st.session_state.example_source = f"Built-in: {example_key}"

    # Bump the refresh counter so the ACE editor picks up the new value.
    st.session_state["editor_refresh_key"] = (
        st.session_state.get("editor_refresh_key", 0) + 1
    )


# ---------------------------------------------------------------------------
# Program execution
# ---------------------------------------------------------------------------


async def run_cy_program_async() -> None:
    """Execute the current Cy program and store the result in session state."""
    code = st.session_state.cy_code

    # Reset logs for this run
    st.session_state.cy_logs = []

    try:
        # Merge default + test tool registries
        tools_dict = default_registry.get_tools_dict()
        tools_dict.update(test_registry.get_tools_dict())

        if "len" not in tools_dict:
            st.session_state.cy_output = (
                "Native functions not loaded. Please restart the server."
            )
            st.session_state.cy_is_error = True
            return

        # Capture log() calls so we can display them in the Logs tab
        captured_logs: list = []

        interpreter = await Cy.create_async(
            tools=tools_dict,
            interpolation_mode=st.session_state.interpolation_mode,
            item_tag=st.session_state.item_tag,
            enable_parallel=st.session_state.parallel_enabled,
            parallel_threshold=st.session_state.parallel_threshold,
            captured_logs=captured_logs,
        )

        # Parse JSON input when it looks like JSON; fall back to raw string.
        input_data = st.session_state.cy_input
        if input_data and input_data.strip().startswith(("{", "[")):
            with contextlib.suppress(json.JSONDecodeError):
                input_data = json.loads(input_data)

        result = await interpreter.run_async(code, input_data)
        st.session_state.cy_output = result
        st.session_state.cy_is_error = False

        # Store captured logs (prefer interpreter's list which may be updated
        # by the runtime; fall back to our local list passed at construction).
        st.session_state.cy_logs = (
            interpreter.captured_logs
            if interpreter.captured_logs is not None
            else captured_logs
        )

    except Exception as exc:
        # Strip ANSI codes from the error message for clean storage
        st.session_state.cy_output = _ANSI_RE.sub("", str(exc))
        st.session_state.cy_is_error = True


def run_cy_program() -> None:
    """Synchronous wrapper that drives the async executor."""
    import asyncio

    t0 = time.perf_counter()
    try:
        asyncio.run(run_cy_program_async())
    except RuntimeError:
        # Already inside a running event loop (common in Streamlit).
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, run_cy_program_async())
            try:
                future.result()
            except Exception as exc:
                st.session_state.cy_output = _ANSI_RE.sub("", str(exc))
                st.session_state.cy_is_error = True
    st.session_state.last_run_ms = round((time.perf_counter() - t0) * 1000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_example_options() -> dict[str, str]:
    """Return {display_name: example_key} for the sidebar selector."""
    test_examples = get_test_examples()
    return {display: key for display, key in EXAMPLES.items() if key in test_examples}


# ---------------------------------------------------------------------------
# UI — Sidebar
# ---------------------------------------------------------------------------

_NAMESPACE_REFERENCE = """\
| Namespace | Key functions |
|-----------|--------------|
| `json::` | `parse`, `stringify` |
| `str::` | `uppercase`, `lowercase`, `split`, `join`, `trim`, `replace` |
| `list::` | `sort`, `reverse`, `take`, `range` |
| `dict::` | `keys`, `values` |
| `math::` | `abs`, `round` |
| `time::` | `now`, `add_duration`, `duration_between` |
| `url::` | `encode`, `decode` |
| `ip::` | `is_v4`, `is_v6`, `is_valid` |
| `regex::` | `match`, `extract` |
| `type::` | `str`, `int`, `num`, `bool` |
"""


def render_sidebar() -> None:
    """Render the sidebar: examples, settings, and reference."""
    # ── Header ──────────────────────────────────────────────────────────
    st.sidebar.markdown("### Cy Editor")
    st.sidebar.caption("Interactive playground for the Cy language")
    st.sidebar.markdown("---")

    # ── Example selector (load on select) ──────────────────────────────
    all_options = _build_example_options()

    if all_options:

        def _on_example_change() -> None:
            key = all_options.get(st.session_state._example_selector)
            if key:
                load_example(key)

        st.sidebar.selectbox(
            "Example program",
            list(all_options.keys()),
            key="_example_selector",
            on_change=_on_example_change,
        )

    st.sidebar.markdown("---")

    # ── Settings ────────────────────────────────────────────────────────
    with st.sidebar.expander("Settings", expanded=False):
        st.selectbox(
            "Interpolation mode",
            ["markdown", "csv", "xml"],
            key="interpolation_mode",
        )

        if st.session_state.interpolation_mode == "xml":
            st.text_input("XML item tag", key="item_tag")

        st.checkbox(
            "Parallel execution",
            key="parallel_enabled",
            help="Automatically parallelize independent async operations.",
        )
        if st.session_state.parallel_enabled:
            st.number_input(
                "Parallel threshold",
                min_value=1,
                max_value=50,
                key="parallel_threshold",
                help="Minimum operations to trigger parallelization.",
            )

    # ── Namespace Reference ─────────────────────────────────────────────
    with st.sidebar.expander("Namespace Reference", expanded=False):
        st.markdown(_NAMESPACE_REFERENCE)

    # ── Available Tools ─────────────────────────────────────────────────
    with st.sidebar.expander("Available Tools", expanded=False):
        descriptions = default_registry.get_tool_descriptions()

        # Group by category
        groups: dict[str, list] = {
            "Native (short names)": [],
            "Namespaced": [],
        }
        for tool in descriptions:
            name = tool["name"]
            if "::" in name:
                groups["Namespaced"].append(tool)
            else:
                groups["Native (short names)"].append(tool)

        for label, tools in groups.items():
            if tools:
                st.markdown(f"**{label}**")
                for t in tools:
                    st.markdown(
                        f"<code style='font-size:0.82em'>{t['name']}</code> "
                        f"— <span style='color:#666;font-size:0.85em'>"
                        f"{t['description']}</span>",
                        unsafe_allow_html=True,
                    )

    # ── Footer ──────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.caption("Development tool — not required for using Cy as a library.")


# ---------------------------------------------------------------------------
# UI — Main area
# ---------------------------------------------------------------------------


def render_main() -> None:
    """Render the editor, action bar, and output area."""
    # ── Title ───────────────────────────────────────────────────────────
    st.markdown("## Cy Language Editor")
    if st.session_state.example_source:
        st.caption(st.session_state.example_source)

    # ── Code Editor ─────────────────────────────────────────────────────
    editor_key = f"editor_{st.session_state.get('editor_refresh_key', 0)}"
    code = st_ace(
        value=st.session_state.cy_code,
        language="python",
        theme="github",
        height=500,
        key=editor_key,
        auto_update=True,
        font_size=14,
        tab_size=4,
        wrap=False,
        show_gutter=True,
        show_print_margin=False,
    )

    # Auto-run when the user saves with Cmd+Enter
    if code != st.session_state.cy_code:
        st.session_state.cy_code = code
        run_cy_program()

    # ── Action bar ──────────────────────────────────────────────────────
    col_btn, col_hint, col_time = st.columns([1, 2, 1])
    with col_btn:
        st.button(
            "Run",
            on_click=run_cy_program,
            use_container_width=True,
            type="primary",
        )
    with col_hint:
        st.caption("**Cmd+Enter** (Mac) / **Ctrl+Enter** (Win/Linux) to save & run")
    with col_time:
        if st.session_state.last_run_ms is not None:
            ms = st.session_state.last_run_ms
            st.markdown(
                f'<span class="exec-time">Ran in {ms} ms</span>',
                unsafe_allow_html=True,
            )

    # ── Output / Logs / Input (tabbed) ────────────────────────────────────
    st.markdown("")  # visual spacing between action bar and tabs

    log_count = len(st.session_state.get("cy_logs", []))
    logs_label = f"Logs ({log_count})" if log_count else "Logs"
    tab_output, tab_logs, tab_input = st.tabs(["Output", logs_label, "Input"])

    with tab_output:
        _render_output()

    with tab_logs:
        _render_logs()

    with tab_input:
        _render_input()


# ---------------------------------------------------------------------------
# Parsing helpers for enhanced error messages
# ---------------------------------------------------------------------------

# Matches lines like "   3 | y = x && 5" produced by ErrorFormatter
_CONTEXT_LINE_RE = re.compile(r"^\s*\d+\s*\|")
# Matches pointer lines like "     |     ^"
_POINTER_LINE_RE = re.compile(r"^\s*\|?\s*\^+\s*$")
# Matches the error type header like "CompilerError at line 3, column 5:"
_ERROR_HEADER_RE = re.compile(
    r"^(CompilerError|SyntaxError|RuntimeError|NameError|ToolError"
    r"|ToolNotFoundError|ToolInvocationError|InterpolationError"
    r"|AmbiguousToolError|ToolResolutionError|NotSupportedYetError)"
    r"\s+at\s+line\s+\d+"
)


def _parse_enhanced_error(text: str) -> dict[str, str | None]:
    """Parse an enhanced error message into structured parts.

    Returns a dict with keys:
        header     -- e.g. "CompilerError at line 3, column 5:"
        context    -- source context lines (numbered + pointer)
        message    -- the core error description
        suggestion -- the suggestion text (without "Suggestion: " prefix)
    Any key may be ``None`` if that part isn't present.
    """
    result: dict[str, str | None] = {
        "header": None,
        "context": None,
        "message": None,
        "suggestion": None,
    }

    # Split off suggestion first
    body = text
    if "Suggestion:" in text:
        body, _, suggestion = text.partition("Suggestion:")
        result["suggestion"] = suggestion.strip()

    lines = body.split("\n")
    header_lines: list[str] = []
    context_lines: list[str] = []
    message_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _ERROR_HEADER_RE.match(stripped):
            header_lines.append(stripped)
        elif _CONTEXT_LINE_RE.match(line) or _POINTER_LINE_RE.match(line):
            context_lines.append(line)
        else:
            message_lines.append(stripped)

    if header_lines:
        result["header"] = "\n".join(header_lines)
    if context_lines:
        result["context"] = "\n".join(context_lines)
    if message_lines:
        result["message"] = "\n".join(message_lines)

    return result


def _render_output() -> None:
    """Display program output with proper formatting.

    Uses the structured ``cy_is_error`` flag instead of fragile substring
    matching.  Success output uses ``st.json()`` for objects/arrays and
    ``st.code()`` for scalar values.  Error output is broken into visual
    sections (header, source context, message, suggestion).
    """
    output = st.session_state.cy_output
    is_error = st.session_state.get("cy_is_error", False)

    # Never-run state
    if not output and st.session_state.last_run_ms is None:
        st.info("Run the program to see output here.", icon="💡")
        return

    # Ran but empty output
    if not output:
        st.success("Program completed with no output.")
        return

    # Always strip ANSI codes for display
    clean = _ANSI_RE.sub("", output)

    # ── Success path ───────────────────────────────────────────────────
    # run_async() returns json.dumps(result), so the output is always a
    # JSON-encoded value.  Decode it so strings display as real text
    # (with actual newlines) and objects/arrays get the interactive viewer.
    if not is_error:
        try:
            decoded = json.loads(clean)
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON — show as-is
            st.code(clean, language=None)
            return

        if isinstance(decoded, (dict, list)):
            st.json(decoded)
        elif isinstance(decoded, str):
            st.code(decoded, language=None)
        else:
            # Numbers, booleans, null
            st.code(str(decoded), language=None)
        return

    # ── Error path ─────────────────────────────────────────────────────
    parts = _parse_enhanced_error(clean)

    # Header (error type + location)
    if parts["header"]:
        st.error(parts["header"])
    elif parts["message"]:
        st.error(parts["message"])
    else:
        st.error(clean)
        return

    # Source context block (line numbers + pointer)
    if parts["context"]:
        st.code(parts["context"], language=None)

    # Core message (only if separate from header)
    if parts["message"] and parts["header"]:
        st.markdown(f"```\n{parts['message']}\n```")

    # Suggestion callout
    if parts["suggestion"]:
        st.info(f"**Suggestion:** {parts['suggestion']}")


def _render_logs() -> None:
    """Render captured log() output from the last program execution."""
    logs = st.session_state.get("cy_logs", [])

    if not logs:
        if st.session_state.last_run_ms is None:
            st.caption("Run the program to capture log() output here.")
        else:
            st.caption("No log() calls were made during execution.")
        return

    # Use the first log timestamp as the baseline so offsets are relative
    from datetime import datetime

    base_ts = logs[0].get("ts", 0.0) if logs else 0.0

    st.caption(f"{len(logs)} log message{'s' if len(logs) != 1 else ''}")
    for entry in logs:
        ts = entry.get("ts", 0.0)
        msg = entry.get("message", "")

        # Show wall-clock time + relative offset from first log
        dt = datetime.fromtimestamp(ts, tz=UTC).astimezone()
        time_str = dt.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        offset_ms = round((ts - base_ts) * 1000)
        offset_str = f"+{offset_ms}ms"

        st.text(f"[{time_str} {offset_str:>8}]  {msg}")


def _render_input() -> None:
    """Render the input panel."""
    st.caption(
        "Optional data available as `$input` in your program. "
        "Supports JSON objects/arrays or plain text."
    )

    def _on_change() -> None:
        st.session_state.cy_input = st.session_state.input_widget

    st.text_area(
        "Input data",
        value=st.session_state.cy_input,
        height=200,
        key="input_widget",
        on_change=_on_change,
        label_visibility="collapsed",
        placeholder='{"key": "value"} or plain text…',
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Launch the Cy Language Editor."""
    st.set_page_config(
        page_title="Cy Editor",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
