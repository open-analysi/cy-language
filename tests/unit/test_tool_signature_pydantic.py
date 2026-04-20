"""
Unit tests for Pydantic conversion of tool signatures.

Tests verify that ParameterSignature, ToolSignature, and ToolRegistry are properly
converted to Pydantic models with validation.

These tests follow TDD - they will FAIL initially since ToolRegistry is currently a dataclass,
and will PASS once we convert to Pydantic with validators.
"""

import pytest

from cy_language.tool_signature import ParameterSignature, ToolRegistry, ToolSignature


class TestParameterSignaturePydantic:
    """Test Pydantic conversion of ParameterSignature."""

    def test_parameter_signature_valid_creation(self):
        """Verify ParameterSignature can be created with valid data."""
        param = ParameterSignature(
            name="count",
            type_schema={"type": "number"},
            required=True,
            description="Number of items",
        )

        assert param.name == "count"
        assert param.type_schema == {"type": "number"}
        assert param.required is True
        assert param.description == "Number of items"

    def test_parameter_signature_defaults(self):
        """Verify default values work correctly (required=True, description="")."""
        param = ParameterSignature(name="value", type_schema={"type": "string"})

        # Defaults should be set
        assert param.required is True
        assert param.description == ""
        assert param.default_value is None

    def test_parameter_signature_optional_with_default(self):
        """Verify optional parameter with default value."""
        param = ParameterSignature(
            name="timeout",
            type_schema={"type": "number"},
            required=False,
            default_value=30,
        )

        assert param.required is False
        assert param.default_value == 30

    def test_parameter_signature_invalid_type_schema(self):
        """
        Verify validation rejects non-dict type_schema.

        PYDANTIC VALIDATION TEST: Will FAIL with dataclass, PASS with Pydantic.
        """
        # Should raise ValidationError when type_schema is not a dict
        with pytest.raises((ValueError, TypeError)) as exc_info:
            ParameterSignature(
                name="bad_param",
                type_schema="not a dict",  # INVALID
            )

        error_msg = str(exc_info.value).lower()
        assert "type_schema" in error_msg or "dict" in error_msg


class TestToolSignaturePydantic:
    """Test Pydantic conversion of ToolSignature."""

    def test_tool_signature_valid_fqn_native(self):
        """Verify native namespace FQN is accepted."""
        sig = ToolSignature(
            function=None,
            fqn="native::tools::len",
            parameters={},
            return_type={"type": "number"},
        )

        assert sig.fqn == "native::tools::len"

    def test_tool_signature_valid_fqn_mcp(self):
        """Verify mcp namespace FQN is accepted."""
        sig = ToolSignature(
            function=None,
            fqn="mcp::server::tool",
            parameters={},
            return_type={"type": "string"},
        )

        assert sig.fqn == "mcp::server::tool"

    def test_tool_signature_valid_fqn_app(self):
        """Verify app namespace FQN is accepted."""
        sig = ToolSignature(
            function=None,
            fqn="app::integration::action",
            parameters={},
            return_type={"type": "object"},
        )

        assert sig.fqn == "app::integration::action"

    def test_tool_signature_valid_fqn_arc(self):
        """Verify arc namespace FQN is accepted."""
        sig = ToolSignature(
            function=None,
            fqn="arc::archetype::task",
            parameters={},
            return_type={"type": "object"},
        )

        assert sig.fqn == "arc::archetype::task"

    def test_tool_signature_with_parameters(self):
        """Verify ToolSignature can store parameter signatures."""
        params = {
            "ip": ParameterSignature(
                name="ip", type_schema={"type": "string"}, required=True
            ),
            "port": ParameterSignature(
                name="port",
                type_schema={"type": "number"},
                required=False,
                default_value=80,
            ),
        }

        sig = ToolSignature(
            function=None,
            fqn="app::scanner::check_port",
            parameters=params,
            return_type={"type": "boolean"},
        )

        assert len(sig.parameters) == 2
        assert sig.parameters["ip"].required is True
        assert sig.parameters["port"].default_value == 80

    def test_tool_signature_invalid_fqn_format_too_few_parts(self):
        """
        Verify FQN with too few parts is rejected.

        PYDANTIC VALIDATION TEST: Will FAIL with dataclass, PASS with Pydantic validator.
        """
        # Should raise ValidationError for FQN with only 2 parts
        with pytest.raises((ValueError, TypeError)) as exc_info:
            ToolSignature(
                function=None,
                fqn="native::len",  # INVALID - only 2 parts
                parameters={},
                return_type={"type": "number"},
            )

        error_msg = str(exc_info.value).lower()
        assert "fqn" in error_msg or "format" in error_msg

    def test_tool_signature_invalid_fqn_format_too_many_parts(self):
        """
        Verify FQN with too many parts is rejected.

        PYDANTIC VALIDATION TEST: Will FAIL with dataclass, PASS with Pydantic validator.
        """
        with pytest.raises((ValueError, TypeError)) as exc_info:
            ToolSignature(
                function=None,
                fqn="native::tools::extra::len",  # INVALID - 4 parts
                parameters={},
                return_type={"type": "number"},
            )

        error_msg = str(exc_info.value).lower()
        assert "fqn" in error_msg or "format" in error_msg

    def test_tool_signature_invalid_namespace(self):
        """
        Verify invalid namespace is rejected.

        PYDANTIC VALIDATION TEST: Valid namespaces are native, mcp, app, arc.
        """
        with pytest.raises((ValueError, TypeError)) as exc_info:
            ToolSignature(
                function=None,
                fqn="invalid::tools::len",  # INVALID namespace
                parameters={},
                return_type={"type": "number"},
            )

        error_msg = str(exc_info.value).lower()
        assert "namespace" in error_msg or "invalid" in error_msg

    def test_tool_signature_empty_fqn(self):
        """Verify empty FQN is rejected."""
        with pytest.raises((ValueError, TypeError)) as exc_info:
            ToolSignature(
                function=None,
                fqn="",  # INVALID - empty
                parameters={},
                return_type={"type": "string"},
            )

        error_msg = str(exc_info.value).lower()
        assert "fqn" in error_msg or "empty" in error_msg or "format" in error_msg


class TestToolRegistryPydantic:
    """Test Pydantic conversion of ToolRegistry."""

    def test_tool_registry_creation(self):
        """Verify ToolRegistry can be created."""
        registry = ToolRegistry()

        assert registry.tools == {}

    def test_tool_registry_add_tool(self):
        """Verify tools can be added to registry."""
        registry = ToolRegistry()

        sig = ToolSignature(
            function=None,
            fqn="native::tools::len",
            parameters={},
            return_type={"type": "number"},
        )

        registry.add_tool(sig)

        assert "native::tools::len" in registry.tools
        assert registry.tools["native::tools::len"] == sig

    def test_tool_registry_merge(self):
        """Verify merge combines two registries."""
        reg1 = ToolRegistry()
        reg1.add_tool(
            ToolSignature(
                function=None,
                fqn="native::tools::len",
                parameters={},
                return_type={"type": "number"},
            )
        )

        reg2 = ToolRegistry()
        reg2.add_tool(
            ToolSignature(
                function=None,
                fqn="native::tools::str",
                parameters={},
                return_type={"type": "string"},
            )
        )

        # Merge reg2 into reg1
        reg1.merge(reg2)

        assert len(reg1.tools) == 2
        assert "native::tools::len" in reg1.tools
        assert "native::tools::str" in reg1.tools

    def test_tool_registry_merge_returns_self(self):
        """Verify merge returns self for method chaining."""
        reg1 = ToolRegistry()
        reg2 = ToolRegistry()

        result = reg1.merge(reg2)

        assert result is reg1

    def test_tool_registry_export_for_analyze_types(self):
        """
        Verify export produces correct dict format for analyze_types().

        STUB TEST: Will FAIL until export_for_analyze_types() is implemented.
        """
        registry = ToolRegistry()
        registry.add_tool(
            ToolSignature(
                function=None,
                fqn="native::tools::len",
                parameters={
                    "obj": ParameterSignature(name="obj", type_schema={"type": "array"})
                },
                return_type={"type": "number"},
            )
        )

        # Currently stubbed - will raise NotImplementedError
        exported = registry.export_for_analyze_types()

        # Expected format: {fqn: {"parameters": {...}, "return_type": {...}}}
        assert exported == {
            "native::tools::len": {
                "parameters": {"obj": {"type": "array"}},
                "return_type": {"type": "number"},
            }
        }

    def test_tool_registry_from_dict_backward_compat(self):
        """
        Verify from_dict() handles legacy dict format.

        STUB TEST: Will FAIL until from_dict() is implemented.
        """
        # Legacy dict format (pre-Pydantic)
        old_format = {
            "native::tools::len": {
                "parameters": {"obj": {"type": "array"}},
                "return_type": {"type": "number"},
            }
        }

        # Currently stubbed - will raise NotImplementedError
        registry = ToolRegistry.from_dict(old_format)

        assert "native::tools::len" in registry.tools
        assert registry.tools["native::tools::len"].return_type == {"type": "number"}

    def test_tool_registry_multiple_tools(self):
        """Verify registry can store multiple tools."""
        registry = ToolRegistry()

        tools = [
            ToolSignature(
                fqn="native::tools::len",
                function=None,
                parameters={},
                return_type={"type": "number"},
            ),
            ToolSignature(
                fqn="native::tools::str",
                function=None,
                parameters={},
                return_type={"type": "string"},
            ),
            ToolSignature(
                fqn="mcp::test::tool",
                function=None,
                parameters={},
                return_type={"type": "object"},
            ),
        ]

        for tool in tools:
            registry.add_tool(tool)

        assert len(registry.tools) == 3

    def test_tool_registry_merge_overwrites_duplicates(self):
        """Verify merge overwrites tools with same FQN."""
        reg1 = ToolRegistry()
        reg1.add_tool(
            ToolSignature(
                function=None,
                fqn="native::tools::test",
                parameters={},
                return_type={"type": "number"},
            )
        )

        reg2 = ToolRegistry()
        reg2.add_tool(
            ToolSignature(
                function=None,
                fqn="native::tools::test",
                parameters={},
                return_type={"type": "string"},  # Different return type
            )
        )

        reg1.merge(reg2)

        # Should have overwritten with reg2's version
        assert reg1.tools["native::tools::test"].return_type == {"type": "string"}
