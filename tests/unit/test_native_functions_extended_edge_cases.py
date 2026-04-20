"""Corner case tests for extended native functions.

Additional edge cases and corner cases beyond the comprehensive tests in
test_native_functions_extended.py to ensure robustness in production.
"""

import math

import pytest

from cy_language.native_functions import (
    abs_function,
    bool_function,
    max_function,
    min_function,
    now_function,
    num_function,
    range_function,
    regex_extract_function,
    regex_match_function,
    replace_function,
    reverse_function,
    round_function,
    sort_function,
    split_function,
    trim_function,
)

# ============================================================================
# TYPE CONVERSION CORNER CASES
# ============================================================================


class TestNumCornerCases:
    """Corner cases for num() function."""

    def test_num_with_scientific_notation(self):
        """Test num() with scientific notation strings."""
        assert num_function("1e3") == 1000.0
        assert num_function("1.5e2") == 150.0
        assert num_function("2.5e-1") == 0.25

    def test_num_with_inf_and_nan(self):
        """Test num() with infinity and NaN strings."""
        result = num_function("inf")
        assert math.isinf(result)

        result = num_function("-inf")
        assert math.isinf(result) and result < 0

        result = num_function("nan")
        assert math.isnan(result)

    def test_num_with_very_large_numbers(self):
        """Test num() with very large numbers."""
        large = "999999999999999999999999.99"
        result = num_function(large)
        assert result > 1e20

    def test_num_with_leading_plus_sign(self):
        """Test num() with explicit plus sign."""
        assert num_function("+42") == 42.0
        assert num_function("+3.14") == 3.14

    def test_num_with_tabs_and_newlines(self):
        """Test num() with various whitespace characters."""
        assert num_function("\t42\n") == 42.0
        assert num_function("\r\n 3.14 \t") == 3.14


class TestBoolCornerCases:
    """Corner cases for bool() function."""

    def test_bool_with_numeric_strings(self):
        """Test bool() with various numeric string representations."""
        # String representations of numbers
        assert bool_function("2") is True  # Non-zero, uses Python truthiness
        assert bool_function("-1") is True  # Non-zero negative
        assert bool_function("0.0") is True  # Non-empty string uses truthiness
        assert bool_function("00") is True  # "00" is not "0", uses truthiness

    def test_bool_with_mixed_case_yes_no(self):
        """Test bool() with mixed case yes/no."""
        assert bool_function("YES") is True
        assert bool_function("Yes") is True
        assert bool_function("yEs") is True
        assert bool_function("NO") is False
        assert bool_function("No") is False
        assert bool_function("nO") is False

    def test_bool_with_unicode_whitespace(self):
        """Test bool() with unicode whitespace characters."""
        # Non-breaking space (U+00A0)
        assert bool_function("\u00a0true\u00a0") is True
        # Various Unicode spaces
        assert bool_function("\u2000false\u2000") is False

    def test_bool_with_special_string_cases(self):
        """Test bool() with special string edge cases."""
        # After strip(), single space becomes empty string which is falsy
        assert bool_function(" ") is False  # Strips to empty string
        assert bool_function("\t") is False  # Strips to empty string
        assert bool_function("\n") is False  # Strips to empty string
        assert bool_function("  text  ") is True  # Has content after strip


# ============================================================================
# TIME CORNER CASES
# ============================================================================


class TestNowCornerCases:
    """Corner cases for now() function."""

    def test_now_with_case_sensitive_timezone(self):
        """Test now() timezone parameter is case-sensitive."""
        # Should work with proper case
        result = now_function("America/New_York")
        assert "T" in result  # ISO format

        # Should work with UTC variants
        result_utc = now_function("UTC")
        assert result_utc.endswith("Z")

    def test_now_timestamp_ordering(self):
        """Test now() produces ordered timestamps."""
        ts1 = now_function()
        ts2 = now_function()
        # Both should be valid ISO timestamps
        assert len(ts1) >= 20  # Minimum ISO 8601 length
        assert len(ts2) >= 20
        # Should be very close in time (within same second typically)
        assert ts1[:19] == ts2[:19] or ts1[:19] <= ts2[:19]


# ============================================================================
# RANGE CORNER CASES
# ============================================================================


class TestRangeCornerCases:
    """Corner cases for range() function."""

    def test_range_with_equal_start_end(self):
        """Test range() when start equals end."""
        assert range_function(5, 5) == []
        assert range_function(0, 0) == []
        assert range_function(-5, -5) == []

    def test_range_with_step_larger_than_range(self):
        """Test range() with step larger than the range."""
        assert range_function(0, 5, 10) == [0]  # Only first value
        assert range_function(1, 3, 5) == [1]  # Only first value

    def test_range_with_negative_range_positive_step(self):
        """Test range() with start > end and positive step."""
        assert range_function(10, 5, 1) == []  # Empty range

    def test_range_with_positive_range_negative_step(self):
        """Test range() with start < end and negative step."""
        assert range_function(5, 10, -1) == []  # Empty range

    def test_range_with_very_large_step(self):
        """Test range() with very large step values."""
        assert range_function(0, 1000000, 999999) == [0, 999999]
        assert range_function(0, 100, 1000) == [0]


# ============================================================================
# STRING CORNER CASES
# ============================================================================


class TestSplitCornerCases:
    """Corner cases for split() function."""

    def test_split_with_empty_delimiter(self):
        """Test split() with empty string delimiter."""
        # Python's split behavior with empty delimiter
        with pytest.raises(ValueError, match="empty separator"):
            split_function("hello", "")

    def test_split_with_multichar_delimiter(self):
        """Test split() with multi-character delimiter."""
        assert split_function("foo::bar::baz", "::") == ["foo", "bar", "baz"]
        assert split_function("a<=>b<=>c", "<=>") == ["a", "b", "c"]

    def test_split_with_unicode_characters(self):
        """Test split() with Unicode strings."""
        assert split_function("hello→world→test", "→") == ["hello", "world", "test"]
        assert split_function("café•bar•baz", "•") == ["café", "bar", "baz"]

    def test_split_consecutive_delimiters(self):
        """Test split() with consecutive delimiters."""
        assert split_function("a,,b,,c", ",") == ["a", "", "b", "", "c"]
        assert split_function("::::", ":") == ["", "", "", "", ""]


class TestReplaceCornerCases:
    """Corner cases for replace() function."""

    def test_replace_with_overlapping_patterns(self):
        """Test replace() with overlapping patterns."""
        # Should replace all non-overlapping occurrences
        assert replace_function("aaa", "aa", "b") == "ba"
        assert replace_function("aaaa", "aa", "b") == "bb"

    def test_replace_with_longer_replacement(self):
        """Test replace() where replacement is longer than original."""
        assert replace_function("cat", "cat", "category") == "category"
        assert replace_function("a", "a", "hello") == "hello"

    def test_replace_with_unicode(self):
        """Test replace() with Unicode characters."""
        assert replace_function("café", "é", "e") == "cafe"
        assert replace_function("hello→world", "→", " ") == "hello world"

    def test_replace_entire_string(self):
        """Test replace() that replaces the entire string."""
        assert replace_function("test", "test", "new") == "new"
        assert replace_function("a", "a", "") == ""


class TestTrimCornerCases:
    """Corner cases for trim() function."""

    def test_trim_with_unicode_spaces(self):
        """Test trim() with various Unicode space characters."""
        # Non-breaking space (U+00A0)
        assert trim_function("\u00a0test\u00a0") == "test"
        # Em space (U+2003)
        assert trim_function("\u2003test\u2003") == "test"

    def test_trim_with_mixed_whitespace(self):
        """Test trim() with mixed whitespace types."""
        assert trim_function(" \t\n\r test \n\t\r ") == "test"
        assert trim_function("\n\n\nvalue\t\t\t") == "value"

    def test_trim_preserves_internal_whitespace(self):
        """Test trim() preserves internal whitespace."""
        assert trim_function("  hello  world  ") == "hello  world"
        assert trim_function("\thello\tworld\t") == "hello\tworld"


class TestRegexCornerCases:
    """Corner cases for regex functions."""

    def test_regex_match_with_special_characters(self):
        """Test regex_match() with regex special characters."""
        # Dot should match any character
        assert regex_match_function("a.c", "abc") is True
        assert regex_match_function("a.c", "a.c") is True

        # Character classes
        assert regex_match_function("[abc]", "a") is True
        assert regex_match_function("[0-9]", "5") is True

    def test_regex_match_with_lookahead(self):
        """Test regex_match() with lookahead assertions."""
        # Positive lookahead
        assert regex_match_function("test(?=ing)", "testing") is True
        assert regex_match_function("test(?=ing)", "tested") is False

    def test_regex_extract_with_nested_groups(self):
        """Test regex_extract() with nested capture groups."""
        # Nested groups - should return first group
        result = regex_extract_function(r"((a)(b))", "ab")
        assert result == "ab"  # First group is the entire match

    def test_regex_extract_with_optional_groups(self):
        """Test regex_extract() with optional capture groups."""
        # Optional group that matches
        result = regex_extract_function(r"test(\d+)?", "test123")
        assert result == "123"

        # Optional group that doesn't match - returns None from match.group(1)
        result = regex_extract_function(r"test(\d+)?", "test")
        assert result is None  # Group exists but matched None

    def test_regex_with_unicode_patterns(self):
        """Test regex functions with Unicode patterns."""
        assert regex_match_function(r"\w+", "café") is True
        assert regex_extract_function(r"([^\s]+)", "hello→world") == "hello→world"

    def test_regex_with_multiline_mode(self):
        """Test regex with multiline strings."""
        text = "line1\nline2\nline3"
        assert regex_match_function(r"line1", text) is True
        assert regex_extract_function(r"line(\d+)", text) == "1"


# ============================================================================
# ARRAY CORNER CASES
# ============================================================================


class TestReverseCornerCases:
    """Corner cases for reverse() function."""

    def test_reverse_with_nested_structures(self):
        """Test reverse() with nested lists and dicts."""
        nested = [[1, 2], [3, 4], [5, 6]]
        result = reverse_function(nested)
        assert result == [[5, 6], [3, 4], [1, 2]]
        # Verify inner lists are not reversed
        assert result[0] == [5, 6]

    def test_reverse_with_mixed_types_complex(self):
        """Test reverse() with complex mixed types."""
        mixed = [1, "two", 3.0, True, None, {"key": "value"}, [1, 2]]
        result = reverse_function(mixed)
        assert result[0] == [1, 2]
        assert result[-1] == 1

    def test_reverse_immutability_deep(self):
        """Test reverse() doesn't modify nested structures."""
        original = [[1, 2], [3, 4]]
        result = reverse_function(original)
        assert original == [[1, 2], [3, 4]]  # Original unchanged
        assert result == [[3, 4], [1, 2]]


class TestSortCornerCases:
    """Corner cases for sort() function."""

    def test_sort_with_duplicates(self):
        """Test sort() with duplicate values."""
        assert sort_function([3, 1, 3, 2, 1, 2]) == [1, 1, 2, 2, 3, 3]
        assert sort_function(["b", "a", "b", "a"]) == ["a", "a", "b", "b"]

    def test_sort_with_all_same_values(self):
        """Test sort() with all identical values."""
        assert sort_function([5, 5, 5, 5]) == [5, 5, 5, 5]
        assert sort_function(["x", "x", "x"]) == ["x", "x", "x"]

    def test_sort_with_special_string_cases(self):
        """Test sort() with special string cases."""
        # Numbers as strings sort lexicographically
        assert sort_function(["10", "2", "1", "20"]) == ["1", "10", "2", "20"]

        # Case sensitivity
        assert sort_function(["B", "a", "C", "b"]) == ["B", "C", "a", "b"]

    def test_sort_with_unicode_strings(self):
        """Test sort() with Unicode strings."""
        result = sort_function(["café", "cafe", "bar"])
        assert result == ["bar", "cafe", "café"]

    def test_sort_stability(self):
        """Test sort() maintains stability for equal elements."""
        # Since we're sorting primitives, stability is hard to test
        # But we can verify equal elements remain in valid order
        result = sort_function([1, 2, 1, 2, 1])
        assert result == [1, 1, 1, 2, 2]


# ============================================================================
# MATH CORNER CASES
# ============================================================================


class TestMathCornerCases:
    """Corner cases for math functions."""

    def test_abs_with_extreme_values(self):
        """Test abs() with extreme numeric values."""
        assert abs_function(1e308) == 1e308  # Near max float
        assert abs_function(-1e308) == 1e308
        assert abs_function(1e-308) == 1e-308  # Near min positive float

    def test_min_max_with_negative_zero(self):
        """Test min/max with negative zero."""
        # Python treats -0.0 and 0.0 as equal
        assert min_function([0.0, -0.0]) == -0.0 or min_function([0.0, -0.0]) == 0.0
        assert max_function([0.0, -0.0]) == 0.0 or max_function([0.0, -0.0]) == -0.0

    def test_min_max_with_inf(self):
        """Test min/max with infinity values."""
        inf = float("inf")
        neg_inf = float("-inf")

        assert min_function([1, 2, inf]) == 1
        assert min_function([inf, neg_inf, 0]) == neg_inf

        assert max_function([1, 2, neg_inf]) == 2
        assert max_function([inf, neg_inf, 0]) == inf

    def test_min_max_with_all_negative(self):
        """Test min/max with all negative numbers."""
        assert min_function([-5, -1, -10, -3]) == -10
        assert max_function([-5, -1, -10, -3]) == -1

    def test_round_with_halfway_cases(self):
        """Test round() with halfway cases (banker's rounding)."""
        # Python 3 uses banker's rounding (round to even)
        assert round_function(0.5, 0) == 0.0  # Rounds to even
        assert round_function(1.5, 0) == 2.0  # Rounds to even
        assert round_function(2.5, 0) == 2.0  # Rounds to even
        assert round_function(3.5, 0) == 4.0  # Rounds to even

    def test_round_with_large_decimals_param(self):
        """Test round() with large decimal places."""
        assert round_function(3.141592653589793, 10) == 3.1415926536
        assert round_function(1.123456789012345, 15) == 1.123456789012345

    def test_round_with_very_small_numbers(self):
        """Test round() with very small numbers."""
        assert round_function(1e-10, 15) == 1e-10
        assert round_function(1.23e-8, 10) == 1.23e-8

    def test_round_precision_edge_cases(self):
        """Test round() near precision limits."""
        # Testing floating point precision limits
        result = round_function(0.1 + 0.2, 1)  # Classic float issue
        assert result == 0.3

        result = round_function(0.1 + 0.1 + 0.1, 10)
        assert abs(result - 0.3) < 1e-9


# ============================================================================
# INTEGRATION CORNER CASES (Cross-function interactions)
# ============================================================================


class TestIntegrationCornerCases:
    """Corner cases involving multiple functions."""

    def test_num_then_round(self):
        """Test converting string to number then rounding."""
        value = num_function("3.141592")
        result = round_function(value, 2)
        assert result == 3.14

    def test_split_then_sort(self):
        """Test splitting then sorting."""
        parts = split_function("zebra,apple,banana", ",")
        sorted_parts = sort_function(parts)
        assert sorted_parts == ["apple", "banana", "zebra"]

    def test_range_then_reverse(self):
        """Test creating range then reversing."""
        nums = range_function(0, 5)
        reversed_nums = reverse_function(nums)
        assert reversed_nums == [4, 3, 2, 1, 0]

    def test_bool_string_combinations(self):
        """Test bool with outputs from other string functions."""
        trimmed = trim_function("  false  ")
        result = bool_function(trimmed)
        assert result is False

        replaced = replace_function("yes", "yes", "no")
        result = bool_function(replaced)
        assert result is False

    def test_regex_extract_then_num(self):
        """Test extracting number from text then converting."""
        extracted = regex_extract_function(r"(\d+\.?\d*)", "price: $42.50")
        value = num_function(extracted)
        assert value == 42.5

    def test_chained_string_operations(self):
        """Test multiple string operations in sequence."""
        text = "  HELLO, WORLD!  "
        trimmed = trim_function(text)
        parts = split_function(trimmed, ", ")
        assert len(parts) == 2
        assert parts[0] == "HELLO"
