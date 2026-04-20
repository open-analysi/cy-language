"""Unit tests for 2-Part Namespaces for Native Functions.

Tests verify:
1. Grammar parsing of 2-part namespaces (json::parse, llm::run)
2. Transformer handling of variable-length namespace parts
3. Compiler validation of 2-part prefixes
4. Backward compatibility with old function names
5. Execution of new namespaced functions
6. Integration syntax (3-part) remains unchanged
7. Polymorphic functions stay flat (len, min, max, sum)
"""

import pytest

from cy_language.compiler import CompilerError, PlanCompiler, compile_cy_program
from cy_language.parser import Parser

# ============================================================================
# GRAMMAR PARSING TESTS
# ============================================================================


class TestGrammarParsing:
    """Test grammar parsing of 2-part namespaces."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_parse_json_parse_with_string_arg(self, parser):
        """Test parsing json::parse('test') - 2-part with string arg."""
        program = "result = json::parse('{\"a\":1}')"
        try:
            ast = parser.parse_only(program)
            assert ast is not None
        except Exception as e:
            pytest.fail(f"Failed to parse 2-part namespace: {e}")

    def test_parse_llm_run_with_named_arg(self, parser):
        """Test parsing llm::run(prompt=x) - 2-part with named arg."""
        program = 'x = "test"\nresult = llm::run(prompt=x)'
        try:
            ast = parser.parse_only(program)
            assert ast is not None
        except Exception as e:
            pytest.fail(f"Failed to parse 2-part namespace with named arg: {e}")

    def test_parse_3part_still_works(self, parser):
        """Test parsing app::splunk::search(query) - 3-part still works."""
        program = 'result = app::splunk::search(query="test")'
        try:
            ast = parser.parse_only(program)
            assert ast is not None
        except Exception as e:
            pytest.fail(f"Failed to parse 3-part namespace: {e}")

    def test_parse_str_lowercase_with_identifier(self, parser):
        """Test parsing str::lowercase(x) - 2-part with identifier arg."""
        program = 'x = "TEST"\nresult = str::lowercase(x)'
        try:
            ast = parser.parse_only(program)
            assert ast is not None
        except Exception as e:
            pytest.fail(f"Failed to parse 2-part with identifier: {e}")

    def test_parse_time_now_no_args(self, parser):
        """Test parsing time::now() - 2-part with no args."""
        program = "result = time::now()"
        try:
            ast = parser.parse_only(program)
            assert ast is not None
        except Exception as e:
            pytest.fail(f"Failed to parse 2-part with no args: {e}")


class TestGrammarParsingNegative:
    """Test grammar parsing rejects invalid patterns."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_parse_too_many_parts_fails(self, parser):
        """Test that 4+ parts fails parsing."""
        program = "result = a::b::c::d::e()"
        with pytest.raises(Exception):
            parser.parse_only(program)

    def test_parse_missing_prefix_fails(self, parser):
        """Test that ::parse() fails parsing."""
        program = "result = ::parse()"
        with pytest.raises(Exception):
            parser.parse_only(program)

    def test_parse_missing_function_name_fails(self, parser):
        """Test that json::() fails parsing."""
        program = "result = json::()"
        with pytest.raises(Exception):
            parser.parse_only(program)


# ============================================================================
# COMPILER VALIDATION TESTS
# ============================================================================


class TestCompilerValidation2Part:
    """Test compiler validates 2-part namespaces correctly."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_validate_json_namespace(self, compiler):
        """Test that json::parse is valid 2-part namespace."""
        compiler._validate_namespace("json::parse")

    def test_validate_str_namespace(self, compiler):
        """Test that str::lowercase is valid 2-part namespace."""
        compiler._validate_namespace("str::lowercase")

    def test_validate_list_namespace(self, compiler):
        """Test that list::sort is valid 2-part namespace."""
        compiler._validate_namespace("list::sort")

    def test_validate_dict_namespace(self, compiler):
        """Test that dict::keys is valid 2-part namespace."""
        compiler._validate_namespace("dict::keys")

    def test_validate_math_namespace(self, compiler):
        """Test that math::abs is valid 2-part namespace."""
        compiler._validate_namespace("math::abs")

    def test_validate_time_namespace(self, compiler):
        """Test that time::now is valid 2-part namespace."""
        compiler._validate_namespace("time::now")

    def test_validate_regex_namespace(self, compiler):
        """Test that regex::match is valid 2-part namespace."""
        compiler._validate_namespace("regex::match")

    def test_validate_url_namespace(self, compiler):
        """Test that url::encode is valid 2-part namespace."""
        compiler._validate_namespace("url::encode")

    def test_validate_ip_namespace(self, compiler):
        """Test that ip::is_v4 is valid 2-part namespace."""
        compiler._validate_namespace("ip::is_v4")

    def test_validate_type_namespace(self, compiler):
        """Test that type::str is valid 2-part namespace."""
        compiler._validate_namespace("type::str")


class TestCompilerValidation2PartNegative:
    """Test compiler rejects invalid 2-part namespaces."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_reject_invalid_2part_prefix(self, compiler):
        """Test that invalid::func raises error for unknown prefix."""
        with pytest.raises(CompilerError, match="Invalid.*namespace"):
            compiler._validate_namespace("invalid::func")

    def test_reject_app_as_2part(self, compiler):
        """Test that app::func raises error (app requires 3 parts)."""
        with pytest.raises(CompilerError):
            compiler._validate_namespace("app::func")

    def test_reject_mcp_as_2part(self, compiler):
        """Test that mcp::func raises error (mcp requires 3 parts)."""
        with pytest.raises(CompilerError):
            compiler._validate_namespace("mcp::func")

    def test_reject_arc_as_2part(self, compiler):
        """Test that arc::func raises error (arc requires 3 parts)."""
        with pytest.raises(CompilerError):
            compiler._validate_namespace("arc::func")


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility:
    """Test that old function names still work."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_from_json_still_works(self, parser):
        """Test that from_json('{}') compiles and runs."""
        program = """
result = from_json('{"a":1}')
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_to_json_still_works(self, parser):
        """Test that to_json({}) compiles and runs."""
        program = """
data = {"a": 1}
result = to_json(data)
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_uppercase_still_works(self, parser):
        """Test that uppercase('test') compiles."""
        program = """
result = uppercase("test")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_lowercase_still_works(self, parser):
        """Test that lowercase('TEST') compiles."""
        program = """
result = lowercase("TEST")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_regex_match_still_works(self, parser):
        """Test that regex_match('a', 'abc') compiles."""
        program = """
result = regex_match("a", "abc")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_url_encode_still_works(self, parser):
        """Test that url_encode('a b') compiles."""
        program = """
result = url_encode("a b")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_url_decode_still_works(self, parser):
        """Test that url_decode('a%20b') compiles."""
        program = """
result = url_decode("a%20b")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None


# ============================================================================
# NEW NAMESPACE EXECUTION TESTS
# ============================================================================


class TestNamespaceExecution:
    """Test that new namespaced functions work."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_json_parse_executes(self, parser):
        """Test that json::parse('{}') compiles."""
        program = """
result = json::parse('{"a":1}')
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_json_stringify_executes(self, parser):
        """Test that json::stringify({}) compiles."""
        program = """
data = {"a": 1}
result = json::stringify(data)
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_str_uppercase_executes(self, parser):
        """Test that str::uppercase('test') compiles."""
        program = """
result = str::uppercase("test")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_str_lowercase_executes(self, parser):
        """Test that str::lowercase('TEST') compiles."""
        program = """
result = str::lowercase("TEST")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_regex_match_executes(self, parser):
        """Test that regex::match('a', 'abc') compiles."""
        program = """
result = regex::match("a", "abc")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_url_encode_executes(self, parser):
        """Test that url::encode('a b') compiles."""
        program = """
result = url::encode("a b")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_url_decode_executes(self, parser):
        """Test that url::decode('a%20b') compiles."""
        program = """
result = url::decode("a%20b")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_time_now_executes(self, parser):
        """Test that time::now() compiles."""
        program = """
result = time::now()
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_ip_is_v4_executes(self, parser):
        """Test that ip::is_v4('192.168.1.1') compiles."""
        program = """
result = ip::is_v4("192.168.1.1")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_ip_is_v6_executes(self, parser):
        """Test that ip::is_v6('::1') compiles."""
        program = """
result = ip::is_v6("::1")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None


# ============================================================================
# INTEGRATION SYNTAX UNCHANGED TESTS
# ============================================================================


class TestIntegrationSyntaxUnchanged:
    """Test that 3-part integration syntax still works."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_native_tools_3part_compiles(self, parser):
        """Test that native::tools::len still compiles."""
        program = """
data = [1, 2, 3]
result = native::tools::len(data)
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None


# ============================================================================
# POLYMORPHIC FUNCTION TESTS (STAY FLAT)
# ============================================================================


class TestPolymorphicFunctionsStayFlat:
    """Test that polymorphic functions remain flat (not namespaced)."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return Parser()

    def test_len_on_string(self, parser):
        """Test len() on string stays flat."""
        program = """
result = len("abc")
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_len_on_list(self, parser):
        """Test len() on list stays flat."""
        program = """
result = len([1, 2, 3])
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_len_on_dict(self, parser):
        """Test len() on dict stays flat."""
        program = """
data = {"a": 1}
result = len(data)
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_min_stays_flat(self, parser):
        """Test min() stays flat."""
        program = """
result = min([1, 2, 3])
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_max_stays_flat(self, parser):
        """Test max() stays flat."""
        program = """
result = max([1, 2, 3])
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_sum_stays_flat(self, parser):
        """Test sum() stays flat."""
        program = """
result = sum([1, 2, 3])
return result
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None

    def test_log_stays_flat(self, parser):
        """Test log() stays flat."""
        program = """
log("test message")
return "done"
"""
        ast = parser.parse_only(program)
        plan = compile_cy_program(ast)
        assert plan is not None


# ============================================================================
# ERROR MESSAGE TESTS
# ============================================================================


class TestErrorMessages:
    """Test that error messages are helpful for namespace issues."""

    @pytest.fixture
    def compiler(self):
        """Create a compiler instance for testing."""
        return PlanCompiler()

    def test_unknown_2part_prefix_error(self, compiler):
        """Test error message for unknown 2-part prefix."""
        with pytest.raises(CompilerError) as exc_info:
            compiler._validate_namespace("foo::bar")
        assert "Invalid" in str(exc_info.value) or "foo" in str(exc_info.value)

    def test_app_needs_3parts_error(self, compiler):
        """Test error message when app:: used with only 2 parts."""
        with pytest.raises(CompilerError) as exc_info:
            compiler._validate_namespace("app::func")
        # Should mention needing 3 parts
        assert "3" in str(exc_info.value) or "parts" in str(exc_info.value).lower()


# ============================================================================
# END-TO-END EXECUTION TESTS
# ============================================================================


class TestEndToEndExecution:
    """Test actual execution of namespaced functions (not just compilation)."""

    @pytest.fixture
    def cy(self):
        """Create Cy interpreter instance."""
        from cy_language.interpreter import Cy

        return Cy()

    def test_json_parse_returns_dict(self, cy):
        """Test json::parse actually returns parsed data - verify via property access."""
        result = cy.run('return json::parse(\'{"name": "Alice", "age": 30}\').name')
        assert result == '"Alice"'

    def test_json_stringify_returns_string(self, cy):
        """Test json::stringify actually returns JSON string."""
        result = cy.run('return json::stringify({"a": 1})')
        assert result == '"{\\"a\\": 1}"'

    def test_str_uppercase_returns_upper(self, cy):
        """Test str::uppercase actually uppercases."""
        result = cy.run('return str::uppercase("hello")')
        assert result == '"HELLO"'

    def test_str_lowercase_returns_lower(self, cy):
        """Test str::lowercase actually lowercases."""
        result = cy.run('return str::lowercase("HELLO")')
        assert result == '"hello"'

    def test_str_split_returns_list(self, cy):
        """Test str::split actually splits and can be accessed by index."""
        result = cy.run('return str::split("a,b,c", ",")[0]')
        assert result == '"a"'

    def test_str_join_returns_string(self, cy):
        """Test str::join actually joins."""
        result = cy.run('return str::join(["a", "b", "c"], "-")')
        assert result == '"a-b-c"'

    def test_str_trim_removes_whitespace(self, cy):
        """Test str::trim removes whitespace."""
        result = cy.run('return str::trim("  hello  ")')
        assert result == '"hello"'

    def test_list_sort_returns_sorted(self, cy):
        """Test list::sort actually sorts - verify by accessing first element."""
        result = cy.run("return list::sort([3, 1, 2])[0]")
        assert result == "1"  # Returns string representation

    def test_list_reverse_returns_reversed(self, cy):
        """Test list::reverse actually reverses - verify by accessing first element."""
        result = cy.run("return list::reverse([1, 2, 3])[0]")
        assert result == "3"  # Returns string representation

    def test_list_take_returns_first_n(self, cy):
        """Test list::take returns first n elements - verify length."""
        result = cy.run("return len(list::take([1, 2, 3, 4, 5], 3))")
        assert result == "3"  # Returns string representation

    def test_dict_keys_returns_keys(self, cy):
        """Test dict::keys returns keys - verify length."""
        result = cy.run('return len(dict::keys({"a": 1, "b": 2}))')
        assert result == "2"  # Returns string representation

    def test_dict_values_returns_values(self, cy):
        """Test dict::values returns values - verify length."""
        result = cy.run('return len(dict::values({"a": 1, "b": 2}))')
        assert result == "2"  # Returns string representation

    def test_math_abs_returns_absolute(self, cy):
        """Test math::abs returns absolute value."""
        result = cy.run("return math::abs(-42)")
        assert result == "42"  # Returns string representation

    def test_math_round_returns_rounded(self, cy):
        """Test math::round returns rounded value."""
        result = cy.run("return math::round(3.14159, 2)")
        assert result == "3.14"  # Returns string representation

    def test_url_encode_encodes(self, cy):
        """Test url::encode actually encodes."""
        result = cy.run('return url::encode("hello world")')
        assert result == '"hello%20world"'

    def test_url_decode_decodes(self, cy):
        """Test url::decode actually decodes."""
        result = cy.run('return url::decode("hello%20world")')
        assert result == '"hello world"'

    def test_ip_is_v4_validates(self, cy):
        """Test ip::is_v4 validates IPv4."""
        result = cy.run('return ip::is_v4("192.168.1.1")')
        assert result == "true"  # Returns JSON boolean
        result = cy.run('return ip::is_v4("not-an-ip")')
        assert result == "false"  # Returns JSON boolean

    def test_ip_is_v6_validates(self, cy):
        """Test ip::is_v6 validates IPv6."""
        result = cy.run('return ip::is_v6("::1")')
        assert result == "true"  # Returns JSON boolean
        result = cy.run('return ip::is_v6("192.168.1.1")')
        assert result == "false"  # Returns JSON boolean

    def test_type_int_converts(self, cy):
        """Test type::int converts to integer."""
        result = cy.run('return type::int("42")')
        assert result == "42"  # Returns string representation

    def test_type_str_converts(self, cy):
        """Test type::str converts to string."""
        result = cy.run("return type::str(42)")
        assert result == '"42"'

    def test_regex_match_returns_bool(self, cy):
        """Test regex::match returns boolean."""
        result = cy.run('return regex::match("\\\\d+", "abc123")')
        assert result == "true"  # Returns JSON boolean
        result = cy.run('return regex::match("\\\\d+", "abc")')
        assert result == "false"  # Returns JSON boolean


# ============================================================================
# MIXED SYNTAX TESTS
# ============================================================================


class TestMixedOldNewSyntax:
    """Test using both old and new syntax in the same program."""

    @pytest.fixture
    def cy(self):
        """Create Cy interpreter instance."""
        from cy_language.interpreter import Cy

        return Cy()

    def test_old_and_new_json_in_same_program(self, cy):
        """Test using both from_json and json::parse in same program."""
        # Access individual properties to verify
        result = cy.run("""
old_result = from_json('{"a": 1}')
new_result = json::parse('{"b": 2}')
return old_result.a
""")
        assert result == "1"  # Returns string representation

    def test_old_and_new_string_funcs(self, cy):
        """Test using both uppercase and str::lowercase in same program."""
        result = cy.run("""
upper_val = uppercase("hello")
lower_val = str::lowercase("WORLD")
return "${upper_val} and ${lower_val}"
""")
        assert result == '"HELLO and world"'

    def test_old_and_new_url_funcs(self, cy):
        """Test using both url_encode and url::decode in same program."""
        result = cy.run("""
encoded = url_encode("hello world")
decoded = url::decode(encoded)
return decoded
""")
        assert result == '"hello world"'


# ============================================================================
# CHAINED NAMESPACE CALLS
# ============================================================================


class TestChainedNamespaceCalls:
    """Test chaining namespaced function calls."""

    @pytest.fixture
    def cy(self):
        """Create Cy interpreter instance."""
        from cy_language.interpreter import Cy

        return Cy()

    def test_chain_str_functions(self, cy):
        """Test chaining str:: functions."""
        result = cy.run('return str::uppercase(str::trim("  hello  "))')
        assert result == '"HELLO"'

    def test_chain_json_and_dict(self, cy):
        """Test chaining json:: and dict:: functions."""
        # Use dict_keys as variable name to avoid conflict with 'keys' function
        result = cy.run("""
data = json::parse('{"a": 1, "b": 2}')
dict_keys = dict::keys(data)
return len(list::sort(dict_keys))
""")
        assert result == "2"  # Returns string representation

    def test_chain_list_functions(self, cy):
        """Test chaining list:: functions."""
        result = cy.run("return list::take(list::sort([5, 3, 1, 4, 2]), 3)[0]")
        assert result == "1"  # First element of [1, 2, 3]

    def test_nested_namespace_calls(self, cy):
        """Test deeply nested namespace calls."""
        result = cy.run("""
return json::stringify({"result": str::uppercase(str::trim("  test  "))})
""")
        assert result == '"{\\"result\\": \\"TEST\\"}"'


# ============================================================================
# INTERPOLATION TESTS
# ============================================================================


class TestNamespacesInInterpolation:
    """Test namespaced functions in string interpolation."""

    @pytest.fixture
    def cy(self):
        """Create Cy interpreter instance."""
        from cy_language.interpreter import Cy

        return Cy()

    def test_str_uppercase_in_interpolation(self, cy):
        """Test str::uppercase in interpolation."""
        result = cy.run("""
name = "alice"
return "Hello, ${str::uppercase(name)}!"
""")
        assert result == '"Hello, ALICE!"'

    def test_math_abs_in_interpolation(self, cy):
        """Test math::abs in interpolation."""
        result = cy.run("""
value = -42
return "Absolute value: ${math::abs(value)}"
""")
        assert result == '"Absolute value: 42"'

    def test_multiple_namespace_calls_in_interpolation(self, cy):
        """Test multiple namespace calls in one interpolation."""
        result = cy.run("""
text = "  hello  "
return "Trimmed: ${str::trim(text)}, Upper: ${str::uppercase(text)}"
""")
        assert result == '"Trimmed: hello, Upper:   HELLO  "'


# ============================================================================
# TOOL RESOLVER UNIT TESTS
# ============================================================================


class TestToolResolver2PartResolution:
    """Test tool resolver handles 2-part namespace resolution."""

    def test_resolve_2part_to_3part_fqn(self):
        """Test that str::uppercase resolves to native::str::uppercase."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        fqn, original = resolver.resolve("str::uppercase")
        assert fqn == "native::str::uppercase"
        assert original == "str::uppercase"

    def test_resolve_json_namespace(self):
        """Test that json::parse resolves correctly."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        fqn, original = resolver.resolve("json::parse")
        assert fqn == "native::json::parse"
        assert original == "json::parse"

    def test_resolve_3part_still_works(self):
        """Test that native::tools::len still resolves correctly."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        fqn, original = resolver.resolve("native::tools::len")
        assert fqn == "native::tools::len"
        assert original == "native::tools::len"

    def test_resolve_short_name_still_works(self):
        """Test that short name 'len' still resolves."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        fqn, original = resolver.resolve("len")
        assert fqn == "native::tools::len"
        assert original == "len"

    def test_invalid_2part_raises_error(self):
        """Test that invalid::func raises ToolResolutionError."""
        from cy_language.errors import ToolResolutionError
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        with pytest.raises(ToolResolutionError):
            resolver.resolve("invalid::func")


class TestFlatNameNoAmbiguity:
    """Test that flat names for aliased functions resolve without ambiguity.

    Regression: register_tool_with_alias registered both the flat name (e.g. "str")
    and the namespaced name (e.g. "type::str") in default_registry. Both produced
    the same short name in the resolver's short_name_index, causing AmbiguousToolError
    whenever a user passed Cy(tools={"str": custom_fn}) or used any flat aliased name
    while a custom override was present.
    """

    def test_flat_str_resolves_to_single_fqn(self):
        """Short name 'str' must map to exactly one FQN."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        matches = resolver.short_name_index.get("str", [])
        assert len(matches) == 1, f"Expected 1 FQN for 'str', got {matches}"

    def test_flat_int_resolves_to_single_fqn(self):
        """Short name 'int' must map to exactly one FQN."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        matches = resolver.short_name_index.get("int", [])
        assert len(matches) == 1, f"Expected 1 FQN for 'int', got {matches}"

    def test_flat_uppercase_resolves_to_single_fqn(self):
        """Short name 'uppercase' must map to exactly one FQN."""
        from cy_language.tool_resolver import ToolResolver

        resolver = ToolResolver.from_native_tools()
        matches = resolver.short_name_index.get("uppercase", [])
        assert len(matches) == 1, f"Expected 1 FQN for 'uppercase', got {matches}"

    def test_str_cast_still_callable_by_flat_name(self):
        """str(value) must still work as a flat call after deduplication."""
        from cy_language import Cy

        cy = Cy()
        assert cy.run("return str(42)") == '"42"'

    def test_override_str_via_namespaced_key_works(self):
        """Overriding type::str via Cy(tools=...) replaces the casting function."""
        from cy_language import Cy

        cy = Cy(tools={"type::str": lambda v: f"CUSTOM:{v}"})
        result = cy.run("return str(42)")
        assert result == '"CUSTOM:42"'

    def test_override_uppercase_via_namespaced_key_works(self):
        """Overriding str::uppercase via Cy(tools=...) replaces the function."""
        from cy_language import Cy

        cy = Cy(tools={"str::uppercase": lambda s: f"UP:{s}"})
        result = cy.run('return uppercase("hello")')
        assert result == '"UP:hello"'
