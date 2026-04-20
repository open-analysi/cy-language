.PHONY: help package install-cli release release-dry \
	lint lint-fix format format-check \
	test test-all test-cli test-mcp test-streamlit test-coverage \
	clean typecheck security-scan ci-quality

help:
	@echo "Available targets:"
	@echo "  package               - Build wheel distribution package"
	@echo ""
	@echo "Testing:"
	@echo "  test                  - Run unit tests (fast, no browser, no MCP subprocess)"
	@echo "  test-cli              - Run CLI tool tests (--tools, --stub-tools)"
	@echo "  test-mcp              - Run MCP stdio end-to-end tests (launches subprocess)"
	@echo "  test-all              - Run all tests including MCP (excludes Streamlit e2e)"
	@echo "  test-streamlit        - Run Streamlit e2e tests only (separate process)"
	@echo "  test-coverage         - Run tests with coverage report (excludes e2e)"
	@echo ""
	@echo "  install-cli           - Install the cy CLI locally (editable, via pipx)"
	@echo "  release               - Bump version (from commits) + reinstall local cy"
	@echo "  release-dry           - Preview what release would do (no changes)"
	@echo "  clean                 - Remove build artifacts and coverage files"
	@echo ""
	@echo "Code quality:"
	@echo "  lint                  - Run ruff linter"
	@echo "  lint-fix              - Run ruff linter with auto-fix"
	@echo "  format                - Format code with ruff"
	@echo "  format-check          - Check formatting without changes"
	@echo "  typecheck             - Run mypy type checker"
	@echo "  security-scan         - Run pip-audit security scan"
	@echo "  ci-quality            - Run all quality checks (lint + format + typecheck)"

install-cli:
	pipx install -e ".[cli]"

release:
	poetry run cz bump --no-verify --changelog
	pipx install --force -e ".[cli]"
	@echo ""
	@echo "Released $$(cy --version) and reinstalled local cy."

release-dry:
	@poetry run cz bump --dry-run || echo "(no unreleased commits found)"

lint:
	poetry run ruff check src/ tests/

lint-fix:
	poetry run ruff check --fix src/ tests/

format:
	poetry run ruff format src/ tests/

format-check:
	poetry run ruff format --check src/ tests/

package:
	@echo "📦 Building wheel package..."
	poetry build -f wheel
	@echo "✅ Wheel package created in dist/"

test:
	poetry run pytest tests/ -m "not e2e and not mcp_stdio" -v

test-cli:
	poetry run pytest tests/unit/test_cli.py tests/unit/test_cli_tools.py tests/unit/test_cli_combinations.py tests/unit/test_cli_mcp.py tests/unit/test_mcp_stdio_bridge.py tests/unit/test_tool_loader.py tests/unit/test_stub_tools.py -m "not mcp_stdio" -v

test-mcp:
	poetry run pytest -m mcp_stdio -v

# Playwright e2e must run in a separate process — its session-scoped event
# loop contaminates asyncio on Python 3.14 and breaks all subsequent async tests.
test-all:
	poetry run pytest tests/ -m "not e2e" -v

test-streamlit:
	poetry run pytest -m e2e -v

test-coverage:
	poetry run pytest tests/ -m "not e2e" --cov=src/cy_language --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

typecheck:
	poetry run mypy src/cy_language/ --ignore-missing-imports

security-scan:
	poetry run pip-audit --strict --desc || true

ci-quality: lint format-check typecheck
	@echo "All quality checks passed"

clean:
	@echo "🧹 Cleaning build artifacts and coverage files..."
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"
