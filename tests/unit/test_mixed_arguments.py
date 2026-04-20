"""Comprehensive tests for mixed positional + named arguments.

Mixed arguments follow the rule: 0+ positional args first, then 0+ named args.
Once a named argument appears, all remaining must be named.
This is the standard pattern used by Python, Kotlin, Swift, etc.
"""

import pytest

from cy_language import Cy
from cy_language.argument_adapter import ArgumentAdapter
from cy_language.tool_signature import bind_arguments

# ---------------------------------------------------------------------------
# Helper tools used across tests
# ---------------------------------------------------------------------------


def _add(a, b):
    return a + b


def _add3(a, b, c):
    return a + b + c


def _add_with_defaults(a, b=10, c=20):
    return a + b + c


def _process(data: str, threshold: float, mode: str = "strict"):
    return f"{data}:{threshold}:{mode}"


def _typed_add(a: int, b: int) -> int:
    return a + b


def _typed_process(a: int, b: str, c: float) -> str:
    return f"{b}:{a}:{c}"


def _single_param(arg):
    return arg


def _concat(*args):
    return "".join(str(a) for a in args)


# ===========================================================================
# Happy path: basic mixed args
# ===========================================================================


class TestMixedArgsBasicHappyPaths:
    """Test that positional-first mixed arguments work correctly."""

    def test_one_positional_one_named(self):
        """Simplest mixed case: func(1, b=2)."""
        cy = Cy(tools={"add": _add})
        result = cy.run("return add(1, b=2)")
        assert result == "3"

    def test_two_positional_one_named(self):
        """func(1, 2, c=3)."""
        cy = Cy(tools={"add3": _add3})
        result = cy.run("return add3(1, 2, c=3)")
        assert result == "6"

    def test_one_positional_two_named(self):
        """func(1, b=2, c=3)."""
        cy = Cy(tools={"add3": _add3})
        result = cy.run("return add3(1, b=2, c=3)")
        assert result == "6"

    def test_all_positional_still_works(self):
        """Regression: pure positional args continue to work."""
        cy = Cy(tools={"add3": _add3})
        result = cy.run("return add3(1, 2, 3)")
        assert result == "6"

    def test_all_named_still_works(self):
        """Regression: pure named args continue to work."""
        cy = Cy(tools={"add3": _add3})
        result = cy.run("return add3(a=1, b=2, c=3)")
        assert result == "6"

    def test_no_args_still_works(self):
        """Regression: no-arg functions continue to work."""
        cy = Cy(tools={"zero": lambda: 0})
        result = cy.run("return zero()")
        assert result == "0"


class TestMixedArgsNamedOrderIndependent:
    """Named args after positional can be in any order."""

    def test_named_in_reverse_order(self):
        """func(1, c=3, b=2) — named args reversed."""
        cy = Cy(tools={"add3": _add3})
        result = cy.run("return add3(1, c=3, b=2)")
        assert result == "6"

    def test_named_order_does_not_affect_result(self):
        """Results must be identical regardless of named arg order."""
        cy = Cy(tools={"process": _process})
        r1 = cy.run('return process("data", threshold=0.5, mode="lax")')
        r2 = cy.run('return process("data", mode="lax", threshold=0.5)')
        assert r1 == r2


class TestMixedArgsWithDefaults:
    """Test mixed args with optional/default parameters."""

    def test_skip_optional_middle_param(self):
        """func(1, c=30) — b uses default."""
        cy = Cy(tools={"add_def": _add_with_defaults})
        result = cy.run("return add_def(1, c=30)")
        assert result == "41"  # 1 + 10 (default b) + 30

    def test_override_optional_with_named(self):
        """func(1, b=5, c=30) — override default b."""
        cy = Cy(tools={"add_def": _add_with_defaults})
        result = cy.run("return add_def(1, b=5, c=30)")
        assert result == "36"  # 1 + 5 + 30

    def test_positional_fills_optional(self):
        """func(1, 5) — positional fills optional b, c uses default."""
        cy = Cy(tools={"add_def": _add_with_defaults})
        result = cy.run("return add_def(1, 5)")
        assert result == "26"  # 1 + 5 + 20 (default c)

    def test_only_required_positional_rest_defaults(self):
        """func(1) — only required a, b and c use defaults."""
        cy = Cy(tools={"add_def": _add_with_defaults})
        result = cy.run("return add_def(1)")
        assert result == "31"  # 1 + 10 + 20


class TestMixedArgsWithExpressions:
    """Test mixed args where arguments are complex expressions."""

    def test_expression_as_positional(self):
        """func(1 + 2, b=3) — expression in positional."""
        cy = Cy(tools={"add": _add})
        result = cy.run("return add(1 + 2, b=3)")
        assert result == "6"

    def test_variable_as_positional(self):
        """func(x, b=y) — variables as args."""
        cy = Cy(tools={"add": _add})
        result = cy.run("x = 10\ny = 20\nreturn add(x, b=y)")
        assert result == "30"

    def test_nested_call_as_positional(self):
        """func(inner(1, 2), b=3) — nested function call as positional."""
        cy = Cy(tools={"add": _add, "add3": _add3})
        result = cy.run("return add3(add(1, 2), b=4, c=5)")
        assert result == "12"  # add(1,2)=3 + 4 + 5

    def test_string_expression_as_named(self):
        """func("hello", mode="world") — string values."""
        cy = Cy(tools={"process": _process})
        result = cy.run('return process("data", threshold=0.5, mode="relaxed")')
        assert result == '"data:0.5:relaxed"'

    def test_list_as_positional(self):
        """func([1,2,3], b=4)."""

        def my_func(items, extra):
            return len(items) + extra

        cy = Cy(tools={"my_func": my_func})
        result = cy.run("return my_func([1, 2, 3], extra=4)")
        assert result == "7"

    def test_dict_as_named(self):
        """func(1, opts={"key": "val"})."""

        def my_func(count, opts):
            return count + len(opts)

        cy = Cy(tools={"my_func": my_func})
        result = cy.run('return my_func(1, opts={"key": "val"})')
        assert result == "2"


class TestMixedArgsInInterpolation:
    """Test mixed args inside string interpolation."""

    def test_mixed_args_in_interpolation(self):
        """String interpolation with mixed-arg function call."""
        cy = Cy(tools={"add": _add})
        result = cy.run('return "sum=${add(1, b=2)}"')
        assert result == '"sum=3"'

    def test_mixed_args_in_interpolation_with_variable(self):
        """Interpolation referencing mixed-arg result."""
        cy = Cy(tools={"add": _add})
        result = cy.run('x = add(10, b=20)\nreturn "result=${x}"')
        assert result == '"result=30"'


class TestMixedArgsMultiline:
    """Test mixed args in multiline function calls."""

    def test_multiline_mixed_args(self):
        """Multiline function call with mixed arguments."""
        cy = Cy(tools={"add3": _add3})
        program = """
        result = add3(
            1,
            b=2,
            c=3
        )
        return result
        """
        result = cy.run(program)
        assert result == "6"

    def test_multiline_mixed_with_comments(self):
        """Multiline with comments between arguments."""
        cy = Cy(tools={"add3": _add3})
        program = """
        result = add3(
            1,        # first positional
            b=2,      # named b
            c=3       # named c
        )
        return result
        """
        result = cy.run(program)
        assert result == "6"


class TestMixedArgsInControlFlow:
    """Test mixed args within control flow constructs."""

    def test_mixed_args_in_if_condition(self):
        """Mixed args in if condition."""
        cy = Cy(tools={"add": _add})
        program = """
        if (add(1, b=2) == 3) {
            return "yes"
        }
        return "no"
        """
        result = cy.run(program)
        assert result == '"yes"'

    def test_mixed_args_in_assignment(self):
        """Mixed args in variable assignment."""
        cy = Cy(tools={"add": _add})
        result = cy.run("x = add(5, b=10)\nreturn x")
        assert result == "15"

    def test_mixed_args_in_loop(self):
        """Mixed args inside a for loop."""
        cy = Cy(tools={"add": _add})
        program = """
        total = 0
        for (i in [1, 2, 3]) {
            total = add(total, b=i)
        }
        return total
        """
        result = cy.run(program)
        assert result == "6"

    def test_mixed_args_in_list_comprehension(self):
        """Mixed args inside list comprehension."""
        cy = Cy(tools={"add": _add})
        program = """
        results = [add(x, b=10) for(x in [1, 2, 3])]
        return results
        """
        result = cy.run(program)
        assert result == "[11, 12, 13]"


# ===========================================================================
# Error paths
# ===========================================================================


class TestMixedArgsNamedFirstRejected:
    """Named args before positional should be a parse error."""

    def test_named_before_positional_is_parse_error(self):
        """func(a=1, 2) should fail at parse time."""
        cy = Cy(tools={"add": _add})
        with pytest.raises(Exception):
            cy.run("return add(a=1, 2)")

    def test_named_before_positional_two_args(self):
        """func(a=1, b=2, 3) should fail at parse time."""
        cy = Cy(tools={"add3": _add3})
        with pytest.raises(Exception):
            cy.run("return add3(a=1, b=2, 3)")


class TestMixedArgsDuplicateDetection:
    """Test duplicate parameter detection (positional + named same param)."""

    def test_duplicate_first_param(self):
        """func(1, a=2) — positional fills 'a', named also provides 'a'."""
        cy = Cy(tools={"add": _add})
        with pytest.raises(Exception, match="[Bb]oth|[Dd]uplicate|multiple values"):
            cy.run("return add(1, a=2)")

    def test_duplicate_second_param(self):
        """func(1, 2, b=3) — positional fills 'b', named also provides 'b'."""
        cy = Cy(tools={"add3": _add3})
        with pytest.raises(Exception, match="[Bb]oth|[Dd]uplicate|multiple values"):
            cy.run("return add3(1, 2, b=3)")

    def test_duplicate_all_params(self):
        """func(1, 2, a=1, b=2) — all params duplicated."""
        cy = Cy(tools={"add": _add})
        with pytest.raises(Exception, match="[Bb]oth|[Dd]uplicate|multiple values"):
            cy.run("return add(1, 2, a=1, b=2)")


class TestMixedArgsTooManyPositional:
    """Test error when too many positional arguments."""

    def test_too_many_positional_with_named(self):
        """func(1, 2, 3, c=4) — 3 positional for 3-param func, plus named."""
        cy = Cy(tools={"add3": _add3})
        # add3 has 3 params, 3 positional fills all, c=4 is duplicate
        with pytest.raises(Exception):
            cy.run("return add3(1, 2, 3, c=4)")

    def test_too_many_positional_no_named(self):
        """func(1, 2, 3, 4) — 4 positional for 3-param func."""
        cy = Cy(tools={"add3": _add3})
        with pytest.raises(Exception, match="[Tt]oo many|arguments"):
            cy.run("return add3(1, 2, 3, 4)")


class TestMixedArgsUnknownNamedParam:
    """Test error when named arg doesn't match any parameter."""

    def test_unknown_named_param(self):
        """func(1, z=2) — 'z' doesn't exist."""
        cy = Cy(tools={"add": _add})
        with pytest.raises(Exception):
            cy.run("return add(1, z=2)")

    def test_unknown_named_with_valid_mixed(self):
        """func(1, b=2, z=3) — 'z' doesn't exist."""
        cy = Cy(tools={"add3": _add3})
        with pytest.raises(Exception):
            cy.run("return add3(1, b=2, z=3)")


# ===========================================================================
# bind_arguments() — the canonical algorithm
# ===========================================================================


class TestBindArguments:
    """Test the canonical bind_arguments() function directly."""

    def test_all_positional(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [1, 2], {})
        assert bound == {"a": 1, "b": 2}
        assert errors == []

    def test_all_named(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [], {"a": 1, "b": 2})
        assert bound == {"a": 1, "b": 2}
        assert errors == []

    def test_mixed(self):
        bound, errors = bind_arguments(["a", "b", "c"], {"a"}, [1], {"b": 2, "c": 3})
        assert bound == {"a": 1, "b": 2, "c": 3}
        assert errors == []

    def test_no_args(self):
        bound, errors = bind_arguments([], set(), [], {})
        assert bound == {}
        assert errors == []

    def test_too_many_positional(self):
        bound, errors = bind_arguments(["a"], {"a"}, [1, 2], {})
        assert len(errors) == 1
        assert "Too many positional" in errors[0]

    def test_duplicate_param(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [1], {"a": 2})
        assert any("both positionally and by name" in e for e in errors)

    def test_unknown_named(self):
        bound, errors = bind_arguments(["a"], {"a"}, [], {"a": 1, "z": 2})
        assert any("Unknown parameter 'z'" in e for e in errors)

    def test_missing_required(self):
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [1], {})
        assert any("Missing required parameter 'b'" in e for e in errors)

    def test_optional_not_required(self):
        """Optional params (not in required set) shouldn't error when missing."""
        bound, errors = bind_arguments(["a", "b"], {"a"}, [1], {})
        assert errors == []
        assert bound == {"a": 1}

    def test_multiple_errors(self):
        """bind_arguments collects all errors, not just the first."""
        bound, errors = bind_arguments(["a", "b"], {"a", "b"}, [], {"z": 1, "w": 2})
        assert len(errors) >= 2  # unknown z, unknown w, missing a, missing b


# ===========================================================================
# ArgumentAdapter unit tests
# ===========================================================================


class TestArgumentAdapterValidation:
    """Test ArgumentAdapter validates arguments via bind_arguments()."""

    def setup_method(self):
        self.adapter = ArgumentAdapter()

    def test_valid_mixed_passes(self):
        """Valid mixed args should not raise."""
        self.adapter.validate_native_call(_add, [1], {"b": 2})

    def test_valid_all_positional(self):
        """All positional should not raise."""
        self.adapter.validate_native_call(_add3, [1, 2, 3], {})

    def test_valid_all_named(self):
        """All named should not raise."""
        self.adapter.validate_native_call(_add, [], {"a": 1, "b": 2})

    def test_valid_with_defaults(self):
        """Skipping optional params should not raise."""
        self.adapter.validate_native_call(_add_with_defaults, [1], {"c": 30})

    def test_duplicate_detection(self):
        """Duplicate param raises ValueError."""
        with pytest.raises(ValueError, match="both positionally and by name"):
            self.adapter.validate_native_call(_add, [1], {"a": 2})

    def test_duplicate_detection_second_param(self):
        """Duplicate on second param raises ValueError."""
        with pytest.raises(ValueError, match="both positionally and by name"):
            self.adapter.validate_native_call(_add, [1, 2], {"b": 3})

    def test_too_many_positional(self):
        """Too many positional raises ValueError."""
        with pytest.raises(ValueError, match="Too many positional"):
            self.adapter.validate_native_call(_add, [1, 2, 3], {})

    def test_unknown_named_param(self):
        """Unknown named param raises ValueError."""
        with pytest.raises(ValueError, match="Unknown parameter"):
            self.adapter.validate_native_call(_add, [1], {"z": 2})

    def test_varargs_skips_validation(self):
        """Functions with *args skip validation."""
        self.adapter.validate_native_call(_concat, [1, 2, 3, 4, 5], {})


class TestArgumentAdapterMixedMCP:
    """Test MCP functions with mixed arguments."""

    def setup_method(self):
        class MockMCPManager:
            def get_tool_parameter_names(self, tool_name):
                if tool_name == "mcp::demo::add":
                    return ["a", "b"]
                if tool_name == "mcp::demo::add3":
                    return ["a", "b", "c"]
                return None

        self.adapter = ArgumentAdapter(mcp_manager=MockMCPManager())

    def test_mcp_mixed_to_named(self):
        """MCP: [5] + {b: 3} → {a: 5, b: 3}."""
        result = self.adapter.normalize_mcp_call("mcp::demo::add", [5], {"b": 3})
        assert result == {"a": 5, "b": 3}

    def test_mcp_mixed_three_params(self):
        """MCP: [1] + {b: 2, c: 3} → {a: 1, b: 2, c: 3}."""
        result = self.adapter.normalize_mcp_call(
            "mcp::demo::add3", [1], {"b": 2, "c": 3}
        )
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_mcp_duplicate_detection(self):
        """MCP: [5] + {a: 10} — duplicate 'a' raises error."""
        with pytest.raises(ValueError, match="both positionally and by name"):
            self.adapter.normalize_mcp_call("mcp::demo::add", [5], {"a": 10})

    def test_mcp_named_only_passthrough(self):
        """MCP: [] + {a: 5, b: 3} → {a: 5, b: 3} (no positional, passthrough)."""
        result = self.adapter.normalize_mcp_call("mcp::demo::add", [], {"a": 5, "b": 3})
        assert result == {"a": 5, "b": 3}


# ===========================================================================
# Type checking with mixed args
# ===========================================================================


class TestMixedArgsTypeChecking:
    """Test that type checker catches errors in mixed arg calls."""

    def test_typed_mixed_args_correct(self):
        """Type-correct mixed call should work."""
        cy = Cy(check_types=True, tools={"typed_add": _typed_add})
        result = cy.run("return typed_add(1, b=2)")
        assert result == "3"

    def test_typed_mixed_positional_wrong_type(self):
        """Wrong type in positional arg should be caught."""
        cy = Cy(check_types=True, tools={"typed_add": _typed_add})
        with pytest.raises(TypeError) as exc_info:
            cy.run('return typed_add("hello", b=2)')
        assert (
            "expects" in str(exc_info.value).lower()
            or "type" in str(exc_info.value).lower()
        )

    def test_typed_mixed_named_wrong_type(self):
        """Wrong type in named arg should be caught."""
        cy = Cy(check_types=True, tools={"typed_add": _typed_add})
        with pytest.raises(TypeError) as exc_info:
            cy.run('return typed_add(1, b="hello")')
        assert (
            "expects" in str(exc_info.value).lower()
            or "type" in str(exc_info.value).lower()
        )

    def test_typed_mixed_duplicate_caught_by_checker(self):
        """Duplicate param should be caught by type checker."""
        cy = Cy(check_types=True, tools={"typed_add": _typed_add})
        with pytest.raises((TypeError, Exception)) as exc_info:
            cy.run("return typed_add(1, a=2)")
        error_msg = str(exc_info.value).lower()
        assert (
            "both" in error_msg or "duplicate" in error_msg or "multiple" in error_msg
        )

    def test_typed_mixed_too_many_positional(self):
        """Too many positional should be caught by type checker."""
        cy = Cy(check_types=True, tools={"typed_add": _typed_add})
        with pytest.raises((TypeError, Exception)):
            cy.run("return typed_add(1, 2, 3)")

    def test_typed_three_params_mixed(self):
        """Three params, one positional + two named, correct types."""
        cy = Cy(check_types=True, tools={"typed_process": _typed_process})
        result = cy.run('return typed_process(42, b="label", c=3.14)')
        assert result == '"label:42:3.14"'


# ===========================================================================
# Edge cases
# ===========================================================================


class TestMixedArgsEdgeCases:
    """Edge cases and boundary conditions."""

    def test_boolean_mixed_arg(self):
        """func(1, flag=True)."""

        def my_func(value, flag=False):
            return value if flag else -value

        cy = Cy(tools={"my_func": my_func})
        result = cy.run("return my_func(42, flag=True)")
        assert result == "42"

    def test_null_as_named_arg(self):
        """func(1, b=null)."""

        def my_func(a, b=None):
            return a if b is None else a + b

        cy = Cy(tools={"my_func": my_func})
        result = cy.run("return my_func(5, b=null)")
        assert result == "5"

    def test_negative_number_as_positional(self):
        """func(-1, b=2)."""
        cy = Cy(tools={"add": _add})
        result = cy.run("return add(-1, b=2)")
        assert result == "1"

    def test_float_as_named_arg(self):
        """func(1, threshold=0.5)."""
        cy = Cy(tools={"process": _process})
        result = cy.run('return process("test", threshold=0.75)')
        assert result == '"test:0.75:strict"'

    def test_mixed_args_result_used_in_another_call(self):
        """Chain: result of mixed-arg call used as arg to another call."""
        cy = Cy(tools={"add": _add, "add3": _add3})
        result = cy.run("x = add(1, b=2)\nreturn add3(x, b=10, c=20)")
        assert result == "33"  # 3 + 10 + 20

    def test_mixed_args_with_string_containing_equals(self):
        """Named arg value contains '=' sign."""

        def echo(msg, tag="default"):
            return f"[{tag}] {msg}"

        cy = Cy(tools={"echo": echo})
        result = cy.run('return echo("key=value", tag="info")')
        assert result == '"[info] key=value"'

    def test_mixed_args_empty_string_positional(self):
        """func("", b=2)."""

        def my_func(a, b):
            return f"{a}:{b}"

        cy = Cy(tools={"my_func": my_func})
        result = cy.run('return my_func("", b=2)')
        assert result == '":2"'

    def test_mixed_args_zero_as_positional(self):
        """func(0, b=1) — zero shouldn't be falsy-confused."""
        cy = Cy(tools={"add": _add})
        result = cy.run("return add(0, b=1)")
        assert result == "1"
