"""Tests for new native functions: unique, flatten, type_of, slice, index_of,
base64_encode, base64_decode.

Each function is tested at the Python level (direct call) AND through the Cy
interpreter (end-to-end) to ensure registration and argument binding work.
"""

import pytest

from cy_language import Cy
from cy_language.native_functions import (
    base64_decode_function,
    base64_encode_function,
    flatten_function,
    index_of_function,
    slice_function,
    type_of_function,
    unique_function,
)

# ============================================================================
# unique()
# ============================================================================


class TestUniqueFunction:
    """Tests for unique() — deduplicate a list preserving order."""

    # --- Direct Python calls ---

    def test_unique_integers(self):
        assert unique_function([1, 2, 2, 3, 1]) == [1, 2, 3]

    def test_unique_strings(self):
        assert unique_function(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_unique_empty(self):
        assert unique_function([]) == []

    def test_unique_no_duplicates(self):
        assert unique_function([1, 2, 3]) == [1, 2, 3]

    def test_unique_all_same(self):
        assert unique_function([5, 5, 5, 5]) == [5]

    def test_unique_mixed_types(self):
        assert unique_function([1, "1", True, 1.0]) == [1, "1", True, 1.0]

    def test_unique_preserves_order(self):
        assert unique_function([3, 1, 4, 1, 5, 9, 2, 6, 5, 3]) == [
            3,
            1,
            4,
            5,
            9,
            2,
            6,
        ]

    def test_unique_with_none(self):
        assert unique_function([None, 1, None, 2]) == [None, 1, 2]

    def test_unique_with_dicts(self):
        """Unhashable items (dicts) should be deduplicated via JSON repr."""
        result = unique_function([{"a": 1}, {"b": 2}, {"a": 1}])
        assert result == [{"a": 1}, {"b": 2}]

    def test_unique_with_nested_lists(self):
        """Unhashable items (lists) should be deduplicated."""
        result = unique_function([[1, 2], [3, 4], [1, 2]])
        assert result == [[1, 2], [3, 4]]

    def test_unique_booleans(self):
        """Booleans are distinct from integers in Cy context."""
        result = unique_function([True, False, True, False])
        assert result == [True, False]

    def test_unique_invalid_type(self):
        with pytest.raises(ValueError, match="requires a list"):
            unique_function("not a list")

    # --- End-to-end Cy interpreter ---

    def test_unique_e2e(self):
        cy = Cy()
        result = cy.run_native("return unique([1, 2, 2, 3, 1])")
        assert result == [1, 2, 3]

    def test_unique_e2e_strings(self):
        cy = Cy()
        result = cy.run_native('return unique(["a", "b", "a"])')
        assert result == ["a", "b"]

    def test_unique_e2e_empty(self):
        cy = Cy()
        result = cy.run_native("return unique([])")
        assert result == []


# ============================================================================
# flatten()
# ============================================================================


class TestFlattenFunction:
    """Tests for flatten() — flatten nested lists one level deep."""

    # --- Direct Python calls ---

    def test_flatten_basic(self):
        assert flatten_function([[1, 2], [3, 4]]) == [1, 2, 3, 4]

    def test_flatten_mixed(self):
        assert flatten_function([[1], 2, [3]]) == [1, 2, 3]

    def test_flatten_empty(self):
        assert flatten_function([]) == []

    def test_flatten_empty_sublists(self):
        assert flatten_function([[], [], []]) == []

    def test_flatten_no_nesting(self):
        assert flatten_function([1, 2, 3]) == [1, 2, 3]

    def test_flatten_one_level_only(self):
        """Should only flatten one level — nested-nested stays nested."""
        assert flatten_function([[1, [2, 3]], [4]]) == [1, [2, 3], 4]

    def test_flatten_strings(self):
        """Strings are not iterable for flatten purposes."""
        assert flatten_function([["a", "b"], ["c"]]) == ["a", "b", "c"]

    def test_flatten_mixed_types(self):
        assert flatten_function([[1], "hello", [True]]) == [1, "hello", True]

    def test_flatten_single_nested(self):
        assert flatten_function([[1, 2, 3]]) == [1, 2, 3]

    def test_flatten_with_dicts(self):
        result = flatten_function([[{"a": 1}], [{"b": 2}]])
        assert result == [{"a": 1}, {"b": 2}]

    def test_flatten_with_none(self):
        assert flatten_function([[None], [1, None]]) == [None, 1, None]

    def test_flatten_invalid_type(self):
        with pytest.raises(ValueError, match="requires a list"):
            flatten_function("not a list")

    # --- End-to-end Cy interpreter ---

    def test_flatten_e2e(self):
        cy = Cy()
        result = cy.run_native("return flatten([[1, 2], [3, 4]])")
        assert result == [1, 2, 3, 4]

    def test_flatten_e2e_mixed(self):
        cy = Cy()
        result = cy.run_native("return flatten([[1], 2, [3]])")
        assert result == [1, 2, 3]

    def test_flatten_e2e_empty(self):
        cy = Cy()
        result = cy.run_native("return flatten([])")
        assert result == []


# ============================================================================
# type_of()
# ============================================================================


class TestTypeOfFunction:
    """Tests for type_of() — runtime type introspection."""

    # --- Direct Python calls ---

    def test_type_of_string(self):
        assert type_of_function("hello") == "string"

    def test_type_of_empty_string(self):
        assert type_of_function("") == "string"

    def test_type_of_integer(self):
        assert type_of_function(42) == "number"

    def test_type_of_float(self):
        assert type_of_function(3.14) == "number"

    def test_type_of_zero(self):
        assert type_of_function(0) == "number"

    def test_type_of_boolean_true(self):
        assert type_of_function(True) == "boolean"

    def test_type_of_boolean_false(self):
        assert type_of_function(False) == "boolean"

    def test_type_of_list(self):
        assert type_of_function([1, 2, 3]) == "list"

    def test_type_of_empty_list(self):
        assert type_of_function([]) == "list"

    def test_type_of_dict(self):
        assert type_of_function({"a": 1}) == "dict"

    def test_type_of_empty_dict(self):
        assert type_of_function({}) == "dict"

    def test_type_of_null(self):
        assert type_of_function(None) == "null"

    def test_type_of_negative_number(self):
        assert type_of_function(-5) == "number"

    # --- End-to-end Cy interpreter ---

    def test_type_of_e2e_string(self):
        cy = Cy()
        assert cy.run_native('return type_of("hello")') == "string"

    def test_type_of_e2e_number(self):
        cy = Cy()
        assert cy.run_native("return type_of(42)") == "number"

    def test_type_of_e2e_boolean(self):
        cy = Cy()
        assert cy.run_native("return type_of(True)") == "boolean"

    def test_type_of_e2e_list(self):
        cy = Cy()
        assert cy.run_native("return type_of([1, 2])") == "list"

    def test_type_of_e2e_dict(self):
        cy = Cy()
        assert cy.run_native('return type_of({"a": 1})') == "dict"

    def test_type_of_e2e_null(self):
        cy = Cy()
        assert cy.run_native("return type_of(null)") == "null"

    def test_type_of_e2e_conditional(self):
        """Common pattern: branch on type at runtime."""
        cy = Cy()
        script = """
val = "hello"
t = type_of(val)
result = if (t == "string") { "is string" } else { "not string" }
return result
"""
        assert cy.run_native(script) == "is string"


# ============================================================================
# slice()
# ============================================================================


class TestSliceFunction:
    """Tests for slice() — sub-range of list or string."""

    # --- Direct Python calls ---

    def test_slice_list_basic(self):
        assert slice_function([1, 2, 3, 4, 5], 1, 3) == [2, 3]

    def test_slice_list_from_start(self):
        assert slice_function([1, 2, 3, 4, 5], 0, 3) == [1, 2, 3]

    def test_slice_list_to_end(self):
        assert slice_function([1, 2, 3, 4, 5], 2) == [3, 4, 5]

    def test_slice_list_negative_start(self):
        assert slice_function([1, 2, 3, 4, 5], -2) == [4, 5]

    def test_slice_list_negative_end(self):
        assert slice_function([1, 2, 3, 4, 5], 1, -1) == [2, 3, 4]

    def test_slice_list_empty_result(self):
        assert slice_function([1, 2, 3], 2, 2) == []

    def test_slice_list_full(self):
        assert slice_function([1, 2, 3], 0) == [1, 2, 3]

    def test_slice_empty_list(self):
        assert slice_function([], 0) == []

    def test_slice_beyond_bounds(self):
        assert slice_function([1, 2, 3], 0, 100) == [1, 2, 3]

    def test_slice_string_basic(self):
        assert slice_function("hello world", 0, 5) == "hello"

    def test_slice_string_to_end(self):
        assert slice_function("hello world", 6) == "world"

    def test_slice_string_negative(self):
        assert slice_function("hello", -3) == "llo"

    def test_slice_single_element(self):
        assert slice_function([10, 20, 30], 1, 2) == [20]

    def test_slice_invalid_type(self):
        with pytest.raises(ValueError, match="requires a list or string"):
            slice_function(42, 0, 1)

    # --- End-to-end Cy interpreter ---

    def test_slice_e2e_list(self):
        cy = Cy()
        result = cy.run_native("return slice([1, 2, 3, 4, 5], 1, 3)")
        assert result == [2, 3]

    def test_slice_e2e_to_end(self):
        cy = Cy()
        result = cy.run_native("return slice([1, 2, 3, 4, 5], 2)")
        assert result == [3, 4, 5]

    def test_slice_e2e_string(self):
        cy = Cy()
        result = cy.run_native('return slice("hello world", 0, 5)')
        assert result == "hello"

    def test_slice_e2e_negative(self):
        cy = Cy()
        result = cy.run_native("return slice([1, 2, 3, 4, 5], -2)")
        assert result == [4, 5]


# ============================================================================
# index_of()
# ============================================================================


class TestIndexOfFunction:
    """Tests for index_of() — find first index of value."""

    # --- Direct Python calls ---

    def test_index_of_list_found(self):
        assert index_of_function([10, 20, 30], 20) == 1

    def test_index_of_list_first_element(self):
        assert index_of_function([10, 20, 30], 10) == 0

    def test_index_of_list_last_element(self):
        assert index_of_function([10, 20, 30], 30) == 2

    def test_index_of_list_not_found(self):
        assert index_of_function([10, 20, 30], 99) == -1

    def test_index_of_list_duplicate_returns_first(self):
        assert index_of_function([1, 2, 3, 2, 1], 2) == 1

    def test_index_of_empty_list(self):
        assert index_of_function([], 1) == -1

    def test_index_of_string_found(self):
        assert index_of_function("hello world", "world") == 6

    def test_index_of_string_at_start(self):
        assert index_of_function("hello", "hel") == 0

    def test_index_of_string_not_found(self):
        assert index_of_function("hello", "xyz") == -1

    def test_index_of_string_single_char(self):
        assert index_of_function("abcde", "c") == 2

    def test_index_of_string_empty_needle(self):
        assert index_of_function("hello", "") == 0

    def test_index_of_list_with_none(self):
        assert index_of_function([1, None, 3], None) == 1

    def test_index_of_list_with_string(self):
        assert index_of_function(["a", "b", "c"], "b") == 1

    def test_index_of_list_with_bool(self):
        assert index_of_function([False, True, False], True) == 1

    def test_index_of_invalid_type(self):
        with pytest.raises(ValueError, match="requires a list or string"):
            index_of_function(42, 1)

    # --- End-to-end Cy interpreter ---

    def test_index_of_e2e_list(self):
        cy = Cy()
        result = cy.run_native("return index_of([10, 20, 30], 20)")
        assert result == 1

    def test_index_of_e2e_not_found(self):
        cy = Cy()
        result = cy.run_native("return index_of([1, 2, 3], 99)")
        assert result == -1

    def test_index_of_e2e_string(self):
        cy = Cy()
        result = cy.run_native('return index_of("hello world", "world")')
        assert result == 6

    def test_index_of_e2e_conditional(self):
        """Common pattern: check if found before using index."""
        cy = Cy()
        script = """
items = ["apple", "banana", "cherry"]
idx = index_of(items, "banana")
result = if (idx >= 0) { "found" } else { "missing" }
return result
"""
        assert cy.run_native(script) == "found"


# ============================================================================
# base64_encode() / base64_decode()
# ============================================================================


class TestBase64Functions:
    """Tests for base64_encode() and base64_decode()."""

    # --- Direct Python calls: encode ---

    def test_encode_basic(self):
        assert base64_encode_function("hello") == "aGVsbG8="

    def test_encode_empty(self):
        assert base64_encode_function("") == ""

    def test_encode_credentials(self):
        assert base64_encode_function("user:pass") == "dXNlcjpwYXNz"

    def test_encode_unicode(self):
        result = base64_encode_function("hello 🌍")
        assert base64_decode_function(result) == "hello 🌍"

    def test_encode_long_string(self):
        text = "A" * 1000
        encoded = base64_encode_function(text)
        assert base64_decode_function(encoded) == text

    def test_encode_special_chars(self):
        text = "line1\nline2\ttab"
        encoded = base64_encode_function(text)
        assert base64_decode_function(encoded) == text

    def test_encode_invalid_type(self):
        with pytest.raises(ValueError, match="requires a string"):
            base64_encode_function(42)

    # --- Direct Python calls: decode ---

    def test_decode_basic(self):
        assert base64_decode_function("aGVsbG8=") == "hello"

    def test_decode_empty(self):
        assert base64_decode_function("") == ""

    def test_decode_credentials(self):
        assert base64_decode_function("dXNlcjpwYXNz") == "user:pass"

    def test_decode_invalid_base64(self):
        with pytest.raises(ValueError, match="invalid base64"):
            base64_decode_function("not-valid-base64!!!")

    def test_decode_invalid_type(self):
        with pytest.raises(ValueError, match="requires a string"):
            base64_decode_function(123)

    # --- Roundtrip ---

    def test_roundtrip(self):
        original = "The quick brown fox jumps over the lazy dog"
        assert base64_decode_function(base64_encode_function(original)) == original

    def test_roundtrip_json(self):
        payload = '{"user": "admin", "role": "root"}'
        encoded = base64_encode_function(payload)
        decoded = base64_decode_function(encoded)
        assert decoded == payload

    # --- End-to-end Cy interpreter ---

    def test_encode_e2e(self):
        cy = Cy()
        result = cy.run_native('return base64_encode("hello")')
        assert result == "aGVsbG8="

    def test_decode_e2e(self):
        cy = Cy()
        result = cy.run_native('return base64_decode("aGVsbG8=")')
        assert result == "hello"

    def test_roundtrip_e2e(self):
        cy = Cy()
        script = """
original = "secret data"
encoded = base64_encode(original)
decoded = base64_decode(encoded)
return decoded
"""
        assert cy.run_native(script) == "secret data"

    def test_encode_decode_e2e_security_use_case(self):
        """Realistic: decode a suspicious base64 payload."""
        cy = Cy()
        script = """
suspicious = "cG93ZXJzaGVsbCAtZW5jIEdFVA=="
decoded = base64_decode(suspicious)
return decoded
"""
        assert cy.run_native(script) == "powershell -enc GET"
