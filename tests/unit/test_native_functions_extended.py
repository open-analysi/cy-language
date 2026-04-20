"""Unit tests for native functions.

Tests for the 16 new native functions added in
- Type conversion: num(), bool()
- Time: now()
- Iteration: range()
- String: split(), replace(), trim(), regex_match(), regex_extract()
- Array: reverse(), sort()
- Math: abs(), min(), max(), round()
"""

import re
from datetime import datetime

import pytest

from cy_language.native_functions import (
    abs_function,
    bool_function,
    keys_function,
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
    url_decode_function,
    url_encode_function,
    values_function,
)

# ============================================================================
# TYPE CONVERSION TESTS
# ============================================================================


class TestNumFunction:
    """Test cases for num() function."""

    def test_num_with_integer(self):
        """Test num() with integer input."""
        assert num_function(42) == 42.0
        assert num_function(0) == 0.0
        assert num_function(-100) == -100.0

    def test_num_with_float(self):
        """Test num() with float input."""
        assert num_function(3.14) == 3.14
        assert num_function(-2.5) == -2.5
        assert num_function(0.0) == 0.0

    def test_num_with_string_integer(self):
        """Test num() with string representation of integer."""
        assert num_function("42") == 42.0
        assert num_function("-100") == -100.0
        assert num_function("0") == 0.0

    def test_num_with_string_float(self):
        """Test num() with string representation of float."""
        assert num_function("3.14") == 3.14
        assert num_function("-2.5") == -2.5
        assert num_function("0.0") == 0.0

    def test_num_with_string_whitespace(self):
        """Test num() with string containing whitespace."""
        assert num_function("  42  ") == 42.0
        assert num_function("\t3.14\n") == 3.14

    def test_num_with_boolean(self):
        """Test num() with boolean input."""
        assert num_function(True) == 1.0
        assert num_function(False) == 0.0

    def test_num_with_invalid_string(self):
        """Test num() with invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot convert string"):
            num_function("not a number")

        with pytest.raises(ValueError, match="Cannot convert string"):
            num_function("abc123")

    def test_num_with_invalid_type(self):
        """Test num() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Cannot convert"):
            num_function([1, 2, 3])

        with pytest.raises(ValueError, match="Cannot convert"):
            num_function({"key": "value"})

        with pytest.raises(ValueError, match="Cannot convert"):
            num_function(None)


class TestBoolFunction:
    """Test cases for bool() function."""

    def test_bool_with_boolean(self):
        """Test bool() with boolean input."""
        assert bool_function(True) is True
        assert bool_function(False) is False

    def test_bool_with_string_true(self):
        """Test bool() with string representations of True."""
        assert bool_function("true") is True
        assert bool_function("True") is True
        assert bool_function("TRUE") is True
        assert bool_function("1") is True
        assert bool_function("yes") is True

    def test_bool_with_string_false(self):
        """Test bool() with string representations of False."""
        assert bool_function("false") is False
        assert bool_function("False") is False
        assert bool_function("FALSE") is False
        assert bool_function("0") is False
        assert bool_function("no") is False
        assert bool_function("") is False

    def test_bool_with_string_whitespace(self):
        """Test bool() with whitespace handling."""
        assert bool_function("  true  ") is True
        assert bool_function("\tfalse\n") is False
        assert bool_function("   ") is False  # whitespace-only is falsy

    def test_bool_with_string_other(self):
        """Test bool() with other strings (Python truthiness)."""
        assert bool_function("hello") is True  # Non-empty string
        assert bool_function("anything") is True

    def test_bool_with_numbers(self):
        """Test bool() with numbers (Python truthiness)."""
        assert bool_function(1) is True
        assert bool_function(0) is False
        assert bool_function(42) is True
        assert bool_function(-1) is True
        assert bool_function(3.14) is True
        assert bool_function(0.0) is False

    def test_bool_with_collections(self):
        """Test bool() with collections (Python truthiness)."""
        assert bool_function([1, 2, 3]) is True
        assert bool_function([]) is False
        assert bool_function({"key": "value"}) is True
        assert bool_function({}) is False

    def test_bool_with_none(self):
        """Test bool() with None."""
        assert bool_function(None) is False


# ============================================================================
# TIME TESTS
# ============================================================================


class TestNowFunction:
    """Test cases for now() function."""

    def test_now_utc_default(self):
        """Test now() with default UTC timezone."""
        result = now_function()

        # Should be in ISO 8601 format with Z suffix
        assert result.endswith("Z")
        assert "T" in result

        # Should be parseable as datetime
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert isinstance(dt, datetime)

    def test_now_utc_explicit(self):
        """Test now() with explicit UTC timezone."""
        result = now_function("UTC")

        assert result.endswith("Z")
        assert "T" in result

    def test_now_with_timezone(self):
        """Test now() with specific timezone."""
        # This test might fail if tzdata is not available
        try:
            result = now_function("US/Pacific")
            assert "T" in result
            # Should have timezone offset, not Z
            assert not result.endswith("Z")
        except ValueError:
            pytest.skip("Timezone data not available")

    def test_now_invalid_timezone(self):
        """Test now() with invalid timezone raises ValueError."""
        with pytest.raises(ValueError, match="Invalid timezone"):
            now_function("Invalid/Timezone")

    def test_now_format_structure(self):
        """Test now() returns correct ISO 8601 format structure."""
        result = now_function()

        # Should match YYYY-MM-DDTHH:MM:SSZ pattern
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        assert re.match(pattern, result)


# ============================================================================
# ITERATION TESTS
# ============================================================================


class TestRangeFunction:
    """Test cases for range() function."""

    def test_range_basic(self):
        """Test range() with basic parameters."""
        assert range_function(0, 5) == [0, 1, 2, 3, 4]
        assert range_function(1, 6) == [1, 2, 3, 4, 5]

    def test_range_with_step(self):
        """Test range() with custom step."""
        assert range_function(0, 10, 2) == [0, 2, 4, 6, 8]
        assert range_function(1, 10, 3) == [1, 4, 7]

    def test_range_negative_step(self):
        """Test range() with negative step."""
        assert range_function(5, 0, -1) == [5, 4, 3, 2, 1]
        assert range_function(10, 0, -2) == [10, 8, 6, 4, 2]

    def test_range_empty(self):
        """Test range() that produces empty list."""
        assert range_function(5, 5) == []
        assert range_function(5, 0) == []  # Invalid without negative step

    def test_range_negative_numbers(self):
        """Test range() with negative numbers."""
        assert range_function(-5, 0) == [-5, -4, -3, -2, -1]
        assert range_function(-10, -5) == [-10, -9, -8, -7, -6]

    def test_range_zero_step_error(self):
        """Test range() with step=0 raises ValueError."""
        with pytest.raises(ValueError, match="step argument must not be zero"):
            range_function(0, 10, 0)

    def test_range_large(self):
        """Test range() with large range."""
        result = range_function(0, 1000)
        assert len(result) == 1000
        assert result[0] == 0
        assert result[-1] == 999

    def test_range_single_arg(self):
        """Test range(n) as shorthand for range(0, n)."""
        assert range_function(5) == [0, 1, 2, 3, 4]
        assert range_function(0) == []
        assert range_function(1) == [0]
        assert range_function(10) == list(range(10))

    def test_range_single_arg_end_to_end(self):
        """Test range(n) works through the Cy interpreter."""
        from cy_language import Cy

        cy = Cy()
        result = cy.run_native("return range(5)")
        assert result == [0, 1, 2, 3, 4]


# ============================================================================
# STRING TESTS
# ============================================================================


class TestSplitFunction:
    """Test cases for split() function."""

    def test_split_default_delimiter(self):
        """Test split() with default space delimiter."""
        assert split_function("hello world") == ["hello", "world"]
        assert split_function("one two three") == ["one", "two", "three"]

    def test_split_custom_delimiter(self):
        """Test split() with custom delimiter."""
        assert split_function("a,b,c", ",") == ["a", "b", "c"]
        assert split_function("a|b|c", "|") == ["a", "b", "c"]

    def test_split_empty_parts(self):
        """Test split() with empty parts."""
        assert split_function("a,,c", ",") == ["a", "", "c"]
        assert split_function("one  two", " ") == ["one", "", "two"]

    def test_split_no_delimiter(self):
        """Test split() when delimiter not found."""
        assert split_function("hello", ",") == ["hello"]

    def test_split_empty_string(self):
        """Test split() with empty string."""
        assert split_function("") == [""]
        assert split_function("", ",") == [""]

    def test_split_invalid_type(self):
        """Test split() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires string"):
            split_function(123)  # type: ignore

        with pytest.raises(ValueError, match="delimiter must be string"):
            split_function("hello", 123)  # type: ignore


class TestReplaceFunction:
    """Test cases for replace() function."""

    def test_replace_basic(self):
        """Test replace() with basic replacement."""
        assert replace_function("hello world", "world", "there") == "hello there"
        assert replace_function("foo bar foo", "foo", "baz") == "baz bar baz"

    def test_replace_all_occurrences(self):
        """Test replace() replaces all occurrences."""
        assert replace_function("foo foo foo", "foo", "bar") == "bar bar bar"

    def test_replace_not_found(self):
        """Test replace() when old substring not found."""
        assert replace_function("hello", "xyz", "abc") == "hello"

    def test_replace_empty_string(self):
        """Test replace() with empty strings."""
        # Python's replace("hello", "", "x") inserts "x" between every character
        assert replace_function("hello", "", "x") == "xhxexlxlxox"
        assert replace_function("", "a", "b") == ""

    def test_replace_case_sensitive(self):
        """Test replace() is case-sensitive."""
        assert replace_function("Hello", "hello", "hi") == "Hello"

    def test_replace_invalid_type(self):
        """Test replace() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires string"):
            replace_function(123, "a", "b")  # type: ignore

        with pytest.raises(ValueError, match="old must be string"):
            replace_function("hello", 123, "b")  # type: ignore

        with pytest.raises(ValueError, match="new must be string"):
            replace_function("hello", "a", 123)  # type: ignore


class TestTrimFunction:
    """Test cases for trim() function."""

    def test_trim_spaces(self):
        """Test trim() with spaces."""
        assert trim_function("  hello  ") == "hello"
        assert trim_function("hello  ") == "hello"
        assert trim_function("  hello") == "hello"

    def test_trim_tabs_newlines(self):
        """Test trim() with tabs and newlines."""
        assert trim_function("\thello\t") == "hello"
        assert trim_function("\nhello\n") == "hello"
        assert trim_function("\n\t hello \t\n") == "hello"

    def test_trim_no_whitespace(self):
        """Test trim() with no whitespace."""
        assert trim_function("hello") == "hello"

    def test_trim_empty_string(self):
        """Test trim() with empty string."""
        assert trim_function("") == ""

    def test_trim_only_whitespace(self):
        """Test trim() with only whitespace."""
        assert trim_function("   ") == ""
        assert trim_function("\n\t") == ""

    def test_trim_invalid_type(self):
        """Test trim() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires string"):
            trim_function(123)  # type: ignore


class TestRegexMatchFunction:
    """Test cases for regex_match() function."""

    def test_regex_match_found(self):
        """Test regex_match() when pattern matches."""
        assert regex_match_function(r"\d+", "abc123") is True
        assert regex_match_function(r"[A-Z]+", "Hello") is True

    def test_regex_match_not_found(self):
        """Test regex_match() when pattern doesn't match."""
        assert regex_match_function(r"\d+", "abc") is False
        assert regex_match_function(r"[A-Z]+", "hello") is False

    def test_regex_match_anchors(self):
        """Test regex_match() with anchors."""
        assert regex_match_function(r"^\d+$", "123") is True
        assert regex_match_function(r"^\d+$", "abc123") is False
        assert regex_match_function(r"^\d+$", "123abc") is False

    def test_regex_match_complex_patterns(self):
        """Test regex_match() with complex patterns."""
        # Email pattern
        assert (
            regex_match_function(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "test@example.com",
            )
            is True
        )

        # IP address pattern
        assert (
            regex_match_function(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "192.168.1.1")
            is True
        )

    def test_regex_match_invalid_pattern(self):
        """Test regex_match() with invalid regex raises ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            regex_match_function(r"[", "text")

    def test_regex_match_invalid_type(self):
        """Test regex_match() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="pattern must be string"):
            regex_match_function(123, "text")  # type: ignore

        with pytest.raises(ValueError, match="text must be string"):
            regex_match_function(r"\d+", 123)  # type: ignore


class TestRegexExtractFunction:
    """Test cases for regex_extract() function."""

    def test_regex_extract_found(self):
        """Test regex_extract() when pattern matches."""
        assert regex_extract_function(r"\d+", "Price: 123 dollars") == "123"
        assert regex_extract_function(r"[A-Z]+", "hello WORLD") == "WORLD"

    def test_regex_extract_not_found(self):
        """Test regex_extract() when pattern doesn't match."""
        assert regex_extract_function(r"\d+", "no numbers") == ""
        assert regex_extract_function(r"[A-Z]+", "lowercase") == ""

    def test_regex_extract_with_group(self):
        """Test regex_extract() with capture group returns first group."""
        assert regex_extract_function(r"(\d+)", "Price: 123") == "123"
        assert regex_extract_function(r"Name: (\w+)", "Name: Alice") == "Alice"

    def test_regex_extract_without_group(self):
        """Test regex_extract() without group returns full match."""
        assert regex_extract_function(r"\d+", "abc123def") == "123"

    def test_regex_extract_multiple_groups(self):
        """Test regex_extract() with multiple groups returns first group."""
        result = regex_extract_function(r"(\d+)-(\w+)", "123-abc")
        assert result == "123"  # First group only

    def test_regex_extract_first_match(self):
        """Test regex_extract() returns only first match."""
        assert regex_extract_function(r"\d+", "123 and 456") == "123"

    def test_regex_extract_invalid_pattern(self):
        """Test regex_extract() with invalid regex raises ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            regex_extract_function(r"[", "text")

    def test_regex_extract_invalid_type(self):
        """Test regex_extract() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="pattern must be string"):
            regex_extract_function(123, "text")  # type: ignore

        with pytest.raises(ValueError, match="text must be string"):
            regex_extract_function(r"\d+", 123)  # type: ignore


# ============================================================================
# ARRAY TESTS
# ============================================================================


class TestReverseFunction:
    """Test cases for reverse() function."""

    def test_reverse_numbers(self):
        """Test reverse() with numbers."""
        assert reverse_function([1, 2, 3]) == [3, 2, 1]
        assert reverse_function([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

    def test_reverse_strings(self):
        """Test reverse() with strings."""
        assert reverse_function(["a", "b", "c"]) == ["c", "b", "a"]

    def test_reverse_empty(self):
        """Test reverse() with empty list."""
        assert reverse_function([]) == []

    def test_reverse_single_element(self):
        """Test reverse() with single element."""
        assert reverse_function([42]) == [42]

    def test_reverse_mixed_types(self):
        """Test reverse() with mixed types."""
        assert reverse_function([1, "two", 3.0]) == [3.0, "two", 1]

    def test_reverse_does_not_modify_original(self):
        """Test reverse() doesn't modify original list."""
        original = [1, 2, 3]
        result = reverse_function(original)
        assert result == [3, 2, 1]
        assert original == [1, 2, 3]  # Original unchanged

    def test_reverse_invalid_type(self):
        """Test reverse() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires list"):
            reverse_function("not a list")  # type: ignore


class TestSortFunction:
    """Test cases for sort() function."""

    def test_sort_numbers(self):
        """Test sort() with numbers."""
        assert sort_function([3, 1, 2]) == [1, 2, 3]
        assert sort_function([5, 2, 8, 1, 9]) == [1, 2, 5, 8, 9]

    def test_sort_strings(self):
        """Test sort() with strings."""
        assert sort_function(["c", "a", "b"]) == ["a", "b", "c"]
        assert sort_function(["zebra", "apple", "mango"]) == ["apple", "mango", "zebra"]

    def test_sort_empty(self):
        """Test sort() with empty list."""
        assert sort_function([]) == []

    def test_sort_single_element(self):
        """Test sort() with single element."""
        assert sort_function([42]) == [42]

    def test_sort_already_sorted(self):
        """Test sort() with already sorted list."""
        assert sort_function([1, 2, 3]) == [1, 2, 3]

    def test_sort_reverse_sorted(self):
        """Test sort() with reverse sorted list."""
        assert sort_function([3, 2, 1]) == [1, 2, 3]

    def test_sort_negative_numbers(self):
        """Test sort() with negative numbers."""
        assert sort_function([-1, -3, -2]) == [-3, -2, -1]
        assert sort_function([3, -1, 2, -3]) == [-3, -1, 2, 3]

    def test_sort_floats(self):
        """Test sort() with floats."""
        assert sort_function([3.14, 1.0, 2.5]) == [1.0, 2.5, 3.14]

    def test_sort_does_not_modify_original(self):
        """Test sort() doesn't modify original list."""
        original = [3, 1, 2]
        result = sort_function(original)
        assert result == [1, 2, 3]
        assert original == [3, 1, 2]  # Original unchanged

    def test_sort_mixed_types_error(self):
        """Test sort() with mixed types raises ValueError."""
        with pytest.raises(ValueError, match="Cannot sort list"):
            sort_function([1, "two", 3])  # type: ignore

    def test_sort_invalid_type(self):
        """Test sort() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires list"):
            sort_function("not a list")  # type: ignore


# ============================================================================
# MATH TESTS
# ============================================================================


class TestAbsFunction:
    """Test cases for abs() function."""

    def test_abs_positive(self):
        """Test abs() with positive numbers."""
        assert abs_function(5) == 5
        assert abs_function(3.14) == 3.14

    def test_abs_negative(self):
        """Test abs() with negative numbers."""
        assert abs_function(-5) == 5
        assert abs_function(-3.14) == 3.14

    def test_abs_zero(self):
        """Test abs() with zero."""
        assert abs_function(0) == 0
        assert abs_function(0.0) == 0.0

    def test_abs_invalid_type(self):
        """Test abs() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires number"):
            abs_function("not a number")  # type: ignore


class TestMinFunction:
    """Test cases for min() function."""

    def test_min_basic(self):
        """Test min() with basic numbers."""
        assert min_function([1, 2, 3]) == 1
        assert min_function([5, 2, 8, 1, 9]) == 1

    def test_min_negative(self):
        """Test min() with negative numbers."""
        assert min_function([-1, -2, -3]) == -3
        assert min_function([3, -1, 2]) == -1

    def test_min_floats(self):
        """Test min() with floats."""
        assert min_function([5.5, 2.1, 3.7]) == 2.1

    def test_min_single_element(self):
        """Test min() with single element."""
        assert min_function([42]) == 42

    def test_min_empty_list_error(self):
        """Test min() with empty list raises ValueError."""
        with pytest.raises(ValueError, match="requires non-empty list"):
            min_function([])

    def test_min_invalid_type(self):
        """Test min() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires list"):
            min_function(123)  # type: ignore


class TestMaxFunction:
    """Test cases for max() function."""

    def test_max_basic(self):
        """Test max() with basic numbers."""
        assert max_function([1, 2, 3]) == 3
        assert max_function([5, 2, 8, 1, 9]) == 9

    def test_max_negative(self):
        """Test max() with negative numbers."""
        assert max_function([-1, -2, -3]) == -1
        assert max_function([3, -1, 2]) == 3

    def test_max_floats(self):
        """Test max() with floats."""
        assert max_function([5.5, 2.1, 3.7]) == 5.5

    def test_max_single_element(self):
        """Test max() with single element."""
        assert max_function([42]) == 42

    def test_max_empty_list_error(self):
        """Test max() with empty list raises ValueError."""
        with pytest.raises(ValueError, match="requires non-empty list"):
            max_function([])

    def test_max_invalid_type(self):
        """Test max() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires list"):
            max_function(123)  # type: ignore


class TestRoundFunction:
    """Test cases for round() function."""

    def test_round_no_decimals(self):
        """Test round() with no decimal places (default)."""
        assert round_function(3.14159) == 3.0
        assert round_function(2.7) == 3.0
        assert round_function(2.5) == 2.0  # Python's banker's rounding

    def test_round_with_decimals(self):
        """Test round() with specified decimal places."""
        assert round_function(3.14159, 2) == 3.14
        assert round_function(3.14159, 3) == 3.142
        assert round_function(3.14159, 4) == 3.1416

    def test_round_zero_decimals(self):
        """Test round() with 0 decimal places."""
        assert round_function(3.7, 0) == 4.0

    def test_round_already_rounded(self):
        """Test round() with already rounded number."""
        assert round_function(3.0, 2) == 3.0

    def test_round_negative_numbers(self):
        """Test round() with negative numbers."""
        assert round_function(-3.14159, 2) == -3.14
        assert round_function(-2.7) == -3.0

    def test_round_invalid_type(self):
        """Test round() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires number"):
            round_function("not a number", 2)  # type: ignore

    def test_round_invalid_decimals(self):
        """Test round() with invalid decimals parameter."""
        with pytest.raises(ValueError, match="decimals must be integer"):
            round_function(3.14, 2.5)  # type: ignore

        with pytest.raises(ValueError, match="decimals must be non-negative"):
            round_function(3.14, -1)


# ============================================================================
# URL FUNCTION TESTS
# ============================================================================


class TestUrlEncodeFunction:
    """Test cases for url_encode() function."""

    def test_url_encode_basic(self):
        """Test url_encode() with basic strings."""
        assert url_encode_function("hello world") == "hello%20world"
        assert url_encode_function("foo bar") == "foo%20bar"

    def test_url_encode_special_characters(self):
        """Test url_encode() with special URL characters."""
        assert url_encode_function("foo@bar.com") == "foo%40bar.com"
        assert url_encode_function("a=b&c=d") == "a%3Db%26c%3Dd"
        assert url_encode_function("hello/world") == "hello%2Fworld"

    def test_url_encode_query_string(self):
        """Test url_encode() with query string components."""
        assert url_encode_function("key=value") == "key%3Dvalue"
        assert url_encode_function("search?q=test") == "search%3Fq%3Dtest"

    def test_url_encode_unicode(self):
        """Test url_encode() with Unicode characters."""
        assert url_encode_function("café") == "caf%C3%A9"
        assert url_encode_function("北京") == "%E5%8C%97%E4%BA%AC"

    def test_url_encode_already_encoded(self):
        """Test url_encode() re-encodes already encoded strings."""
        # Double encoding
        assert url_encode_function("hello%20world") == "hello%2520world"

    def test_url_encode_empty_string(self):
        """Test url_encode() with empty string."""
        assert url_encode_function("") == ""

    def test_url_encode_invalid_type(self):
        """Test url_encode() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires string"):
            url_encode_function(123)  # type: ignore


class TestUrlDecodeFunction:
    """Test cases for url_decode() function."""

    def test_url_decode_basic(self):
        """Test url_decode() with basic encoded strings."""
        assert url_decode_function("hello%20world") == "hello world"
        assert url_decode_function("foo%20bar") == "foo bar"

    def test_url_decode_special_characters(self):
        """Test url_decode() with encoded special characters."""
        assert url_decode_function("foo%40bar.com") == "foo@bar.com"
        assert url_decode_function("a%3Db%26c%3Dd") == "a=b&c=d"
        assert url_decode_function("hello%2Fworld") == "hello/world"

    def test_url_decode_unicode(self):
        """Test url_decode() with encoded Unicode."""
        assert url_decode_function("caf%C3%A9") == "café"
        assert url_decode_function("%E5%8C%97%E4%BA%AC") == "北京"

    def test_url_decode_plus_signs(self):
        """Test url_decode() with plus signs (not converted to spaces)."""
        # urllib.parse.unquote does not convert + to space
        assert url_decode_function("hello+world") == "hello+world"

    def test_url_decode_no_encoding(self):
        """Test url_decode() with non-encoded string."""
        assert url_decode_function("hello") == "hello"
        assert url_decode_function("test123") == "test123"

    def test_url_decode_empty_string(self):
        """Test url_decode() with empty string."""
        assert url_decode_function("") == ""

    def test_url_decode_roundtrip(self):
        """Test url_encode() and url_decode() are inverse operations."""
        test_strings = [
            "hello world",
            "foo@bar.com",
            "a=b&c=d",
            "café",
            "test?query=value",
        ]
        for original in test_strings:
            encoded = url_encode_function(original)
            decoded = url_decode_function(encoded)
            assert decoded == original

    def test_url_decode_invalid_type(self):
        """Test url_decode() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires string"):
            url_decode_function(123)  # type: ignore


# ============================================================================
# DICT FUNCTION TESTS
# ============================================================================


class TestKeysFunction:
    """Test cases for keys() function."""

    def test_keys_basic(self):
        """Test keys() with basic dict."""
        assert keys_function({"a": 1, "b": 2, "c": 3}) == ["a", "b", "c"]
        assert keys_function({"name": "Alice", "age": 30}) == ["name", "age"]

    def test_keys_empty_dict(self):
        """Test keys() with empty dict."""
        assert keys_function({}) == []

    def test_keys_single_item(self):
        """Test keys() with single item dict."""
        assert keys_function({"key": "value"}) == ["key"]

    def test_keys_various_types(self):
        """Test keys() with various key types."""
        # String keys
        assert keys_function({"a": 1, "b": 2}) == ["a", "b"]

        # Mixed value types (keys still strings)
        result = keys_function(
            {"str": "text", "num": 42, "list": [1, 2], "dict": {"nested": True}}
        )
        assert result == ["str", "num", "list", "dict"]

    def test_keys_order_preserved(self):
        """Test keys() preserves insertion order (Python 3.7+)."""
        data = {"z": 1, "a": 2, "m": 3}
        assert keys_function(data) == ["z", "a", "m"]

    def test_keys_invalid_type(self):
        """Test keys() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires dict"):
            keys_function([1, 2, 3])  # type: ignore

        with pytest.raises(ValueError, match="requires dict"):
            keys_function("not a dict")  # type: ignore


class TestValuesFunction:
    """Test cases for values() function."""

    def test_values_basic(self):
        """Test values() with basic dict."""
        assert values_function({"a": 1, "b": 2, "c": 3}) == [1, 2, 3]
        assert values_function({"name": "Alice", "age": 30}) == ["Alice", 30]

    def test_values_empty_dict(self):
        """Test values() with empty dict."""
        assert values_function({}) == []

    def test_values_single_item(self):
        """Test values() with single item dict."""
        assert values_function({"key": "value"}) == ["value"]

    def test_values_various_types(self):
        """Test values() with various value types."""
        data = {
            "str": "text",
            "num": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        result = values_function(data)
        assert result == ["text", 42, 3.14, True, None, [1, 2, 3], {"nested": "value"}]

    def test_values_duplicates(self):
        """Test values() with duplicate values."""
        assert values_function({"a": 1, "b": 1, "c": 1}) == [1, 1, 1]
        assert values_function({"x": "same", "y": "same"}) == ["same", "same"]

    def test_values_order_preserved(self):
        """Test values() preserves insertion order (Python 3.7+)."""
        data = {"z": 100, "a": 200, "m": 300}
        assert values_function(data) == [100, 200, 300]

    def test_values_invalid_type(self):
        """Test values() with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="requires dict"):
            values_function([1, 2, 3])  # type: ignore

        with pytest.raises(ValueError, match="requires dict"):
            values_function("not a dict")  # type: ignore
