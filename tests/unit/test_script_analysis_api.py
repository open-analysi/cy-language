"""Unit tests for analyze_script() API.

Tests verify that static analysis correctly extracts tools_used and
external_variables from Cy scripts without executing them.
"""

import pytest

from cy_language.script_analysis_api import analyze_script


class TestAnalyzeScriptBasic:
    """Basic tests for analyze_script()."""

    def test_simple_script_one_tool_one_external(self):
        """Simple script: one tool call, one external variable."""
        code = """
result = len(items)
return result
"""
        result = analyze_script(code)

        assert "native::tools::len" in result["tools_used"]
        assert "items" in result["external_variables"]
        # 'result' is assigned, not external
        assert "result" not in result["external_variables"]

    def test_multiple_tools_and_input_as_external(self):
        """Multiple tools + input as external variable."""
        code = """
x = len(input.items)
y = uppercase(input.name)
return y
"""
        result = analyze_script(code)

        assert "native::tools::len" in result["tools_used"]
        assert "native::str::uppercase" in result["tools_used"]
        assert "input" in result["external_variables"]

    def test_all_variables_assigned_internally(self):
        """All variables assigned internally → no externals."""
        code = """
x = 5
y = 10
z = x + y
return z
"""
        result = analyze_script(code)

        assert result["external_variables"] == []

    def test_empty_script_returns_empty(self):
        """Empty script returns empty lists."""
        result = analyze_script("")

        assert result == {"tools_used": [], "external_variables": []}

    def test_whitespace_only_returns_empty(self):
        """Whitespace-only script returns empty lists."""
        result = analyze_script("   \n  \n  ")

        assert result == {"tools_used": [], "external_variables": []}

    def test_syntax_error_raises(self):
        """Syntax error raises SyntaxError."""
        with pytest.raises(SyntaxError):
            analyze_script("x = = = broken")

    def test_variable_assigned_then_read_is_not_external(self):
        """Variable assigned then read is NOT external."""
        code = """
config = {"key": "value"}
result = config["key"]
return result
"""
        result = analyze_script(code)

        assert "config" not in result["external_variables"]

    def test_results_are_sorted(self):
        """Results are returned in sorted order for determinism."""
        code = """
z = len(c_var)
y = uppercase(b_var)
x = lowercase(a_var)
return x
"""
        result = analyze_script(code)

        assert result["external_variables"] == sorted(result["external_variables"])
        assert result["tools_used"] == sorted(result["tools_used"])


class TestAnalyzeScriptForLoop:
    """Tests for for-in loop handling."""

    def test_for_in_loop_internal_vars_filtered(self):
        """For-in loop compiler-generated vars (__for_idx_*, __for_iterable_*) are filtered."""
        code = """
items = [1, 2, 3]
total = 0
for (item in items) {
    total = total + item
}
return total
"""
        result = analyze_script(code)

        # No __for_idx_* or __for_iterable_* should appear
        for var in result["external_variables"]:
            assert not var.startswith("__for_idx_")
            assert not var.startswith("__for_iterable_")

    def test_for_in_inside_if_body(self):
        """For-in loop nested inside an if body should not crash."""
        code = """
if (true) {
    for (x in [1, 2]) {
        y = x
    }
}
return y
"""
        result = analyze_script(code)

        # y is assigned inside the loop, not external
        assert "y" not in result["external_variables"]

    def test_for_in_inside_elif_body(self):
        """For-in loop nested inside an elif body."""
        code = """
if (false) {
    y = 0
} elif (true) {
    for (x in [1, 2]) {
        y = x
    }
}
return y
"""
        result = analyze_script(code)
        assert "y" not in result["external_variables"]

    def test_for_in_inside_else_body(self):
        """For-in loop nested inside an else body."""
        code = """
if (false) {
    y = 0
} else {
    for (x in [1, 2]) {
        y = x
    }
}
return y
"""
        result = analyze_script(code)
        assert "y" not in result["external_variables"]

    def test_for_in_inside_while_body(self):
        """For-in loop nested inside a while body."""
        code = """
i = 0
while (i < 1) {
    for (x in items) {
        y = x
    }
    i = i + 1
}
return y
"""
        result = analyze_script(code)
        assert "items" in result["external_variables"]

    def test_for_in_inside_try_body(self):
        """For-in loop nested inside a try body."""
        code = """
try {
    for (x in items) {
        y = x
    }
} catch (e) {
    y = "error"
}
return y
"""
        result = analyze_script(code)
        assert "items" in result["external_variables"]

    def test_for_in_inside_catch_body(self):
        """For-in loop nested inside a catch body."""
        code = """
try {
    y = len(data)
} catch (e) {
    for (x in fallback_items) {
        y = x
    }
}
return y
"""
        result = analyze_script(code)
        assert "fallback_items" in result["external_variables"]

    def test_for_in_inside_finally_body(self):
        """For-in loop nested inside a finally body."""
        code = """
try {
    y = 1
} catch (e) {
    y = 2
} finally {
    for (x in cleanup_list) {
        z = x
    }
}
return y
"""
        result = analyze_script(code)
        assert "cleanup_list" in result["external_variables"]

    def test_nested_for_in_loops(self):
        """For-in inside for-in."""
        code = """
for (row in matrix) {
    for (cell in row) {
        z = cell
    }
}
return z
"""
        result = analyze_script(code)
        assert "matrix" in result["external_variables"]

    def test_deeply_nested_if_for_while(self):
        """if → for → while nesting."""
        code = """
if (flag) {
    for (x in items) {
        i = 0
        while (i < x) {
            y = len(data)
            i = i + 1
        }
    }
}
return y
"""
        result = analyze_script(code)
        assert "flag" in result["external_variables"]
        assert "items" in result["external_variables"]
        assert "data" in result["external_variables"]
        assert "native::tools::len" in result["tools_used"]

    def test_for_in_with_external_iterable(self):
        """For-in loop over external variable reports it as external."""
        code = """
total = 0
for (item in external_list) {
    total = total + item
}
return total
"""
        result = analyze_script(code)

        assert "external_list" in result["external_variables"]


class TestAnalyzeScriptConditional:
    """Tests for if/elif/else with tools and vars in all branches."""

    def test_if_elif_else_all_branches(self):
        """Tools and variables in all branches are found."""
        code = """
if (flag == true) {
    x = len(items)
} elif (flag == false) {
    x = uppercase(name)
} else {
    x = lowercase(other)
}
return x
"""
        result = analyze_script(code)

        # Tools from all branches
        assert "native::tools::len" in result["tools_used"]
        assert "native::str::uppercase" in result["tools_used"]
        assert "native::str::lowercase" in result["tools_used"]

        # External variables from all branches
        assert "flag" in result["external_variables"]
        assert "items" in result["external_variables"]
        assert "name" in result["external_variables"]
        assert "other" in result["external_variables"]


class TestAnalyzeScriptTryCatch:
    """Tests for try/catch handling."""

    def test_catch_exception_var_not_external(self):
        """CatchClause.exception_var counts as implicit assignment, not external."""
        code = """
try {
    result = len(items)
} catch (err) {
    result = "error: " + err
}
return result
"""
        result = analyze_script(code)

        # err is the catch variable — not external
        assert "err" not in result["external_variables"]
        # items is external (read but not assigned)
        assert "items" in result["external_variables"]

    def test_try_catch_finally(self):
        """Tools/vars in try, catch, and finally bodies are all collected."""
        code = """
try {
    x = len(data)
} catch (e) {
    y = uppercase(fallback)
} finally {
    z = lowercase(cleanup)
}
return x
"""
        result = analyze_script(code)

        assert "native::tools::len" in result["tools_used"]
        assert "native::str::uppercase" in result["tools_used"]
        assert "native::str::lowercase" in result["tools_used"]
        assert "data" in result["external_variables"]
        assert "fallback" in result["external_variables"]
        assert "cleanup" in result["external_variables"]
        assert "e" not in result["external_variables"]


class TestAnalyzeScriptNestedToolCalls:
    """Tests for nested tool calls."""

    def test_nested_tool_calls(self):
        """Nested tool calls: result = tool1(tool2(x))."""
        code = """
result = uppercase(lowercase(text))
return result
"""
        result = analyze_script(code)

        assert "native::str::uppercase" in result["tools_used"]
        assert "native::str::lowercase" in result["tools_used"]
        assert "text" in result["external_variables"]


class TestAnalyzeScriptInterpolation:
    """Tests for string interpolation."""

    def test_variable_in_interpolation_is_external(self):
        """Variable used only in interpolation is reported as external."""
        code = """
msg = "Hello ${name}, you have ${count} items"
return msg
"""
        result = analyze_script(code)

        assert "name" in result["external_variables"]
        assert "count" in result["external_variables"]


class TestAnalyzeScriptUnknownTools:
    """Tests for unknown/custom tool handling."""

    def test_unknown_tool_still_in_tools_used(self):
        """Unknown tool is handled gracefully and still appears in tools_used."""
        code = """
result = custom_tool(data)
return result
"""
        result = analyze_script(code)

        # The unknown tool should appear (possibly with its resolved FQN)
        assert len(result["tools_used"]) > 0
        assert "data" in result["external_variables"]

    def test_unknown_tool_with_tool_registry(self):
        """Custom tool from tool_registry is resolved properly."""
        code = """
result = ip_reputation(ip_address)
return result
"""
        registry = {
            "app::virustotal::ip_reputation": {
                "parameters": {"ip": {"type": "string"}},
                "return_type": {"type": "object"},
            }
        }
        result = analyze_script(code, tool_registry=registry)

        assert "app::virustotal::ip_reputation" in result["tools_used"]
        assert "ip_address" in result["external_variables"]

    def test_multiple_unknown_tools(self):
        """Multiple unknown tools are all collected."""
        code = """
a = custom_tool_a(x)
b = custom_tool_b(y)
return a + b
"""
        result = analyze_script(code)

        # Both tools should be registered and collected
        assert len(result["tools_used"]) >= 2
        assert "x" in result["external_variables"]
        assert "y" in result["external_variables"]


class TestAnalyzeScriptInputVariable:
    """Tests for input as an external variable."""

    def test_input_field_access(self):
        """input.field reports input as external."""
        code = """
x = len(input.items)
return x
"""
        result = analyze_script(code)

        assert "input" in result["external_variables"]

    def test_input_indexed_access(self):
        """input["key"] reports input as external."""
        code = """
x = input["key"]
return x
"""
        result = analyze_script(code)

        assert "input" in result["external_variables"]


class TestAnalyzeScriptWhileLoop:
    """Tests for while loop analysis."""

    def test_while_loop_tools_and_vars(self):
        """Tools and variables inside while loop body are collected."""
        code = """
i = 0
while (i < count) {
    x = len(items)
    i = i + 1
}
return x
"""
        result = analyze_script(code)

        assert "native::tools::len" in result["tools_used"]
        assert "count" in result["external_variables"]
        assert "items" in result["external_variables"]


class TestAnalyzeScriptNodeCoverage:
    """Corner-case tests exercising every _walk_node branch."""

    def test_indexed_assign_node(self):
        """IndexedAssignNode: data[key] = value walks both target and value."""
        code = """
data = {}
data["status"] = external_value
return data
"""
        result = analyze_script(code)

        assert "external_value" in result["external_variables"]
        assert "data" not in result["external_variables"]

    def test_field_assign_node(self):
        """FieldAssignNode: obj.field = value walks both target and value."""
        code = """
obj = {}
obj.name = external_name
return obj
"""
        result = analyze_script(code)

        assert "external_name" in result["external_variables"]
        assert "obj" not in result["external_variables"]

    def test_boolean_op_node(self):
        """BooleanOpNode: x and y / x or y reports both operands."""
        code = """
result = flag_a and flag_b
return result
"""
        result = analyze_script(code)

        assert "flag_a" in result["external_variables"]
        assert "flag_b" in result["external_variables"]

    def test_unary_op_node(self):
        """UnaryOpNode: not flag reports the operand."""
        code = """
result = not flag
return result
"""
        result = analyze_script(code)

        assert "flag" in result["external_variables"]

    def test_list_node_with_variable_elements(self):
        """ListNode: [a, b, c] reports variable elements as external."""
        code = """
items = [alpha, beta, 42]
return items
"""
        result = analyze_script(code)

        assert "alpha" in result["external_variables"]
        assert "beta" in result["external_variables"]

    def test_dict_node_with_variable_values(self):
        """DictNode: {"k": v} reports variable values as external."""
        code = """
d = {"key": ext_val}
return d
"""
        result = analyze_script(code)

        assert "ext_val" in result["external_variables"]

    def test_tool_call_named_arguments(self):
        """ToolCallNode named arguments are walked."""
        code = """
result = replace(source, old="x", new=replacement)
return result
"""
        result = analyze_script(code)

        assert "source" in result["external_variables"]
        assert "replacement" in result["external_variables"]

    def test_zero_arg_tool_call(self):
        """Zero-argument tool call collects the tool but no extra vars."""
        code = """
t = time::now()
return t
"""
        result = analyze_script(code)

        assert "native::time::now" in result["tools_used"]

    def test_duplicate_tool_deduplicated(self):
        """Same tool called twice appears only once in tools_used."""
        code = """
a = len(x)
b = len(y)
return a + b
"""
        result = analyze_script(code)

        len_count = result["tools_used"].count("native::tools::len")
        assert len_count == 1

    def test_chained_field_access(self):
        """Chained field access a.b.c only reports root variable a."""
        code = """
x = config.database.host
return x
"""
        result = analyze_script(code)

        assert "config" in result["external_variables"]
        # "database" and "host" are field names, not variables
        assert "database" not in result["external_variables"]
        assert "host" not in result["external_variables"]


class TestAnalyzeScriptDomainAliases:
    """Tests for domain aliases (str::len, list::sum, etc.)."""

    def test_str_len_alias(self):
        """str::len resolves and appears in tools_used."""
        code = """
x = str::len("hello")
return x
"""
        result = analyze_script(code)

        assert "native::str::len" in result["tools_used"]

    def test_list_sum_alias(self):
        """list::sum resolves and appears in tools_used."""
        code = """
x = list::sum([1, 2, 3])
return x
"""
        result = analyze_script(code)

        assert "native::list::sum" in result["tools_used"]

    def test_list_min_max_aliases(self):
        """list::min and list::max resolve correctly."""
        code = """
lo = list::min([3, 1, 2])
hi = list::max([3, 1, 2])
return lo + hi
"""
        result = analyze_script(code)

        assert "native::list::min" in result["tools_used"]
        assert "native::list::max" in result["tools_used"]


class TestAnalyzeScriptSmokeTest:
    """Smoke tests matching the plan's verification section."""

    def test_smoke_len_input(self):
        """Smoke test: len(input.items) with return."""
        code = "x = len(input.items)\nreturn x"
        result = analyze_script(code)

        assert "native::tools::len" in result["tools_used"]
        assert "input" in result["external_variables"]
