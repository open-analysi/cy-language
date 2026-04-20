"""Configuration and fixtures for UI tests.

Provides both mock-based fixtures for unit tests and Playwright fixtures
for end-to-end browser testing of the Streamlit application.

Playwright fixtures are only registered when the ``playwright`` package is
installed (``poetry install --with e2e``).  Without it, the E2E tests are
simply not collected and the unit tests work as before.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from collections.abc import Generator

import pytest

# ---------------------------------------------------------------------------
# Playwright fixtures — guarded behind an import check so CI (which doesn't
# install the optional e2e group) can still collect the unit tests in this
# directory without hitting a ModuleNotFoundError.
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import Page

    _HAS_PLAYWRIGHT = True
except ModuleNotFoundError:
    _HAS_PLAYWRIGHT = False


def _find_free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> None:
    """Block until the Streamlit server is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(
        f"Streamlit server did not start within {timeout}s on port {port}"
    )


if _HAS_PLAYWRIGHT:

    @pytest.fixture(scope="session")
    def streamlit_server() -> Generator[str, None, None]:
        """Launch a Streamlit server for the Cy Editor and yield its base URL.

        The server runs for the entire test session and is terminated on teardown.
        """
        port = _find_free_port()
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/cy_language/ui/app.py",
                "--server.port",
                str(port),
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
                "--server.fileWatcherType",
                "none",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            _wait_for_server(port)
            yield f"http://127.0.0.1:{port}"
        finally:
            proc.terminate()
            proc.wait(timeout=10)

    @pytest.fixture
    def app_page(page: Page, streamlit_server: str) -> Page:
        """Navigate to the Streamlit app and wait for it to be fully loaded."""
        page.goto(streamlit_server, wait_until="networkidle")
        page.wait_for_selector("[data-testid='stAppViewContainer']", timeout=20000)
        page.wait_for_selector(
            "[data-testid='stSidebar'] >> text=Cy Editor", timeout=20000
        )
        page.wait_for_timeout(3000)
        return page
