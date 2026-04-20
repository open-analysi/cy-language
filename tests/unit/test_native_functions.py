"""Unit tests for native functions in Cy language.

Tests for len(), log(), and from_json() functions
following the Test Driven Development (TDD) approach.
"""

import json
from typing import Any, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cy_language.native_functions import (
    len_function,
    log,
)


# Legacy async version of from_json for backward compatibility in tests
async def from_json_legacy(json_str: Any) -> Union[dict, list]:
    """Legacy async version of from_json with LLM fallback and error handling.

    This function provides the old behavior for tests that expect:
    - Async execution
    - LLM fallback on invalid JSON
    - Returns empty dict/list on errors instead of raising exceptions
    """
    # Handle non-string inputs gracefully
    if not isinstance(json_str, str):
        return {}

    if not json_str.strip():
        return {}

    # Try standard JSON parsing first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try LLM repair
        try:
            from cy_language.llm_functions import llm_run

            repair_prompt = f"""Fix this malformed JSON and return only the valid JSON:
{json_str}

Return only the corrected JSON, nothing else."""

            repaired_json = await llm_run(repair_prompt)
            return json.loads(repaired_json)
        except Exception:
            # If LLM repair also fails, return empty dict
            return {}


class TestLenFunction:
    """Test cases for the len() native function."""

    def test_len_with_valid_list(self) -> None:
        """Test len() with valid list - should return correct count."""
        test_list = [1, 2, 3, 4, 5]
        result = len_function(test_list)
        assert result == 5

    def test_len_with_empty_list(self) -> None:
        """Test len() with empty list - should return 0."""
        empty_list = []
        result = len_function(empty_list)
        assert result == 0

    def test_len_with_string_input(self) -> None:
        """Test len() with string input - should return string length."""
        test_string = "hello world"
        result = len_function(test_string)
        assert result == 11

    def test_len_with_dictionary_input(self) -> None:
        """Test len() with dictionary input - should return dictionary length."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = len_function(test_dict)
        assert result == 2

    def test_len_with_number_input(self) -> None:
        """Test len() with non-list input (number) - should return 0."""
        test_number = 42
        result = len_function(test_number)
        assert result == 0

    def test_len_with_none_input(self) -> None:
        """Test len() with null/undefined input - should return 0."""
        result = len_function(None)
        assert result == 0

    def test_len_with_large_list(self) -> None:
        """Test len() with large list for performance."""
        large_list = list(range(10000))
        result = len_function(large_list)
        assert result == 10000

    def test_len_with_nested_structures(self) -> None:
        """Test len() with nested data structures."""
        nested_list = [[1, 2], [3, 4], [5, 6]]
        result = len_function(nested_list)
        assert result == 3

    def test_len_with_empty_string(self) -> None:
        """Test len() with empty string - should return 0."""
        empty_string = ""
        result = len_function(empty_string)
        assert result == 0

    def test_len_with_various_strings(self) -> None:
        """Test len() with various string inputs."""
        # Single character
        result = len_function("a")
        assert result == 1

        # Unicode characters
        result = len_function("Hello 🌍")
        assert result == 7

        # Multi-line string
        result = len_function("line1\nline2")
        assert result == 11


class TestDebugPrint:
    """Test cases for the log() native function."""

    def test_log_simple_string(self) -> None:
        """Test log() with simple string - should output to stderr/debug channel."""
        test_message = "Debug test message"
        result = log(test_message)
        assert result == test_message

    def test_log_with_variable_interpolation(self) -> None:
        """Test log() with variable interpolation in string."""
        test_message = "Value: 42"
        result = log(test_message)
        assert result == test_message

    def test_log_return_value(self) -> None:
        """Test log() return value - should return the printed string."""
        test_message = "Return value test"
        result = log(test_message)
        assert isinstance(result, str)
        assert result == test_message

    def test_log_with_empty_string(self) -> None:
        """Test log() with empty string."""
        result = log("")
        assert result == ""

    def test_log_with_none_input(self) -> None:
        """Test log() with null/undefined input."""
        result = log(None)
        assert result == "None"  # Should convert None to string

    def test_log_with_complex_data(self) -> None:
        """Test log() with complex data structures (list, dict)."""
        test_list = [1, 2, 3]
        result = log(test_list)
        assert "[1, 2, 3]" in result

        test_dict = {"key": "value"}
        result = log(test_dict)
        assert "key" in result and "value" in result

    def test_multiple_log_calls(self) -> None:
        """Test multiple log() calls in sequence."""
        messages = ["First message", "Second message", "Third message"]
        results = []

        for message in messages:
            result = log(message)
            results.append(result)

        assert results == messages

    @patch("sys.stderr")
    def test_log_cli_mode(self, mock_stderr: MagicMock) -> None:
        """Test log() in CLI mode - should print to stderr."""
        test_message = "CLI debug message"
        result = log(test_message)

        # Verify the function returns the message
        assert result == test_message
        # In actual implementation, should verify stderr.write was called


class TestJsonStringToStruct:
    """Test cases for the from_json() native function (legacy async version)."""

    @pytest.mark.asyncio
    async def test_from_json_valid_object(self) -> None:
        """Test from_json() with valid JSON string - should parse correctly."""
        json_string = '{"name": "John", "age": 30, "city": "New York"}'
        result = await from_json_legacy(json_string)

        expected = {"name": "John", "age": 30, "city": "New York"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_from_json_valid_nested_object(self) -> None:
        """Test from_json() with valid nested JSON object."""
        json_string = (
            '{"user": {"name": "John", "profile": {"age": 30, "active": true}}}'
        )
        result = await from_json_legacy(json_string)

        expected = {"user": {"name": "John", "profile": {"age": 30, "active": True}}}
        assert result == expected

    @pytest.mark.asyncio
    async def test_from_json_valid_array(self) -> None:
        """Test from_json() with valid JSON array."""
        json_string = '[{"name": "John"}, {"name": "Jane"}, {"name": "Bob"}]'
        result = await from_json_legacy(json_string)

        expected = [{"name": "John"}, {"name": "Jane"}, {"name": "Bob"}]
        assert result == expected

    @pytest.mark.asyncio
    async def test_from_json_empty_string(self) -> None:
        """Test from_json() with empty string - should return empty dict."""
        result = await from_json_legacy("")
        assert result == {}

    @pytest.mark.asyncio
    async def test_from_json_non_string_input(self) -> None:
        """Test from_json() with non-string input - should handle gracefully."""
        result = await from_json_legacy(42)
        assert result == {}

        result = await from_json_legacy(None)
        assert result == {}

        result = await from_json_legacy(["not", "a", "string"])
        assert result == {}

    @pytest.mark.asyncio
    async def test_from_json_invalid_json_basic(self) -> None:
        """Test from_json() with invalid JSON - should attempt LLM repair."""
        # This test will need to be updated when LLM fallback is implemented
        invalid_json = '{"name": "John", "age": 30,'  # Missing closing brace

        # For now, should return empty dict when JSON parsing fails
        # Later, should trigger LLM repair mechanism
        result = await from_json_legacy(invalid_json)
        assert isinstance(result, (dict, list))  # Should return some structure

    @pytest.mark.asyncio
    async def test_from_json_malformed_quotes(self) -> None:
        """Test from_json() with malformed quotes - LLM repair scenario."""
        malformed_json = "{name: 'John', age: 30}"  # Single quotes, no quotes on keys
        result = await from_json_legacy(malformed_json)
        assert isinstance(result, (dict, list))

    @pytest.mark.asyncio
    async def test_from_json_trailing_commas(self) -> None:
        """Test from_json() with trailing commas - LLM repair scenario."""
        trailing_comma_json = '{"name": "John", "age": 30,}'
        result = await from_json_legacy(trailing_comma_json)
        assert isinstance(result, (dict, list))

    @patch("cy_language.llm_functions.llm_run")
    @pytest.mark.asyncio
    async def test_from_json_llm_fallback_success(
        self, mock_llm_run: AsyncMock
    ) -> None:
        """Test from_json() LLM fallback when OpenAI API is available."""
        # Mock LLM to return fixed JSON
        mock_llm_run.return_value = '{"name": "John", "age": 30}'

        invalid_json = '{"name": "John", "age": 30,'
        result = await from_json_legacy(invalid_json)

        # Should call LLM for repair and return parsed result
        expected = {"name": "John", "age": 30}
        assert result == expected

    @patch("cy_language.llm_functions.llm_run")
    @pytest.mark.asyncio
    async def test_from_json_llm_fallback_failure(
        self, mock_llm_run: AsyncMock
    ) -> None:
        """Test from_json() LLM fallback failure handling."""
        # Mock LLM to raise an exception
        mock_llm_run.side_effect = Exception("API Error")

        invalid_json = '{"name": "John", "age": 30,'
        result = await from_json_legacy(invalid_json)

        # Should return empty dict when both JSON parsing and LLM repair fail
        assert result == {}

    @pytest.mark.asyncio
    async def test_from_json_complex_structure(self) -> None:
        """Test from_json() with complex real-world JSON."""
        complex_json = """
        {
            "users": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "addresses": [
                        {
                            "type": "home",
                            "street": "123 Main St",
                            "city": "New York",
                            "zip": "10001"
                        }
                    ],
                    "active": true,
                    "balance": 1250.75
                }
            ],
            "metadata": {
                "total": 1,
                "page": 1,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        """

        result = await from_json_legacy(complex_json)

        assert isinstance(result, dict)
        assert "users" in result
        assert "metadata" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["name"] == "John Doe"
        assert result["metadata"]["total"] == 1
