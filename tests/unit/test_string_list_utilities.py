"""Tests for String and List Utility Functions."""

import pytest

from cy_language.native_functions import endswith, startswith, strip_markdown, take

# ============================================================================
# strip_markdown() Tests
# ============================================================================


class TestStripMarkdown:
    """Test cases for strip_markdown() function."""

    def test_strip_markdown_fenced_code_block(self):
        """Test removing fenced code blocks."""
        text = "```python\nprint('hello')\n```"
        result = strip_markdown(text)
        assert result == "print('hello')\n"

    def test_strip_markdown_fenced_code_block_no_language(self):
        """Test removing fenced code blocks without language."""
        text = "```\nsome code\n```"
        result = strip_markdown(text)
        assert result == "some code\n"

    def test_strip_markdown_multiple_fenced_blocks(self):
        """Test removing multiple fenced code blocks."""
        text = "```python\ncode1\n```\ntext\n```javascript\ncode2\n```"
        result = strip_markdown(text)
        assert result == "code1\ntext\ncode2\n"

    def test_strip_markdown_inline_code(self):
        """Test removing inline code."""
        text = "Use `code` here and `another` there"
        result = strip_markdown(text)
        assert result == "Use code here and another there"

    def test_strip_markdown_mixed(self):
        """Test removing both fenced and inline code."""
        text = "```python\ndef foo():\n    pass\n```\nUse `bar()` function"
        result = strip_markdown(text)
        assert result == "def foo():\n    pass\nUse bar() function"

    def test_strip_markdown_no_markdown(self):
        """Test text without markdown."""
        text = "Plain text without any markdown"
        result = strip_markdown(text)
        assert result == text

    def test_strip_markdown_empty_string(self):
        """Test empty string."""
        result = strip_markdown("")
        assert result == ""

    def test_strip_markdown_only_backticks(self):
        """Test strings with only backticks."""
        text = "```"
        result = strip_markdown(text)
        assert result == ""

    def test_strip_markdown_llm_response(self):
        """Test realistic LLM response with code."""
        text = """Here's the solution:

```python
def calculate_sum(a, b):
    return a + b
```

You can call it with `calculate_sum(5, 3)`."""

        result = strip_markdown(text)
        assert "```" not in result
        assert "`" not in result
        assert "def calculate_sum(a, b):" in result
        assert "calculate_sum(5, 3)" in result

    def test_strip_markdown_nested_backticks(self):
        """Test inline code with backticks inside fenced block."""
        text = "```\ncode with `backticks`\n```"
        result = strip_markdown(text)
        assert result == "code with backticks\n"

    def test_strip_markdown_invalid_type(self):
        """Test with non-string type."""
        with pytest.raises(ValueError, match="requires string"):
            strip_markdown(123)

        with pytest.raises(ValueError, match="requires string"):
            strip_markdown(None)


# ============================================================================
# take() Tests
# ============================================================================


class TestTake:
    """Test cases for take() function."""

    def test_take_basic(self):
        """Test basic take operation."""
        result = take([1, 2, 3, 4, 5], 3)
        assert result == [1, 2, 3]

    def test_take_zero(self):
        """Test taking zero elements."""
        result = take([1, 2, 3], 0)
        assert result == []

    def test_take_all(self):
        """Test taking all elements."""
        items = [1, 2, 3, 4, 5]
        result = take(items, 5)
        assert result == items

    def test_take_more_than_length(self):
        """Test taking more elements than list has."""
        result = take([1, 2], 5)
        assert result == [1, 2]

    def test_take_empty_list(self):
        """Test taking from empty list."""
        result = take([], 5)
        assert result == []

    def test_take_strings(self):
        """Test taking string elements."""
        result = take(["a", "b", "c", "d"], 2)
        assert result == ["a", "b"]

    def test_take_dicts(self):
        """Test taking dict elements."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = take(items, 2)
        assert result == [{"id": 1}, {"id": 2}]

    def test_take_does_not_modify_original(self):
        """Test that take does not modify original list."""
        original = [1, 2, 3, 4, 5]
        result = take(original, 3)
        assert original == [1, 2, 3, 4, 5]  # Original unchanged
        assert result == [1, 2, 3]

    def test_take_negative_n(self):
        """Test taking negative number of elements."""
        with pytest.raises(ValueError, match="must be >= 0"):
            take([1, 2, 3], -1)

    def test_take_invalid_type_list(self):
        """Test with non-list type."""
        with pytest.raises(ValueError, match="requires list"):
            take("not a list", 3)

        with pytest.raises(ValueError, match="requires list"):
            take(123, 3)

    def test_take_invalid_type_n(self):
        """Test with non-int n."""
        with pytest.raises(ValueError, match="n must be int"):
            take([1, 2, 3], "3")

        with pytest.raises(ValueError, match="n must be int"):
            take([1, 2, 3], 3.5)

    def test_take_workflow_first_alerts(self):
        """Test realistic workflow: get first N alerts."""
        alerts = [
            {"id": 1, "severity": "high"},
            {"id": 2, "severity": "medium"},
            {"id": 3, "severity": "low"},
            {"id": 4, "severity": "high"},
            {"id": 5, "severity": "medium"},
        ]

        top_3 = take(alerts, 3)
        assert len(top_3) == 3
        assert top_3[0]["id"] == 1
        assert top_3[2]["id"] == 3


# ============================================================================
# startswith() Tests
# ============================================================================


class TestStartsWith:
    """Test cases for startswith() function."""

    def test_startswith_basic(self):
        """Test basic startswith operation."""
        assert startswith("hello world", "hello") is True
        assert startswith("hello world", "world") is False

    def test_startswith_exact_match(self):
        """Test when prefix is the entire string."""
        assert startswith("hello", "hello") is True

    def test_startswith_empty_prefix(self):
        """Test with empty prefix (always matches)."""
        assert startswith("hello", "") is True
        assert startswith("", "") is True

    def test_startswith_empty_string(self):
        """Test with empty string and non-empty prefix."""
        assert startswith("", "test") is False

    def test_startswith_case_sensitive(self):
        """Test case sensitivity."""
        assert startswith("Hello World", "hello") is False
        assert startswith("Hello World", "Hello") is True

    def test_startswith_ip_addresses(self):
        """Test with IP addresses."""
        assert startswith("192.168.1.1", "192.168") is True
        assert startswith("10.0.0.1", "192.168") is False
        assert startswith("192.168.1.1", "192") is True

    def test_startswith_alert_titles(self):
        """Test filtering alert titles."""
        assert startswith("CRITICAL: Server down", "CRITICAL:") is True
        assert startswith("ERROR: Failed login", "ERROR:") is True
        assert startswith("INFO: User login", "CRITICAL:") is False

    def test_startswith_file_paths(self):
        """Test with file paths."""
        assert startswith("/var/log/app.log", "/var/log") is True
        assert startswith("/etc/config", "/var") is False

    def test_startswith_invalid_type_text(self):
        """Test with non-string text."""
        with pytest.raises(ValueError, match="text must be string"):
            startswith(123, "test")

        with pytest.raises(ValueError, match="text must be string"):
            startswith(None, "test")

    def test_startswith_invalid_type_prefix(self):
        """Test with non-string prefix."""
        with pytest.raises(ValueError, match="prefix must be string"):
            startswith("hello", 123)

        with pytest.raises(ValueError, match="prefix must be string"):
            startswith("hello", None)

    def test_startswith_workflow_filtering(self):
        """Test realistic workflow: filter by prefix."""
        logs = [
            {"level": "ERROR", "msg": "Failed"},
            {"level": "INFO", "msg": "Started"},
            {"level": "ERROR", "msg": "Timeout"},
            {"level": "WARNING", "msg": "Slow"},
        ]

        errors = [log for log in logs if startswith(log["level"], "ERROR")]
        assert len(errors) == 2
        assert all(log["level"] == "ERROR" for log in errors)


# ============================================================================
# endswith() Tests
# ============================================================================


class TestEndsWith:
    """Test cases for endswith() function."""

    def test_endswith_basic(self):
        """Test basic endswith operation."""
        assert endswith("hello world", "world") is True
        assert endswith("hello world", "hello") is False

    def test_endswith_exact_match(self):
        """Test when suffix is the entire string."""
        assert endswith("world", "world") is True

    def test_endswith_empty_suffix(self):
        """Test with empty suffix (always matches)."""
        assert endswith("hello", "") is True
        assert endswith("", "") is True

    def test_endswith_empty_string(self):
        """Test with empty string and non-empty suffix."""
        assert endswith("", "test") is False

    def test_endswith_case_sensitive(self):
        """Test case sensitivity."""
        assert endswith("Hello World", "world") is False
        assert endswith("Hello World", "World") is True

    def test_endswith_file_extensions(self):
        """Test with file extensions."""
        assert endswith("script.py", ".py") is True
        assert endswith("data.json", ".json") is True
        assert endswith("file.txt", ".py") is False

    def test_endswith_emails(self):
        """Test with email domains."""
        assert endswith("user@company.com", "@company.com") is True
        assert endswith("user@example.org", "@company.com") is False

    def test_endswith_urls(self):
        """Test with URL paths."""
        assert endswith("https://api.com/v1/users", "/users") is True
        assert endswith("https://api.com/v1/posts", "/users") is False

    def test_endswith_multiple_extensions(self):
        """Test checking multiple extensions."""
        filename = "archive.tar.gz"
        assert endswith(filename, ".gz") is True
        assert endswith(filename, ".tar.gz") is True
        assert endswith(filename, ".zip") is False

    def test_endswith_invalid_type_text(self):
        """Test with non-string text."""
        with pytest.raises(ValueError, match="text must be string"):
            endswith(123, "test")

        with pytest.raises(ValueError, match="text must be string"):
            endswith(None, "test")

    def test_endswith_invalid_type_suffix(self):
        """Test with non-string suffix."""
        with pytest.raises(ValueError, match="suffix must be string"):
            endswith("hello", 123)

        with pytest.raises(ValueError, match="suffix must be string"):
            endswith("hello", None)

    def test_endswith_workflow_file_filtering(self):
        """Test realistic workflow: filter files by extension."""
        files = [
            {"name": "script.py", "size": 1024},
            {"name": "data.json", "size": 2048},
            {"name": "config.py", "size": 512},
            {"name": "readme.md", "size": 256},
        ]

        python_files = [f for f in files if endswith(f["name"], ".py")]
        assert len(python_files) == 2
        assert all(endswith(f["name"], ".py") for f in python_files)


# ============================================================================
# Integration Tests
# ============================================================================


class TestUtilityIntegration:
    """Test integration of utility functions."""

    def test_combined_string_filtering(self):
        """Test using startswith and endswith together."""
        urls = [
            "https://api.example.com/users",
            "https://api.example.com/posts",
            "http://old.example.com/users",
            "https://api.example.com/admin",
        ]

        # Find HTTPS API URLs
        api_urls = [
            url
            for url in urls
            if startswith(url, "https://api") and endswith(url, "/users")
        ]

        assert len(api_urls) == 1
        assert api_urls[0] == "https://api.example.com/users"

    def test_take_with_filtered_list(self):
        """Test take() on filtered results."""
        alerts = [
            {"title": "CRITICAL: DB down", "id": 1},
            {"title": "INFO: User login", "id": 2},
            {"title": "CRITICAL: API failure", "id": 3},
            {"title": "WARNING: Slow query", "id": 4},
            {"title": "CRITICAL: Disk full", "id": 5},
        ]

        # Get first 2 critical alerts
        critical = [a for a in alerts if startswith(a["title"], "CRITICAL:")]
        top_critical = take(critical, 2)

        assert len(top_critical) == 2
        assert top_critical[0]["id"] == 1
        assert top_critical[1]["id"] == 3

    def test_strip_markdown_from_llm_then_parse(self):
        """Test extracting code from LLM response."""
        llm_response = """Here's the Python code:

```python
def process_alert(alert):
    if alert.severity == "high":
        return True
    return False
```

Use this function to filter alerts."""

        clean_code = strip_markdown(llm_response)

        # Verify code blocks removed
        assert "```" not in clean_code
        assert "def process_alert(alert):" in clean_code
        assert "filter alerts" in clean_code

    def test_workflow_alert_processing(self):
        """Test realistic alert processing workflow."""
        alerts = [
            {"src_ip": "192.168.1.100", "msg": "Login failed", "file": "auth.log"},
            {"src_ip": "10.0.0.50", "msg": "Access denied", "file": "access.log"},
            {"src_ip": "192.168.1.101", "msg": "Session timeout", "file": "auth.log"},
            {"src_ip": "8.8.8.8", "msg": "External request", "file": "access.log"},
            {"src_ip": "192.168.2.1", "msg": "Login success", "file": "auth.log"},
        ]

        # Find internal IPs (192.168.*) from auth.log, take first 2
        internal_auth = [
            a
            for a in alerts
            if startswith(a["src_ip"], "192.168") and endswith(a["file"], "auth.log")
        ]
        top_2 = take(internal_auth, 2)

        assert len(top_2) == 2
        assert top_2[0]["src_ip"] == "192.168.1.100"
        assert top_2[1]["src_ip"] == "192.168.1.101"
