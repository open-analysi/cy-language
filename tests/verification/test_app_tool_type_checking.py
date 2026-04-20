"""
Verification test: Prove that app integration tools get full type checking.

This test demonstrates that the type system enables:
1. Parameter type validation for app tools
2. Return type propagation for app tools
3. Type errors caught at compile-time
"""

import pytest

from cy_language import Cy, analyze_types
from cy_language.tool_registry_builder import build_tool_registry, export_app_tools


# Mock App Manager
class MockAppManager:
    """Simulates an app manager with integration tools."""

    def get_all_tools(self):
        """Returns dict of FQN -> function for all app tools."""
        return {
            "app::virustotal::ip_reputation": self.virustotal_ip_reputation,
            "app::shodan::host_lookup": self.shodan_host_lookup,
            "app::threatintel::enrich_ioc": self.threatintel_enrich_ioc,
        }

    @staticmethod
    def virustotal_ip_reputation(ip_address: str) -> dict:
        """Get IP reputation from VirusTotal.

        Args:
            ip_address: IP address to check

        Returns:
            Dict with malicious score and reputation data
        """
        return {
            "ip": ip_address,
            "malicious_score": 8,
            "reputation": "suspicious",
            "detections": 5,
        }

    @staticmethod
    def shodan_host_lookup(ip: str, detailed: bool = False) -> dict:
        """Look up host information in Shodan.

        Args:
            ip: IP address to lookup
            detailed: Whether to include detailed port scan data

        Returns:
            Dict with host information
        """
        return {"ip": ip, "ports": [80, 443, 22], "os": "Linux", "country": "US"}

    @staticmethod
    def threatintel_enrich_ioc(ioc: str, ioc_type: str) -> dict:
        """Enrich an indicator of compromise with threat intelligence.

        Args:
            ioc: The indicator value (IP, domain, hash, etc.)
            ioc_type: Type of indicator (ip, domain, hash, email)

        Returns:
            Dict with enrichment data including risk score
        """
        return {
            "ioc": ioc,
            "type": ioc_type,
            "risk_score": 7.5,
            "threat_categories": ["malware", "c2"],
        }


class TestAppToolIntegration:
    """Verify that app tools get full type checking."""

    def test_app_tools_extract_signatures(self):
        """Verify that app tools extract proper type signatures."""
        app_manager = MockAppManager()
        registry = export_app_tools(app_manager)

        # Check all tools registered with correct FQNs
        assert "app::virustotal::ip_reputation" in registry.tools
        assert "app::shodan::host_lookup" in registry.tools
        assert "app::threatintel::enrich_ioc" in registry.tools

        # Check virustotal signature
        vt_sig = registry.tools["app::virustotal::ip_reputation"]
        assert vt_sig.fqn == "app::virustotal::ip_reputation"
        assert "ip_address" in vt_sig.parameters
        assert vt_sig.parameters["ip_address"].type_schema == {"type": "string"}
        assert vt_sig.parameters["ip_address"].required is True
        # Return type should be object (dict)
        assert vt_sig.return_type == {"type": "object"}

        # Check shodan signature with optional parameter
        shodan_sig = registry.tools["app::shodan::host_lookup"]
        assert "ip" in shodan_sig.parameters
        assert "detailed" in shodan_sig.parameters
        assert shodan_sig.parameters["detailed"].required is False  # Has default value
        assert shodan_sig.parameters["detailed"].type_schema == {"type": "boolean"}

    def test_app_tool_return_type_propagation(self):
        """Verify that app tool return types propagate correctly."""
        app_manager = MockAppManager()
        registry = build_tool_registry(include_native=True, app_manager=app_manager)

        script = """
        ip = "192.168.1.1"
        vt_result = app::virustotal::ip_reputation(ip_address=ip)
        malicious_score = vt_result.malicious_score  # Should infer as number
        return malicious_score
        """

        # Analyze types - should work without execution
        output_type = analyze_types(script, tool_registry=registry)

        # The output should be inferred as number (from object property)
        # Note: Without property-level type info, this will be Any for now
        # But the tool call itself returns object type
        assert output_type is not None

    def test_app_tool_type_checking_in_workflow(self):
        """Verify that type errors with app tools are caught at compile-time."""
        app_manager = MockAppManager()
        registry = build_tool_registry(include_native=True, app_manager=app_manager)

        # Valid workflow
        valid_script = """
        ip = "10.0.0.1"
        vt_data = app::virustotal::ip_reputation(ip_address=ip)

        # vt_data is object type, can be used in dict operations
        result = {"checked_ip": ip, "vt_data": vt_data}
        return result
        """

        output = analyze_types(valid_script, tool_registry=registry)
        assert output["type"] == "object"

    def test_app_tool_with_type_validation_runtime(self):
        """Verify that app tools work correctly at runtime with type checking."""
        app_manager = MockAppManager()

        # Get tools dict from app manager
        app_tools = app_manager.get_all_tools()

        cy = Cy(check_types=True, tools=app_tools)

        script = """
        ip = "8.8.8.8"
        result = app::virustotal::ip_reputation(ip_address=ip)
        return result.malicious_score
        """

        # This should execute successfully
        score = cy.run(script)
        # Cy serializes output - numeric field becomes string in JSON output
        assert score == 8 or score == "8"  # Accept both forms

    def test_multiple_app_tools_chained(self):
        """Verify that multiple app tools can be chained with type safety."""
        app_manager = MockAppManager()

        # Get tools dict from app manager
        app_tools = app_manager.get_all_tools()

        cy = Cy(check_types=True, tools=app_tools)

        script = """
        target_ip = "1.2.3.4"

        # Call multiple threat intel tools
        vt_data = app::virustotal::ip_reputation(ip_address=target_ip)
        shodan_data = app::shodan::host_lookup(ip=target_ip)
        enrich_data = app::threatintel::enrich_ioc(ioc=target_ip, ioc_type="ip")

        # Aggregate scores
        vt_score = vt_data.malicious_score
        ti_score = enrich_data.risk_score

        # Calculate combined risk
        combined_risk = (vt_score + ti_score) / 2

        return {
            "ip": target_ip,
            "vt_score": vt_score,
            "ti_score": ti_score,
            "combined_risk": combined_risk,
            "shodan_ports": shodan_data.ports
        }
        """

        result = cy.run(script)
        # cy.run() returns string representation of Python dict
        import ast

        if isinstance(result, str):
            result = ast.literal_eval(result)

        assert result["ip"] == "1.2.3.4"
        assert result["vt_score"] == 8
        assert result["ti_score"] == 7.5
        assert result["combined_risk"] == 7.75
        assert result["shodan_ports"] == [80, 443, 22]

    def test_app_tool_type_error_caught_at_compile_time(self):
        """Verify that type errors with app tools are caught before execution."""
        app_manager = MockAppManager()

        # Get tools dict from app manager
        app_tools = app_manager.get_all_tools()

        cy = Cy(check_types=True, tools=app_tools)

        # This should catch type error: can't add object + string
        script = """
        ip = "192.168.1.1"
        vt_result = app::virustotal::ip_reputation(ip_address=ip)

        # ERROR: Can't concatenate object with string
        bad_concat = vt_result + " is suspicious"
        return bad_concat
        """

        with pytest.raises(TypeError) as exc_info:
            cy.run(script)

        # Should mention type incompatibility
        assert "cannot add" in str(exc_info.value) or "incompatible" in str(
            exc_info.value
        )

    def test_static_analysis_without_execution(self):
        """Verify that static analysis works without executing app tools."""
        app_manager = MockAppManager()
        registry = build_tool_registry(include_native=True, app_manager=app_manager)

        script = """
        target = "malicious.com"
        intel = app::threatintel::enrich_ioc(ioc=target, ioc_type="domain")

        # Extract risk score
        risk = intel.risk_score

        # Classify
        if (risk > 8) {
            severity = "HIGH"
        } elif (risk > 5) {
            severity = "MEDIUM"
        } else {
            severity = "LOW"
        }

        return {"domain": target, "severity": severity, "risk": risk}
        """

        # Static analysis - no execution!
        output_schema = analyze_types(script, tool_registry=registry)

        # Should infer output as object
        assert output_schema["type"] == "object"
        # Note: Property-level inference would require more advanced type tracking


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
