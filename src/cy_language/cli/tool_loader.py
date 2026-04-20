"""Load external tools from Python files for CLI commands."""

import importlib.util
import sys
from pathlib import Path
from typing import Any


def load_tools_from_file(path: Path) -> dict[str, Any]:
    """Import a Python file and return its ``tools`` dict.

    The file must define a module-level ``tools`` variable that is a dict
    mapping tool names (str) to callables.

    Args:
        path: Path to the Python file.

    Returns:
        Dictionary of tool name → callable.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file has no ``tools`` attribute or it's not a dict.
        Exception: Any import-time error from the user's file.
    """
    if not path.exists():
        raise FileNotFoundError(f"Tools file not found: {path}")

    spec = importlib.util.spec_from_file_location("_cy_user_tools", str(path))
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load Python module from: {path}")

    module = importlib.util.module_from_spec(spec)
    # Add the file's parent directory to sys.path so relative imports work
    parent_dir = str(path.parent)
    added_to_path = parent_dir not in sys.path
    if added_to_path:
        sys.path.insert(0, parent_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if added_to_path:
            sys.path.remove(parent_dir)

    if not hasattr(module, "tools"):
        raise ValueError(
            f"Tools file {path} must define a `tools` dict "
            f'(e.g. tools = {{"my_func": my_func}})'
        )

    tools = module.tools
    if not isinstance(tools, dict):
        raise ValueError(
            f"Tools file {path}: `tools` must be a dict, got {type(tools).__name__}"
        )

    return tools
