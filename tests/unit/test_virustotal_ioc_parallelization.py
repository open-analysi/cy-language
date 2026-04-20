"""
Test parallelization of VirusTotal IOC batch analysis pattern.

This test verifies that when processing multiple IOCs (Indicators of Compromise)
through async task_run calls, the operations are properly parallelized.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestVirusTotalIOCParallelization:
    """Test VirusTotal IOC batch analysis parallelization."""

    @pytest.mark.asyncio
    async def test_ioc_batch_analysis_parallelization(self):
        """Test that IOC analysis with async task_run calls are parallelized."""

        # Simple async task_run that just sleeps
        async def mock_task_run(task_name, params):
            """Simple async sleep to test parallelization."""
            await asyncio.sleep(0.2)  # Simulate API latency
            return {"result": "completed", "task": task_name}

        # Get default tools and add our mock task_run
        tools = default_registry.get_tools_dict()
        tools["task_run"] = AsyncMock(side_effect=mock_task_run)

        # Test data with multiple IOCs
        test_alert = {
            "iocs": [
                {"value": "malicious.com", "type": "domain"},
                {"value": "192.168.1.100", "type": "ip"},
                {"value": "evil.org", "type": "domain"},
                {"value": "10.0.0.1", "type": "ip"},
                {"value": "suspicious.net", "type": "domain"},
                {"value": "172.16.0.1", "type": "ip"},
                {"value": "http://bad.url", "type": "url"},
                {"value": "d41d8cd98f00b204e9800998ecf8427e", "type": "md5"},
            ],
            "context": {
                "alert_id": "TEST-001",
                "severity": "high",
                "source": "firewall",
            },
        }

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

    # Call task_run for async operations (simplified for testing)
    if (ioc_type == "domain") {
        # Async call that will be parallelized
        vt_analysis = task_run("process_domain", {"value": ioc_value})
    } elif (ioc_type == "ip") {
        # Async call that will be parallelized
        vt_analysis = task_run("process_ip", {"value": ioc_value})
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
            "note": "IOC type '${ioc_type}' not supported for VirusTotal analysis"
        }
    }

    # Add VirusTotal analysis to the current IOC
    current_ioc["vt_analysis"] = vt_analysis
}

# Return the enriched alert
output = alert
return output
        """

        # Test with parallel execution enabled
        cy_parallel = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=2,  # Parallelize with 2+ IOCs
        )

        start = time.time()
        result_parallel = await cy_parallel.run_async(cy_code, input_data=test_alert)
        duration_parallel = time.time() - start

        # Parse the result - it's returned as JSON
        result_dict = json.loads(result_parallel)

        # Verify all IOCs were processed
        assert len(result_dict["iocs"]) == 8

        # Check that domain and IP IOCs have analysis results
        domain_iocs = [ioc for ioc in result_dict["iocs"] if ioc["type"] == "domain"]
        for ioc in domain_iocs:
            assert "vt_analysis" in ioc
            assert "result" in ioc["vt_analysis"]
            assert ioc["vt_analysis"]["result"] == "completed"

        # Check that IP IOCs have analysis results
        ip_iocs = [ioc for ioc in result_dict["iocs"] if ioc["type"] == "ip"]
        for ioc in ip_iocs:
            assert "vt_analysis" in ioc
            assert "result" in ioc["vt_analysis"]
            assert ioc["vt_analysis"]["result"] == "completed"

        # Check that URL and hash IOCs have placeholder analysis
        url_iocs = [ioc for ioc in result_dict["iocs"] if ioc["type"] == "url"]
        for ioc in url_iocs:
            assert "vt_analysis" in ioc
            assert ioc["vt_analysis"]["detection_type"] == "url_not_implemented"

        hash_iocs = [
            ioc
            for ioc in result_dict["iocs"]
            if ioc["type"] in ["md5", "sha1", "sha256", "hash"]
        ]
        for ioc in hash_iocs:
            assert "vt_analysis" in ioc
            assert ioc["vt_analysis"]["detection_type"] == "hash_not_implemented"

        # Reset mock for sequential test
        tools["task_run"].reset_mock()

        # Recreate tools to get fresh mocks
        tools = default_registry.get_tools_dict()
        tools["task_run"] = AsyncMock(side_effect=mock_task_run)

        # Test with sequential execution for comparison
        cy_sequential = await Cy.create_async(tools=tools, enable_parallel=False)

        start = time.time()
        result_sequential = await cy_sequential.run_async(
            cy_code, input_data=test_alert
        )
        duration_sequential = time.time() - start

        # Results should be identical
        assert result_parallel == result_sequential

        # With 8 IOCs (3 domains + 3 IPs that make async calls)
        # Sequential: 6 * 0.2s = 1.2s
        # Parallel: Should complete in ~0.2s (all in parallel)

        print("\n🔍 VirusTotal IOC Analysis Timing:")
        print(f"   Sequential: {duration_sequential:.2f}s")
        print(f"   Parallel:   {duration_parallel:.2f}s")
        print(f"   Speedup:    {duration_sequential / duration_parallel:.2f}x")

        # Parallel should be significantly faster
        # Add buffer for system overhead
        assert duration_parallel < 0.5, (
            f"Parallel IOC analysis took {duration_parallel:.2f}s (expected <0.5s)"
        )
        assert duration_sequential > 1.0, (
            f"Sequential IOC analysis took {duration_sequential:.2f}s (expected >1.0s)"
        )

        # Verify significant speedup
        speedup = duration_sequential / duration_parallel
        assert speedup > 2.0, f"Expected >2x speedup, got {speedup:.2f}x"

    @pytest.mark.asyncio
    async def test_ioc_analysis_with_dependencies(self):
        """Test IOC analysis when there are dependencies between iterations."""

        # Mock task_run with correlation detection
        async def mock_task_run_with_correlation(task_name, params):
            """Simulate VT API with correlation detection."""
            await asyncio.sleep(0.1)

            # Check for previous IOC correlations
            context = params.get("context", {})
            previous_iocs = context.get("previous_iocs", [])

            base_response = {
                "detection_type": task_name.split("_")[1],
                "threat_level": "Medium",
                "risk_score": 50,
            }

            # Add correlation info if previous IOCs exist
            if previous_iocs:
                base_response["correlations"] = len(previous_iocs)
                base_response["correlated_iocs"] = previous_iocs[:2]  # Keep first 2

            return base_response

        # Get default tools and add our mock task_run
        tools = default_registry.get_tools_dict()
        tools["task_run"] = AsyncMock(side_effect=mock_task_run_with_correlation)

        cy_code_with_deps = """
# Process IOCs with correlation tracking
alert = input
iocs = alert["iocs"]
processed_iocs = []

for (current_ioc in iocs) {
    ioc_value = current_ioc["value"]
    ioc_type = current_ioc["type"]

    # Build context with previously processed IOCs
    enriched_context = {
        "alert_id": alert["context"]["alert_id"],
        "previous_iocs": processed_iocs
    }

    # Call VT with enriched context
    vt_result = task_run("virustotal_domain_reputation_analysis", {
        "domain": ioc_value,
        "context": enriched_context
    })

    # Add to processed list for next iteration
    processed_iocs = processed_iocs + [ioc_value]

    # Add result to current IOC
    current_ioc["vt_analysis"] = vt_result
    current_ioc["processed_order"] = len(processed_iocs)
}

output = alert
return output
        """

        test_alert = {
            "iocs": [
                {"value": "site1.com", "type": "domain"},
                {"value": "site2.com", "type": "domain"},
                {"value": "site3.com", "type": "domain"},
            ],
            "context": {"alert_id": "TEST-002"},
        }

        # This should NOT be parallelized due to dependencies
        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Check if it would be parallelized
        would_parallelize = cy.would_parallelize(cy_code_with_deps)

        # Should NOT parallelize due to accumulator pattern (processed_iocs)
        assert would_parallelize is False, (
            "Loop with dependencies should not be parallelized"
        )

        # Run and verify correctness
        result = await cy.run_async(cy_code_with_deps, input_data=test_alert)
        result_dict = json.loads(result)

        # Verify processing order is maintained
        for i, ioc in enumerate(result_dict["iocs"]):
            assert ioc["processed_order"] == i + 1

            # Check correlations increase with each iteration
            if i > 0:
                assert "correlations" in ioc["vt_analysis"]
                assert ioc["vt_analysis"]["correlations"] == i

    @pytest.mark.asyncio
    async def test_mixed_sync_async_ioc_processing(self):
        """Test IOC processing with mixed sync and async operations."""

        def sync_enrich(ioc_value):
            """Synchronous enrichment function."""
            return {
                "enriched": True,
                "length": len(ioc_value),
                "uppercase": ioc_value.upper(),
            }

        async def async_validate(ioc_value):
            """Async validation function."""
            await asyncio.sleep(0.1)
            return {"valid": True, "confidence": 0.95, "validated_value": ioc_value}

        # Get default tools and add our custom tools
        tools = default_registry.get_tools_dict()
        tools["enrich_ioc"] = Mock(side_effect=sync_enrich)
        tools["validate_ioc"] = AsyncMock(side_effect=async_validate)
        tools["task_run"] = AsyncMock(
            side_effect=lambda name, params: asyncio.create_task(
                async_validate(params.get("value", ""))
            )
        )

        cy_code_mixed = """
alert = input
iocs = alert["iocs"]

# Process each IOC with mixed operations
for (ioc in iocs) {
    # Synchronous enrichment
    enrichment = enrich_ioc(ioc["value"])

    # Async validation
    validation = validate_ioc(ioc["value"])

    # Combine results
    ioc["enrichment"] = enrichment
    ioc["validation"] = validation
}

output = alert
return output
        """

        test_alert = {
            "iocs": [{"value": f"ioc{i}", "type": "generic"} for i in range(5)]
        }

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        start = time.time()
        result = await cy.run_async(cy_code_mixed, input_data=test_alert)
        duration = time.time() - start

        result_dict = json.loads(result)

        # Verify all IOCs processed correctly
        for ioc in result_dict["iocs"]:
            assert "enrichment" in ioc
            assert "validation" in ioc
            assert ioc["enrichment"]["enriched"] is True
            assert ioc["validation"]["valid"] is True

        # With async operations, should complete faster than sequential
        # 5 IOCs * 0.1s = 0.5s sequential, ~0.1s parallel
        assert duration < 0.3, f"Mixed operations took {duration:.2f}s"

        print(f"\n🔄 Mixed Sync/Async IOC Processing: {duration:.2f}s")
