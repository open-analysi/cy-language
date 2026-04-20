"""Tests for stub_tools feature — accepting unknown tools at compile and runtime."""

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError
from cy_language.tool_resolver import ToolResolver

# ── ToolResolver stub_unknown ─────────────────────────────────────────────


class TestToolResolverStubUnknown:
    """Tests for ToolResolver.stub_unknown flag."""

    def test_stub_unknown_false_raises_on_unknown(self):
        """Default behavior: unknown tools raise ToolResolutionError."""
        resolver = ToolResolver()
        with pytest.raises(Exception, match="unknown_func"):
            resolver.resolve("unknown_func")

    def test_stub_unknown_true_accepts_flat_name(self):
        """stub_unknown=True auto-registers unknown flat names."""
        resolver = ToolResolver(stub_unknown=True)
        fqn, original = resolver.resolve("unknown_func")
        assert fqn == "native::tools::unknown_func"
        assert original == "unknown_func"
        assert fqn in resolver.stubbed_tools

    def test_stub_unknown_true_accepts_namespaced_name(self):
        """stub_unknown=True auto-registers unknown 2-part namespaced names."""
        resolver = ToolResolver(stub_unknown=True)
        fqn, original = resolver.resolve("custom::action")
        assert fqn == "custom::action"
        assert original == "custom::action"
        assert fqn in resolver.stubbed_tools

    def test_stub_unknown_true_accepts_3part_fqn(self):
        """stub_unknown=True auto-registers unknown 3-part FQNs."""
        resolver = ToolResolver(stub_unknown=True)
        fqn, original = resolver.resolve("app::splunk::search")
        assert fqn == "app::splunk::search"
        assert original == "app::splunk::search"
        assert fqn in resolver.stubbed_tools

    def test_stub_unknown_doesnt_affect_known_tools(self):
        """Known tools resolve normally even with stub_unknown=True."""
        resolver = ToolResolver(stub_unknown=True)
        resolver.register_tool("native::tools::len", len)
        resolver.register_short_name("len", "native::tools::len")

        fqn, original = resolver.resolve("len")
        assert fqn == "native::tools::len"
        # Known tools should NOT appear in stubbed_tools
        assert fqn not in resolver.stubbed_tools

    def test_stub_unknown_tracks_all_stubs(self):
        """All stubbed tools are tracked in stubbed_tools set."""
        resolver = ToolResolver(stub_unknown=True)
        resolver.resolve("foo")
        resolver.resolve("bar")
        resolver.resolve("app::x::y")

        assert len(resolver.stubbed_tools) == 3


# ── Cy interpreter with stub_tools ────────────────────────────────────────


class TestCyStubTools:
    """Tests for Cy(stub_tools=True) — end-to-end stub behavior."""

    def test_unknown_tool_fails_without_stub(self):
        """Without stub_tools, unknown tools fail at compile time."""
        cy = Cy()
        with pytest.raises(CompilerError):
            cy.run('return unknown_func("hello")')

    def test_unknown_tool_returns_null_with_stub(self):
        """With stub_tools, unknown tools return null at runtime."""
        cy = Cy(stub_tools=True)
        result = cy.run_native('return unknown_func("hello")')
        assert result is None

    def test_stub_with_null_coalescing(self):
        """Stubbed tool + ?? gives a default value."""
        cy = Cy(stub_tools=True)
        result = cy.run_native('return unknown_func("hello") ?? "default"')
        assert result == "default"

    def test_native_tools_work_with_stub(self):
        """Native tools still work normally when stub_tools is enabled."""
        cy = Cy(stub_tools=True)
        result = cy.run_native("return len([1, 2, 3])")
        assert result == 3

    def test_custom_and_stub_tools_together(self):
        """Custom tools execute, unknown tools are stubbed."""

        def greet(name):
            return f"Hello, {name}!"

        cy = Cy(tools={"greet": greet}, stub_tools=True)
        result = cy.run_native("""
            greeting = greet("Alice")
            extra = unknown_func("test")
            return {"greeting": greeting, "extra": extra ?? "stubbed"}
        """)
        assert result == {"greeting": "Hello, Alice!", "extra": "stubbed"}

    def test_stub_namespaced_tool(self):
        """Namespaced unknown tools are also stubbed."""
        cy = Cy(stub_tools=True)
        result = cy.run_native("""
            data = app::threat::lookup(ip="1.2.3.4")
            return data ?? "no data"
        """)
        assert result == "no data"
