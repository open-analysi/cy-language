"""
Integration tests for Tool Signature System.

Tests verify end-to-end flows work correctly across all components.
"""

import json

from cy_language.tool_resolver import ToolResolver
from cy_language.tool_signature import (
    ParameterSignature,
    ToolSignature,
    extract_signature_from_function,
)


class TestEndToEndWorkflows:
    """Test end-to-end workflow integration."""

    def test_e2e_native_function_to_signature_query(self):
        """Full flow: native function → extract → query.

        Create a simple Python function with type hints, use
        extract_signature_from_function() to get signature, register
        with ToolResolver, and verify signature is correct.
        """

        # Step 1: Define a function
        def multiply(x: int, y: int) -> int:
            """Multiply two numbers."""
            return x * y

        # Step 2: Extract signature
        sig = extract_signature_from_function(
            fqn="test::math::multiply",
            function=multiply,
            description="Multiply two integers",
        )

        # Step 3: Register with ToolResolver
        resolver = ToolResolver()
        resolver.register_tool_with_types(sig)

        # Step 4: Query and verify
        retrieved_sig = resolver.get_signature("test::math::multiply")
        assert retrieved_sig is not None
        assert retrieved_sig.fqn == "test::math::multiply"
        assert retrieved_sig.return_type == {"type": "number"}
        assert len(retrieved_sig.parameters) == 2
        assert "x" in retrieved_sig.parameters
        assert "y" in retrieved_sig.parameters

    def test_e2e_all_native_functions_have_signatures(self):
        """Verify all native tools work.

        Use ToolResolver.from_native_tools() and verify that for each
        native function, get_signature() returns valid signature and
        return types match function annotations.
        """
        resolver = ToolResolver.from_native_tools()

        # Check key native functions (fqn, expected_return_type)
        # Note: str is registered as native::type::str (not native::tools::str)
        expected_functions = [
            ("native::tools::len", {"type": "number"}),
            ("native::tools::sum", {"type": "number"}),  # Union[int, float] → number
            ("native::type::str", {"type": "string"}),
            ("native::str::uppercase", {"type": "string"}),
            ("native::str::lowercase", {"type": "string"}),
            ("native::str::join", {"type": "string"}),
        ]

        for fqn, expected_return in expected_functions:
            assert resolver.has_signature(fqn), f"Missing signature for {fqn}"

            sig = resolver.get_signature(fqn)
            assert sig is not None, f"Signature is None for {fqn}"
            assert sig.return_type == expected_return, (
                f"Wrong return type for {fqn}: {sig.return_type}"
            )

    def test_e2e_fqn_resolution_with_types(self):
        """Verify + integration.

        Register tool with types, resolve using short name, and verify
        resolved FQN returns correct signature.
        """
        # Create and register signature
        sig = ToolSignature(
            fqn="app::demo::greet",
            function=lambda name: f"Hello, {name}!",
            parameters={
                "name": ParameterSignature(
                    name="name", type_schema={"type": "string"}, required=True
                )
            },
            return_type={"type": "string"},
            description="Greet someone",
        )

        resolver = ToolResolver()
        resolver.register_tool_with_types(sig)

        # Resolve using short name
        fqn, original = resolver.resolve("greet")
        assert fqn == "app::demo::greet"
        assert original == "greet"

        # Verify signature is accessible
        retrieved_sig = resolver.get_signature(fqn)
        assert retrieved_sig is not None
        assert retrieved_sig.return_type == {"type": "string"}

    def test_e2e_export_signatures_to_json_file(self):
        """Verify serialization works.

        Create resolver with multiple tools, export signatures to JSON
        dict, and verify JSON is valid and contains all expected data.
        """
        resolver = ToolResolver()

        # Register multiple tools
        for i in range(3):
            sig = ToolSignature(
                fqn=f"test::tools::tool{i}",
                function=None,
                parameters={},
                return_type={"type": "string"},
                description=f"Test tool {i}",
            )
            resolver.register_tool_with_types(sig)

        # Export
        exported = resolver.export_signatures()

        # Verify it's JSON-serializable
        json_str = json.dumps(exported)
        assert json_str is not None

        # Verify all tools present
        assert "test::tools::tool0" in exported
        assert "test::tools::tool1" in exported
        assert "test::tools::tool2" in exported

    def test_e2e_import_external_mcp_signatures(self):
        """Simulate MCP tool registration.

        Create MCP-style tool signature JSON, import into ToolResolver,
        verify signatures are queryable, and verify short names work for
        imported tools.
        """
        # Simulate MCP tool definitions
        mcp_tools = {
            "mcp::github::create_issue": {
                "fqn": "mcp::github::create_issue",
                "parameters": {
                    "title": {
                        "name": "title",
                        "type_schema": {"type": "string"},
                        "required": True,
                    },
                    "body": {
                        "name": "body",
                        "type_schema": {"type": "string"},
                        "required": False,
                    },
                },
                "return_type": {
                    "type": "object",
                    "properties": {
                        "issue_number": {"type": "number"},
                        "url": {"type": "string"},
                    },
                },
                "description": "Create a GitHub issue",
            }
        }

        # Import
        resolver = ToolResolver()
        resolver.import_signatures(mcp_tools)

        # Verify queryable
        assert resolver.has_signature("mcp::github::create_issue")
        sig = resolver.get_signature("mcp::github::create_issue")
        assert sig is not None
        assert sig.return_type["type"] == "object"
        assert "title" in sig.parameters

        # Verify short name works
        fqn, _ = resolver.resolve("create_issue")
        assert fqn == "mcp::github::create_issue"


class TestCrossComponentIntegration:
    """Test integration across multiple components."""

    def test_type_converter_used_in_extraction(self):
        """Verify Python types convert during extraction.

        Function with List[Dict[str, int]] parameter should have correct
        JSON Schema after extraction.
        """

        def process_data(items: list[dict[str, int]]) -> str:
            """Process list of dicts."""
            return "processed"

        sig = extract_signature_from_function(
            fqn="test::data::process", function=process_data
        )

        # Verify complex type was converted correctly
        items_param = sig.parameters["items"]
        assert items_param.type_schema["type"] == "array"
        assert items_param.type_schema["items"]["type"] == "object"

    def test_signature_validation_with_real_calls(self):
        """Verify validate_call() catches errors.

        Register function signature, try calling with wrong argument types,
        and verify validation returns appropriate errors.
        """
        sig = ToolSignature(
            fqn="test::calc::divide",
            function=None,
            parameters={
                "numerator": ParameterSignature(
                    name="numerator", type_schema={"type": "number"}, required=True
                ),
                "denominator": ParameterSignature(
                    name="denominator", type_schema={"type": "number"}, required=True
                ),
            },
            return_type={"type": "number"},
        )

        # Valid call
        errors = sig.validate_call({"numerator": 10, "denominator": 2})
        assert len(errors) == 0

        # Invalid call - missing parameter
        errors = sig.validate_call({"numerator": 10})
        assert len(errors) > 0
        assert any("denominator" in err.lower() for err in errors)

        # Invalid call - extra parameter
        errors = sig.validate_call({"numerator": 10, "denominator": 2, "extra": "bad"})
        assert len(errors) > 0


class TestPerformance:
    """Performance tests."""

    def test_signature_extraction_performance(self):
        """Verify extraction is fast enough.

        Extract signatures from 50+ functions and verify completes in < 1 second.
        """
        import time

        # Create 50 test functions
        functions = []
        for i in range(50):

            def test_func(x: int, y: str = "default") -> bool:
                return True

            functions.append((f"test::perf::func{i}", test_func))

        # Time the extraction
        start = time.time()
        for fqn, func in functions:
            sig = extract_signature_from_function(fqn, func)
            assert sig is not None
        elapsed = time.time() - start

        # Should complete in < 1 second
        assert elapsed < 1.0, f"Extraction took {elapsed:.2f}s (expected < 1.0s)"
