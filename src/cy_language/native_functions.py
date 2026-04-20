"""Native functions for the Cy language.

This module implements the core native functions that are available
to all Cy scripts by default.
"""

import base64
import ipaddress
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Union

from cy_language.ui.tools import (
    default_registry,
    register_tool,
    register_tool_with_alias,
)


@register_tool(default_registry, "len", "Return the length of a string, list, or dict")
def len_function(arg: Any) -> int:
    """Return the length of a string, list, or dictionary.

    Args:
        arg: The argument to get the length of

    Returns:
        Length of the string, list, or dictionary, otherwise 0
    """
    if isinstance(arg, (list, str, dict)):
        return len(arg)
    return 0


# Domain aliases for len — polymorphic but users expect it under each namespace
default_registry.register("str::len", len_function, "Return the length of a string")
default_registry.register("list::len", len_function, "Return the length of a list")
default_registry.register("dict::len", len_function, "Return the length of a dict")


@register_tool(default_registry, "sum", "Sum all numbers in a list")
def sum_function(items: list[Union[int, float]]) -> Union[int, float]:
    """Sum all numbers in a list.

    Args:
        items: List of numbers to sum

    Returns:
        Sum of all numbers in the list, or 0 if empty or non-numeric
    """
    if not isinstance(items, list):
        return 0

    try:
        return sum(items)
    except (TypeError, ValueError):
        # If items contains non-numeric values, return 0
        return 0


# Domain alias for sum
default_registry.register("list::sum", sum_function, "Sum all numbers in a list")


@register_tool_with_alias(
    default_registry, "str", "type::str", "Convert a value to a string"
)
def str_function(value: Any) -> str:
    """Convert a value to its string representation.

    Args:
        value: The value to convert to a string

    Returns:
        String representation of the value
    """
    return str(value)


@register_tool_with_alias(
    default_registry, "int", "type::int", "Convert a value to an integer"
)
def int_function(value: Any) -> int:
    """Convert a value to an integer.

    Args:
        value: The value to convert to an integer (string or number)

    Returns:
        Integer representation of the value

    Raises:
        ValueError: If value cannot be converted to integer
    """
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot convert {type(value).__name__} to int: {e}")


@register_tool(
    default_registry,
    "log",
    "Log messages without interfering with output",
)
def log(message: Any) -> str:
    """Log a message to captured_logs list or stderr.

    This function logs information without interfering with the program's
    main output. If captured_logs list is provided to Cy interpreter,
    messages are appended there. Otherwise, falls back to stderr output.

    Args:
        message: The message to log

    Returns:
        The string that was logged
    """
    # Convert message to string representation
    message_str = str(message)

    # Try to get captured_logs from thread-local context
    import threading

    current_thread = threading.current_thread()
    cy_context = getattr(current_thread, "cy_context", None)

    if (
        cy_context
        and hasattr(cy_context, "captured_logs")
        and cy_context.captured_logs is not None
    ):
        # Guard: limit log entries to prevent memory issues (default 1000)
        max_logs = getattr(cy_context, "max_captured_logs", 1000)
        if len(cy_context.captured_logs) >= max_logs:
            # Add truncation marker once, then silently drop
            if (
                not cy_context.captured_logs
                or cy_context.captured_logs[-1].get("message")
                != "[LOG TRUNCATED — max entries reached]"
            ):
                import time

                cy_context.captured_logs.append(
                    {
                        "ts": time.time(),
                        "message": "[LOG TRUNCATED — max entries reached]",
                    }
                )
            return message_str

        import time

        cy_context.captured_logs.append(
            {
                "ts": time.time(),
                "message": message_str,
            }
        )
    else:
        import sys

        sys.stderr.write(f"LOG: {message_str}\n")
        sys.stderr.flush()

    return message_str


@register_tool_with_alias(
    default_registry,
    "from_json",
    "json::parse",
    "Parse JSON string to structured data (dict or list)",
)
def from_json(json_str: str) -> Union[dict, list, Any]:
    """Parse a JSON string into structured data.

    Args:
        json_str: The JSON string to parse

    Returns:
        The parsed JSON data structure (dict or list)

    Raises:
        ValueError: If JSON parsing fails
    """
    # Handle non-string inputs
    if not isinstance(json_str, str):
        raise ValueError("from_json() requires a string argument")

    # Handle empty string
    if not json_str.strip():
        return {}

    # Parse JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e!s}")


@register_tool_with_alias(
    default_registry,
    "to_json",
    "json::stringify",
    "Convert data structure to JSON string",
)
def to_json(data: Any, indent: int | None = None) -> str:
    """Convert a data structure to a JSON string.

    Args:
        data: The data structure to convert (dict, list, etc.)
        indent: Optional indentation for pretty-printing (default: None for compact)

    Returns:
        JSON string representation of the data

    Raises:
        ValueError: If data cannot be serialized to JSON
    """
    try:
        return json.dumps(data, indent=indent)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot convert to JSON: {e!s}")


@register_tool_with_alias(
    default_registry, "uppercase", "str::uppercase", "Convert a string to uppercase"
)
def uppercase(text: str) -> str:
    """Convert a string to uppercase.

    Args:
        text: The string to convert

    Returns:
        The uppercase version of the string
    """
    return str(text).upper()


@register_tool_with_alias(
    default_registry, "lowercase", "str::lowercase", "Convert a string to lowercase"
)
def lowercase(text: str) -> str:
    """Convert a string to lowercase.

    Args:
        text: The string to convert

    Returns:
        The lowercase version of the string
    """
    return str(text).lower()


@register_tool_with_alias(
    default_registry, "join", "str::join", "Join a list of items with a separator"
)
def join(items: list[Any], separator: str = ", ") -> str:
    """Join a list of items with a separator.

    Args:
        items: The list of items to join
        separator: The separator to use (default: ", ")

    Returns:
        The joined string
    """
    return separator.join(str(item) for item in items)


@register_tool(
    default_registry,
    "__to_iterable",
    "Convert collection to iterable list (internal compiler use)",
)
def to_iterable(collection: Any) -> list[Any]:
    """Convert a collection to an iterable list for for-in loops.

    This function is used internally by the compiler to normalize collections
    before iteration, enabling for-in loops to work uniformly with:
    - Arrays: returned as-is
    - Dicts: converted to list of keys (like Python/JavaScript)
    - Strings: converted to list of characters

    Args:
        collection: The collection to convert (list, dict, str, etc.)

    Returns:
        A list that can be iterated with numeric indexing:
        - For lists: the original list
        - For dicts: list of keys (in insertion order)
        - For strings: list of characters

    Raises:
        TypeError: If collection is not a list, dict, or string
    """
    if isinstance(collection, list):
        # Arrays are already iterable - return as-is
        return collection
    if isinstance(collection, dict):
        # Dicts: return list of keys (enables iteration over keys)
        return list(collection.keys())
    if isinstance(collection, str):
        # Strings: return list of characters
        return list(collection)
    raise TypeError(
        f"Cannot iterate over {type(collection).__name__}. "
        f"for-in loops support lists, dicts, and strings only."
    )


# ============================================================================
# TYPE CONVERSION FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "num", "type::num", "Convert a value to a number (float)"
)
def num_function(value: Any) -> float:
    """Convert a value to a number (float).

    Converts strings, integers, booleans to float. Handles string
    representations of numbers including integers and decimals.

    Args:
        value: The value to convert to number

    Returns:
        Float representation of the value

    Raises:
        ValueError: If the value cannot be converted to a number

    Examples:
        num("42") -> 42.0
        num("3.14") -> 3.14
        num(100) -> 100.0
        num(True) -> 1.0
    """
    if isinstance(value, (int, float, bool)):
        return float(value)
    if isinstance(value, str):
        # Try to convert string to float
        try:
            return float(value.strip())
        except ValueError:
            raise ValueError(f"Cannot convert string '{value}' to number")
    else:
        raise ValueError(f"Cannot convert {type(value).__name__} to number")


@register_tool_with_alias(
    default_registry, "bool", "type::bool", "Convert a value to a boolean"
)
def bool_function(value: Any) -> bool:
    """Convert a value to a boolean.

    Handles string representations of booleans ("true", "false", "True",
    "False", "TRUE", "FALSE", "1", "0") as well as standard Python
    truthiness rules for other types.

    Args:
        value: The value to convert to boolean

    Returns:
        Boolean representation of the value

    Examples:
        bool("true") -> True
        bool("False") -> False
        bool("1") -> True
        bool("") -> False
        bool(0) -> False
        bool([1, 2]) -> True
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        # Handle string representations
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes"):
            return True
        if normalized in ("false", "0", "no", ""):
            return False
        # For other strings, use Python truthiness (non-empty = True)
        return bool(value.strip())
    # Use Python truthiness rules
    return bool(value)


# ============================================================================
# TIME FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "now", "time::now", "Get current timestamp in ISO 8601 format"
)
def now_function(timezone: str = "UTC") -> str:
    """Get current timestamp in ISO 8601 format.

    Returns current time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
    Supports optional timezone parameter.

    Args:
        timezone: Timezone name (default: "UTC"). Examples: "UTC", "US/Pacific",
                  "Europe/London", "Asia/Tokyo"

    Returns:
        ISO 8601 formatted timestamp string

    Raises:
        ValueError: If timezone is invalid

    Examples:
        now() -> "2025-10-31T14:30:00Z"
        now("US/Pacific") -> "2025-10-31T06:30:00-08:00"
    """
    from datetime import datetime

    try:
        import zoneinfo
    except ImportError:
        # Fallback for Python < 3.9
        import pytz as zoneinfo  # type: ignore

    try:
        if timezone == "UTC":
            # UTC special case - use Z suffix
            dt = datetime.now(
                tz=zoneinfo.ZoneInfo("UTC")
                if hasattr(zoneinfo, "ZoneInfo")
                else zoneinfo.UTC  # type: ignore[attr-defined]
            )
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Other timezones - use offset
        tz = (
            zoneinfo.ZoneInfo(timezone)
            if hasattr(zoneinfo, "ZoneInfo")
            else zoneinfo.timezone(timezone)  # type: ignore[attr-defined]
        )
        dt = datetime.now(tz=tz)
        return dt.isoformat()
    except (KeyError, TypeError, ValueError, OSError) as e:
        # KeyError: ZoneInfoNotFoundError (subclass of KeyError)
        # TypeError: non-string timezone argument
        # ValueError: malformed timezone key
        # OSError: system timezone database issue
        raise ValueError(f"Invalid timezone '{timezone}': {e}")


# ============================================================================
# ITERATION FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry,
    "range",
    "list::range",
    "Generate a list of numbers from start to end",
)
def range_function(start: int, end: int | None = None, step: int = 1) -> list[int]:
    """Generate a list of numbers from start to end (exclusive).

    Creates a list of integers. Supports two calling conventions:
    - range(stop)              → [0, 1, ..., stop-1]
    - range(start, stop)       → [start, start+1, ..., stop-1]
    - range(start, stop, step) → [start, start+step, ..., <stop]

    Mirrors Python's range() behavior.

    Args:
        start: If end is omitted, this is the stop value (start defaults to 0).
               Otherwise, this is the starting number (inclusive).
        end: Ending number (exclusive). Optional — when omitted, start is
             treated as end and start becomes 0.
        step: Step size (default: 1). Can be negative for reverse ranges.

    Returns:
        List of integers in the specified range

    Raises:
        ValueError: If step is 0

    Examples:
        range(5) -> [0, 1, 2, 3, 4]
        range(0, 5) -> [0, 1, 2, 3, 4]
        range(1, 10, 2) -> [1, 3, 5, 7, 9]
        range(5, 0, -1) -> [5, 4, 3, 2, 1]
    """
    if end is None:
        end = start
        start = 0

    if step == 0:
        raise ValueError("range() step argument must not be zero")

    return list(range(start, end, step))


# ============================================================================
# STRING FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "split", "str::split", "Split a string by delimiter"
)
def split_function(text: str, delimiter: str = " ") -> list[str]:
    """Split a string into a list using delimiter.

    Args:
        text: The string to split
        delimiter: The delimiter to split by (default: " ")

    Returns:
        List of string parts

    Examples:
        split("hello world") -> ["hello", "world"]
        split("a,b,c", ",") -> ["a", "b", "c"]
        split("one  two", " ") -> ["one", "", "two"]
    """
    if not isinstance(text, str):
        raise ValueError(f"split() requires string, got {type(text).__name__}")
    if not isinstance(delimiter, str):
        raise ValueError(
            f"split() delimiter must be string, got {type(delimiter).__name__}"
        )

    return text.split(delimiter)


@register_tool_with_alias(
    default_registry, "replace", "str::replace", "Replace occurrences in a string"
)
def replace_function(text: str, old: str, new: str) -> str:
    """Replace all occurrences of old substring with new substring.

    Args:
        text: The string to perform replacements on
        old: The substring to find
        new: The substring to replace with

    Returns:
        String with replacements made

    Examples:
        replace("hello world", "world", "there") -> "hello there"
        replace("foo foo foo", "foo", "bar") -> "bar bar bar"
    """
    if not isinstance(text, str):
        raise ValueError(f"replace() requires string, got {type(text).__name__}")
    if not isinstance(old, str):
        raise ValueError(f"replace() old must be string, got {type(old).__name__}")
    if not isinstance(new, str):
        raise ValueError(f"replace() new must be string, got {type(new).__name__}")

    return text.replace(old, new)


@register_tool_with_alias(
    default_registry, "trim", "str::trim", "Remove leading and trailing whitespace"
)
def trim_function(text: str) -> str:
    """Remove leading and trailing whitespace from a string.

    Args:
        text: The string to trim

    Returns:
        String with whitespace removed from both ends

    Examples:
        trim("  hello  ") -> "hello"
        trim("\n\tworld\t\n") -> "world"
    """
    if not isinstance(text, str):
        raise ValueError(f"trim() requires string, got {type(text).__name__}")

    return text.strip()


@register_tool_with_alias(
    default_registry, "regex_match", "regex::match", "Check if pattern matches text"
)
def regex_match_function(pattern: str, text: str) -> bool:
    """Check if a regular expression pattern matches the text.

    Uses Python's re.search() to check if pattern appears anywhere in text.

    Args:
        pattern: Regular expression pattern
        text: Text to search in

    Returns:
        True if pattern matches, False otherwise

    Examples:
        regex_match(r"\\d+", "abc123") -> True
        regex_match(r"^\\d+$", "abc123") -> False
        regex_match(r"[A-Z]+", "hello") -> False
    """
    import re

    if not isinstance(pattern, str):
        raise ValueError(
            f"regex_match() pattern must be string, got {type(pattern).__name__}"
        )
    if not isinstance(text, str):
        raise ValueError(
            f"regex_match() text must be string, got {type(text).__name__}"
        )

    try:
        return bool(re.search(pattern, text))
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern}': {e}")


@register_tool_with_alias(
    default_registry, "regex_extract", "regex::extract", "Extract text matching pattern"
)
def regex_extract_function(pattern: str, text: str) -> str:
    """Extract first match of regular expression pattern from text.

    Uses Python's re.search() and returns the matched text. If the pattern
    contains groups, returns the first group. Returns empty string if no match.

    Args:
        pattern: Regular expression pattern
        text: Text to search in

    Returns:
        Matched text, or empty string if no match

    Examples:
        regex_extract(r"\\d+", "Price: 123 dollars") -> "123"
        regex_extract(r"([A-Z]+)", "hello WORLD") -> "WORLD"
        regex_extract(r"\\d+", "no numbers") -> ""
    """
    import re

    if not isinstance(pattern, str):
        raise ValueError(
            f"regex_extract() pattern must be string, got {type(pattern).__name__}"
        )
    if not isinstance(text, str):
        raise ValueError(
            f"regex_extract() text must be string, got {type(text).__name__}"
        )

    try:
        match = re.search(pattern, text)
        if match:
            # If pattern has groups, return first group, otherwise return full match
            return match.group(1) if match.groups() else match.group(0)
        return ""
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern}': {e}")


# ============================================================================
# ARRAY FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "reverse", "list::reverse", "Reverse the order of items in a list"
)
def reverse_function(items: list) -> list:
    """Reverse the order of items in a list.

    Returns a new list with items in reverse order. Does not modify original.

    Args:
        items: The list to reverse

    Returns:
        New list with items in reverse order

    Examples:
        reverse([1, 2, 3]) -> [3, 2, 1]
        reverse(["a", "b", "c"]) -> ["c", "b", "a"]
    """
    if not isinstance(items, list):
        raise ValueError(f"reverse() requires list, got {type(items).__name__}")

    return list(reversed(items))


@register_tool_with_alias(
    default_registry, "sort", "list::sort", "Sort items in a list"
)
def sort_function(items: list) -> list:
    """Sort items in a list in ascending order.

    Returns a new sorted list. Items must be comparable (same type).
    Does not modify original list.

    Args:
        items: The list to sort

    Returns:
        New list with items sorted in ascending order

    Raises:
        ValueError: If items cannot be compared

    Examples:
        sort([3, 1, 2]) -> [1, 2, 3]
        sort(["c", "a", "b"]) -> ["a", "b", "c"]
    """
    if not isinstance(items, list):
        raise ValueError(f"sort() requires list, got {type(items).__name__}")

    try:
        return sorted(items)
    except TypeError as e:
        raise ValueError(f"Cannot sort list: {e}")


# ============================================================================
# MATH FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "abs", "math::abs", "Get absolute value of a number"
)
def abs_function(value: float) -> float:
    """Get the absolute value of a number.

    Args:
        value: The number to get absolute value of

    Returns:
        Absolute value (always non-negative)

    Examples:
        abs(-5) -> 5
        abs(3.14) -> 3.14
        abs(-2.5) -> 2.5
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"abs() requires number, got {type(value).__name__}")

    return abs(value)


@register_tool(default_registry, "min", "Get minimum value from a list")
def min_function(items: list) -> float:
    """Get the minimum value from a list of numbers.

    Args:
        items: List of numbers

    Returns:
        Minimum value from the list

    Raises:
        ValueError: If list is empty or contains non-numbers

    Examples:
        min([1, 2, 3]) -> 1
        min([5.5, 2.1, 3.7]) -> 2.1
    """
    if not isinstance(items, list):
        raise ValueError(f"min() requires list, got {type(items).__name__}")
    if len(items) == 0:
        raise ValueError("min() requires non-empty list")

    try:
        return float(min(items))
    except TypeError as e:
        raise ValueError(f"min() requires list of numbers: {e}")


# Domain alias for min
default_registry.register("list::min", min_function, "Get minimum value from a list")


@register_tool(default_registry, "max", "Get maximum value from a list")
def max_function(items: list) -> float:
    """Get the maximum value from a list of numbers.

    Args:
        items: List of numbers

    Returns:
        Maximum value from the list

    Raises:
        ValueError: If list is empty or contains non-numbers

    Examples:
        max([1, 2, 3]) -> 3
        max([5.5, 2.1, 3.7]) -> 5.5
    """
    if not isinstance(items, list):
        raise ValueError(f"max() requires list, got {type(items).__name__}")
    if len(items) == 0:
        raise ValueError("max() requires non-empty list")

    try:
        return float(max(items))
    except TypeError as e:
        raise ValueError(f"max() requires list of numbers: {e}")


# Domain alias for max
default_registry.register("list::max", max_function, "Get maximum value from a list")


@register_tool_with_alias(
    default_registry,
    "round",
    "math::round",
    "Round a number to specified decimal places",
)
def round_function(value: float, decimals: int = 0) -> float:
    """Round a number to a specified number of decimal places.

    Args:
        value: The number to round
        decimals: Number of decimal places (default: 0)

    Returns:
        Rounded number

    Examples:
        round(3.14159) -> 3.0
        round(3.14159, 2) -> 3.14
        round(2.5) -> 2.0  # Python's banker's rounding
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"round() requires number, got {type(value).__name__}")
    if not isinstance(decimals, int):
        raise ValueError(
            f"round() decimals must be integer, got {type(decimals).__name__}"
        )
    if decimals < 0:
        raise ValueError("round() decimals must be non-negative")

    return round(value, decimals)


# ============================================================================
# URL FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "url_encode", "url::encode", "URL encode a string"
)
def url_encode_function(text: str) -> str:
    """URL encode a string (percent-encoding).

    Encodes special characters in a string for safe use in URLs.
    Uses Python's urllib.parse.quote with safe=''.

    Args:
        text: The string to URL encode

    Returns:
        URL-encoded string

    Examples:
        url_encode("hello world") -> "hello%20world"
        url_encode("foo@bar.com") -> "foo%40bar.com"
        url_encode("a=b&c=d") -> "a%3Db%26c%3Dd"
    """
    from urllib.parse import quote

    if not isinstance(text, str):
        raise ValueError(f"url_encode() requires string, got {type(text).__name__}")

    return quote(text, safe="")


@register_tool_with_alias(
    default_registry, "url_decode", "url::decode", "URL decode a string"
)
def url_decode_function(text: str) -> str:
    """URL decode a string (percent-decoding).

    Decodes percent-encoded characters in a URL string.
    Uses Python's urllib.parse.unquote.

    Args:
        text: The URL-encoded string to decode

    Returns:
        Decoded string

    Raises:
        ValueError: If text contains invalid percent-encoding

    Examples:
        url_decode("hello%20world") -> "hello world"
        url_decode("foo%40bar.com") -> "foo@bar.com"
        url_decode("a%3Db%26c%3Dd") -> "a=b&c=d"
    """
    from urllib.parse import unquote

    if not isinstance(text, str):
        raise ValueError(f"url_decode() requires string, got {type(text).__name__}")

    try:
        return unquote(text)
    except (ValueError, UnicodeDecodeError) as e:
        raise ValueError(f"url_decode() failed: {e}")


# ============================================================================
# DICT FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry, "keys", "dict::keys", "Get dictionary keys as a list"
)
def keys_function(data: dict) -> list:
    """Get all keys from a dictionary as a list.

    Returns first-level keys only (not nested keys).
    Order is preserved (Python 3.7+).

    Args:
        data: The dictionary to get keys from

    Returns:
        List of dictionary keys

    Examples:
        keys({"a": 1, "b": 2}) -> ["a", "b"]
        keys({"name": "Alice", "age": 30}) -> ["name", "age"]
        keys({}) -> []
    """
    if not isinstance(data, dict):
        raise ValueError(f"keys() requires dict, got {type(data).__name__}")

    return list(data.keys())


@register_tool_with_alias(
    default_registry, "values", "dict::values", "Get dictionary values as a list"
)
def values_function(data: dict) -> list:
    """Get all values from a dictionary as a list.

    Returns first-level values only (not nested values).
    Order is preserved (Python 3.7+).

    Args:
        data: The dictionary to get values from

    Returns:
        List of dictionary values

    Examples:
        values({"a": 1, "b": 2}) -> [1, 2]
        values({"name": "Alice", "age": 30}) -> ["Alice", 30]
        values({}) -> []
    """
    if not isinstance(data, dict):
        raise ValueError(f"values() requires dict, got {type(data).__name__}")

    return list(data.values())


# ============================================================================
# Time Arithmetic Functions
# ============================================================================


def _parse_duration_string(duration: str) -> timedelta:
    """Parse duration string to Python timedelta.

    Supports: Xw, Xd, Xh, Xm, Xs and combinations
    Examples:
        "1h" -> 1 hour
        "30m" -> 30 minutes
        "1h30m" -> 1 hour 30 minutes
        "2d12h" -> 2 days 12 hours
        "1w" -> 1 week (7 days)

    Args:
        duration: Duration string (e.g., "1h", "30m", "1h30m")

    Returns:
        Python timedelta object

    Raises:
        ValueError: If duration format is invalid
    """
    pattern = r"(\d+)([wdhms])"
    matches = re.findall(pattern, duration.lower())

    if not matches:
        raise ValueError(
            f"Invalid duration format: '{duration}'. "
            f"Expected format like '1h', '30m', '1h30m', '2d', '1w'"
        )

    units = {"w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
    kwargs: dict[str, int] = {}

    for value, unit in matches:
        if unit not in units:
            raise ValueError(
                f"Invalid duration unit: '{unit}'. Valid units: w, d, h, m, s"
            )
        kwargs[units[unit]] = kwargs.get(units[unit], 0) + int(value)

    return timedelta(**kwargs)


def _parse_iso8601(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime.

    Handles various ISO 8601 formats including:
        - "2025-10-31T14:30:00Z" (UTC with Z suffix)
        - "2025-10-31T14:30:00+00:00" (UTC with offset)
        - "2025-10-31T14:30:00-08:00" (timezone offset)

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Python datetime object

    Raises:
        ValueError: If timestamp format is invalid
    """
    # Handle Z suffix (convert to +00:00 format)
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(timestamp)
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 timestamp: '{timestamp}': {e}")


def _format_iso8601(dt: datetime) -> str:
    """Format datetime to ISO 8601 string.

    Args:
        dt: Python datetime object

    Returns:
        ISO 8601 timestamp string
    """
    # Use isoformat() which preserves timezone
    iso_str = dt.isoformat()

    # If UTC and no timezone info, add Z suffix
    if dt.tzinfo is None or dt.utcoffset() == timedelta(0):
        if not iso_str.endswith("+00:00") and not iso_str.endswith("Z"):
            iso_str += "Z"
        elif iso_str.endswith("+00:00"):
            iso_str = iso_str[:-6] + "Z"

    return iso_str


@register_tool_with_alias(
    default_registry,
    "parse_duration",
    "time::parse_duration",
    "Parse duration string to seconds",
)
def parse_duration(duration: str) -> float:
    """Parse duration string to total seconds.

    Useful for comparing durations or converting to seconds for calculations.

    Supported units:
        w: weeks (7 days)
        d: days
        h: hours
        m: minutes
        s: seconds

    Args:
        duration: Duration string (e.g., "1h", "30m", "1h30m", "2d12h", "1w")

    Returns:
        Total seconds as float

    Examples:
        parse_duration("1h") -> 3600.0
        parse_duration("30m") -> 1800.0
        parse_duration("1h30m") -> 5400.0
        parse_duration("2d") -> 172800.0
        parse_duration("1w") -> 604800.0

    Raises:
        ValueError: If duration format is invalid
    """
    if not isinstance(duration, str):
        raise ValueError(
            f"parse_duration() requires string, got {type(duration).__name__}"
        )

    try:
        td = _parse_duration_string(duration)
        return td.total_seconds()
    except ValueError as e:
        raise ValueError(f"parse_duration() failed: {e}")


@register_tool_with_alias(
    default_registry, "add_duration", "time::add_duration", "Add duration to timestamp"
)
def add_duration(timestamp: str, duration: str) -> str:
    """Add duration to ISO 8601 timestamp.

    Preserves timezone information from the original timestamp.

    Args:
        timestamp: ISO 8601 timestamp string
        duration: Duration string (e.g., "1h", "30m", "1d")

    Returns:
        New ISO 8601 timestamp string

    Examples:
        add_duration("2025-10-31T14:30:00Z", "1h") -> "2025-10-31T15:30:00Z"
        add_duration("2025-10-31T14:30:00Z", "1d") -> "2025-11-01T14:30:00Z"
        add_duration("2025-10-31T14:30:00-08:00", "2h") -> "2025-10-31T16:30:00-08:00"

    Raises:
        ValueError: If timestamp or duration format is invalid
    """
    if not isinstance(timestamp, str):
        raise ValueError(
            f"add_duration() timestamp must be string, got {type(timestamp).__name__}"
        )
    if not isinstance(duration, str):
        raise ValueError(
            f"add_duration() duration must be string, got {type(duration).__name__}"
        )

    try:
        dt = _parse_iso8601(timestamp)
        td = _parse_duration_string(duration)
        new_dt = dt + td
        return _format_iso8601(new_dt)
    except ValueError as e:
        raise ValueError(f"add_duration() failed: {e}")


@register_tool_with_alias(
    default_registry,
    "subtract_duration",
    "time::subtract_duration",
    "Subtract duration from timestamp",
)
def subtract_duration(timestamp: str, duration: str) -> str:
    """Subtract duration from ISO 8601 timestamp.

    Preserves timezone information from the original timestamp.

    Args:
        timestamp: ISO 8601 timestamp string
        duration: Duration string (e.g., "1h", "30m", "1d")

    Returns:
        New ISO 8601 timestamp string

    Examples:
        subtract_duration("2025-10-31T14:30:00Z", "1h") -> "2025-10-31T13:30:00Z"
        subtract_duration("2025-10-31T14:30:00Z", "1d") -> "2025-10-30T14:30:00Z"
        subtract_duration("2025-10-31T14:30:00-08:00", "2h") -> "2025-10-31T12:30:00-08:00"

    Raises:
        ValueError: If timestamp or duration format is invalid
    """
    if not isinstance(timestamp, str):
        raise ValueError(
            f"subtract_duration() timestamp must be string, got {type(timestamp).__name__}"
        )
    if not isinstance(duration, str):
        raise ValueError(
            f"subtract_duration() duration must be string, got {type(duration).__name__}"
        )

    try:
        dt = _parse_iso8601(timestamp)
        td = _parse_duration_string(duration)
        new_dt = dt - td
        return _format_iso8601(new_dt)
    except ValueError as e:
        raise ValueError(f"subtract_duration() failed: {e}")


@register_tool_with_alias(
    default_registry,
    "duration_between",
    "time::duration_between",
    "Get duration between two timestamps",
)
def duration_between(start: str, end: str) -> str:
    """Get duration between two ISO 8601 timestamps.

    Returns duration as a human-readable string.

    Args:
        start: Start ISO 8601 timestamp string
        end: End ISO 8601 timestamp string

    Returns:
        Duration string (e.g., "2h30m", "1d12h", "45s")

    Examples:
        duration_between("2025-10-31T14:00:00Z", "2025-10-31T16:30:00Z") -> "2h30m"
        duration_between("2025-10-31T14:00:00Z", "2025-11-01T14:00:00Z") -> "1d"
        duration_between("2025-10-31T16:00:00Z", "2025-10-31T14:00:00Z") -> "-2h" (negative)

    Raises:
        ValueError: If timestamp format is invalid
    """
    if not isinstance(start, str):
        raise ValueError(
            f"duration_between() start must be string, got {type(start).__name__}"
        )
    if not isinstance(end, str):
        raise ValueError(
            f"duration_between() end must be string, got {type(end).__name__}"
        )

    try:
        start_dt = _parse_iso8601(start)
        end_dt = _parse_iso8601(end)
        diff = end_dt - start_dt
        return str(format_duration(diff.total_seconds()))
    except ValueError as e:
        raise ValueError(f"duration_between() failed: {e}")


@register_tool_with_alias(
    default_registry,
    "format_duration",
    "time::format_duration",
    "Format seconds to duration string",
)
def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration string.

    Args:
        seconds: Total seconds (can be negative)

    Returns:
        Duration string (e.g., "1h", "2h30m", "1d12h")

    Examples:
        format_duration(3600) -> "1h"
        format_duration(5400) -> "1h30m"
        format_duration(90061) -> "1d1h1m1s"
        format_duration(-3600) -> "-1h"

    Raises:
        ValueError: If seconds is not a number
    """
    if not isinstance(seconds, (int, float)):
        raise ValueError(
            f"format_duration() requires number, got {type(seconds).__name__}"
        )

    # Handle negative durations
    if seconds < 0:
        return "-" + str(format_duration(-seconds))

    # Convert to absolute value for calculation
    total_seconds = int(abs(seconds))

    # Calculate components
    weeks, remainder = divmod(total_seconds, 604800)  # 7 * 24 * 60 * 60
    days, remainder = divmod(remainder, 86400)  # 24 * 60 * 60
    hours, remainder = divmod(remainder, 3600)  # 60 * 60
    minutes, secs = divmod(remainder, 60)

    # Build duration string
    parts = []
    if weeks > 0:
        parts.append(f"{weeks}w")
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Include seconds if non-zero or if no other parts
        parts.append(f"{secs}s")

    return "".join(parts)


@register_tool_with_alias(
    default_registry, "timestamp_compare", "time::compare", "Compare two timestamps"
)
def timestamp_compare(timestamp1: str, operator: str, timestamp2: str) -> bool:
    """Compare two ISO 8601 timestamps.

    Useful for filtering or conditional logic with timestamps.

    Args:
        timestamp1: First ISO 8601 timestamp string
        operator: Comparison operator ("<", ">", "<=", ">=", "==", "!=")
        timestamp2: Second ISO 8601 timestamp string

    Returns:
        Boolean result of comparison

    Examples:
        timestamp_compare("2025-10-31T14:00:00Z", "<", "2025-10-31T15:00:00Z") -> True
        timestamp_compare("2025-10-31T14:00:00Z", ">", "2025-10-31T15:00:00Z") -> False
        timestamp_compare("2025-10-31T14:00:00Z", "==", "2025-10-31T14:00:00Z") -> True

    Raises:
        ValueError: If timestamps are invalid or operator is not supported
    """
    if not isinstance(timestamp1, str):
        raise ValueError(
            f"timestamp_compare() timestamp1 must be string, got {type(timestamp1).__name__}"
        )
    if not isinstance(timestamp2, str):
        raise ValueError(
            f"timestamp_compare() timestamp2 must be string, got {type(timestamp2).__name__}"
        )
    if not isinstance(operator, str):
        raise ValueError(
            f"timestamp_compare() operator must be string, got {type(operator).__name__}"
        )

    valid_operators = {"<", ">", "<=", ">=", "==", "!="}
    if operator not in valid_operators:
        raise ValueError(
            f"timestamp_compare() invalid operator: '{operator}'. "
            f"Valid operators: {', '.join(sorted(valid_operators))}"
        )

    try:
        dt1 = _parse_iso8601(timestamp1)
        dt2 = _parse_iso8601(timestamp2)

        if operator == "<":
            return dt1 < dt2
        if operator == ">":
            return dt1 > dt2
        if operator == "<=":
            return dt1 <= dt2
        if operator == ">=":
            return dt1 >= dt2
        if operator == "==":
            return dt1 == dt2
        if operator == "!=":
            return dt1 != dt2
        # Should never reach here due to validation above
        raise ValueError(f"Unsupported operator: {operator}")
    except ValueError as e:
        raise ValueError(f"timestamp_compare() failed: {e}")


@register_tool_with_alias(
    default_registry,
    "from_epoch",
    "time::from_epoch",
    "Convert Unix epoch timestamp to ISO 8601",
)
def from_epoch(seconds: float, timezone: str = "UTC") -> str:
    """Convert Unix epoch timestamp to ISO 8601 string.

    Args:
        seconds: Unix epoch timestamp (seconds since 1970-01-01 00:00:00 UTC)
        timezone: Timezone name (default: "UTC"). Examples: "US/Pacific", "Europe/London"

    Returns:
        ISO 8601 timestamp string

    Examples:
        from_epoch(1698765432) -> "2023-10-31T14:30:32Z"
        from_epoch(1698765432, "US/Pacific") -> "2023-10-31T06:30:32-08:00"
        from_epoch(0) -> "1970-01-01T00:00:00Z"

    Raises:
        ValueError: If seconds is not a number or timezone is invalid
    """
    if not isinstance(seconds, (int, float)):
        raise ValueError(
            f"from_epoch() seconds must be number, got {type(seconds).__name__}"
        )
    if not isinstance(timezone, str):
        raise ValueError(
            f"from_epoch() timezone must be string, got {type(timezone).__name__}"
        )

    try:
        from zoneinfo import ZoneInfo

        # Create datetime from epoch (always in UTC)
        dt_utc = datetime.fromtimestamp(seconds, tz=UTC)

        # Convert to requested timezone if not UTC
        if timezone.upper() != "UTC":
            try:
                target_tz = ZoneInfo(timezone)
                dt = dt_utc.astimezone(target_tz)
            except (KeyError, TypeError, ValueError, OSError) as e:
                raise ValueError(f"Invalid timezone '{timezone}': {e}")
        else:
            dt = dt_utc

        return _format_iso8601(dt)
    except (ValueError, OSError) as e:
        raise ValueError(f"from_epoch() failed: {e}")


@register_tool_with_alias(
    default_registry,
    "to_epoch",
    "time::to_epoch",
    "Convert ISO 8601 timestamp to Unix epoch",
)
def to_epoch(timestamp: str) -> float:
    """Convert ISO 8601 timestamp to Unix epoch seconds.

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Unix epoch timestamp (seconds since 1970-01-01 00:00:00 UTC) as float

    Examples:
        to_epoch("2023-10-31T14:30:32Z") -> 1698765432.0
        to_epoch("2023-10-31T06:30:32-08:00") -> 1698765432.0  # Same absolute time
        to_epoch("1970-01-01T00:00:00Z") -> 0.0

    Raises:
        ValueError: If timestamp format is invalid
    """
    if not isinstance(timestamp, str):
        raise ValueError(f"to_epoch() requires string, got {type(timestamp).__name__}")

    try:
        dt = _parse_iso8601(timestamp)
        return dt.timestamp()
    except ValueError as e:
        raise ValueError(f"to_epoch() failed: {e}")


# ============================================================================
# Network Address Utilities
# ============================================================================


@register_tool_with_alias(
    default_registry, "is_ipv4", "ip::is_v4", "Check if string is a valid IPv4 address"
)
def is_ipv4(ip: str) -> bool:
    """Check if a string is a valid IPv4 address.

    Validates IPv4 addresses including:
        - Standard notation: "192.168.1.1"
        - With leading zeros: "192.168.001.001" (normalized)
        - Localhost: "127.0.0.1"
        - Broadcast: "255.255.255.255"

    Args:
        ip: String to validate as IPv4 address

    Returns:
        True if valid IPv4 address, False otherwise

    Examples:
        is_ipv4("192.168.1.1") -> True
        is_ipv4("10.0.0.1") -> True
        is_ipv4("256.1.1.1") -> False (out of range)
        is_ipv4("192.168.1") -> False (incomplete)
        is_ipv4("::1") -> False (IPv6)
        is_ipv4("not-an-ip") -> False
    """
    if not isinstance(ip, str):
        return False

    try:
        ipaddress.IPv4Address(ip)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


@register_tool_with_alias(
    default_registry, "is_ipv6", "ip::is_v6", "Check if string is a valid IPv6 address"
)
def is_ipv6(ip: str) -> bool:
    """Check if a string is a valid IPv6 address.

    Validates IPv6 addresses including:
        - Standard notation: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        - Compressed notation: "2001:db8::1"
        - Localhost: "::1"
        - IPv4-mapped: "::ffff:192.168.1.1"

    Args:
        ip: String to validate as IPv6 address

    Returns:
        True if valid IPv6 address, False otherwise

    Examples:
        is_ipv6("2001:db8::1") -> True
        is_ipv6("::1") -> True
        is_ipv6("fe80::1") -> True
        is_ipv6("192.168.1.1") -> False (IPv4)
        is_ipv6("not-an-ip") -> False
        is_ipv6("gggg::1") -> False (invalid hex)
    """
    if not isinstance(ip, str):
        return False

    try:
        ipaddress.IPv6Address(ip)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


@register_tool_with_alias(
    default_registry,
    "is_ip",
    "ip::is_valid",
    "Check if string is a valid IP address (IPv4 or IPv6)",
)
def is_ip(ip: str) -> bool:
    """Check if a string is a valid IP address (IPv4 or IPv6).

    Convenience function that checks for both IPv4 and IPv6 validity.

    Args:
        ip: String to validate as IP address

    Returns:
        True if valid IPv4 or IPv6 address, False otherwise

    Examples:
        is_ip("192.168.1.1") -> True (IPv4)
        is_ip("2001:db8::1") -> True (IPv6)
        is_ip("::1") -> True (IPv6)
        is_ip("10.0.0.1") -> True (IPv4)
        is_ip("not-an-ip") -> False
        is_ip("256.1.1.1") -> False
    """
    if not isinstance(ip, str):
        return False

    return bool(is_ipv4(ip) or is_ipv6(ip))


# ============================================================================
# String and List Utilities
# ============================================================================


@register_tool_with_alias(
    default_registry,
    "strip_markdown",
    "str::strip_markdown",
    "Remove markdown code blocks from text",
)
def strip_markdown(text: str) -> str:
    """Remove markdown code blocks from text (e.g., LLM output).

    Removes both fenced code blocks (```...```) and inline code (`...`),
    leaving only the plain text content.

    Args:
        text: Text containing markdown code blocks

    Returns:
        Text with markdown code blocks removed

    Examples:
        strip_markdown("```python\\nprint('hello')\\n```") -> "print('hello')"
        strip_markdown("Use `code` here") -> "Use code here"
        strip_markdown("```\\ncode\\n```\\ntext") -> "code\\ntext"
        strip_markdown("No markdown here") -> "No markdown here"

    Common use case:
        # Extract code from LLM response
        llm_response = "```python\\ndef foo():\\n    pass\\n```"
        clean_code = strip_markdown(llm_response)
    """
    if not isinstance(text, str):
        raise ValueError(f"strip_markdown() requires string, got {type(text).__name__}")

    result = text

    # Remove fenced code blocks (```...```)
    # Pattern matches ``` optionally followed by language name, then content, then ```
    result = re.sub(r"```[a-zA-Z]*\n", "", result)
    result = re.sub(r"```", "", result)

    # Remove inline code (`...`)
    result = re.sub(r"`([^`]+)`", r"\1", result)

    return result


@register_tool_with_alias(
    default_registry, "take", "list::take", "Get first n elements from a list"
)
def take(items: list, n: int) -> list:
    """Get the first n elements from a list.

    Safely handles cases where n is larger than the list length.

    Args:
        items: List to take elements from
        n: Number of elements to take (must be >= 0)

    Returns:
        New list with first n elements

    Examples:
        take([1, 2, 3, 4, 5], 3) -> [1, 2, 3]
        take([1, 2], 5) -> [1, 2] (n larger than list)
        take([1, 2, 3], 0) -> []
        take([], 5) -> []

    Common use cases:
        # Get first 10 alerts
        recent_alerts = take(alerts, 10)

        # Preview first 5 results
        preview = take(results, 5)
    """
    if not isinstance(items, list):
        raise ValueError(f"take() requires list, got {type(items).__name__}")

    if not isinstance(n, int):
        raise ValueError(f"take() n must be int, got {type(n).__name__}")

    if n < 0:
        raise ValueError(f"take() n must be >= 0, got {n}")

    return items[:n]


@register_tool_with_alias(
    default_registry,
    "startswith",
    "str::startswith",
    "Check if string starts with prefix",
)
def startswith(text: str, prefix: str) -> bool:
    """Check if a string starts with a given prefix.

    Args:
        text: String to check
        prefix: Prefix to look for

    Returns:
        True if text starts with prefix, False otherwise

    Examples:
        startswith("hello world", "hello") -> True
        startswith("hello world", "world") -> False
        startswith("192.168.1.1", "192.168") -> True
        startswith("error: failed", "error:") -> True
        startswith("", "test") -> False
        startswith("test", "") -> True (empty prefix always matches)

    Common use cases:
        # Filter alerts by title prefix
        critical_alerts = alerts.filter(a => startswith(a.title, "CRITICAL:"))

        # Check if IP is in subnet
        is_private = startswith(ip, "192.168") or startswith(ip, "10.")

        # Filter log levels
        errors = logs.filter(log => startswith(log.level, "ERROR"))
    """
    if not isinstance(text, str):
        raise ValueError(f"startswith() text must be string, got {type(text).__name__}")

    if not isinstance(prefix, str):
        raise ValueError(
            f"startswith() prefix must be string, got {type(prefix).__name__}"
        )

    return text.startswith(prefix)


@register_tool_with_alias(
    default_registry, "endswith", "str::endswith", "Check if string ends with suffix"
)
def endswith(text: str, suffix: str) -> bool:
    """Check if a string ends with a given suffix.

    Args:
        text: String to check
        suffix: Suffix to look for

    Returns:
        True if text ends with suffix, False otherwise

    Examples:
        endswith("hello world", "world") -> True
        endswith("hello world", "hello") -> False
        endswith("file.txt", ".txt") -> True
        endswith("script.py", ".py") -> True
        endswith("", "test") -> False
        endswith("test", "") -> True (empty suffix always matches)

    Common use cases:
        # Filter files by extension
        python_files = files.filter(f => endswith(f.name, ".py"))

        # Check domain
        is_internal = endswith(email, "@company.com")

        # Filter URLs
        api_endpoints = urls.filter(url => endswith(url, "/api"))
    """
    if not isinstance(text, str):
        raise ValueError(f"endswith() text must be string, got {type(text).__name__}")

    if not isinstance(suffix, str):
        raise ValueError(
            f"endswith() suffix must be string, got {type(suffix).__name__}"
        )

    return text.endswith(suffix)


# ============================================================================
# COLLECTION UTILITY FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry,
    "unique",
    "list::unique",
    "Remove duplicate values from a list, preserving order",
)
def unique_function(items: list) -> list:
    """Remove duplicate values from a list, preserving first-occurrence order.

    Args:
        items: List to deduplicate

    Returns:
        New list with duplicates removed

    Examples:
        unique([1, 2, 2, 3, 1]) -> [1, 2, 3]
        unique(["a", "b", "a"]) -> ["a", "b"]
        unique([]) -> []
    """
    if not isinstance(items, list):
        raise ValueError(f"unique() requires a list, got {type(items).__name__}")

    seen: set[int] = set()
    result: list = []
    for item in items:
        # Use id-based dedup for unhashable items, hash-based for hashable
        try:
            key = (type(item), item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        except TypeError:
            # Unhashable item (e.g. dict, list) — use JSON repr as key
            key_str = json.dumps(item, sort_keys=True, default=str)
            hashable_key = (type(item).__name__, key_str)
            if hashable_key not in seen:
                seen.add(hashable_key)
                result.append(item)
    return result


@register_tool_with_alias(
    default_registry,
    "flatten",
    "list::flatten",
    "Flatten nested lists into a single list",
)
def flatten_function(items: list) -> list:
    """Flatten nested lists into a single flat list (one level deep).

    Args:
        items: List potentially containing nested lists

    Returns:
        New flat list

    Examples:
        flatten([[1, 2], [3, 4]]) -> [1, 2, 3, 4]
        flatten([[1], 2, [3, [4]]]) -> [1, 2, 3, [4]]
        flatten([]) -> []
    """
    if not isinstance(items, list):
        raise ValueError(f"flatten() requires a list, got {type(items).__name__}")

    result: list = []
    for item in items:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


@register_tool_with_alias(
    default_registry,
    "type_of",
    "type::type_of",
    "Return the runtime type of a value as a string",
)
def type_of_function(value: Any) -> str:
    """Return the runtime type of a value as a string.

    Args:
        value: Any value

    Returns:
        Type name: "string", "number", "boolean", "list", "dict", or "null"

    Examples:
        type_of("hello") -> "string"
        type_of(42) -> "number"
        type_of(3.14) -> "number"
        type_of(True) -> "boolean"
        type_of([1, 2]) -> "list"
        type_of({"a": 1}) -> "dict"
        type_of(null) -> "null"
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "unknown"


@register_tool_with_alias(
    default_registry,
    "slice",
    "list::slice",
    "Return a sub-range of a list or string",
)
def slice_function(
    items: Union[list, str], start: int, end: int | None = None
) -> Union[list, str]:
    """Return a sub-range of a list or string.

    Args:
        items: List or string to slice
        start: Start index (inclusive). Negative indices count from end.
        end: End index (exclusive). If omitted, slices to the end.
             Negative indices count from end.

    Returns:
        New list or string with elements from start to end

    Examples:
        slice([1, 2, 3, 4, 5], 1, 3) -> [2, 3]
        slice([1, 2, 3, 4, 5], 2) -> [3, 4, 5]
        slice("hello", 1, 3) -> "el"
        slice([1, 2, 3], -2) -> [2, 3]
    """
    if not isinstance(items, (list, str)):
        raise ValueError(
            f"slice() requires a list or string, got {type(items).__name__}"
        )

    if end is None:
        return items[start:]
    return items[start:end]


@register_tool_with_alias(
    default_registry,
    "index_of",
    "list::index_of",
    "Find the first index of a value in a list or substring in a string",
)
def index_of_function(items: Union[list, str], value: Any) -> int:
    """Find the first index of a value in a list or substring in a string.

    Args:
        items: List or string to search
        value: Value or substring to find

    Returns:
        Index of first occurrence, or -1 if not found

    Examples:
        index_of([10, 20, 30], 20) -> 1
        index_of(["a", "b", "c"], "b") -> 1
        index_of([1, 2, 3], 99) -> -1
        index_of("hello world", "world") -> 6
        index_of("hello", "xyz") -> -1
    """
    if not isinstance(items, (list, str)):
        raise ValueError(
            f"index_of() requires a list or string, got {type(items).__name__}"
        )

    try:
        return items.index(value)
    except ValueError:
        return -1


# ============================================================================
# ENCODING FUNCTIONS
# ============================================================================


@register_tool_with_alias(
    default_registry,
    "base64_encode",
    "str::base64_encode",
    "Encode a string to base64",
)
def base64_encode_function(text: str) -> str:
    """Encode a string to base64.

    Args:
        text: String to encode

    Returns:
        Base64-encoded string

    Examples:
        base64_encode("hello") -> "aGVsbG8="
        base64_encode("user:pass") -> "dXNlcjpwYXNz"
    """
    if not isinstance(text, str):
        raise ValueError(
            f"base64_encode() requires a string, got {type(text).__name__}"
        )
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


@register_tool_with_alias(
    default_registry,
    "base64_decode",
    "str::base64_decode",
    "Decode a base64-encoded string",
)
def base64_decode_function(text: str) -> str:
    """Decode a base64-encoded string.

    Args:
        text: Base64-encoded string to decode

    Returns:
        Decoded string

    Raises:
        ValueError: If input is not valid base64

    Examples:
        base64_decode("aGVsbG8=") -> "hello"
        base64_decode("dXNlcjpwYXNz") -> "user:pass"
    """
    if not isinstance(text, str):
        raise ValueError(
            f"base64_decode() requires a string, got {type(text).__name__}"
        )
    try:
        return base64.b64decode(text).decode("utf-8")
    except Exception as e:
        raise ValueError(f"base64_decode() invalid base64 input: {e}")
