"""Validate Python code examples embedded in documentation markdown files.

Extracts ```python fenced code blocks from markdown and validates them
by executing them, catching documentation divergence when the API evolves.

Annotation protocol (HTML comments before code blocks):
  (none)                             → skip (not tested by default)
  <!-- py-test: run -->              → execute block (must succeed)
  <!-- py-test: skip -->             → explicitly skip
  <!-- py-test: expect-error -->     → must raise an exception
  <!-- py-test: expect-error: X -->  → must raise error containing X

Both directions are caught:
  - Code that should run but raises   → test FAILS (regression)
  - Code marked expect-error that passes → test FAILS (API changed)
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Markdown files containing ```python blocks to validate ────────────────

DOC_FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "TUTORIAL.md",
]

# ── Regex patterns ────────────────────────────────────────────────────────

ANNOTATION_RE = re.compile(r"<!--\s*py-test:\s*(.*?)\s*-->")
PY_BLOCK_RE = re.compile(r"^```python\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)


# ── Block extraction ──────────────────────────────────────────────────────


def _extract_python_blocks(filepath: Path) -> list[dict]:
    """Extract ```python code blocks with their annotations from a markdown file."""
    text = filepath.read_text()
    blocks = []

    for match in PY_BLOCK_RE.finditer(text):
        code = match.group(1)
        start_pos = match.start()
        line_num = text[:start_pos].count("\n") + 1

        # Look for py-test annotation in the 3 non-empty lines before ```python
        annotation = None
        prefix_lines = text[:start_pos].rstrip().split("\n")
        for line in reversed(prefix_lines[-3:]):
            stripped = line.strip()
            if not stripped:
                continue
            m = ANNOTATION_RE.search(stripped)
            if m:
                annotation = m.group(1).strip()
            break  # stop at first non-empty line

        blocks.append(
            {
                "code": code,
                "annotation": annotation,
                "line": line_num,
                "file": str(filepath.relative_to(PROJECT_ROOT)),
            }
        )

    return blocks


# ── Test collection ───────────────────────────────────────────────────────


def _collect_all_blocks():
    """Collect annotated python blocks from all doc files for parametrization."""
    params = []
    for doc_file in DOC_FILES:
        if not doc_file.exists():
            continue
        blocks = _extract_python_blocks(doc_file)
        for block in blocks:
            ann = block["annotation"]
            if not ann:
                continue
            ann_lower = ann.lower()
            if ann_lower.startswith("run") or ann_lower.startswith("expect-error"):
                test_id = f"{block['file']}:L{block['line']}"
                params.append(pytest.param(block, id=test_id))
    return params


# ── Test ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("block", _collect_all_blocks())
def test_doc_python_block(block):
    """Validate a Python code block from documentation.

    - run          → must execute without errors
    - expect-error → must raise an exception
    - skip / none  → not collected (skipped at collection time)
    """
    code = block["code"].strip()
    annotation = block["annotation"]

    if not code:
        return

    ann_lower = annotation.lower()
    source_label = f"<{block['file']}:L{block['line']}>"

    if ann_lower.startswith("run"):
        exec(compile(code, source_label, "exec"), {})

    elif ann_lower.startswith("expect-error"):
        expected_msg = None
        rest = annotation.split("expect-error", 1)[1]
        if ":" in rest:
            expected_msg = rest.split(":", 1)[1].strip()
        with pytest.raises(Exception) as exc_info:
            exec(compile(code, source_label, "exec"), {})
        if expected_msg:
            assert expected_msg.lower() in str(exc_info.value).lower(), (
                f"Expected error containing '{expected_msg}', got: {exc_info.value}"
            )
