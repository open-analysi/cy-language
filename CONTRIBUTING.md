# Contributing to Cy Language

Thank you for your interest in contributing to Cy!

## Getting Started

1. Fork the repository and clone your fork
2. Install dependencies:
   ```bash
   poetry install --extras all
   ```
3. Run the tests to make sure everything works:
   ```bash
   poetry run pytest tests/unit/ -x -q
   ```

## Development Workflow

1. Create a branch for your change
2. Write tests for new functionality or bug fixes
3. Make your changes
4. Run the full test suite:
   ```bash
   make test
   ```
5. Run linting and formatting:
   ```bash
   make lint
   make format
   ```
6. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat: add new feature`
   - `fix: correct a bug`
   - `docs: update documentation`
   - `test: add or update tests`
   - `refactor: restructure code without changing behavior`
7. Open a pull request against `main`

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type hints are required for all public functions
- Run `poetry run ruff check src/ tests/` and `poetry run ruff format --check src/ tests/` before submitting

## Testing

- All new code should have tests in `tests/unit/`
- Documentation code blocks in markdown files are validated by `tests/unit/test_doc_cy_blocks.py` — if you add or modify ```` ```cy ```` blocks, run that test to verify they parse correctly
- Use `<!-- cy-test: expect-error -->` before code blocks that demonstrate intentionally invalid syntax

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- For security vulnerabilities, see [SECURITY.md](SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
