"""
TDD Test: Reproduce bug where optional parameters are incorrectly marked as required.

Bug: ToolRegistry.from_dict() marks ALL parameters as required=True,
even when the "required" field in metadata specifies only some are required.

This causes validation errors like "Missing required parameter 'indent'"
when calling to_json(data) without the optional indent parameter.
"""

from cy_language.tool_signature import ToolRegistry


class TestOptionalParametersBug:
    """Test that optional parameters are correctly handled in from_dict()."""

    def test_from_dict_respects_required_field(self):
        """
        Verify that from_dict() correctly marks parameters as optional
        when they're not in the "required" list.

        This test reproduces the bug where to_json(data, indent) was
        treating 'indent' as required when it should be optional.
        """
        # Legacy dict format with "required" field
        # to_json has 'data' as required, 'indent' as optional
        legacy_format = {
            "native::tools::to_json": {
                "parameters": {
                    "data": {"type": "object"},
                    "indent": {"type": "number"},
                },
                "required": ["data"],  # Only 'data' is required
                "return_type": {"type": "string"},
            }
        }

        # Create registry from legacy format
        registry = ToolRegistry.from_dict(legacy_format)

        # Get the tool signature
        tool_sig = registry.tools["native::tools::to_json"]

        # Verify 'data' is required
        assert "data" in tool_sig.parameters
        assert tool_sig.parameters["data"].required is True, (
            "Parameter 'data' should be required"
        )

        # Verify 'indent' is optional (BUG: currently fails - marked as required)
        assert "indent" in tool_sig.parameters
        assert tool_sig.parameters["indent"].required is False, (
            "Parameter 'indent' should be optional (BUG: incorrectly marked as required)"
        )

    def test_from_dict_defaults_all_required_when_no_required_field(self):
        """
        Verify backward compatibility: when "required" field is missing,
        all parameters should default to required=True.
        """
        legacy_format = {
            "native::tools::len": {
                "parameters": {"obj": {"type": "array"}},
                # No "required" field - should default to all required
                "return_type": {"type": "number"},
            }
        }

        registry = ToolRegistry.from_dict(legacy_format)
        tool_sig = registry.tools["native::tools::len"]

        # Should default to required=True when "required" field is missing
        assert tool_sig.parameters["obj"].required is True

    def test_from_dict_with_multiple_optional_parameters(self):
        """
        Test a tool with multiple optional parameters.
        """
        legacy_format = {
            "app::api::fetch": {
                "parameters": {
                    "url": {"type": "string"},
                    "timeout": {"type": "number"},
                    "headers": {"type": "object"},
                    "retry": {"type": "boolean"},
                },
                "required": ["url"],  # Only url is required
                "return_type": {"type": "object"},
            }
        }

        registry = ToolRegistry.from_dict(legacy_format)
        tool_sig = registry.tools["app::api::fetch"]

        # url should be required
        assert tool_sig.parameters["url"].required is True

        # All others should be optional
        assert tool_sig.parameters["timeout"].required is False
        assert tool_sig.parameters["headers"].required is False
        assert tool_sig.parameters["retry"].required is False

    def test_from_dict_empty_required_list(self):
        """
        Test that empty "required" list means all parameters are optional.
        """
        legacy_format = {
            "app::utils::get_config": {
                "parameters": {"key": {"type": "string"}, "default": {"type": "any"}},
                "required": [],  # No parameters required
                "return_type": {"type": "any"},
            }
        }

        registry = ToolRegistry.from_dict(legacy_format)
        tool_sig = registry.tools["app::utils::get_config"]

        # All parameters should be optional
        assert tool_sig.parameters["key"].required is False
        assert tool_sig.parameters["default"].required is False
