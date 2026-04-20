"""Validate Cy code examples embedded in documentation markdown files.

Extracts ```cy fenced code blocks from markdown and validates them
against the Cy parser, catching documentation divergence when the
language syntax evolves.

ALL docs are strict: every block must either parse successfully or
carry an explicit annotation.  There is no auto-classification — if
a block is intentionally wrong, it MUST have an annotation.  This
ensures accidental errors are never silently masked.

Annotation protocol (HTML comments before code blocks):
  (none)                             → parse-only (syntax check)
  <!-- cy-test: skip -->             → skip this block
  <!-- cy-test: skip: reason -->     → skip with reason
  <!-- cy-test: run -->              → compile + execute (must succeed)
  <!-- cy-test: compile-only -->     → parse + transform (no execution)
  <!-- cy-test: expect-error -->     → must raise any error during parse
  <!-- cy-test: expect-error: X -->  → must raise error containing X

Both directions are caught:
  - Code that should parse but doesn't   → test FAILS (regression)
  - Code marked expect-error that parses → test FAILS (language changed)
"""

import re
from pathlib import Path

import pytest

from cy_language.parser import Parser as CyParser

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_BUNDLED_SKILLS = (
    PROJECT_ROOT / "src" / "cy_language" / "bundled_skills" / "cy-language-programming"
)

# ── Markdown files containing ```cy blocks to validate ─────────────────────

DOC_FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "TUTORIAL.md",
    _BUNDLED_SKILLS / "SKILL.md",
    _BUNDLED_SKILLS / "reference" / "syntax-basics.md",
    _BUNDLED_SKILLS / "reference" / "control-flow.md",
    _BUNDLED_SKILLS / "reference" / "functions-tools.md",
    _BUNDLED_SKILLS / "reference" / "type-checking.md",
    _BUNDLED_SKILLS / "reference" / "advanced.md",
    _BUNDLED_SKILLS / "reference" / "time-arithmetic.md",
]

# ── Regex patterns ─────────────────────────────────────────────────────────

ANNOTATION_RE = re.compile(r"<!--\s*cy-test:\s*(.*?)\s*-->")
CY_BLOCK_RE = re.compile(r"^```cy\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)


# ── Block extraction ───────────────────────────────────────────────────────


def _extract_cy_blocks(filepath: Path) -> list[dict]:
    """Extract ```cy code blocks with their annotations from a markdown file."""
    text = filepath.read_text()
    blocks = []

    for match in CY_BLOCK_RE.finditer(text):
        code = match.group(1)
        start_pos = match.start()
        line_num = text[:start_pos].count("\n") + 1

        # Look for cy-test annotation in the 3 non-empty lines before ```cy
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


# ── Test collection ────────────────────────────────────────────────────────


def _collect_all_blocks():
    """Collect all cy blocks from all doc files for parametrization."""
    params = []
    for doc_file in DOC_FILES:
        if not doc_file.exists():
            continue
        blocks = _extract_cy_blocks(doc_file)
        for block in blocks:
            test_id = f"{block['file']}:L{block['line']}"
            params.append(pytest.param(block, id=test_id))
    return params


# ── Test ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("block", _collect_all_blocks())
def test_doc_cy_block(block):
    """Validate a Cy code block from documentation.

    Every block is strict:
    - No annotation     → must parse successfully
    - expect-error      → must FAIL to parse
    - skip              → skipped (for non-Cy content)
    - run               → must compile and execute
    - compile-only      → must parse and transform
    """
    code = block["code"].strip()
    annotation = block["annotation"]

    if not code:
        return

    if not annotation:
        # Default: must parse successfully
        parser = CyParser()
        parser.parse_only(code)
        return

    ann_lower = annotation.lower()

    if ann_lower.startswith("skip"):
        reason = annotation.split(":", 1)[1].strip() if ":" in annotation else ""
        pytest.skip(reason)

    elif ann_lower.startswith("expect-error"):
        expected_msg = None
        rest = annotation.split("expect-error", 1)[1]
        if ":" in rest:
            expected_msg = rest.split(":", 1)[1].strip()
        with pytest.raises(Exception) as exc_info:
            parser = CyParser()
            parser.parse_only(code)
        if expected_msg:
            assert expected_msg.lower() in str(exc_info.value).lower(), (
                f"Expected error containing '{expected_msg}', got: {exc_info.value}"
            )

    elif ann_lower == "run":
        from cy_language import Cy

        cy = Cy(validate_output=False, check_types=False)
        cy.run(code)

    elif ann_lower == "compile-only":
        parser = CyParser()
        parser.parse_only(code)


# ── Streamlit UI examples ─────────────────────────────────────────────────


def _collect_ui_examples():
    """Collect Streamlit UI example programs for validation."""
    from cy_language.ui.examples import get_test_examples

    return [
        pytest.param(name, code, id=f"ui-example:{name}")
        for name, code in get_test_examples().items()
    ]


@pytest.mark.parametrize(("name", "code"), _collect_ui_examples())
def test_ui_example_runs(name, code):
    """Streamlit UI examples must compile and execute without errors."""
    from cy_language import Cy

    cy = Cy(validate_output=False, check_types=False)
    cy.run(code)
