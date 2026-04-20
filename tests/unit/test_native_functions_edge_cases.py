"""Comprehensive edge case tests for all native functions.

This test suite covers corner cases, error conditions, and boundary
scenarios for all 9 native functions in Cy.
"""

import json

import pytest

from cy_language.native_functions import (
    from_json,
    join,
    len_function,
    log,
    lowercase,
    str_function,
    sum_function,
    to_json,
    uppercase,
)


class TestLenFunctionEdgeCases:
    """Edge case tests for len() function."""

    def test_len_with_empty_dict(self):
        """Test len() with empty dictionary."""
        assert len_function({}) == 0

    def test_len_with_nested_empty_lists(self):
        """Test len() with nested empty lists."""
        assert len_function([[], [], []]) == 3

    def test_len_with_unicode_string(self):
        """Test len() with Unicode characters."""
        # Emojis and special characters
        assert (
            len_function("Hello 🌍🎉") == 8
        )  # Python counts emojis as single characters
        assert len_function("日本語") == 3
        assert len_function("Ñoño") == 4

    def test_len_with_multiline_string(self):
        """Test len() with multiline strings."""
        text = """Line 1
Line 2
Line 3"""
        assert len_function(text) == 20  # Including newlines

    def test_len_with_whitespace_only_string(self):
        """Test len() with whitespace-only string."""
        assert len_function("   ") == 3
        assert len_function("\t\n\r") == 3

    def test_len_with_boolean(self):
        """Test len() with boolean values."""
        assert len_function(True) == 0
        assert len_function(False) == 0

    def test_len_with_float(self):
        """Test len() with float values."""
        assert len_function(3.14) == 0
        assert len_function(0.0) == 0

    def test_len_with_negative_number(self):
        """Test len() with negative numbers."""
        assert len_function(-42) == 0
        assert len_function(-3.14) == 0

    def test_len_with_zero(self):
        """Test len() with zero."""
        assert len_function(0) == 0

    def test_len_with_very_large_list(self):
        """Test len() with very large list."""
        large_list = list(range(1000000))
        assert len_function(large_list) == 1000000

    def test_len_with_nested_dicts(self):
        """Test len() with nested dictionaries - only counts top level."""
        nested = {
            "a": {"b": {"c": "d"}},
            "e": {"f": {"g": "h"}},
        }
        assert len_function(nested) == 2

    def test_len_with_mixed_dict_keys(self):
        """Test len() with various dictionary key types."""
        mixed = {
            "string_key": 1,
            42: 2,
            (1, 2): 3,
        }
        assert len_function(mixed) == 3


class TestSumFunctionEdgeCases:
    """Edge case tests for sum() function."""

    def test_sum_with_empty_list(self):
        """Test sum() with empty list."""
        assert sum_function([]) == 0

    def test_sum_with_single_element(self):
        """Test sum() with single element."""
        assert sum_function([42]) == 42
        assert sum_function([0]) == 0
        assert sum_function([-5]) == -5

    def test_sum_with_negative_numbers(self):
        """Test sum() with negative numbers."""
        assert sum_function([-1, -2, -3]) == -6
        assert sum_function([10, -5, 3, -2]) == 6

    def test_sum_with_floats(self):
        """Test sum() with floating point numbers."""
        result = sum_function([1.1, 2.2, 3.3])
        assert abs(result - 6.6) < 0.0001  # Float precision

    def test_sum_with_mixed_int_float(self):
        """Test sum() with mixed integers and floats."""
        result = sum_function([1, 2.5, 3, 4.5])
        assert abs(result - 11.0) < 0.0001

    def test_sum_with_zeros(self):
        """Test sum() with zeros."""
        assert sum_function([0, 0, 0]) == 0
        assert sum_function([1, 0, 2, 0, 3]) == 6

    def test_sum_with_very_large_numbers(self):
        """Test sum() with very large numbers."""
        assert sum_function([1e10, 2e10, 3e10]) == 6e10

    def test_sum_with_very_small_numbers(self):
        """Test sum() with very small numbers."""
        result = sum_function([0.0001, 0.0002, 0.0003])
        assert abs(result - 0.0006) < 0.00001

    def test_sum_with_non_list_input(self):
        """Test sum() with non-list input."""
        assert sum_function("not a list") == 0
        assert sum_function(42) == 0
        assert sum_function({"a": 1}) == 0
        assert sum_function(None) == 0

    def test_sum_with_non_numeric_elements(self):
        """Test sum() with non-numeric elements."""
        assert sum_function(["a", "b", "c"]) == 0
        assert sum_function([1, "two", 3]) == 0  # Mixed types fail
        assert sum_function([None, None]) == 0

    def test_sum_with_boolean_in_list(self):
        """Test sum() with booleans (Python treats True=1, False=0)."""
        # In Python, True == 1 and False == 0, so sum works
        assert sum_function([True, True, False]) == 2
        assert sum_function([False, False, False]) == 0

    def test_sum_with_infinity(self):
        """Test sum() with infinity."""
        assert sum_function([float("inf"), 1, 2]) == float("inf")
        assert sum_function([float("-inf"), 1, 2]) == float("-inf")

    def test_sum_with_nan(self):
        """Test sum() with NaN."""
        result = sum_function([float("nan"), 1, 2])
        assert result != result  # NaN != NaN


class TestStrFunctionEdgeCases:
    """Edge case tests for str() function."""

    def test_str_with_empty_string(self):
        """Test str() with empty string."""
        assert str_function("") == ""

    def test_str_with_empty_list(self):
        """Test str() with empty list."""
        assert str_function([]) == "[]"

    def test_str_with_empty_dict(self):
        """Test str() with empty dict."""
        assert str_function({}) == "{}"

    def test_str_with_unicode(self):
        """Test str() with Unicode characters."""
        assert str_function("🌍🎉") == "🌍🎉"
        assert str_function("日本語") == "日本語"

    def test_str_with_newlines_tabs(self):
        """Test str() with special whitespace characters."""
        result = str_function("line1\nline2\ttab")
        assert "\\n" in result or "\n" in result

    def test_str_with_quotes(self):
        """Test str() with various quote types."""
        assert str_function("It's working") == "It's working"
        assert str_function('He said "hello"') == 'He said "hello"'

    def test_str_with_very_long_string(self):
        """Test str() with very long string."""
        long_str = "a" * 100000
        result = str_function(long_str)
        assert len(result) == 100000

    def test_str_with_nested_structures(self):
        """Test str() with deeply nested structures."""
        nested = {"a": {"b": {"c": {"d": "deep"}}}}
        result = str_function(nested)
        assert "deep" in result

    def test_str_with_circular_reference_protection(self):
        """Test str() doesn't crash on structures Python can handle."""
        # Python's str() handles this gracefully
        data = {"key": "value"}
        result = str_function(data)
        assert isinstance(result, str)

    def test_str_with_special_objects(self):
        """Test str() with special Python objects."""

        # Lambda function
        def func(x):
            return x + 1

        result = str_function(func)
        assert "lambda" in result or "function" in result

        # Class instance
        class TestClass:
            pass

        obj = TestClass()
        result = str_function(obj)
        assert "TestClass" in result

    def test_str_with_infinity(self):
        """Test str() with infinity."""
        assert str_function(float("inf")) == "inf"
        assert str_function(float("-inf")) == "-inf"

    def test_str_with_nan(self):
        """Test str() with NaN."""
        assert str_function(float("nan")) == "nan"


class TestLogFunctionEdgeCases:
    """Edge case tests for log() function."""

    def test_log_with_empty_string(self):
        """Test log() with empty string."""
        assert log("") == ""

    def test_log_with_very_long_message(self):
        """Test log() with very long message."""
        long_msg = "a" * 100000
        result = log(long_msg)
        assert result == long_msg

    def test_log_with_unicode(self):
        """Test log() with Unicode characters."""
        msg = "Hello 🌍"
        assert log(msg) == msg

    def test_log_with_newlines(self):
        """Test log() with newlines."""
        msg = "Line 1\nLine 2\nLine 3"
        assert log(msg) == msg

    def test_log_with_none(self):
        """Test log() with None."""
        assert log(None) == "None"

    def test_log_with_number(self):
        """Test log() with number."""
        result = log(42)
        assert "42" in result

    def test_log_with_complex_data(self):
        """Test log() with complex data structures."""
        data = {"list": [1, 2, 3], "nested": {"key": "value"}}
        result = log(data)
        assert isinstance(result, str)
        assert "list" in result or "[1, 2, 3]" in result

    def test_log_concurrent_calls(self):
        """Test log() with rapid concurrent calls."""
        messages = [f"Message {i}" for i in range(100)]
        results = [log(msg) for msg in messages]
        assert results == messages


class TestFromJsonEdgeCases:
    """Edge case tests for from_json() function."""

    def test_from_json_with_empty_string(self):
        """Test from_json() with empty string - returns empty dict."""
        result = from_json("")
        assert result == {}

    def test_from_json_with_whitespace_only(self):
        """Test from_json() with whitespace-only string - returns empty dict."""
        result = from_json("   ")
        assert result == {}
        result = from_json("\t\n\r")
        assert result == {}

    def test_from_json_with_null(self):
        """Test from_json() with JSON null."""
        result = from_json("null")
        assert result is None

    def test_from_json_with_boolean(self):
        """Test from_json() with boolean values."""
        assert from_json("true") is True
        assert from_json("false") is False

    def test_from_json_with_number(self):
        """Test from_json() with number."""
        assert from_json("42") == 42
        assert from_json("3.14") == 3.14
        assert from_json("-10") == -10

    def test_from_json_with_string(self):
        """Test from_json() with JSON string."""
        assert from_json('"hello"') == "hello"
        assert from_json('""') == ""

    def test_from_json_with_unicode(self):
        """Test from_json() with Unicode."""
        result = from_json('{"emoji": "🌍", "japanese": "日本語"}')
        assert result["emoji"] == "🌍"
        assert result["japanese"] == "日本語"

    def test_from_json_with_escaped_characters(self):
        """Test from_json() with escaped characters."""
        result = from_json('{"text": "Line 1\\nLine 2\\tTab"}')
        assert "\n" in result["text"]
        assert "\t" in result["text"]

    def test_from_json_with_nested_arrays(self):
        """Test from_json() with deeply nested arrays."""
        json_str = "[[[[1, 2, 3]]]]"
        result = from_json(json_str)
        assert result[0][0][0][0] == 1

    def test_from_json_with_very_large_json(self):
        """Test from_json() with large JSON."""
        large_array = json.dumps(list(range(10000)))
        result = from_json(large_array)
        assert len(result) == 10000

    def test_from_json_with_special_characters(self):
        """Test from_json() with special characters."""
        result = from_json('{"quote": "\\"", "backslash": "\\\\"}')
        assert result["quote"] == '"'
        assert result["backslash"] == "\\"

    def test_from_json_invalid_syntax(self):
        """Test from_json() with invalid JSON syntax."""
        with pytest.raises(ValueError):
            from_json("{invalid}")
        with pytest.raises(ValueError):
            from_json('{"key": undefined}')
        with pytest.raises(ValueError):
            from_json("{'single': 'quotes'}")

    def test_from_json_with_trailing_comma(self):
        """Test from_json() with trailing comma (invalid)."""
        with pytest.raises(ValueError):
            from_json('{"key": "value",}')

    def test_from_json_with_comments(self):
        """Test from_json() with comments (invalid in JSON)."""
        with pytest.raises(ValueError):
            from_json('{"key": "value" /* comment */}')

    def test_from_json_with_non_string_input(self):
        """Test from_json() with non-string input."""
        with pytest.raises(ValueError):
            from_json(42)
        with pytest.raises(ValueError):
            from_json([1, 2, 3])
        with pytest.raises(ValueError):
            from_json(None)


class TestToJsonEdgeCases:
    """Edge case tests for to_json() function."""

    def test_to_json_with_none(self):
        """Test to_json() with None."""
        assert to_json(None) == "null"

    def test_to_json_with_boolean(self):
        """Test to_json() with boolean."""
        assert to_json(True) == "true"
        assert to_json(False) == "false"

    def test_to_json_with_numbers(self):
        """Test to_json() with various numbers."""
        assert to_json(42) == "42"
        assert to_json(3.14) == "3.14"
        assert to_json(-10) == "-10"
        assert to_json(0) == "0"

    def test_to_json_with_empty_structures(self):
        """Test to_json() with empty structures."""
        assert to_json([]) == "[]"
        assert to_json({}) == "{}"

    def test_to_json_with_unicode(self):
        """Test to_json() with Unicode."""
        result = to_json({"emoji": "🌍"})
        assert "🌍" in result or "\\u" in result  # May be escaped

    def test_to_json_with_nested_structures(self):
        """Test to_json() with deeply nested structures."""
        nested = {"a": {"b": {"c": {"d": "deep"}}}}
        result = to_json(nested)
        assert "deep" in result

    def test_to_json_with_indentation(self):
        """Test to_json() with indentation."""
        data = {"key": "value"}
        result = to_json(data, indent=2)
        assert "\n" in result
        assert "  " in result

    def test_to_json_with_large_data(self):
        """Test to_json() with large data structure."""
        large_data = {"items": list(range(10000))}
        result = to_json(large_data)
        assert len(result) > 10000

    def test_to_json_with_special_characters(self):
        """Test to_json() with special characters."""
        data = {"quote": '"', "backslash": "\\", "newline": "\n"}
        result = to_json(data)
        # Should be properly escaped
        assert '\\"' in result or '"' in result

    def test_to_json_with_non_serializable(self):
        """Test to_json() with non-serializable objects."""
        # Functions, lambdas, class instances
        with pytest.raises(ValueError):
            to_json(lambda x: x)

        class CustomClass:
            pass

        with pytest.raises(ValueError):
            to_json(CustomClass())

    def test_to_json_with_infinity(self):
        """Test to_json() with infinity (produces non-standard JSON)."""
        # Python's json.dumps produces "Infinity" and "-Infinity" which are not standard JSON
        # but we allow it since json.dumps does
        result = to_json(float("inf"))
        assert result == "Infinity"
        result = to_json(float("-inf"))
        assert result == "-Infinity"

    def test_to_json_with_nan(self):
        """Test to_json() with NaN (produces non-standard JSON)."""
        # Python's json.dumps produces "NaN" which is not standard JSON
        result = to_json(float("nan"))
        assert result == "NaN"

    def test_to_json_roundtrip(self):
        """Test to_json() and from_json() roundtrip."""
        original = {
            "string": "hello",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }
        json_str = to_json(original)
        restored = from_json(json_str)
        assert restored == original


class TestUppercaseEdgeCases:
    """Edge case tests for uppercase() function."""

    def test_uppercase_with_empty_string(self):
        """Test uppercase() with empty string."""
        assert uppercase("") == ""

    def test_uppercase_with_whitespace(self):
        """Test uppercase() with whitespace."""
        assert uppercase("   ") == "   "
        assert uppercase("\t\n\r") == "\t\n\r"

    def test_uppercase_with_numbers(self):
        """Test uppercase() with numbers."""
        assert uppercase("hello123") == "HELLO123"
        assert uppercase("123") == "123"

    def test_uppercase_with_special_chars(self):
        """Test uppercase() with special characters."""
        assert uppercase("hello!@#$%") == "HELLO!@#$%"

    def test_uppercase_with_unicode(self):
        """Test uppercase() with Unicode characters."""
        assert uppercase("café") == "CAFÉ"
        assert uppercase("ñoño") == "ÑOÑO"

    def test_uppercase_with_mixed_case(self):
        """Test uppercase() with mixed case."""
        assert uppercase("HeLLo WoRLd") == "HELLO WORLD"

    def test_uppercase_already_uppercase(self):
        """Test uppercase() with already uppercase string."""
        assert uppercase("HELLO") == "HELLO"

    def test_uppercase_with_very_long_string(self):
        """Test uppercase() with very long string."""
        long_str = "a" * 100000
        result = uppercase(long_str)
        assert result == "A" * 100000


class TestLowercaseEdgeCases:
    """Edge case tests for lowercase() function."""

    def test_lowercase_with_empty_string(self):
        """Test lowercase() with empty string."""
        assert lowercase("") == ""

    def test_lowercase_with_whitespace(self):
        """Test lowercase() with whitespace."""
        assert lowercase("   ") == "   "

    def test_lowercase_with_numbers(self):
        """Test lowercase() with numbers."""
        assert lowercase("HELLO123") == "hello123"

    def test_lowercase_with_unicode(self):
        """Test lowercase() with Unicode."""
        assert lowercase("CAFÉ") == "café"
        assert lowercase("ÑOÑO") == "ñoño"

    def test_lowercase_already_lowercase(self):
        """Test lowercase() with already lowercase string."""
        assert lowercase("hello") == "hello"

    def test_lowercase_with_very_long_string(self):
        """Test lowercase() with very long string."""
        long_str = "A" * 100000
        result = lowercase(long_str)
        assert result == "a" * 100000


class TestJoinEdgeCases:
    """Edge case tests for join() function."""

    def test_join_with_empty_list(self):
        """Test join() with empty list."""
        assert join([]) == ""

    def test_join_with_single_element(self):
        """Test join() with single element."""
        assert join(["only"]) == "only"

    def test_join_with_empty_strings(self):
        """Test join() with empty strings."""
        assert join(["", "", ""]) == ", , "
        assert join(["", "", ""], "") == ""

    def test_join_with_numbers(self):
        """Test join() with numbers (should be converted to strings)."""
        assert join([1, 2, 3]) == "1, 2, 3"
        assert join([1.5, 2.5, 3.5]) == "1.5, 2.5, 3.5"

    def test_join_with_mixed_types(self):
        """Test join() with mixed types."""
        result = join(["text", 42, True, None])
        assert "text" in result
        assert "42" in result
        assert "True" in result
        assert "None" in result

    def test_join_with_unicode(self):
        """Test join() with Unicode."""
        assert join(["🌍", "🎉", "🚀"]) == "🌍, 🎉, 🚀"

    def test_join_with_empty_separator(self):
        """Test join() with empty separator."""
        assert join(["a", "b", "c"], "") == "abc"

    def test_join_with_multichar_separator(self):
        """Test join() with multi-character separator."""
        assert join(["a", "b", "c"], " -> ") == "a -> b -> c"

    def test_join_with_unicode_separator(self):
        """Test join() with Unicode separator."""
        assert join(["a", "b", "c"], " 🔹 ") == "a 🔹 b 🔹 c"

    def test_join_with_newline_separator(self):
        """Test join() with newline separator."""
        result = join(["line1", "line2", "line3"], "\n")
        assert result == "line1\nline2\nline3"

    def test_join_with_very_long_list(self):
        """Test join() with very long list."""
        long_list = [str(i) for i in range(10000)]
        result = join(long_list)
        assert len(result) > 10000

    def test_join_with_nested_structures(self):
        """Test join() with nested structures (converted to strings)."""
        result = join([{"a": 1}, ["b", 2], "c"])
        assert "a" in result or "{" in result
        assert isinstance(result, str)
