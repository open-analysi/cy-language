"""Security tests for Cy language sandbox isolation.

Tests for:
1. Variable mutation escape (shallow copy)
2. Object attribute leaking via getattr()
3. Resource exhaustion (DoS)
4. XML output injection
5. Tool error message information leakage
"""

import pytest

from cy_language import Cy

# ---------------------------------------------------------------------------
# Fix 1: Deep copy variables — mutation must not escape the sandbox
# ---------------------------------------------------------------------------


class TestVariableMutationEscape:
    """Cy scripts must not be able to mutate the host's variable data."""

    def test_list_mutation_does_not_escape(self):
        """Mutating a list inside Cy must not affect the original."""
        original = [1, 2, 3]
        cy = Cy(variables={"data": original})
        cy.run("data[0] = 999\nreturn data")
        assert original == [1, 2, 3], "Host list was mutated by Cy script"

    def test_nested_dict_mutation_does_not_escape(self):
        """Mutating a nested dict inside Cy must not affect the original."""
        original = {"config": {"debug": False, "level": "info"}}
        cy = Cy(variables={"data": original})
        cy.run('data["config"]["debug"] = True\nreturn data')
        assert original["config"]["debug"] is False, (
            "Host nested dict was mutated by Cy script"
        )

    def test_list_inside_dict_mutation_does_not_escape(self):
        """Mutating a list inside a dict must not affect the original."""
        original = {"users": [{"name": "admin", "role": "admin"}]}
        cy = Cy(variables={"data": original})
        cy.run('data["users"][0]["role"] = "hacker"\nreturn data')
        assert original["users"][0]["role"] == "admin", (
            "Host list-in-dict was mutated by Cy script"
        )

    def test_multiple_runs_are_isolated(self):
        """Each run() call should start with the original variables."""
        original = {"counter": [0]}
        cy = Cy(variables={"data": original})

        cy.run("data['counter'][0] = 1\nreturn data")
        result2 = cy.run_native("return data['counter'][0]")

        assert original["counter"][0] == 0, "Host data mutated"
        assert result2 == 0, "Second run saw mutations from first run"


# ---------------------------------------------------------------------------
# Fix 2: Restrict getattr() — field access must not leak object internals
# ---------------------------------------------------------------------------


class TestObjectAttributeLeaking:
    """Field access on non-dict objects must not expose arbitrary attributes."""

    def test_class_attribute_not_accessible(self):
        """Class-level attributes must not be readable from Cy."""

        class Widget:
            class_secret = "SECRET_VALUE"

            def __init__(self):
                self.name = "widget"

        cy = Cy(tools={"make": lambda: Widget()})
        result = cy.run_native("w = make()\nreturn w.class_secret")
        assert result is None, f"Class attribute leaked: {result}"

    def test_instance_attribute_not_accessible(self):
        """Instance attributes on non-dict objects must not be readable."""

        class Service:
            def __init__(self):
                self.api_key = "sk-secret-123"

        cy = Cy(tools={"get_svc": lambda: Service()})
        result = cy.run_native("s = get_svc()\nreturn s.api_key")
        assert result is None, f"Instance attribute leaked: {result}"

    def test_str_repr_does_not_leak_type_info(self):
        """str() on an opaque object must not reveal Python class info."""

        class Internal:
            pass

        cy = Cy(tools={"make": lambda: Internal()})
        result = cy.run_native("o = make()\nreturn str(o)")
        assert "__main__" not in str(result), f"Type info leaked via str(): {result}"

    def test_dict_field_access_still_works(self):
        """Dict field access must continue to work normally."""
        cy = Cy(variables={"data": {"name": "Alice", "age": 30}})
        result = cy.run_native("return data.name")
        assert result == "Alice"

    def test_dict_returned_from_tool_accessible(self):
        """Dicts returned from tools must remain accessible via field access."""

        def get_info():
            return {"status": "ok", "count": 42}

        cy = Cy(tools={"get_info": get_info})
        result = cy.run_native("info = get_info()\nreturn info.status")
        assert result == "ok"

    def test_nested_dict_from_tool_accessible(self):
        """Nested dicts returned from tools must remain accessible."""

        def get_data():
            return {"outer": {"inner": "value"}}

        cy = Cy(tools={"get_data": get_data})
        result = cy.run_native("d = get_data()\nouter = d.outer\nreturn outer.inner")
        assert result == "value"

    def test_list_method_refs_not_accessible(self):
        """Built-in type method references must not be accessible."""
        cy = Cy()
        result = cy.run_native("lst = [1,2,3]\nval = lst.append\nreturn val")
        assert result is None, f"List method ref leaked: {result}"

    def test_string_method_refs_not_accessible(self):
        """String method references must not be accessible."""
        cy = Cy()
        result = cy.run_native('s = "hello"\nval = s.upper\nreturn val')
        assert result is None, f"String method ref leaked: {result}"


# ---------------------------------------------------------------------------
# Fix 3: Execution limits — prevent DoS via resource exhaustion
# ---------------------------------------------------------------------------


class TestExecutionLimits:
    """Cy must enforce resource limits to prevent DoS from untrusted scripts."""

    def test_string_doubling_hits_iteration_limit(self):
        """Repeated string doubling must be stopped by the iteration cap.

        With max_iterations=20, the loop stops after ~20 doublings (1MB),
        well before the 2^30 = 1GB that would cause memory issues.
        """
        cy = Cy(max_iterations=20)
        with pytest.raises(Exception, match="[Ii]teration|[Ll]imit|[Ll]oop"):
            cy.run(
                """
s = "A"
i = 0
while (i < 100000) {
    s = s + s
    i += 1
}
return s
"""
            )

    def test_nested_for_loops_hit_iteration_limit(self):
        """Deeply nested for loops must be capped by total iteration counter."""
        cy = Cy(max_iterations=500)
        # 10 * 10 * 10 = 1000 iterations — exceeds 500 cap
        with pytest.raises(Exception, match="[Ii]teration|[Ll]imit|[Ll]oop"):
            cy.run(
                """
items = [0,1,2,3,4,5,6,7,8,9]
count = 0
for (a in items) {
    for (b in items) {
        for (c in items) {
            count += 1
        }
    }
}
return count
"""
            )

    def test_normal_loops_still_work(self):
        """Normal loops within limits must still execute fine."""
        cy = Cy(max_iterations=1000)
        result = cy.run_native(
            """
total = 0
for (i in [1,2,3,4,5]) {
    for (j in [10,20,30]) {
        total += i * j
    }
}
return total
"""
        )
        assert result == 900  # sum of i*j for i in 1..5, j in 10,20,30

    def test_default_max_iterations_exists(self):
        """PlanExecutor should have a default max_iterations even if not specified."""
        from cy_language.executor import PlanExecutor

        # The default is set on PlanExecutor, not Cy
        assert PlanExecutor.DEFAULT_MAX_ITERATIONS > 0

        # When Cy doesn't specify max_iterations, the executor uses its default
        cy = Cy()
        assert hasattr(cy, "max_iterations")

    def test_default_limit_catches_runaway_loop(self):
        """The default limit must catch runaway loops without explicit config."""
        cy = Cy()  # no max_iterations — uses PlanExecutor default
        with pytest.raises(Exception, match="[Ii]teration|[Ll]imit|[Ll]oop"):
            cy.run(
                """
i = 0
while (True) {
    i += 1
}
return i
"""
            )


# ---------------------------------------------------------------------------
# Fix 4: XML output injection — values must be escaped
# ---------------------------------------------------------------------------


class TestXmlOutputInjection:
    """XML formatter must escape special characters to prevent injection."""

    def test_xml_escapes_angle_brackets_in_values(self):
        """< and > in values must be escaped in XML output."""
        cy = Cy()
        result = cy.run(
            'data = [{"name": "<script>alert(1)</script>"}]\nreturn "${data|xml}"'
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result or "\\u003c" in result

    def test_xml_escapes_ampersand_in_values(self):
        """& in values must be escaped in XML output."""
        cy = Cy()
        result = cy.run('data = [{"company": "A&B Corp"}]\nreturn "${data|xml}"')
        assert "A&B" not in result or "&amp;" in result

    def test_xml_escapes_in_dict_values(self):
        """Dict XML formatter must also escape values."""
        cy = Cy()
        result = cy.run(
            'data = {"key": "</key><injected>pwned</injected>"}\nreturn "${data|xml}"'
        )
        assert "</key><injected>" not in result

    def test_xml_nested_dict_escapes(self):
        """Nested structures must have values escaped recursively."""
        cy = Cy()
        result = cy.run(
            'data = {"outer": {"inner": "<img onerror=alert(1)>"}}\n'
            'return "${data|xml}"'
        )
        assert "<img " not in result

    def test_xml_normal_values_unaffected(self):
        """Normal values without special chars must render correctly."""
        cy = Cy()
        result = cy.run('data = [{"name": "Alice", "score": 95}]\nreturn "${data|xml}"')
        assert "Alice" in result
        assert "95" in result


# ---------------------------------------------------------------------------
# Fix 5: Tool error sanitization — prevent info leakage via exceptions
# ---------------------------------------------------------------------------


class TestToolErrorSanitization:
    """Tool error messages must not leak sensitive host information."""

    def test_file_paths_are_redacted(self):
        """Absolute file paths in tool errors must be redacted."""

        def leaky():
            raise ValueError("Cannot read /etc/shadow")

        cy = Cy(tools={"check": leaky})
        with pytest.raises(Exception) as exc_info:
            cy.run("x = check()\nreturn x")

        error_msg = str(exc_info.value)
        assert "/etc/shadow" not in error_msg, f"File path leaked in error: {error_msg}"

    def test_home_paths_are_redacted(self):
        """Home directory paths in tool errors must be redacted."""

        def leaky():
            raise ValueError("File not found: /Users/admin/.ssh/id_rsa")

        cy = Cy(tools={"check": leaky})
        with pytest.raises(Exception) as exc_info:
            cy.run("x = check()\nreturn x")

        error_msg = str(exc_info.value)
        assert "/Users/admin" not in error_msg, (
            f"Home path leaked in error: {error_msg}"
        )
        assert ".ssh/id_rsa" not in error_msg, (
            f"SSH key path leaked in error: {error_msg}"
        )

    def test_windows_paths_are_redacted(self):
        """Windows-style paths must also be redacted."""

        def leaky():
            raise ValueError(r"Cannot open C:\Users\admin\secrets.txt")

        cy = Cy(tools={"check": leaky})
        with pytest.raises(Exception) as exc_info:
            cy.run("x = check()\nreturn x")

        error_msg = str(exc_info.value)
        assert r"C:\Users" not in error_msg, (
            f"Windows path leaked in error: {error_msg}"
        )

    def test_generic_error_message_preserved(self):
        """Non-sensitive error messages must still be informative."""

        def failing():
            raise ValueError("Invalid input: expected integer")

        cy = Cy(tools={"validate": failing})
        with pytest.raises(Exception) as exc_info:
            cy.run("x = validate()\nreturn x")

        error_msg = str(exc_info.value)
        # The error type/context should still be present
        assert "validate" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_env_vars_not_leaked(self):
        """Environment variable values must not appear in error messages."""
        import os

        secret = os.environ.get("HOME", "/Users/testuser")

        def leaky():
            raise ValueError(f"Config error at {secret}/config.yaml")

        cy = Cy(tools={"load_config": leaky})
        with pytest.raises(Exception) as exc_info:
            cy.run("x = load_config()\nreturn x")

        error_msg = str(exc_info.value)
        assert secret not in error_msg, f"HOME env var leaked in error: {error_msg}"
