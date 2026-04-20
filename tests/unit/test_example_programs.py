"""Smoke tests that run example .cy programs through the CLI.

Catches regressions where examples that should work start failing
after language or runtime changes.  MCP examples run against an
in-process test server (tests/mcp_test_server.py).
"""

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cy_language.cli import app

runner = CliRunner()

PROJECT_ROOT = Path(__file__).parent.parent.parent

# ── Programs that need external deps (MCP, LLM, app integrations) ──────────
SKIP_EXTERNAL = {
    # LLM-dependent (tested separately in test_llm_example below)
    "llm/basic_usage.cy",
    # MCP-dependent (tested separately in test_mcp_example_runs below)
    "mcp/basic_calling.cy",
    "mcp/interpolation.cy",
    "mcp/native_plus_mcp.cy",
    "mcp/virustotal_analysis.cy",
    "mcp/parallel_timing.cy",
    "mcp/loop_sequential.cy",
    "mcp/parallel_execution.cy",
}

# MCP examples that can run against the in-process test server.
MCP_EXAMPLES = [
    "mcp/basic_calling.cy",
    "mcp/interpolation.cy",
    "mcp/native_plus_mcp.cy",
    "mcp/parallel_timing.cy",
    "mcp/loop_sequential.cy",
    "mcp/parallel_execution.cy",
]

# MCP examples that also need non-MCP custom tools — tested with extra tools
MCP_PLUS_CUSTOM_EXAMPLES = [
    # virustotal_analysis needs debug_print() for the Streamlit UI
    (
        "mcp/virustotal_analysis.cy",
        {"debug_print": lambda message="": message},
    ),
]

# ── Skill examples that need external deps ─────────────────────────────────
SKIP_SKILL_EXAMPLES = {
    "api-workflow.cy",
    "type-safe-workflow.cy",
    "security-analysis.cy",
    "basic-processing.cy",  # needs input data with JSON
}


def _collect_examples():
    """Collect all .cy files under examples/."""
    example_dir = PROJECT_ROOT / "examples"
    programs = []
    for cy_file in sorted(example_dir.rglob("*.cy")):
        rel = cy_file.relative_to(example_dir)
        if str(rel) in SKIP_EXTERNAL:
            continue
        programs.append(pytest.param(cy_file, id=str(rel)))
    return programs


def _collect_skill_examples():
    """Collect all .cy files under bundled_skills/cy-language-programming/examples/."""
    examples_dir = (
        PROJECT_ROOT
        / "src"
        / "cy_language"
        / "bundled_skills"
        / "cy-language-programming"
        / "examples"
    )
    if not examples_dir.exists():
        return []
    programs = []
    for cy_file in sorted(examples_dir.rglob("*.cy")):
        if cy_file.name in SKIP_SKILL_EXAMPLES:
            continue
        programs.append(pytest.param(cy_file, id=f"skill/{cy_file.name}"))
    return programs


@pytest.mark.parametrize("cy_file", _collect_examples())
def test_example_program_runs(cy_file):
    """Each example program should run without errors."""
    result = runner.invoke(app, ["run", str(cy_file), "--no-check-types"])
    assert result.exit_code == 0, (
        f"{cy_file.name} failed with exit code {result.exit_code}:\n{result.output}"
    )


@pytest.mark.parametrize("cy_file", _collect_skill_examples())
def test_skill_example_runs(cy_file):
    """Each bundled skill example should run without errors."""
    if cy_file.name == "bubble-sort.cy":
        # bubble-sort needs input data
        result = runner.invoke(
            app,
            [
                "run",
                str(cy_file),
                "--no-check-types",
                "--input",
                '{"array": [5, 3, 8, 1, 2]}',
            ],
        )
    else:
        result = runner.invoke(app, ["run", str(cy_file), "--no-check-types"])
    assert result.exit_code == 0, (
        f"{cy_file.name} failed with exit code {result.exit_code}:\n{result.output}"
    )


# ── Compile check — all self-contained programs should also compile ────────


@pytest.mark.parametrize("cy_file", _collect_examples())
def test_example_program_compiles(cy_file):
    """Each example program should compile to a valid execution plan."""
    result = runner.invoke(app, ["compile", str(cy_file), "--no-check-types"])
    assert result.exit_code == 0, f"{cy_file.name} failed to compile:\n{result.output}"
    data = json.loads(result.output)
    assert "version" in data
    assert "nodes" in data


# ── MCP example programs (run against in-process test server) ──────────────


@pytest.fixture(scope="module")
def mcp_base_url():
    """Start an in-process MCP test server for the duration of the module."""
    from tests.mcp_test_server import start_server

    server, base_url = start_server()
    yield base_url
    server.shutdown()


def _mcp_servers_config(base_url: str) -> dict:
    """Build MCP server config pointing demo + virustotal at test server."""
    return {
        "demo": {"base_url": base_url, "mcp_id": "demo"},
        "virustotal": {"base_url": base_url, "mcp_id": "virustotal"},
    }


def _collect_mcp_examples():
    example_dir = PROJECT_ROOT / "examples"
    return [pytest.param(example_dir / rel, id=rel) for rel in MCP_EXAMPLES]


def _collect_mcp_custom_examples():
    example_dir = PROJECT_ROOT / "examples"
    return [
        pytest.param(example_dir / rel, tools, id=rel)
        for rel, tools in MCP_PLUS_CUSTOM_EXAMPLES
    ]


@pytest.mark.parametrize("cy_file", _collect_mcp_examples())
async def test_mcp_example_runs(cy_file, mcp_base_url):
    """MCP examples should run against the in-process test server."""
    from cy_language import Cy

    script = cy_file.read_text()
    cy = await Cy.create_async(
        mcp_servers=_mcp_servers_config(mcp_base_url),
        validate_output=False,
        check_types=False,
    )
    result = await cy.run_async(script)
    assert result is not None


@pytest.mark.parametrize(("cy_file", "extra_tools"), _collect_mcp_custom_examples())
async def test_mcp_custom_example_runs(cy_file, extra_tools, mcp_base_url):
    """MCP examples that also need custom tools."""
    from cy_language import Cy

    script = cy_file.read_text()
    cy = await Cy.create_async(
        mcp_servers=_mcp_servers_config(mcp_base_url),
        tools=extra_tools,
        validate_output=False,
        check_types=False,
    )
    result = await cy.run_async(script)
    assert result is not None


# ── LLM example (requires OPENAI_API_KEY) ─────────────────────────────────


def test_llm_example_runs():
    """The LLM example should run when OPENAI_API_KEY is set."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from cy_language import Cy
    from cy_language.llm_config import llm_config
    from cy_language.llm_functions import llm_registry

    # Use cheapest model with minimal tokens — just proving the wiring works
    llm_config.model = "gpt-4o-mini"
    llm_config.max_tokens = 20

    script = (PROJECT_ROOT / "examples" / "llm" / "basic_usage.cy").read_text()
    cy = Cy(
        tools=llm_registry.get_tools_dict(),
        validate_output=False,
        check_types=False,
    )
    result = cy.run(script)
    assert result is not None


# ── SOC log triage example ─────────────────────────────────────────────────


def test_soc_log_triage_runs():
    """SOC log triage pipeline produces a valid structured report."""
    import cy_language.native_functions  # noqa: F401
    from cy_language import Cy
    from cy_language.ui.tools import default_registry

    script = (PROJECT_ROOT / "examples" / "basics" / "soc_log_triage.cy").read_text()
    cy = Cy(tools=default_registry.get_tools_dict())
    raw = cy.run(script)
    result = json.loads(raw)

    summary = result["report"]["summary"]

    # Correct event count
    assert summary["total_events"] == 8

    # All events classified
    classified = (
        summary["critical"] + summary["high"] + summary["medium"] + summary["low"]
    )
    assert classified == 8

    # At least one critical event (malware beacon scores 40)
    assert summary["critical"] >= 1

    # Max score is the malware beacon: 10 * 4 = 40
    assert summary["max_risk_score"] == 40

    # Average score is positive
    assert summary["avg_risk_score"] > 0

    # Top event is the malware beacon
    top_events = result["report"]["top_events"]
    assert len(top_events) == 3
    assert top_events[0]["id"] == "EVT-004"
    assert top_events[0]["severity"] == "critical"
    assert top_events[0]["risk_score"] == 40

    # All scored events have required fields
    for evt in result["report"]["all_events_by_risk"]:
        assert "id" in evt
        assert "type" in evt
        assert "risk_score" in evt
        assert "severity" in evt
        assert evt["severity"] in ("critical", "high", "medium", "low")

    # Events are sorted descending by risk score
    scores = [e["risk_score"] for e in result["report"]["all_events_by_risk"]]
    assert scores == sorted(scores, reverse=True)

    # Triage text is populated and contains expected sections
    triage = result["triage_text"]
    assert "SOC TRIAGE REPORT" in triage
    assert "SUMMARY" in triage
    assert "TOP 3 EVENTS BY RISK" in triage
    assert "CRITICAL" in triage
    assert "malware_beacon" in triage
    assert "EVT-004" in triage

    # All IPs in sample data are valid IPv4
    assert summary["invalid_ips"] == 0
