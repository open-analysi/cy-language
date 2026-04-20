"""Unit tests for ArgumentAdapter and bind_arguments()."""

import pytest

from cy_language.argument_adapter import ArgumentAdapter
from cy_language.tool_signature import bind_arguments


class TestBindArguments:
    """Test the canonical bind_arguments() algorithm."""

    def test_all_positional(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [5, 3], {})
        assert bound == {"a": 5, "b": 3}
        assert errors == []

    def test_all_named(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [], {"a": 5, "b": 3})
        assert bound == {"a": 5, "b": 3}
        assert errors == []

    def test_mixed_positional_then_named(self):
        bound, errors = bind_arguments(["a", "b", "c"], {"a"}, [5], {"b": 3, "c": 7})
        assert bound == {"a": 5, "b": 3, "c": 7}
        assert errors == []

    def test_optional_params_not_required(self):
        """Omitting optional params is fine."""
        bound, errors = bind_arguments(
            ["value", "option"], {"value"}, [], {"value": "test"}
        )
        assert bound == {"value": "test"}
        assert errors == []

    def test_varargs_not_supported(self):
        """bind_arguments doesn't handle *args — caller must skip for those."""
        # With only 1 param defined, 4 positional is "too many"
        _, errors = bind_arguments(["a"], {"a"}, [1, 2, 3, 4], {})
        assert any("Too many" in e for e in errors)

    def test_too_many_positional(self):
        _, errors = bind_arguments(["a"], {"a"}, [1, 2, 3], {})
        assert len(errors) == 1
        assert "Too many positional" in errors[0]

    def test_duplicate_param(self):
        _, errors = bind_arguments(["a", "b"], {"a", "b"}, [5], {"a": 10})
        assert any("both positionally and by name" in e for e in errors)

    def test_unknown_named(self):
        _, errors = bind_arguments(["a", "b"], {"a", "b"}, [], {"a": 1, "z": 99})
        assert any("Unknown parameter 'z'" in e for e in errors)

    def test_missing_required(self):
        _, errors = bind_arguments(["a", "b"], {"a", "b"}, [5], {})
        assert any("Missing required parameter 'b'" in e for e in errors)


class TestArgumentAdapterNativeValidation:
    """Test validate_native_call()."""

    def setup_method(self):
        self.adapter = ArgumentAdapter()

    def test_valid_call(self):
        def add(a: int, b: int) -> int:
            return a + b

        # Should not raise
        self.adapter.validate_native_call(add, [5, 3], {})

    def test_valid_mixed_call(self):
        def add(a: int, b: int) -> int:
            return a + b

        self.adapter.validate_native_call(add, [5], {"b": 3})

    def test_defaults_handled(self):
        def func_with_defaults(value: str, option: bool = True) -> str:
            return f"{value}_{option}"

        self.adapter.validate_native_call(func_with_defaults, [], {"value": "test"})

    def test_varargs_passthrough(self):
        def add_multiple(*args) -> int:
            return sum(args)

        # Should not raise — *args functions skip validation
        self.adapter.validate_native_call(add_multiple, [1, 2, 3, 4], {})

    def test_signature_caching(self):
        def test_func(param: int) -> int:
            return param

        sig1 = self.adapter.get_signature(test_func)
        sig2 = self.adapter.get_signature(test_func)
        assert sig1 is sig2

    def test_too_many_positional(self):
        def simple_func(a: int) -> int:
            return a

        with pytest.raises(ValueError, match="Too many.*arguments"):
            self.adapter.validate_native_call(simple_func, [1, 2, 3], {})

    def test_duplicate_param(self):
        def add(a: int, b: int) -> int:
            return a + b

        with pytest.raises(ValueError, match="both positionally and by name"):
            self.adapter.validate_native_call(add, [1], {"a": 2})


class TestArgumentAdapterMCPNormalization:
    """Test normalize_mcp_call()."""

    def setup_method(self):
        class MockMCPManager:
            def get_tool_parameter_names(self, tool_name):
                if tool_name == "mcp::demo::add":
                    return ["a", "b"]
                return None

        self.adapter = ArgumentAdapter(mcp_manager=MockMCPManager())

    def test_positional_to_named(self):
        result = self.adapter.normalize_mcp_call("mcp::demo::add", [5, 3], {})
        assert result == {"a": 5, "b": 3}

    def test_named_passthrough(self):
        result = self.adapter.normalize_mcp_call("mcp::demo::add", [], {"a": 5, "b": 3})
        assert result == {"a": 5, "b": 3}

    def test_mixed_to_named(self):
        result = self.adapter.normalize_mcp_call("mcp::demo::add", [5], {"b": 3})
        assert result == {"a": 5, "b": 3}

    def test_no_schema_rejects_positional(self):
        """MCP tool without schema can't accept positional args."""
        with pytest.raises(ValueError, match="requires named arguments"):
            self.adapter.normalize_mcp_call("mcp::unknown::tool", [1, 2], {})


class TestLegacyNormalizeArguments:
    """Test the legacy normalize_arguments() compatibility method."""

    def setup_method(self):
        class MockMCPManager:
            def get_tool_parameter_names(self, tool_name):
                if tool_name == "mcp::demo::add":
                    return ["a", "b"]
                return None

        self.adapter = ArgumentAdapter(mcp_manager=MockMCPManager())

    def test_native_passthrough(self):
        def add(a: int, b: int) -> int:
            return a + b

        args, kwargs = self.adapter.normalize_arguments("native", add, [1], {"b": 2})
        assert args == [1]
        assert kwargs == {"b": 2}

    def test_mcp_converts_to_named(self):
        args, kwargs = self.adapter.normalize_arguments(
            "mcp", None, [5, 3], {}, func_name="mcp::demo::add"
        )
        assert args == []
        assert kwargs == {"a": 5, "b": 3}
