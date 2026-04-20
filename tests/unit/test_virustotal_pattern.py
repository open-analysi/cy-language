"""
Permanent test for the exact VirusTotal IOC batch analysis pattern.

This test ensures that the specific pattern used in security operations
for processing IOCs with VirusTotal continues to work efficiently with parallelization.
"""

import ast
import asyncio
import time

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestVirusTotalPattern:
    """Test the exact VirusTotal IOC analysis pattern."""

    @pytest.mark.asyncio
    async def test_exact_virustotal_pattern(self):
        """Test the exact pattern from the user's VirusTotal batch IOC analysis."""

        # Mock task_run to simulate VirusTotal API calls
        async def mock_task_run(task_name, params):
            """Simulate VirusTotal API with realistic delay."""
            await asyncio.sleep(0.1)  # Simulate API latency

            if "domain" in task_name:
                return {
                    "detection_type": "domain",
                    "threat_level": "High",
                    "risk_score": 85,
                    "domain": params.get("domain"),
                }
            if "ip" in task_name:
                return {
                    "detection_type": "ip",
                    "threat_level": "Medium",
                    "risk_score": 45,
                    "ip": params.get("ip"),
                }
            return {
                "detection_type": "unknown",
                "threat_level": "Unknown",
                "risk_score": 0,
            }

        tools = default_registry.get_tools_dict()
        tools["task_run"] = mock_task_run

        # The EXACT pattern from the user's example
        cy_code = """
# VirusTotal Batch IOC Analysis
# Iterates through IOCs and enriches each with VirusTotal analysis results

# Get alert data
alert = input

# Extract IOCs array and context from alert
iocs = alert["iocs"]
alert_context = alert["context"]

# Process each IOC and add VirusTotal analysis

for (current_ioc in iocs) {
    ioc_value = current_ioc["value"]
    ioc_type = current_ioc["type"]

    # Initialize VirusTotal analysis result
    vt_analysis = {}

    # Call appropriate VirusTotal task based on IOC type
    if (ioc_type == "domain") {
        # Call domain reputation analysis task
        vt_analysis = task_run("virustotal_domain_reputation_analysis", {"domain": ioc_value, "context": alert_context})
    } elif (ioc_type == "ip") {
        # Call IP reputation analysis task
        vt_analysis = task_run("virustotal_ip_reputation_analysis", {"ip": ioc_value, "context": alert_context})
    } elif (ioc_type == "url") {
        # URL analysis not implemented yet
        vt_analysis = {
            "detection_type": "url_not_implemented",
            "threat_level": "Unknown",
            "risk_score": 0,
            "note": "URL reputation analysis not yet available"
        }
    } elif (ioc_type == "hash" or ioc_type == "md5" or ioc_type == "sha1" or ioc_type == "sha256") {
        # Hash analysis not implemented yet
        vt_analysis = {
            "detection_type": "hash_not_implemented",
            "threat_level": "Unknown",
            "risk_score": 0,
            "note": "Hash reputation analysis not yet available"
        }
    } else {
        # Unknown IOC type
        vt_analysis = {
            "detection_type": "unsupported",
            "threat_level": "Unknown",
            "risk_score": 0,
            "note": "IOC type '" + ioc_type + "' not supported for VirusTotal analysis"
        }
    }

    # Add VirusTotal analysis to the current IOC
    current_ioc["vt_analysis"] = vt_analysis
}

# Return the enriched alert
return alert
"""

        # Test data with various IOC types
        test_alert = {
            "iocs": [
                {"value": "malicious.com", "type": "domain"},
                {"value": "192.168.1.100", "type": "ip"},
                {"value": "evil.org", "type": "domain"},
                {"value": "10.0.0.1", "type": "ip"},
                {"value": "suspicious.net", "type": "domain"},
                {"value": "http://bad.url", "type": "url"},
                {"value": "d41d8cd98f00b204e9800998ecf8427e", "type": "md5"},
            ],
            "context": {"alert_id": "ALERT-001", "severity": "high", "source": "SIEM"},
        }

        # Create interpreter with parallelization enabled
        cy = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=2,  # Parallelize with 2+ iterations
        )

        # 1. Verify the pattern is detected as parallelizable
        analysis = cy.analyze_parallelization(cy_code)
        assert analysis["would_parallelize"] is True, (
            "VirusTotal pattern should be detected as parallelizable"
        )

        # 2. Measure parallel execution performance
        start = time.time()
        result_parallel = await cy.run_async(cy_code, input_data=test_alert)
        duration_parallel = time.time() - start

        # Parse result
        result_dict = ast.literal_eval(result_parallel)

        # 3. Verify all IOCs were processed correctly
        assert len(result_dict["iocs"]) == 7

        # Check domain IOCs have proper analysis
        for ioc in result_dict["iocs"]:
            assert "vt_analysis" in ioc, f"IOC missing analysis: {ioc}"

            if ioc["type"] == "domain":
                assert ioc["vt_analysis"]["detection_type"] == "domain"
                assert ioc["vt_analysis"]["threat_level"] == "High"
            elif ioc["type"] == "ip":
                assert ioc["vt_analysis"]["detection_type"] == "ip"
                assert ioc["vt_analysis"]["threat_level"] == "Medium"
            elif ioc["type"] == "url":
                assert ioc["vt_analysis"]["detection_type"] == "url_not_implemented"
            elif ioc["type"] in ["md5", "sha1", "sha256", "hash"]:
                assert ioc["vt_analysis"]["detection_type"] == "hash_not_implemented"

        # 4. Compare with sequential execution
        cy_sequential = await Cy.create_async(tools=tools, enable_parallel=False)

        start = time.time()
        result_sequential = await cy_sequential.run_async(
            cy_code, input_data=test_alert
        )
        duration_sequential = time.time() - start

        # Results should be identical
        assert result_parallel == result_sequential, (
            "Parallel and sequential results should be identical"
        )

        # 5. Verify performance improvement
        # With 5 async calls (3 domains + 2 IPs), parallel should be much faster
        speedup = duration_sequential / duration_parallel

        print("\n🔍 VirusTotal Pattern Performance:")
        print(f"   Sequential: {duration_sequential:.2f}s")
        print(f"   Parallel:   {duration_parallel:.2f}s")
        print(f"   Speedup:    {speedup:.2f}x")
        print("   Async calls: 5 (3 domains + 2 IPs)")

        # Should have significant speedup (at least 2x for 5 async calls)
        assert speedup > 2.0, (
            f"Expected >2x speedup for 5 async calls, got {speedup:.2f}x"
        )

        # Parallel should complete in roughly the time of one call (~0.1s)
        assert duration_parallel < 0.3, (
            f"Parallel should complete quickly, took {duration_parallel:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_virustotal_pattern_correctness(self):
        """Verify the VirusTotal pattern produces correct results."""

        call_order = []

        async def tracking_task_run(task_name, params):
            """Track call order while simulating API."""
            call_order.append(
                {
                    "task": task_name,
                    "domain": params.get("domain"),
                    "ip": params.get("ip"),
                }
            )
            await asyncio.sleep(0.05)
            return {"result": "success", "task": task_name}

        tools = default_registry.get_tools_dict()
        tools["task_run"] = tracking_task_run

        simple_code = """
alert = input
iocs = alert["iocs"]

for (ioc in iocs) {
    if (ioc["type"] == "domain") {
        ioc["result"] = task_run("analyze_domain", {"domain": ioc["value"]})
    } elif (ioc["type"] == "ip") {
        ioc["result"] = task_run("analyze_ip", {"ip": ioc["value"]})
    }
}

return alert
"""

        test_data = {
            "iocs": [
                {"type": "domain", "value": "site1.com"},
                {"type": "ip", "value": "1.1.1.1"},
                {"type": "domain", "value": "site2.com"},
            ]
        }

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Should be parallelizable
        assert cy.would_parallelize(simple_code) is True

        # Execute and verify
        result = await cy.run_async(simple_code, input_data=test_data)
        result_dict = ast.literal_eval(result)

        # All IOCs should have results
        for ioc in result_dict["iocs"]:
            assert "result" in ioc
            assert ioc["result"]["result"] == "success"

        # Verify all calls were made
        assert len(call_order) == 3
        assert call_order[0]["task"] == "analyze_domain"
        assert call_order[1]["task"] == "analyze_ip"
        assert call_order[2]["task"] == "analyze_domain"
