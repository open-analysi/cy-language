"""Shared error formatting and CLI helpers."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer

from cy_language.errors import CyError


def require_file(path: Path) -> None:
    """Exit with error if *path* does not exist."""
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        raise typer.Exit(code=1)


def load_external_tools(tools_path: Path | None) -> dict[str, Any] | None:
    """Load tools from a Python file, or return None if not requested.

    Handles errors with a user-facing message and ``typer.Exit(1)``.
    """
    if tools_path is None:
        return None
    from cy_language.cli.tool_loader import load_tools_from_file

    try:
        return load_tools_from_file(tools_path)
    except Exception as e:
        # Broad catch is intentional: load_tools_from_file exec()s user Python
        # code, which can raise any exception type (SyntaxError, NameError,
        # RuntimeError, etc.). All of them should produce a friendly CLI error.
        print(f"Error loading tools file: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def handle_cli_errors(action: Callable[[], Any]) -> Any:
    """Run *action*, printing a formatted error and exiting on failure.

    ``CyError`` subclasses get rich formatting via ``format_cy_error``;
    all other exceptions get a plain ``Error: ...`` message on stderr.
    Always exits with code 1 on error.
    """
    try:
        return action()
    except CyError as e:
        try:
            format_cy_error(e)
        except Exception:
            # format_cy_error can invoke ErrorContext.format_error via str(e),
            # which may fail.  Fall back to a plain message so the user always
            # sees *something* instead of an internal traceback.
            print(f"Error [{e.__class__.__name__}]: {e.message}", file=sys.stderr)
        raise typer.Exit(code=1)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        # typer.Exit inherits from click.exceptions.Exit which inherits
        # from Exception.  Let it pass through without printing a duplicate
        # error message — the caller already printed the real error.
        import click.exceptions

        if isinstance(e, click.exceptions.Exit):
            raise
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def format_cy_error(e: CyError) -> None:
    """Print a CyError to stderr with source context when available."""
    error_type = e.__class__.__name__
    error_message = str(e)
    line_info = (
        f"Line {e.line}, Col {e.col}: "
        if e.line is not None and e.col is not None
        else ""
    )

    if (
        hasattr(e, "line")
        and hasattr(e, "col")
        and e.line is not None
        and e.col is not None
    ):
        if hasattr(e, "text") and e.text is not None:
            lines = e.text.splitlines()
            if 0 <= e.line - 1 < len(lines):
                code_line = lines[e.line - 1]
                pointer = " " * (e.col - 1) + "^"

                print(
                    f"Error [{error_type}]: {line_info}{error_message}",
                    file=sys.stderr,
                )
                print(f"\n{code_line}", file=sys.stderr)
                print(f"{pointer}", file=sys.stderr)
            else:
                print(
                    f"Error [{error_type}]: {line_info}{error_message}",
                    file=sys.stderr,
                )
        else:
            print(
                f"Error [{error_type}]: {line_info}{error_message}",
                file=sys.stderr,
            )
    else:
        print(f"Error [{error_type}]: {error_message}", file=sys.stderr)
