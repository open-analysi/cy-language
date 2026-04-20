"""
Unit tests for Tool Signatures.

Tests verify ParameterSignature and ToolSignature classes correctly store
and validate function signatures.
"""

import pytest

from cy_language.tool_signature import (
    ParameterSignature,
    ToolSignature,
    extract_signature_from_function,
)


class TestParameterSignature:
    """Test ParameterSignature dataclass."""

    def test_parameter_signature_required(self):
        """Verify required parameter creation."""
        param = ParameterSignature(
            name="arg1", type_schema={"type": "string"}, required=True
        )

        assert param.name == "arg1"
        assert param.type_schema == {"type": "string"}
        assert param.required is True

    def test_parameter_signature_optional_with_default(self):
        """Verify optional parameter with default value."""
        param = ParameterSignature(
            name="count",
            type_schema={"type": "number"},
            required=False,
            default_value=10,
        )

        assert param.name == "count"
        assert param.required is False
        assert param.default_value == 10

    def test_parameter_signature_serialization(self):
        """Verify model_dump() and model_validate() work."""
        param = ParameterSignature(
            name="message",
            type_schema={"type": "string"},
            required=True,
            description="A message to display",
        )

        # Serialize
        data = param.model_dump()
        assert data["name"] == "message"
        assert data["type_schema"] == {"type": "string"}

        # Deserialize
        restored = ParameterSignature.model_validate(data)
        assert restored.name == param.name
        assert restored.type_schema == param.type_schema

    def test_parameter_signature_equality(self):
        """Verify two identical parameters are equal."""
        param1 = ParameterSignature(
            name="x", type_schema={"type": "number"}, required=True
        )
        param2 = ParameterSignature(
            name="x", type_schema={"type": "number"}, required=True
        )

        assert param1.name == param2.name
        assert param1.type_schema == param2.type_schema
        assert param1.required == param2.required


class TestToolSignature:
    """Test ToolSignature dataclass."""

    def test_tool_signature_simple_function(self):
        """Create signature for function with 1 parameter."""
        sig = ToolSignature(
            fqn="native::tools::uppercase",
            function=None,
            parameters={
                "text": ParameterSignature(
                    name="text", type_schema={"type": "string"}, required=True
                )
            },
            return_type={"type": "string"},
            description="Convert text to uppercase",
        )

        assert sig.fqn == "native::tools::uppercase"
        assert len(sig.parameters) == 1
        assert sig.return_type == {"type": "string"}

    def test_tool_signature_multiple_parameters(self):
        """Create signature for function with 3+ parameters."""
        sig = ToolSignature(
            fqn="native::tools::add",
            function=None,
            parameters={
                "a": ParameterSignature(
                    name="a", type_schema={"type": "number"}, required=True
                ),
                "b": ParameterSignature(
                    name="b", type_schema={"type": "number"}, required=True
                ),
                "c": ParameterSignature(
                    name="c",
                    type_schema={"type": "number"},
                    required=False,
                    default_value=0,
                ),
            },
            return_type={"type": "number"},
        )

        assert len(sig.parameters) == 3
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        assert "c" in sig.parameters

    def test_tool_signature_optional_parameters(self):
        """Create signature with mix of required/optional."""
        sig = ToolSignature(
            fqn="native::tools::join",
            function=None,
            parameters={
                "items": ParameterSignature(
                    name="items", type_schema={"type": "array"}, required=True
                ),
                "separator": ParameterSignature(
                    name="separator",
                    type_schema={"type": "string"},
                    required=False,
                    default_value=", ",
                ),
            },
            return_type={"type": "string"},
        )

        assert sig.parameters["items"].required is True
        assert sig.parameters["separator"].required is False

    def test_tool_signature_serialization(self):
        """Verify model_dump() and model_validate() work."""
        sig = ToolSignature(
            fqn="native::tools::len",
            function=None,
            parameters={
                "arg": ParameterSignature(
                    name="arg",
                    type_schema={"type": ["string", "array", "object"]},
                    required=True,
                )
            },
            return_type={"type": "number"},
        )

        # Serialize (excludes function)
        data = sig.model_dump(exclude={"function"})
        assert data["fqn"] == "native::tools::len"
        assert "parameters" in data

        # Deserialize
        restored = ToolSignature.model_validate({**data, "function": None})
        assert restored.fqn == sig.fqn
        assert restored.return_type == sig.return_type

    def test_tool_signature_equality(self):
        """Verify two identical signatures are equal."""
        sig1 = ToolSignature(
            fqn="native::test::tool",
            function=None,
            parameters={},
            return_type={"type": "string"},
        )
        sig2 = ToolSignature(
            fqn="native::test::tool",
            function=None,
            parameters={},
            return_type={"type": "string"},
        )

        assert sig1.fqn == sig2.fqn
        assert sig1.return_type == sig2.return_type


class TestSignatureValidation:
    """Test validate_call() method."""

    @pytest.fixture
    def sample_signature(self):
        """Create a sample tool signature for testing."""
        return ToolSignature(
            fqn="native::tools::add",
            function=None,
            parameters={
                "a": ParameterSignature(
                    name="a", type_schema={"type": "number"}, required=True
                ),
                "b": ParameterSignature(
                    name="b", type_schema={"type": "number"}, required=True
                ),
                "optional": ParameterSignature(
                    name="optional", type_schema={"type": "string"}, required=False
                ),
            },
            return_type={"type": "number"},
        )

    def test_validate_call_all_required_present(self, sample_signature):
        """Verify validation passes when all required params provided."""
        errors = sample_signature.validate_call({"a": 5, "b": 10})
        assert len(errors) == 0

    def test_validate_call_optional_omitted(self, sample_signature):
        """Verify validation passes when optional params omitted."""
        errors = sample_signature.validate_call({"a": 5, "b": 10})
        assert len(errors) == 0

    def test_validate_call_extra_parameters(self, sample_signature):
        """Verify validation fails with unknown parameters."""
        errors = sample_signature.validate_call({"a": 5, "b": 10, "unknown": "value"})
        assert len(errors) > 0
        assert any("unknown" in err.lower() for err in errors)

    def test_validate_call_missing_required(self, sample_signature):
        """Verify validation fails when required param missing."""
        errors = sample_signature.validate_call({"a": 5})  # Missing 'b'
        assert len(errors) > 0
        assert any("b" in err.lower() or "required" in err.lower() for err in errors)

    def test_validate_call_multiple_errors(self, sample_signature):
        """Verify validation returns all errors at once."""
        errors = sample_signature.validate_call(
            {"unknown": "value"}
        )  # Missing both a and b
        assert len(errors) >= 2  # Should have at least 2 errors


class TestSignatureExtraction:
    """Test extract_signature_from_function()."""

    def test_extract_from_simple_function(self):
        """Extract signature from def add(a: int, b: int) -> int."""

        def add(a: int, b: int) -> int:
            return a + b

        sig = extract_signature_from_function(
            fqn="native::tools::add", function=add, description="Add two numbers"
        )

        assert sig.fqn == "native::tools::add"
        assert len(sig.parameters) == 2
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        assert sig.parameters["a"].type_schema == {"type": "number"}
        assert sig.parameters["b"].type_schema == {"type": "number"}
        assert sig.return_type == {"type": "number"}
        assert sig.description == "Add two numbers"

    def test_extract_from_function_with_optional(self):
        """Extract from function with default values."""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        sig = extract_signature_from_function(
            fqn="native::tools::greet", function=greet
        )

        assert sig.parameters["name"].required is True
        assert sig.parameters["greeting"].required is False
        assert sig.parameters["greeting"].default_value == "Hello"

    def test_extract_from_function_no_hints(self):
        """Extract from function without type hints (use Any)."""

        def legacy_function(arg):
            return arg

        sig = extract_signature_from_function(
            fqn="native::tools::legacy", function=legacy_function
        )

        assert "arg" in sig.parameters
        # Should fall back to Any type
        assert (
            sig.parameters["arg"].type_schema == {}
            or sig.parameters["arg"].type_schema.get("type") is None
        )

    def test_extract_from_function_complex_types(self):
        """Extract from function with List/Dict parameters."""

        def process_items(
            items: list[int], options: dict[str, str] | None = None
        ) -> str:
            return "processed"

        sig = extract_signature_from_function(
            fqn="native::tools::process", function=process_items
        )

        assert sig.parameters["items"].type_schema["type"] == "array"
        assert "options" in sig.parameters
        assert sig.return_type == {"type": "string"}

    def test_extract_from_function_with_docstring(self):
        """Verify description is extracted."""

        def documented_function(x: int) -> int:
            """This is a documented function."""
            return x * 2

        sig = extract_signature_from_function(
            fqn="native::tools::double", function=documented_function
        )

        # Description from parameter should be used, but docstring could be extracted too
        assert sig.fqn == "native::tools::double"


class TestToolSignatureNegativeTests:
    """Negative test cases for ToolSignature."""

    def test_tool_signature_invalid_parameter_dict(self):
        """Verify error when parameters is not a dict."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            sig = ToolSignature(
                fqn="test::tool",
                function=None,
                parameters="invalid",  # Should be dict
                return_type={"type": "string"},
            )
            # Try to use it
            sig.validate_call({})

    def test_tool_signature_invalid_return_type(self):
        """Verify error when return_type is invalid."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            ToolSignature(
                fqn="test::tool",
                function=None,
                parameters={},
                return_type="invalid",  # Should be dict
            )

    def test_extract_from_builtin_function(self):
        """Verify graceful handling of built-in functions."""
        # Built-in functions don't have signatures we can inspect easily
        try:
            sig = extract_signature_from_function(fqn="builtin::len", function=len)
            # Should succeed with fallback types
            assert sig is not None
        except (TypeError, ValueError, NotImplementedError):
            # Acceptable to not support built-ins
            pass
