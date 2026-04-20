"""Unit tests for LLM-based functions in Cy language.

Tests for llm_run(), llm_evaluate_results(), llm_give_feedback(), and llm_revise_task()
using mocked LLM responses for fast execution without API calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cy_language.llm_functions import (
    llm_evaluate_results,
    llm_give_feedback,
    llm_revise_task,
    llm_run,
)


class TestLLMRun:
    """Test cases for the llm_run() function with mocked responses."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_simple_prompt(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() with simple prompt - should return string response."""
        # Mock LLM client to return a simple response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is a test response"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "What is 2 + 2?"
        result = await llm_run(prompt)

        assert isinstance(result, str)
        assert result == "This is a test response"
        mock_client.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_with_tool_list(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() with toolList parameter - should restrict available tools."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response with specific tools"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Calculate something"
        tool_list = ["add", "multiply"]
        result = await llm_run(prompt, toolList=tool_list)

        assert isinstance(result, str)
        assert result == "Response with specific tools"
        # Verify toolList was passed to the LLM configuration
        mock_client.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_with_context_true(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() with useContext=True - should include context in prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response with context"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Analyze the data"
        result = await llm_run(prompt, useContext=True)

        assert isinstance(result, str)
        assert result == "Response with context"
        # In actual implementation, should verify context was included in prompt

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_with_context_false(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() with useContext=False - should exclude context."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response without context"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Simple question"
        result = await llm_run(prompt, useContext=False)

        assert isinstance(result, str)
        assert result == "Response without context"

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_with_empty_tool_list(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_run() with empty toolList - should use all available tools."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response with all tools"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Do something complex"
        result = await llm_run(prompt, toolList=[])

        assert isinstance(result, str)
        assert result == "Response with all tools"

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_default_parameters(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() with default parameters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Default response"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Test with defaults"
        result = await llm_run(prompt)

        assert isinstance(result, str)
        assert result == "Default response"

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_api_failure(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() error handling for API failures."""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("API connection failed"))
        mock_get_client.return_value = mock_client

        prompt = "This will fail"

        # Should handle the exception gracefully
        with pytest.raises(Exception, match="API connection failed"):
            await llm_run(prompt)

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_run_invalid_prompt(self, mock_get_client: MagicMock) -> None:
        """Test llm_run() error handling for invalid prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Handled invalid prompt"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        # Test with None prompt
        result = await llm_run(None)
        assert isinstance(result, str)

        # Test with empty prompt
        result = await llm_run("")
        assert isinstance(result, str)


class TestLLMEvaluateResults:
    """Test cases for the llm_evaluate_results() function."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_evaluate_results_positive(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_evaluate_results() with good results - should return True."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "True"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "What is the capital of France?"
        results = "Paris"
        goals = "Provide correct geographical information"

        evaluation = await llm_evaluate_results(prompt, results, goals)
        assert isinstance(evaluation, bool)
        assert evaluation is True

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_evaluate_results_negative(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_evaluate_results() with poor results - should return False."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "False"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "What is the capital of France?"
        results = "London"
        goals = "Provide correct geographical information"

        evaluation = await llm_evaluate_results(prompt, results, goals)
        assert isinstance(evaluation, bool)
        assert evaluation is False

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_evaluate_results_with_specific_goals(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_evaluate_results() with specific goals parameter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "True"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Write a story"
        results = "Once upon a time, there was a brave knight..."
        goals = "The story should be engaging and have a clear beginning"

        evaluation = await llm_evaluate_results(prompt, results, goals)
        assert isinstance(evaluation, bool)
        assert evaluation is True

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_evaluate_results_boolean_conversion_edge_cases(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_evaluate_results() boolean conversion edge cases."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Test various LLM responses that should be interpreted as boolean
        test_cases = [
            ("yes", True),
            ("Yes", True),
            ("YES", True),
            ("no", False),
            ("No", False),
            ("NO", False),
            ("true", True),
            ("TRUE", True),
            ("false", False),
            ("FALSE", False),
            ("1", True),
            ("0", False),
        ]

        for llm_response, expected_result in test_cases:
            mock_response = MagicMock()
            mock_response.content = llm_response
            mock_client.ainvoke = AsyncMock(return_value=mock_response)

            result = await llm_evaluate_results("test", "test", "test")
            assert result is expected_result, f"Failed for response: {llm_response}"

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_evaluate_results_api_failure(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_evaluate_results() error handling for API failures."""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("Evaluation API failed"))
        mock_get_client.return_value = mock_client

        # Should return False on API failure, not raise exception
        result = await llm_evaluate_results("prompt", "results", "goals")
        assert result is False


class TestLLMGiveFeedback:
    """Test cases for the llm_give_feedback() function."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_give_feedback_basic(self, mock_get_client: MagicMock) -> None:
        """Test llm_give_feedback() with prompt and results - should return feedback string."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = (
            "Consider adding more details to make the story more engaging."
        )
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Write a short story"
        results = "Once upon a time."

        feedback = await llm_give_feedback(prompt, results)
        assert isinstance(feedback, str)
        assert len(feedback) > 0
        assert "Consider adding" in feedback

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_give_feedback_different_quality_results(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_give_feedback() with different quality of results."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Good results - should get minimal feedback
        mock_response = MagicMock()
        mock_response.content = "The response is well-structured and complete."
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        good_results = "Paris is the capital and largest city of France."
        feedback = await llm_give_feedback(
            "What is the capital of France?", good_results
        )
        assert "well-structured" in feedback

        # Poor results - should get detailed improvement suggestions
        mock_response = MagicMock()
        mock_response.content = (
            "The answer is incomplete. Consider providing more context and details."
        )
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        poor_results = "Paris"
        feedback = await llm_give_feedback(
            "What is the capital of France?", poor_results
        )
        assert "incomplete" in feedback

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_give_feedback_with_tool_list(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_give_feedback() with toolList parameter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Use the calculation tools for better accuracy."
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        prompt = "Calculate the area of a circle"
        results = "Approximately 78.5"
        tool_list = ["multiply", "add"]

        feedback = await llm_give_feedback(prompt, results, toolList=tool_list)
        assert isinstance(feedback, str)
        assert "calculation tools" in feedback

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_give_feedback_api_failure(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_give_feedback() error handling for API failures."""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("Feedback API failed"))
        mock_get_client.return_value = mock_client

        # Should return error message string on API failure, not raise exception
        result = await llm_give_feedback("prompt", "results")
        assert isinstance(result, str)
        assert "Unable to generate feedback" in result


class TestLLMReviseTask:
    """Test cases for the llm_revise_task() function."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_revise_task_basic(self, mock_get_client: MagicMock) -> None:
        """Test llm_revise_task() with prompt and feedback - should return revised prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = (
            "Write a detailed short story with character development and plot"
        )
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        original_prompt = "Write a story"
        feedback = "Add more details and character development"

        revised = await llm_revise_task(original_prompt, feedback)
        assert isinstance(revised, str)
        assert len(revised) > len(original_prompt)
        assert "detailed" in revised
        assert "character development" in revised

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_revise_task_different_feedback_types(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_revise_task() with different types of feedback."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        original_prompt = "Explain quantum physics"

        # Feedback about complexity
        mock_response = MagicMock()
        mock_response.content = "Explain quantum physics in simple terms for beginners"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        complexity_feedback = "Make it simpler for beginners"
        revised = await llm_revise_task(original_prompt, complexity_feedback)
        assert "simple terms" in revised or "beginners" in revised

        # Feedback about specificity
        mock_response = MagicMock()
        mock_response.content = "Explain the double-slit experiment in quantum physics"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        specificity_feedback = "Be more specific about experiments"
        revised = await llm_revise_task(original_prompt, specificity_feedback)
        assert "experiment" in revised or "specific" in revised

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_revise_task_with_parameters(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_revise_task() with toolList and useContext parameters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Calculate the area using mathematical tools"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        original_prompt = "Find the area"
        feedback = "Use proper mathematical tools"
        tool_list = ["multiply", "divide"]

        revised = await llm_revise_task(
            original_prompt, feedback, toolList=tool_list, useContext=True
        )
        assert isinstance(revised, str)
        assert "mathematical tools" in revised

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_revise_task_iterative_revisions(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_revise_task() with iterative revisions."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First revision
        mock_response = MagicMock()
        mock_response.content = "Write a detailed story about adventure"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        prompt_v1 = "Write a story"
        feedback_v1 = "Add more details"
        revised_v1 = await llm_revise_task(prompt_v1, feedback_v1)

        # Second revision
        mock_response = MagicMock()
        mock_response.content = "Write a detailed adventure story with a brave hero"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        feedback_v2 = "Include a hero character"
        revised_v2 = await llm_revise_task(revised_v1, feedback_v2)

        assert len(revised_v2) > len(revised_v1)
        assert "hero" in revised_v2

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_revise_task_api_failure(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test llm_revise_task() error handling for API failures."""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("Revision API failed"))
        mock_get_client.return_value = mock_client

        # Should return error message string on API failure, not raise exception
        result = await llm_revise_task("prompt", "feedback")
        assert isinstance(result, str)
        assert "Unable to revise prompt" in result


class TestLLMFunctionsIntegration:
    """Integration tests for LLM functions working together."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_functions_workflow(self, mock_get_client: MagicMock) -> None:
        """Test a complete workflow using all LLM functions together."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Step 1: Initial LLM run
        mock_response = MagicMock()
        mock_response.content = "A short story."
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        initial_result = await llm_run("Write a story")
        assert initial_result == "A short story."

        # Step 2: Evaluate results (poor quality)
        mock_response = MagicMock()
        mock_response.content = "False"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        evaluation = await llm_evaluate_results(
            "Write a story", initial_result, "Create an engaging story"
        )
        assert evaluation is False

        # Step 3: Get feedback
        mock_response = MagicMock()
        mock_response.content = "Add more details and character development"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        feedback = await llm_give_feedback("Write a story", initial_result)
        assert "details" in feedback

        # Step 4: Revise the task
        mock_response = MagicMock()
        mock_response.content = "Write a detailed story with characters and plot"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        revised_prompt = await llm_revise_task("Write a story", feedback)
        assert len(revised_prompt) > len("Write a story")

        # Step 5: Run again with revised prompt
        mock_response = MagicMock()
        mock_response.content = (
            "Once upon a time, there was a brave knight named Sir Arthur..."
        )
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        final_result = await llm_run(revised_prompt)
        assert len(final_result) > len(initial_result)

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_llm_functions_parameter_consistency(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test that all LLM functions handle parameters consistently."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        tool_list = ["add", "multiply"]
        use_context = False

        # All functions should accept the same optional parameters
        await llm_run("test", toolList=tool_list, useContext=use_context)
        await llm_evaluate_results(
            "test", "test", "test", toolList=tool_list, useContext=use_context
        )
        await llm_give_feedback(
            "test", "test", toolList=tool_list, useContext=use_context
        )
        await llm_revise_task(
            "test", "test", toolList=tool_list, useContext=use_context
        )

        # Each function should have been called
        assert mock_client.ainvoke.call_count == 4
