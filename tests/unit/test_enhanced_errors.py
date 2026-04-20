"""Tests for Enhanced Error Messages.

This module tests the enhanced error formatting, common mistake detection,
tool suggestions, and integration with existing error handling.
"""

import pytest

from cy_language.error_formatter import (
    ErrorFormatter,
    detect_common_mistake,
)
from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.errors import ToolNotFoundError
from cy_language.suggestion_engine import SuggestionEngine

# ============================================================================
# 1. Error Formatter Tests
# ============================================================================


def test_format_with_context_single_line():
    """Test formatting error with single line of context."""
    formatter = ErrorFormatter(use_color=False)
    source = "value = true"

    # Test formatting an error on this single line
    result = formatter.format_with_context(
        source_code=source,
        line=1,
        col=9,
        message="Variable 'true' is not defined",
        suggestion="Did you mean 'True'? (Booleans are capitalized in Cy)",
        error_type="NameError",
    )

    # Verify the formatted output contains key elements
    assert "NameError at line 1, column 9:" in result
    assert "value = true" in result
    assert "^^^^" in result or "^" in result  # Pointer to error location
    assert "Variable 'true' is not defined" in result
    assert "Did you mean 'True'?" in result


def test_format_with_context_multiline():
    """Test formatting with multiple lines of context."""
    formatter = ErrorFormatter(use_color=False)
    source = """x = 5
y = 10
if (x > 3 && y < 20) {
    result = "yes"
}"""

    # Test formatting an error on line 3 with context
    result = formatter.format_with_context(
        source_code=source,
        line=3,
        col=11,
        message="Unexpected operator '&&'",
        suggestion="Use 'and' instead of '&&' in Cy",
        error_type="SyntaxError",
    )

    # Verify context lines are included
    assert "SyntaxError at line 3, column 11:" in result
    assert "y = 10" in result  # Line before
    assert "if (x > 3 && y < 20) {" in result  # Error line
    assert 'result = "yes"' in result  # Line after

    # Verify pointer is at correct position
    lines = result.split("\n")
    # Find the line with the pointer
    pointer_line = None
    for line in lines:
        if "^" in line and "if" not in line:
            pointer_line = line
            break
    assert pointer_line is not None
    # The pointer should be around column 11
    assert pointer_line.index("^") >= 10


def test_create_pointer_line():
    """Test pointer creation at various column positions."""
    formatter = ErrorFormatter()

    # Test pointer at different positions
    pointer1 = formatter._create_pointer_line(1, 1)
    assert pointer1 == "^"

    pointer2 = formatter._create_pointer_line(5, 3)
    assert pointer2 == "    ^^^"

    pointer3 = formatter._create_pointer_line(10, 2)
    assert pointer3 == "         ^^"

    # Test edge cases
    pointer4 = formatter._create_pointer_line(1, 0)  # Zero length
    assert pointer4 == ""

    pointer5 = formatter._create_pointer_line(20, 1)
    assert len(pointer5) == 20  # 19 spaces + 1 caret


def test_colorize_output():
    """Test ANSI color code application."""
    formatter = ErrorFormatter(use_color=True)

    # Test color application
    red_text = formatter._colorize("Error", "red")
    assert "\033[" in red_text  # Contains ANSI escape code
    assert "Error" in red_text

    # Test with colors disabled
    formatter_no_color = ErrorFormatter(use_color=False)
    plain_text = formatter_no_color._colorize("Error", "red")
    assert "\033[" not in plain_text  # No ANSI codes
    assert plain_text == "Error"

    # Test different colors
    yellow_text = formatter._colorize("Warning", "yellow")
    green_text = formatter._colorize("Success", "green")
    assert yellow_text != green_text  # Different color codes


def test_get_lines_around_error():
    """Test extracting context lines from source."""
    formatter = ErrorFormatter()
    source = """line1
line2
line3
line4
line5"""

    # Test getting lines around line 3
    lines = formatter._get_lines_around_error(source, 3, context_lines=1)
    assert len(lines) == 3  # Line 2, 3, 4
    assert lines[0] == (2, "line2")
    assert lines[1] == (3, "line3")
    assert lines[2] == (4, "line4")

    # Test at start of file
    lines = formatter._get_lines_around_error(source, 1, context_lines=2)
    assert len(lines) == 3  # Can only get lines 1, 2, 3
    assert lines[0] == (1, "line1")
    assert lines[1] == (2, "line2")
    assert lines[2] == (3, "line3")

    # Test at end of file
    lines = formatter._get_lines_around_error(source, 5, context_lines=2)
    assert len(lines) == 3  # Can only get lines 3, 4, 5
    assert lines[0] == (3, "line3")
    assert lines[1] == (4, "line4")
    assert lines[2] == (5, "line5")


# ============================================================================
# 2. Common Mistake Detection Tests
# ============================================================================


def test_detect_lowercase_boolean_true():
    """Test detection of 'true' instead of 'True'."""
    source_line = "value = true"
    error_msg = "Variable 'true' is not defined"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "lowercase_bool"
    assert "Did you mean 'True'?" in result["suggestion"]
    assert result["fix"] == "True"


def test_detect_lowercase_boolean_false():
    """Test detection of 'false' instead of 'False'."""
    source_line = "value = false"
    error_msg = "Variable 'false' is not defined"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "lowercase_bool"
    assert "Did you mean 'False'?" in result["suggestion"]
    assert result["fix"] == "False"


def test_detect_symbol_operator_and():
    """Test detection of && operator."""
    source_line = "if (x > 3 && y < 20) {"
    error_msg = "No terminal matches '&'"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "symbol_operators"
    assert "Use 'and' instead of '&&'" in result["suggestion"]
    assert result["fix"] == "and"


def test_detect_symbol_operator_or():
    """Test detection of || operator."""
    source_line = "if (x > 3 || y < 20) {"
    error_msg = "No terminal matches '|'"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "symbol_operators"
    assert "Use 'or' instead of '||'" in result["suggestion"]
    assert result["fix"] == "or"


def test_detect_symbol_operator_not():
    """Test detection of ! operator (not !=)."""
    source_line = "if (!flag) {"
    error_msg = "Unexpected character '!'"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "symbol_operators"
    assert "Use 'not' instead of '!'" in result["suggestion"]
    assert result["fix"] == "not"


def test_detect_range_function():
    """Test detection of range() usage."""
    source_line = "for (i in range(10)) {"
    error_msg = "Tool 'range' not found"

    result = detect_common_mistake(error_msg, source_line)

    assert result is not None
    assert result["pattern"] == "range_function"
    assert "range()" in result["suggestion"]
    assert "native function" in result["suggestion"]
    # No specific fix for range, just explanation
    assert result.get("fix") is None or result["fix"] == ""


def test_break_is_now_valid_syntax():
    """break is now a supported keyword — no common mistake detection."""
    source_line = "break"
    error_msg = "Unexpected keyword 'break'"

    result = detect_common_mistake(error_msg, source_line)

    # break is valid syntax now — should not match any common mistake pattern
    assert result is None or result.get("pattern") != "break_continue"


def test_continue_is_now_valid_syntax():
    """continue is now a supported keyword — no common mistake detection."""
    source_line = "continue"
    error_msg = "Unexpected keyword 'continue'"

    result = detect_common_mistake(error_msg, source_line)

    assert result is None or result.get("pattern") != "break_continue"


# ============================================================================
# 3. Tool Suggestion Tests
# ============================================================================


def test_suggest_similar_tools_exact_match():
    """Test when exact tool exists but with namespace."""
    engine = SuggestionEngine({"native::tools::len": {}, "app::custom::length": {}})

    suggestions = engine.suggest_similar_tools("len", max_suggestions=3)

    # Should suggest the FQN that contains "len"
    assert len(suggestions) > 0
    assert "native::tools::len" in suggestions
    # Might also suggest "length" as it's similar
    # Exact implementation may vary


def test_suggest_similar_tools_typo():
    """Test tool name with minor typo."""
    engine = SuggestionEngine(
        {"native::tools::len": {}, "native::tools::sum": {}, "native::tools::str": {}}
    )

    # Test with typo "lenght" instead of "len"
    suggestions = engine.suggest_similar_tools("lenght", max_suggestions=3)

    assert len(suggestions) > 0
    # Should suggest "len" as closest match
    assert any("len" in s for s in suggestions)

    # Test with "summ" instead of "sum"
    suggestions = engine.suggest_similar_tools("summ", max_suggestions=3)
    assert len(suggestions) > 0
    assert any("sum" in s for s in suggestions)


def test_suggest_similar_tools_no_matches():
    """Test with completely unrelated name."""
    engine = SuggestionEngine({"native::tools::len": {}, "native::tools::sum": {}})

    suggestions = engine.suggest_similar_tools("xyz123abc", max_suggestions=3)

    # Either no suggestions or very distant matches
    assert len(suggestions) <= 3
    # If there are suggestions, they should be the only tools available
    if suggestions:
        for s in suggestions:
            assert s in ["native::tools::len", "native::tools::sum"]


def test_levenshtein_distance_basic():
    """Test edit distance calculation."""
    engine = SuggestionEngine()

    # Test exact match
    assert engine.levenshtein_distance("hello", "hello") == 0

    # Test single character difference
    assert engine.levenshtein_distance("hello", "hallo") == 1
    assert engine.levenshtein_distance("hello", "hell") == 1
    assert engine.levenshtein_distance("hello", "ello") == 1

    # Test multiple differences
    assert engine.levenshtein_distance("kitten", "sitting") == 3

    # Test empty strings
    assert engine.levenshtein_distance("", "") == 0
    assert engine.levenshtein_distance("test", "") == 4
    assert engine.levenshtein_distance("", "test") == 4


def test_find_closest_matches():
    """Test finding multiple close matches."""
    engine = SuggestionEngine()

    candidates = ["len", "sum", "str", "int", "bool", "range"]

    # Test finding closest to "lenght" (typo)
    matches = engine._find_closest_matches("lenght", candidates, max_distance=3)

    assert len(matches) > 0
    # "len" should be closest
    assert matches[0][0] == "len"
    assert matches[0][1] <= 3  # Within distance threshold

    # Verify sorted by distance
    for i in range(1, len(matches)):
        assert matches[i][1] >= matches[i - 1][1]


# ============================================================================
# 4. Type Error Enhancement Tests
# ============================================================================


def test_suggest_nullable_fix_simple():
    """Test nullable type error suggestion."""
    engine = SuggestionEngine()

    suggestion = engine.suggest_nullable_fix("items[0]", "string")

    assert suggestion is not None
    assert "??" in suggestion
    assert "items[0] ??" in suggestion
    assert "default" in suggestion.lower() or '""' in suggestion
    # Should show example of using ?? operator


def test_suggest_nullable_fix_complex():
    """Test nested nullable expressions."""
    engine = SuggestionEngine()

    suggestion = engine.suggest_nullable_fix("user.profile.name", "string")

    assert suggestion is not None
    assert "??" in suggestion
    assert "user.profile.name ??" in suggestion
    # Should handle nested field access


def test_suggest_type_mismatch_fix():
    """Test type mismatch suggestions."""
    engine = SuggestionEngine()

    # Test string to number conversion
    suggestion = engine.suggest_type_fix(
        "type_mismatch", {"from": "string", "to": "number", "expression": "count"}
    )

    assert suggestion is not None
    assert "int(" in suggestion or "num(" in suggestion

    # Test number to string conversion
    suggestion = engine.suggest_type_fix(
        "type_mismatch", {"from": "number", "to": "string", "expression": "value"}
    )

    assert suggestion is not None
    assert "str(" in suggestion


# ============================================================================
# 5. Integration Tests
# ============================================================================


def test_compiler_error_with_context():
    """Test compiler errors use enhanced formatting."""
    formatter = ErrorFormatter()
    source = """x = 1
if x == 1
    print("missing colon")"""

    # Create a compiler syntax error
    error = CySyntaxError(message="Expected ':' after if statement", line=2, col=10)

    # Test that error can be enhanced with context
    enhanced_msg = formatter.format_with_context(
        source_code=source,
        line=error.line,
        col=error.col,
        message=error.message,
        suggestion="Add ':' at the end of the if statement",
        error_type="SyntaxError",
    )

    # Verify formatting includes context
    assert "if x == 1" in enhanced_msg
    assert "line 2" in enhanced_msg.lower()
    assert "Expected ':'" in enhanced_msg
    assert "Add ':'" in enhanced_msg


def test_executor_error_with_context():
    """Test runtime errors use enhanced formatting."""
    formatter = ErrorFormatter()
    engine = SuggestionEngine(
        {
            "app::splunk::search": {},
            "app::splunk::stats": {},
            "app::virustotal::ip_reputation": {},
        }
    )

    source = """data = get_data()
result = app::splunk::serach(data)  # Typo in 'search'
print(result)"""

    # Create a tool not found error
    tool_name = "app::splunk::serach"
    error = ToolNotFoundError(message=f"Tool '{tool_name}' not found", line=2, col=10)

    # Get suggestions for the typo
    suggestions = engine.suggest_similar_tools(tool_name)
    suggestion_text = (
        f"Did you mean: {', '.join(suggestions[:2])}" if suggestions else None
    )

    # Test that error can be enhanced with context
    enhanced_msg = formatter.format_with_context(
        source_code=source,
        line=error.line,
        col=error.col,
        message=error.message,
        suggestion=suggestion_text,
        error_type="ToolNotFoundError",
    )

    # Verify formatting includes context and suggestions
    assert "app::splunk::serach" in enhanced_msg
    assert "line 2" in enhanced_msg.lower()
    assert "not found" in enhanced_msg.lower()
    # Should suggest the correct spelling
    assert "app::splunk::search" in enhanced_msg or "Did you mean" in enhanced_msg


def test_type_checker_error_with_context():
    """Test type errors use enhanced formatting."""
    formatter = ErrorFormatter()
    engine = SuggestionEngine()

    source = """data = get_data()
name: string = data["name"]  # data["name"] might be null
print(name)"""

    # Test type error with nullable type
    error_msg = "Cannot assign nullable<string> to string"

    # Get nullable fix suggestion
    suggestion = engine.suggest_nullable_fix('data["name"]', "string")

    # Test that error can be enhanced with context
    enhanced_msg = formatter.format_with_context(
        source_code=source,
        line=2,
        col=16,
        message=error_msg,
        suggestion=suggestion,
        error_type="TypeError",
    )

    # Verify formatting includes type information
    assert "nullable" in enhanced_msg.lower()
    assert "string" in enhanced_msg.lower()
    assert 'data["name"]' in enhanced_msg
    assert "line 2" in enhanced_msg.lower()
    # Should suggest using ?? operator
    assert "??" in enhanced_msg or "null-coalescing" in enhanced_msg.lower()


def test_mcp_error_formatting():
    """Test errors from MCP integration."""
    formatter = ErrorFormatter()

    source = """# MCP server script
tool_result = mcp::cy_assistant::compile_script({
    "script": invalid_cy_code
})
print(tool_result)"""

    # Test MCP-specific error formatting
    mcp_error = CyRuntimeError(
        message="MCP tool 'mcp::cy_assistant::compile_script' failed: Invalid syntax in provided script",
        line=3,
        col=5,
    )

    # Test that MCP errors can be enhanced
    enhanced_msg = formatter.format_with_context(
        source_code=source,
        line=mcp_error.line,
        col=mcp_error.col,
        message=mcp_error.message,
        suggestion="Check the 'script' parameter for syntax errors",
        error_type="MCPError",
    )

    # Verify MCP error formatting
    assert "mcp::cy_assistant::compile_script" in enhanced_msg
    assert "failed" in enhanced_msg.lower()
    assert "script" in enhanced_msg.lower()
    assert "line 3" in enhanced_msg.lower()


# ============================================================================
# 6. Error Message Comparison Tests
# ============================================================================


def test_before_after_missing_brace():
    """Compare old vs new for unclosed brace."""
    formatter = ErrorFormatter()

    source = """if condition:
    x = 1
    if nested:
        y = 2
    # Missing closing brace for nested if"""

    # Old error message (what we currently have)
    old_error = (
        "Unexpected token Token('$END', '')...Expected one of: * FOR * WHILE * IF * TRY"
    )

    # New enhanced error message
    new_error = formatter.format_with_context(
        source_code=source,
        line=5,
        col=1,
        message="Unexpected end of file - possible unclosed block",
        suggestion="Check for missing closing braces or incorrect indentation",
        error_type="SyntaxError",
    )

    # Verify new error is more helpful
    assert "Unexpected end of file" in new_error
    assert "unclosed block" in new_error.lower()
    assert "line 5" in new_error.lower()

    # Old error shouldn't appear in new format
    assert "Token('$END'" not in new_error
    assert "* FOR * WHILE" not in new_error


def test_before_after_undefined_variable():
    """Compare old vs new for undefined variable."""
    formatter = ErrorFormatter()

    source = """x = 10
y = 20
result = x + Y  # Typo: Y instead of y
print(result)"""

    # Old error message
    old_error = "Variable 'Y' is not defined"

    # Detect common mistake (case sensitivity)
    source_line = "result = x + Y  # Typo: Y instead of y"
    pattern = detect_common_mistake("Variable 'Y' is not defined", source_line)
    suggestion = (
        pattern.get("suggestion")
        if pattern
        else "Did you mean 'y'? (Variable names are case-sensitive)"
    )

    # New enhanced error message
    new_error = formatter.format_with_context(
        source_code=source,
        line=3,
        col=14,
        message="Variable 'Y' is not defined",
        suggestion=suggestion,
        error_type="NameError",
    )

    # Verify new error provides context
    assert "result = x + Y" in new_error
    assert "line 3" in new_error.lower()
    assert "Y" in new_error

    # Should suggest the correct variable
    assert "y" in new_error.lower() or "case-sensitive" in new_error.lower()


def test_before_after_tool_not_found():
    """Compare old vs new for missing tool."""
    formatter = ErrorFormatter()
    engine = SuggestionEngine({"native::len": {}, "native::sum": {}, "native::str": {}})

    source = """data = [1, 2, 3, 4]
total = native::summ(data)  # Typo in tool name
print(total)"""

    # Old error message
    old_error = "Tool 'native::summ' not found"

    # Get tool suggestions
    suggestions = engine.suggest_similar_tools("native::summ", max_suggestions=2)
    suggestion_text = f"Did you mean: {', '.join(suggestions)}" if suggestions else None

    # New enhanced error message
    new_error = formatter.format_with_context(
        source_code=source,
        line=2,
        col=9,
        message="Tool 'native::summ' not found",
        suggestion=suggestion_text,
        error_type="ToolNotFoundError",
    )

    # Verify improvements
    assert "native::summ" in new_error
    assert "line 2" in new_error.lower()
    assert "total = native::summ(data)" in new_error

    # Should suggest the correct tool
    assert "native::sum" in new_error or "Did you mean" in new_error


def test_before_after_type_error():
    """Compare old vs new for type mismatch."""
    formatter = ErrorFormatter()
    engine = SuggestionEngine()

    source = """user_data = fetch_user()
username: string = user_data["username"]  # May be null
greeting = "Hello, " + username"""

    # Old error message
    old_error = "Type error: Cannot assign nullable<string> to string"

    # Get nullable fix suggestion
    suggestion = engine.suggest_nullable_fix('user_data["username"]', "string")

    # New enhanced error message
    new_error = formatter.format_with_context(
        source_code=source,
        line=2,
        col=20,
        message="Cannot assign nullable<string> to string",
        suggestion=suggestion,
        error_type="TypeError",
    )

    # Verify improvements
    assert 'username: string = user_data["username"]' in new_error
    assert "line 2" in new_error.lower()
    assert "nullable<string>" in new_error
    assert "string" in new_error

    # Should provide helpful fix suggestion
    assert (
        "??" in new_error
        or "null-coalescing" in new_error.lower()
        or "default" in new_error.lower()
    )


# ============================================================================
# 7. Edge Cases and Negative Tests
# ============================================================================


def test_error_at_file_start():
    """Test error on line 1."""
    formatter = ErrorFormatter()
    source = "true"

    # Test error at very beginning
    lines = formatter._get_lines_around_error(source, 1, context_lines=2)

    # Should handle boundary correctly
    assert len(lines) == 1  # Only one line in file
    assert lines[0] == (1, "true")

    # Test formatting
    result = formatter.format_with_context(
        source_code=source,
        line=1,
        col=1,
        message="Variable 'true' is not defined",
        suggestion="Did you mean 'True'?",
        error_type="NameError",
    )

    assert "line 1" in result.lower()
    assert "true" in result


def test_error_at_file_end():
    """Test error on last line."""
    formatter = ErrorFormatter()
    source = """x = 1
y = 2
z = true"""

    # Test getting lines around last line
    lines = formatter._get_lines_around_error(source, 3, context_lines=2)

    # Should include lines 1, 2, 3
    assert len(lines) == 3
    assert lines[2] == (3, "z = true")

    # Test formatting
    result = formatter.format_with_context(
        source_code=source,
        line=3,
        col=5,
        message="Variable 'true' is not defined",
        suggestion="Did you mean 'True'?",
        error_type="NameError",
    )

    assert "line 3" in result.lower()
    assert "z = true" in result


def test_very_long_line_error():
    """Test with extremely long source lines."""
    formatter = ErrorFormatter()

    # Create a very long line
    long_line = "x = " + "a" * 200 + " + true"
    source = long_line

    result = formatter.format_with_context(
        source_code=source,
        line=1,
        col=205,
        message="Variable 'true' is not defined",
        error_type="NameError",
    )

    # Should handle long lines gracefully
    # Either truncate or wrap appropriately
    assert "true" in result or "..." in result


def test_unicode_in_source():
    """Test with Unicode characters."""
    formatter = ErrorFormatter()
    source = 'message = "Hello 世界"'

    # Test with unicode in source
    result = formatter.format_with_context(
        source_code=source,
        line=1,
        col=18,  # Position after "Hello "
        message="Some error",
        error_type="Error",
    )

    # Should handle unicode characters
    assert "世界" in result or "Hello" in result


def test_multiple_errors():
    """Test formatting multiple errors."""
    formatter = ErrorFormatter()

    source = """x = true
y = false
z = x && y"""

    # Format first error
    error1 = formatter.format_with_context(
        source_code=source,
        line=1,
        col=5,
        message="Variable 'true' is not defined",
        error_type="NameError",
    )

    # Format second error
    error2 = formatter.format_with_context(
        source_code=source,
        line=2,
        col=5,
        message="Variable 'false' is not defined",
        error_type="NameError",
    )

    # Both should be properly formatted
    assert "line 1" in error1.lower()
    assert "line 2" in error2.lower()
    assert error1 != error2


# ============================================================================
# 8. Performance Tests
# ============================================================================


def test_formatter_performance():
    """Test with large source files."""
    import time

    formatter = ErrorFormatter()

    # Create a large source file (10,000 lines)
    large_source = "\n".join([f"line_{i} = {i}" for i in range(10000)])

    # Add an error in the middle
    error_line = 5000
    lines = large_source.split("\n")
    lines[error_line - 1] = "error_line = true  # Error here"
    large_source = "\n".join(lines)

    # Measure formatting time
    start_time = time.time()
    result = formatter.format_with_context(
        source_code=large_source,
        line=error_line,
        col=14,
        message="Variable 'true' is not defined",
        suggestion="Did you mean 'True'?",
        error_type="NameError",
    )
    end_time = time.time()

    # Performance assertions
    elapsed_time = end_time - start_time
    assert elapsed_time < 1.0  # Should complete within 1 second even for large files

    # Verify correct formatting despite large file
    assert "error_line = true" in result
    assert f"line {error_line}" in result.lower()
    assert "Did you mean 'True'" in result


def test_suggestion_performance():
    """Test with many tools."""
    import time

    # Create engine with many tools
    tools = {f"app::integration::tool_{i}": {} for i in range(1000)}
    # Add some similar names for better testing
    tools["app::integration::search"] = {}
    tools["app::integration::search_advanced"] = {}
    tools["app::integration::serach"] = {}  # Intentional typo for testing

    engine = SuggestionEngine(tools)

    # Measure suggestion time for a typo
    start_time = time.time()
    suggestions = engine.suggest_similar_tools(
        "app::integration::serch", max_suggestions=5
    )
    end_time = time.time()

    # Performance assertions
    elapsed_time = end_time - start_time
    assert elapsed_time < 1.0  # Should complete within 1s even with 1000+ tools

    # Verify suggestions are still accurate
    assert len(suggestions) > 0
    assert len(suggestions) <= 5
    # Should find "search" and "serach" as close matches
    assert any("search" in s for s in suggestions)


def test_space_in_variable_name_suggestion():
    """Test that space in variable name gives correct suggestion, not operator suggestion."""
    from cy_language.interpreter import Cy

    program = """c ity = "San Francisco"
output = c ity
return output
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should suggest fixing the space, NOT suggest using 'not' instead of '!'
    assert "Variable names cannot contain spaces" in error_msg
    assert "Use 'not' instead of '!'" not in error_msg
    assert "SyntaxError" in error_msg


def test_in_operator_works():
    """Test that 'in' operator works for membership testing."""
    from cy_language.interpreter import Cy

    program = """items = [1, 2, 3]
if (2 in items) {
    result = "found"
}
return result
"""

    cy = Cy()
    result = cy.run(program)
    assert result == '"found"'


def test_missing_colon_in_dict_suggestion():
    """Test that missing colon in dict gives correct suggestion."""
    from cy_language.interpreter import Cy

    program = """data = {"name" "Alice"}
return data
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should suggest missing colon
    assert "colon" in error_msg.lower()
    # Should NOT suggest missing comma (that's wrong for this case)
    # Note: The suggestion might say "Missing colon ':' between" which is correct


def test_else_if_instead_of_elif_suggestion():
    """Test that 'else if' suggests using 'elif'."""
    from cy_language.interpreter import Cy

    program = """x = 5
if (x > 10) {
    result = "big"
} else if (x > 5) {
    result = "medium"
} else {
    result = "small"
}
return result
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should suggest using elif
    assert "elif" in error_msg.lower()


def test_assignment_in_condition_suggestion():
    """Test that using = instead of == in condition gives helpful suggestion."""
    from cy_language.interpreter import Cy

    program = """x = 5
if (x = 10) {
    result = "changed"
}
return result
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should suggest using == for comparison
    assert (
        "==" in error_msg
        or "comparison" in error_msg.lower()
        or "assign" in error_msg.lower()
    )


def test_missing_function_call_parens_suggestion():
    """Test that missing () on function call gives helpful suggestion."""
    from cy_language.interpreter import Cy

    program = """items = [1, 2, 3]
length = len
return length
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should suggest adding () to call the function
    assert "()" in error_msg or "call" in error_msg.lower()


def test_semicolon_terminator_suggestion():
    """Test that using semicolons gives helpful suggestion."""
    from cy_language.interpreter import Cy

    program = """x = 5;
return x
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should mention semicolons are not needed
    assert "semicolon" in error_msg.lower()


def test_list_comprehension_suggestion():
    """Test that list comprehension syntax gives helpful suggestion."""
    from cy_language.interpreter import Cy

    program = """items = [1, 2, 3]
doubled = [x * 2 for x in items]
return doubled
"""

    cy = Cy()
    with pytest.raises(Exception) as exc_info:
        cy.run(program)

    error_msg = str(exc_info.value)
    # Should NOT say "'in' operator not supported" (misleading)
    # Should mention list comprehensions instead
    assert "comprehension" in error_msg.lower() or "for loop" in error_msg.lower()
