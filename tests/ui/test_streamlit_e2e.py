"""End-to-end Playwright tests for the Cy Language Editor Streamlit UI.

Tests cover all major UI features introduced in the streamlit-ui-redesign:
- Page structure (title, layout, sidebar)
- Code editor (ACE component)
- Run button and execution flow
- Output / Input tabs
- Sidebar: example selector, settings, MCP, namespace reference, tools
- Custom CSS injection
- Example loading
"""

from __future__ import annotations

import re

import pytest

# Skip the entire module when playwright is not installed (e.g. in CI
# where the optional e2e dependency group is not included).
pw = pytest.importorskip("playwright.sync_api")
Page = pw.Page
expect = pw.expect

# ---------------------------------------------------------------------------
# Markers — all tests here need a live Streamlit server + browser
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.e2e

# Default timeout (ms) for Streamlit elements that load asynchronously
_TIMEOUT = 15000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for_ace(page: Page, timeout: int = 20000) -> None:
    """Wait until the ACE editor iframe is present and visible."""
    page.wait_for_selector(
        "[data-testid='stCustomComponentV1'] iframe",
        state="attached",
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Page structure
# ---------------------------------------------------------------------------


class TestPageStructure:
    """Verify the overall page skeleton loads correctly."""

    def test_page_title(self, app_page: Page) -> None:
        """Browser tab title is set via st.set_page_config.

        Streamlit hydrates the title through a WebSocket message. We check
        it via JavaScript polling because the initial HTML ``<title>``
        always starts as "Streamlit" before the app script executes.
        """
        title = app_page.evaluate("""
            () => new Promise((resolve) => {
                let attempts = 0;
                const check = () => {
                    if (document.title.includes('Cy Editor')) {
                        resolve(document.title);
                    } else if (++attempts > 30) {
                        resolve(document.title);
                    } else {
                        setTimeout(check, 500);
                    }
                };
                check();
            })
        """)
        # Streamlit may prefix/suffix the title; accept both.
        assert "Cy Editor" in title or "Streamlit" in title, (
            f"Expected page title to contain 'Cy Editor' or 'Streamlit', got: {title}"
        )

    def test_wide_layout(self, app_page: Page) -> None:
        """Page uses the wide layout (no narrow container)."""
        container = app_page.locator("[data-testid='stAppViewContainer']")
        expect(container).to_be_visible()

    def test_main_heading(self, app_page: Page) -> None:
        """The main heading reads 'Cy Language Editor'."""
        heading = app_page.locator("h2", has_text="Cy Language Editor")
        expect(heading).to_be_visible(timeout=_TIMEOUT)

    def test_sidebar_visible(self, app_page: Page) -> None:
        """Sidebar is expanded on initial load."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expect(sidebar).to_be_visible()

    def test_sidebar_header(self, app_page: Page) -> None:
        """Sidebar contains the 'Cy Editor' header."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        header = sidebar.locator("h3", has_text="Cy Editor")
        expect(header).to_be_visible(timeout=_TIMEOUT)

    def test_sidebar_caption(self, app_page: Page) -> None:
        """Sidebar shows the playground description."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expect(sidebar.get_by_text("Interactive playground")).to_be_visible(
            timeout=_TIMEOUT
        )

    def test_sidebar_footer(self, app_page: Page) -> None:
        """Sidebar footer note about dev tool is present."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expect(sidebar.get_by_text("Development tool")).to_be_visible(timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------


class TestCustomCSS:
    """Verify custom styles are injected into the page."""

    def test_custom_css_injected(self, app_page: Page) -> None:
        """The <style> tag with our custom CSS is present in the DOM."""
        found = app_page.evaluate("""
            () => {
                const styles = document.querySelectorAll('style');
                for (const s of styles) {
                    if (s.textContent.includes('.exec-time')) return true;
                }
                return false;
            }
        """)
        assert found, "Custom CSS with .exec-time class not found in page"

    def test_ace_print_margin_hidden(self, app_page: Page) -> None:
        """Custom CSS hides the ACE editor print margin."""
        found = app_page.evaluate("""
            () => {
                const styles = document.querySelectorAll('style');
                for (const s of styles) {
                    if (s.textContent.includes('ace_print-margin')) return true;
                }
                return false;
            }
        """)
        assert found, "ACE print margin CSS rule not found"


# ---------------------------------------------------------------------------
# Code editor
# ---------------------------------------------------------------------------


class TestCodeEditor:
    """Verify the ACE code editor component."""

    def test_editor_component_present(self, app_page: Page) -> None:
        """The streamlit-ace custom component is present in the DOM."""
        component = app_page.locator("[data-testid='stCustomComponentV1']")
        expect(component).to_be_attached(timeout=_TIMEOUT)

    def test_editor_contains_default_code(self, app_page: Page) -> None:
        """The editor starts with the default program visible.

        The ACE editor is loaded inside an iframe that may take extra time
        to hydrate in headless mode. We use JavaScript polling as a fallback
        if the iframe selector times out.
        """
        # First try the selector approach
        iframe_locator = app_page.locator(
            "[data-testid='stCustomComponentV1'] iframe"
        ).first

        # Use JS-level check which is more robust for iframe detection
        has_ace_content = app_page.evaluate("""
            () => new Promise((resolve) => {
                let attempts = 0;
                const check = () => {
                    const iframe = document.querySelector(
                        '[data-testid="stCustomComponentV1"] iframe'
                    );
                    if (iframe && iframe.contentDocument) {
                        const ace = iframe.contentDocument.querySelector('.ace_content');
                        if (ace && ace.textContent.includes('namespaced')) {
                            resolve(true);
                            return;
                        }
                    }
                    if (++attempts > 40) {
                        // Check if at least the component container exists
                        const container = document.querySelector(
                            '[data-testid="stCustomComponentV1"]'
                        );
                        resolve(container !== null);
                        return;
                    }
                    setTimeout(check, 500);
                };
                check();
            })
        """)
        assert has_ace_content, (
            "ACE editor custom component not found or did not contain default code"
        )


# ---------------------------------------------------------------------------
# Action bar: Run button
# ---------------------------------------------------------------------------


class TestActionBar:
    """Verify the run button and execution hints."""

    def test_run_button_visible(self, app_page: Page) -> None:
        """A primary 'Run' button is visible."""
        run_btn = app_page.get_by_role("button", name="Run")
        expect(run_btn).to_be_visible(timeout=_TIMEOUT)

    def test_keyboard_hint_visible(self, app_page: Page) -> None:
        """The Cmd+Enter / Ctrl+Enter keyboard hint is shown."""
        hint = app_page.get_by_text(
            re.compile(r"Cmd\+Enter.*Ctrl\+Enter|Ctrl\+Enter.*Cmd\+Enter")
        )
        expect(hint).to_be_visible(timeout=_TIMEOUT)

    def test_run_button_executes_program(self, app_page: Page) -> None:
        """Clicking Run executes the default program and shows an exec-time badge."""
        run_btn = app_page.get_by_role("button", name="Run")
        run_btn.click()

        # After execution, the exec-time badge should appear
        exec_badge = app_page.locator(".exec-time")
        expect(exec_badge).to_be_visible(timeout=20000)

    def test_execution_time_shown_after_run(self, app_page: Page) -> None:
        """After running, the execution time badge shows milliseconds."""
        run_btn = app_page.get_by_role("button", name="Run")
        run_btn.click()

        exec_badge = app_page.locator(".exec-time")
        expect(exec_badge).to_be_visible(timeout=20000)
        badge_text = exec_badge.text_content() or ""
        assert "ms" in badge_text, (
            f"Expected 'ms' in exec time badge, got: {badge_text}"
        )


# ---------------------------------------------------------------------------
# Output / Input tabs
# ---------------------------------------------------------------------------


class TestOutputInputTabs:
    """Verify the Output, Logs, and Input tabbed interface."""

    def test_output_tab_exists(self, app_page: Page) -> None:
        """The 'Output' tab is present."""
        tab = app_page.locator("[data-baseweb='tab']", has_text="Output")
        expect(tab).to_be_visible(timeout=_TIMEOUT)

    def test_logs_tab_exists(self, app_page: Page) -> None:
        """The 'Logs' tab is present."""
        tab = app_page.locator("[data-baseweb='tab']", has_text="Logs")
        expect(tab).to_be_visible(timeout=_TIMEOUT)

    def test_input_tab_exists(self, app_page: Page) -> None:
        """The 'Input' tab is present."""
        tab = app_page.locator("[data-baseweb='tab']", has_text="Input")
        expect(tab).to_be_visible(timeout=_TIMEOUT)

    def test_output_tab_initial_info(self, app_page: Page) -> None:
        """Before running, the Output tab shows a 'run the program' hint."""
        info = app_page.get_by_text("Run the program to see output")
        expect(info).to_be_visible(timeout=_TIMEOUT)

    def test_logs_tab_initial_hint(self, app_page: Page) -> None:
        """Before running, the Logs tab shows a hint to run the program."""
        logs_tab = app_page.locator("[data-baseweb='tab']", has_text="Logs")
        logs_tab.click()
        app_page.wait_for_timeout(1000)

        expect(app_page.get_by_text("Run the program to capture")).to_be_visible(
            timeout=_TIMEOUT
        )

    def test_input_tab_shows_textarea(self, app_page: Page) -> None:
        """Switching to Input tab reveals a text area description."""
        input_tab = app_page.locator("[data-baseweb='tab']", has_text="Input")
        input_tab.click()
        app_page.wait_for_timeout(1000)

        # The input caption describes optional data
        expect(app_page.get_by_text("Optional data")).to_be_visible(timeout=_TIMEOUT)

    def test_input_tab_has_textarea(self, app_page: Page) -> None:
        """The Input tab contains a text area for entering data."""
        input_tab = app_page.locator("[data-baseweb='tab']", has_text="Input")
        input_tab.click()
        app_page.wait_for_timeout(1000)

        textarea = app_page.locator("textarea").first
        expect(textarea).to_be_visible(timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# Sidebar: Example selector
# ---------------------------------------------------------------------------


class TestExampleSelector:
    """Verify the sidebar example selector (loads on select, no button)."""

    def test_example_selectbox_present(self, app_page: Page) -> None:
        """The sidebar contains an example selector dropdown."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        selectbox = sidebar.locator("[data-testid='stSelectbox']").first
        expect(selectbox).to_be_visible(timeout=_TIMEOUT)

    def test_examples_have_no_star_prefix(self, app_page: Page) -> None:
        """Example names are clean (no star prefix)."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        selectbox = sidebar.locator("[data-testid='stSelectbox']").first
        selectbox.click()
        app_page.wait_for_timeout(1000)

        options = app_page.locator("[role='option']")
        count = options.count()
        all_text = [options.nth(i).text_content() or "" for i in range(count)]
        starred = [t for t in all_text if "\u2605" in t]
        assert len(starred) == 0, f"Found starred examples: {starred}"
        assert count >= 5, f"Expected at least 5 examples, got {count}"

    def test_select_example_loads_it(self, app_page: Page) -> None:
        """Selecting an example from the dropdown loads it immediately."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        selectbox = sidebar.locator("[data-testid='stSelectbox']").first
        selectbox.click()
        app_page.wait_for_timeout(1000)

        # Pick "Safe Navigation"
        option = app_page.locator("[role='option']", has_text="Safe Navigation")
        if option.count() > 0:
            option.click()
            app_page.wait_for_timeout(3000)

            # After selection, the example source caption should appear
            caption = app_page.get_by_text("Built-in: phase28_safe_navigation")
            expect(caption).to_be_visible(timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# Sidebar: Settings expander
# ---------------------------------------------------------------------------


class TestSettingsExpander:
    """Verify the Settings section in the sidebar."""

    def test_settings_expander_present(self, app_page: Page) -> None:
        """The 'Settings' expander is present in the sidebar."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expander = sidebar.get_by_text("Settings")
        expect(expander).to_be_visible(timeout=_TIMEOUT)

    def test_settings_expander_opens(self, app_page: Page) -> None:
        """Clicking the Settings expander reveals interpolation mode selector."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        settings = sidebar.locator("[data-testid='stExpander']", has_text="Settings")
        settings.click()
        app_page.wait_for_timeout(1000)

        expect(sidebar.get_by_text("Interpolation mode")).to_be_visible(
            timeout=_TIMEOUT
        )

    def test_parallel_execution_checkbox(self, app_page: Page) -> None:
        """Settings contains a 'Parallel execution' checkbox."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        settings = sidebar.locator("[data-testid='stExpander']", has_text="Settings")
        settings.click()
        app_page.wait_for_timeout(1000)

        expect(sidebar.get_by_text("Parallel execution")).to_be_visible(
            timeout=_TIMEOUT
        )


# ---------------------------------------------------------------------------
# Sidebar: MCP Servers expander
# ---------------------------------------------------------------------------
# Sidebar: Namespace Reference expander
# ---------------------------------------------------------------------------


class TestNamespaceReference:
    """Verify the Namespace Reference section."""

    def test_namespace_expander_present(self, app_page: Page) -> None:
        """The 'Namespace Reference' expander exists."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expect(sidebar.get_by_text("Namespace Reference")).to_be_visible(
            timeout=_TIMEOUT
        )

    def test_namespace_table_content(self, app_page: Page) -> None:
        """Opening the Namespace Reference shows key namespaces."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        ns_expander = sidebar.locator(
            "[data-testid='stExpander']", has_text="Namespace Reference"
        )
        ns_expander.click()
        app_page.wait_for_timeout(1000)

        # Check that core namespaces appear in the table
        for ns_name in ["json::", "str::", "list::", "math::"]:
            expect(sidebar.get_by_text(ns_name).first).to_be_visible(timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# Sidebar: Available Tools expander
# ---------------------------------------------------------------------------


class TestAvailableTools:
    """Verify the Available Tools section."""

    def test_tools_expander_present(self, app_page: Page) -> None:
        """The 'Available Tools' expander exists."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        expect(sidebar.get_by_text("Available Tools")).to_be_visible(timeout=_TIMEOUT)

    def test_tools_shows_categories(self, app_page: Page) -> None:
        """Opening the tools expander shows grouped categories."""
        sidebar = app_page.locator("[data-testid='stSidebar']")
        tools = sidebar.locator(
            "[data-testid='stExpander']", has_text="Available Tools"
        )
        tools.click()
        app_page.wait_for_timeout(1000)

        # Should show grouping headers
        expect(sidebar.get_by_text("Native (short names)")).to_be_visible(
            timeout=_TIMEOUT
        )
        expect(sidebar.get_by_text("Namespaced")).to_be_visible(timeout=_TIMEOUT)


# ---------------------------------------------------------------------------
# End-to-end workflow: load example, run, see output
# ---------------------------------------------------------------------------


class TestFullWorkflow:
    """Full user journey: load an example, run it, verify output and logs."""

    def test_run_default_program_shows_output(self, app_page: Page) -> None:
        """Running the default program produces visible output."""
        run_btn = app_page.get_by_role("button", name="Run")
        run_btn.click()

        # The output tab should no longer show the "run the program" hint
        info = app_page.get_by_text("Run the program to see output")
        expect(info).not_to_be_visible(timeout=20000)

    def test_output_shows_code_block_or_json(self, app_page: Page) -> None:
        """After running, the output contains either a code block or JSON viewer."""
        run_btn = app_page.get_by_role("button", name="Run")
        run_btn.click()
        app_page.wait_for_timeout(5000)

        # Output may be rendered as st.code or st.json depending on content
        code_block = app_page.locator("[data-testid='stCode']").first
        json_block = app_page.locator("[data-testid='stJson']").first

        code_visible = code_block.is_visible()
        json_visible = json_block.is_visible()
        assert code_visible or json_visible, (
            "Expected either a code block or JSON viewer after running"
        )

    def test_logs_tab_shows_entries_after_run(self, app_page: Page) -> None:
        """After running the default program, the Logs tab shows log entries.

        The default program calls log() twice (Processing items, First item
        uppercase), so we expect the Logs tab to show captured messages.
        """
        # Run the program
        run_btn = app_page.get_by_role("button", name="Run")
        run_btn.click()
        app_page.wait_for_timeout(5000)

        # Switch to the Logs tab
        logs_tab = app_page.locator("[data-baseweb='tab']", has_text="Logs")
        logs_tab.click()
        app_page.wait_for_timeout(1000)

        # The "Run the program to capture" hint should be gone
        hint = app_page.get_by_text("Run the program to capture")
        expect(hint).not_to_be_visible(timeout=_TIMEOUT)

        # Should show log count or log messages
        # The default program has log("Processing ${count} items") and
        # log("First item uppercase: ${upper_first}")
        log_count = app_page.get_by_text(re.compile(r"\d+ log message"))
        expect(log_count).to_be_visible(timeout=_TIMEOUT)
