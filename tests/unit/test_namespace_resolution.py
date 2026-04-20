"""
Integration tests for compile-time namespace resolution.

These tests verify end-to-end compile-time function resolution with various
namespace patterns (FQN and short names).
"""

import pytest

from cy_language.compiler import compile_cy_program
from cy_language.errors import AmbiguousToolError, ToolResolutionError
from cy_language.parser import Parser


class TestFQNCompilation:
    """Test FQN compilation patterns."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_compile_native_fqn(self, parser):
        """Test compiling program with native::tools::len()."""
        program = """
result = native::tools::len([1, 2, 3])
output = result
return output
"""

        ast_tree = parser.parse_only(program)
        plan = compile_cy_program(ast_tree)

        # Verify plan was created
        assert plan is not None

    def test_compile_short_name_native(self, parser):
        """Test compiling with unique short name 'len()'."""
        program = """
result = len([1, 2, 3])
output = result
return output
"""

        ast_tree = parser.parse_only(program)
        plan = compile_cy_program(ast_tree)

        assert plan is not None


class TestAmbiguousResolution:
    """Test ambiguous short name detection."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_compile_ambiguous_short_name_error(self, parser):
        """Test that ambiguous short name causes CompilerError."""
        from cy_language.tool_resolver import ToolResolver

        # Create resolver with CONFLICTING tools (same short name)
        resolver = ToolResolver()
        resolver.register_tool("app::virustotal::lookup_ip", None)
        resolver.register_short_name("lookup_ip", "app::virustotal::lookup_ip")
        resolver.register_tool("arc::threatintel::lookup_ip", None)
        resolver.register_short_name("lookup_ip", "arc::threatintel::lookup_ip")

        program = """
result = lookup_ip("8.8.8.8")
output = result
"""

        ast_tree = parser.parse_only(program)

        # Should raise AmbiguousToolError because 'lookup_ip' matches 2 FQNs
        with pytest.raises(AmbiguousToolError) as exc_info:
            compile_cy_program(ast_tree, tool_resolver=resolver)

        # Verify error contains both matches
        assert "app::virustotal::lookup_ip" in str(exc_info.value)
        assert "arc::threatintel::lookup_ip" in str(exc_info.value)

    def test_ambiguous_error_at_correct_line(self, parser):
        """Test that error reports correct line number."""
        from cy_language.tool_resolver import ToolResolver

        # Create resolver with conflicting tools
        resolver = ToolResolver()
        resolver.register_tool("app::service1::process", None)
        resolver.register_short_name("process", "app::service1::process")
        resolver.register_tool("app::service2::process", None)
        resolver.register_short_name("process", "app::service2::process")

        program = """
# Line 2: comment
x = 5
result = process("test")
output = result
"""

        ast_tree = parser.parse_only(program)

        with pytest.raises(AmbiguousToolError) as exc_info:
            compile_cy_program(ast_tree, tool_resolver=resolver)

        # Should report line 4 where the ambiguous call is
        assert exc_info.value.line == 4
        assert "Line 4" in str(exc_info.value)


class TestToolNotFound:
    """Test tool resolution failure scenarios."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_compile_nonexistent_short_name_error(self, parser):
        """Test that unknown short name causes ToolResolutionError."""
        program = """
result = nonexistent_function("test")
output = result
"""

        ast_tree = parser.parse_only(program)

        with pytest.raises(ToolResolutionError) as exc_info:
            compile_cy_program(ast_tree)

        # Verify error message
        assert "nonexistent_function" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_not_found_error_has_suggestions(self, parser):
        """Test that error includes suggestions."""
        program = """
result = leng([1, 2, 3])
output = result
"""

        ast_tree = parser.parse_only(program)

        with pytest.raises(ToolResolutionError) as exc_info:
            compile_cy_program(ast_tree)

        # Should suggest 'len' (native::tools::len is registered by default)
        assert exc_info.value.suggestions is not None
        assert len(exc_info.value.suggestions) > 0
        # The suggestion should contain 'len' somewhere
        suggestions_str = " ".join(exc_info.value.suggestions)
        assert "len" in suggestions_str


class TestMixedUsage:
    """Test programs mixing FQN and short names."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_compile_mixed_fqn_and_short_names(self, parser):
        """Test program using both FQN and short names."""
        program = """
# Short name
count = len([1, 2, 3])

# FQN
full_name = native::tools::len([4, 5, 6, 7])

output = count
return output
"""

        ast_tree = parser.parse_only(program)
        plan = compile_cy_program(ast_tree)

        assert plan is not None
