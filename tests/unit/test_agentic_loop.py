"""Integration tests for complete agentic loop workflows.

Tests the full agentic execution loop combining all LLM functions
for realistic AI agent scenarios as described in the design document.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cy_language.llm_functions import (
    llm_evaluate_results,
    llm_give_feedback,
    llm_revise_task,
    llm_run,
)


class TestAgenticLoopMocked:
    """Test agentic loops with mocked LLM responses for predictable testing."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_basic_agentic_loop_success_first_try(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop that succeeds on first try."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock sequence: run -> evaluate (success)
        mock_responses = [
            "A comprehensive story about Mars with detailed characters and plot.",  # llm_run
            "True",  # llm_evaluate_results
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        # Execute basic agentic loop
        task = "Write a story about Mars"
        goals = "Create an engaging story with characters and plot"

        # Step 1: Initial execution
        result = await llm_run(task)
        assert isinstance(result, str)
        assert "Mars" in result

        # Step 2: Evaluation
        evaluation = await llm_evaluate_results(task, result, goals)
        assert evaluation is True

        # Since evaluation passed, no feedback/revision needed
        assert mock_client.ainvoke.call_count == 2

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_with_one_iteration(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop that requires one improvement iteration."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock sequence: run -> evaluate (fail) -> feedback -> revise -> run -> evaluate (success)
        mock_responses = [
            "Mars is red.",  # Initial llm_run (poor quality)
            "False",  # llm_evaluate_results (fails)
            "The story needs more detail, characters, and plot development.",  # llm_give_feedback
            "Write a detailed story about Mars with interesting characters and a compelling plot.",  # llm_revise_task
            "On the red planet Mars, Commander Sarah Chen discovered ancient ruins...",  # Improved llm_run
            "True",  # llm_evaluate_results (success)
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        # Execute iterative agentic loop
        task = "Write a story about Mars"
        goals = "Create an engaging story with characters and plot"
        max_iterations = 3

        current_task = task
        for _iteration in range(max_iterations):
            # Step 1: Execute current task
            result = await llm_run(current_task)
            assert isinstance(result, str)

            # Step 2: Evaluate result
            evaluation = await llm_evaluate_results(current_task, result, goals)
            assert isinstance(evaluation, bool)

            if evaluation:
                # Success! Break out of loop
                break

            # Step 3: Get feedback for improvement
            feedback = await llm_give_feedback(current_task, result)
            assert isinstance(feedback, str)
            assert len(feedback) > 0

            # Step 4: Revise the task based on feedback
            current_task = await llm_revise_task(current_task, feedback)
            assert isinstance(current_task, str)
            assert len(current_task) > len(task)  # Should be more detailed

        # Should have succeeded after one iteration
        assert evaluation is True
        assert mock_client.ainvoke.call_count == 6

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_max_iterations_reached(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop that reaches maximum iterations without success."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock all evaluations to fail
        mock_responses = []
        for i in range(5):  # 5 iterations
            mock_responses.extend(
                [
                    f"Attempt {i + 1}: Still not good enough.",  # llm_run
                    "False",  # llm_evaluate_results (always fails)
                    f"Iteration {i + 1}: Need more improvement.",  # llm_give_feedback
                    f"Revised task attempt {i + 1}: Write better story with more details.",  # llm_revise_task
                ]
            )

        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        # Execute agentic loop with max iterations
        task = "Write a story"
        goals = "Perfect story"
        max_iterations = 5

        current_task = task
        final_evaluation = False

        for iteration in range(max_iterations):
            result = await llm_run(current_task)
            evaluation = await llm_evaluate_results(current_task, result, goals)

            if evaluation:
                final_evaluation = True
                break

            if iteration < max_iterations - 1:  # Don't get feedback on last iteration
                feedback = await llm_give_feedback(current_task, result)
                current_task = await llm_revise_task(current_task, feedback)

        # Should have reached max iterations without success
        assert final_evaluation is False
        assert iteration == max_iterations - 1

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_with_tool_restrictions(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop with specific tool restrictions."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "Calculated: 78.54",  # llm_run with math tools
            "False",  # Not detailed enough
            "Show the calculation steps",  # feedback
            "Calculate the area of a circle with radius 5, showing all steps",  # revised
            "Area = π × r² = 3.14159 × 5² = 3.14159 × 25 = 78.54",  # improved result
            "True",  # Success
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        # Test with restricted tool list
        task = "Calculate the area of a circle with radius 5"
        goals = "Provide accurate calculation with clear steps"
        tool_list = ["multiply", "add"]

        # Execute agentic loop with tools
        current_task = task
        for _iteration in range(3):
            result = await llm_run(current_task, toolList=tool_list)
            evaluation = await llm_evaluate_results(
                current_task, result, goals, toolList=tool_list
            )

            if evaluation:
                break

            feedback = await llm_give_feedback(current_task, result, toolList=tool_list)
            current_task = await llm_revise_task(
                current_task, feedback, toolList=tool_list
            )

        assert evaluation is True

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_error_recovery(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop handles errors gracefully."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock an API error on second call, then recovery
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content="Initial result"),  # llm_run succeeds
            Exception("API temporarily unavailable"),  # llm_evaluate_results fails
            MagicMock(content="False"),  # llm_evaluate_results succeeds on retry
            MagicMock(content="Add more details"),  # llm_give_feedback
            MagicMock(content="Write detailed story"),  # llm_revise_task
            MagicMock(content="Detailed story result"),  # llm_run
            MagicMock(content="True"),  # llm_evaluate_results success
        ]

        task = "Write a story"
        goals = "Good story"

        # Should handle the API error and continue
        result = await llm_run(task)

        # First evaluation attempt fails (but returns False instead of raising)
        evaluation = await llm_evaluate_results(task, result, goals)
        assert evaluation is False  # Should return False on API error

        # Retry evaluation (simulating error recovery)
        evaluation = await llm_evaluate_results(task, result, goals)
        assert evaluation is False

        # Continue with feedback loop
        feedback = await llm_give_feedback(task, result)
        revised_task = await llm_revise_task(task, feedback)
        improved_result = await llm_run(revised_task)
        final_evaluation = await llm_evaluate_results(
            revised_task, improved_result, goals
        )

        assert final_evaluation is True


class TestAgenticLoopComplexScenarios:
    """Test complex agentic loop scenarios with realistic use cases."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_creative_writing_agentic_loop(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop for creative writing improvement."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Simulate a creative writing improvement process
        mock_responses = [
            "A short story about a robot.",  # Initial attempt
            "False",  # Not creative enough
            "Add more character development, dialogue, and emotional depth.",  # Feedback
            "Write a compelling story about a robot with rich character development, meaningful dialogue, and emotional depth.",  # Revised task
            "ARIA-7 had served the Murphy family for three years, but tonight felt different. 'Mommy, why is ARIA sad?' asked little Emma, pointing at the robot's dimmed optical sensors...",  # Improved story
            "True",  # Success
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        # Execute creative writing loop
        results = await self._execute_agentic_loop(
            task="Write a story about a robot",
            goals="Create an emotionally engaging story with character development",
            max_iterations=3,
        )

        assert results["success"] is True
        assert results["iterations"] == 2
        assert len(results["final_result"]) > len("A short story about a robot.")

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_technical_explanation_agentic_loop(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop for technical explanation improvement."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "Quantum computing uses qubits.",  # Too brief
            "False",  # Not detailed enough
            "Provide more detail about how qubits work and why they're different from classical bits.",
            "Explain quantum computing in detail, covering how qubits work and their advantages over classical bits.",
            "Quantum computing leverages quantum mechanical phenomena like superposition and entanglement. Unlike classical bits that exist in definite 0 or 1 states, qubits can exist in superposition...",
            "True",
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        results = await self._execute_agentic_loop(
            task="Explain quantum computing",
            goals="Provide a clear, detailed explanation suitable for technical audience",
            max_iterations=3,
        )

        assert results["success"] is True
        assert "superposition" in results["final_result"]
        assert "qubits" in results["final_result"]

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_data_analysis_agentic_loop(self, mock_get_client: MagicMock) -> None:
        """Test agentic loop for data analysis task improvement."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "The data shows some trends.",  # Vague analysis
            "False",  # Not specific enough
            "Provide specific numbers, trends, and actionable insights from the data.",
            "Analyze the sales data providing specific metrics, trend analysis, and actionable business insights.",
            "Sales analysis reveals 23% increase in Q3, driven primarily by mobile segment (45% growth). Recommend expanding mobile marketing budget by 30% for Q4...",
            "True",
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        results = await self._execute_agentic_loop(
            task="Analyze the sales data",
            goals="Provide specific insights with numbers and recommendations",
            max_iterations=3,
            tool_list=["add", "multiply", "summarize"],
        )

        assert results["success"] is True
        assert "23%" in results["final_result"]
        assert "Recommend" in results["final_result"]

    async def _execute_agentic_loop(
        self,
        task: str,
        goals: str,
        max_iterations: int = 5,
        tool_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """Helper method to execute a complete agentic loop."""
        current_task = task
        iteration = 0
        success = False
        final_result = ""

        for iteration in range(max_iterations):
            # Execute task
            result = await llm_run(current_task, toolList=tool_list)
            final_result = result

            # Evaluate result
            evaluation = await llm_evaluate_results(
                current_task, result, goals, toolList=tool_list
            )

            if evaluation:
                success = True
                break

            # Get feedback and revise
            feedback = await llm_give_feedback(current_task, result, toolList=tool_list)
            current_task = await llm_revise_task(
                current_task, feedback, toolList=tool_list
            )

        return {
            "success": success,
            "iterations": iteration + 1,
            "final_result": final_result,
            "final_task": current_task,
        }


class TestAgenticLoopEdgeCases:
    """Test edge cases and error conditions in agentic loops."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_empty_responses(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop handles empty LLM responses."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "",  # Empty initial response
            "False",  # Evaluation
            "The response was empty. Please provide a substantive answer.",  # Feedback
            "Provide a detailed response to: What is artificial intelligence?",  # Revised
            "Artificial intelligence is a field of computer science...",  # Good response
            "True",  # Success
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        results = await self._execute_agentic_loop(
            task="What is artificial intelligence?",
            goals="Provide informative explanation",
            max_iterations=3,
        )

        assert results["success"] is True
        assert len(results["final_result"]) > 0

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_agentic_loop_inconsistent_evaluation(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop handles inconsistent evaluation responses."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Include non-standard evaluation responses
        mock_responses = [
            "Sample response",  # llm_run
            "Maybe",  # Non-boolean evaluation
            "Be more specific",  # feedback
            "Provide more specific response",  # revision
            "More specific response here",  # llm_run
            "Yes",  # Boolean-like evaluation
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        task = "Provide an example"
        goals = "Clear example"

        # First iteration with unclear evaluation
        result1 = await llm_run(task)
        evaluation1 = await llm_evaluate_results(task, result1, goals)

        # Should handle non-standard responses (implementation dependent)
        assert isinstance(evaluation1, bool)

        # Continue with improvement
        feedback = await llm_give_feedback(task, result1)
        revised_task = await llm_revise_task(task, feedback)
        result2 = await llm_run(revised_task)
        evaluation2 = await llm_evaluate_results(revised_task, result2, goals)

        assert isinstance(evaluation2, bool)

    async def _execute_agentic_loop(
        self,
        task: str,
        goals: str,
        max_iterations: int = 5,
        tool_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """Helper method to execute a complete agentic loop."""
        current_task = task
        iteration = 0
        success = False
        final_result = ""

        for iteration in range(max_iterations):
            # Execute task
            result = await llm_run(current_task, toolList=tool_list)
            final_result = result

            # Evaluate result
            evaluation = await llm_evaluate_results(
                current_task, result, goals, toolList=tool_list
            )

            if evaluation:
                success = True
                break

            # Get feedback and revise
            feedback = await llm_give_feedback(current_task, result, toolList=tool_list)
            current_task = await llm_revise_task(
                current_task, feedback, toolList=tool_list
            )

        return {
            "success": success,
            "iterations": iteration + 1,
            "final_result": final_result,
            "final_task": current_task,
        }


class TestAgenticLoopRealWorldScenarios:
    """Test agentic loops with real-world inspired scenarios."""

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_code_generation_improvement_loop(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop for iterative code improvement."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "def sort_list(lst): return sorted(lst)",  # Basic implementation
            "False",  # Missing error handling
            "Add input validation and error handling for edge cases.",
            "Write a robust list sorting function with input validation and error handling.",
            "def sort_list(lst):\n    if not isinstance(lst, list):\n        raise TypeError('Input must be a list')\n    if not lst:\n        return []\n    return sorted(lst)",
            "True",
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        results = await self._execute_agentic_loop(
            task="Write a function to sort a list",
            goals="Robust function with error handling and validation",
            max_iterations=3,
        )

        assert results["success"] is True
        assert "TypeError" in results["final_result"]
        assert "isinstance" in results["final_result"]

    @pytest.mark.asyncio
    @patch("cy_language.llm_config.llm_config.get_client")
    async def test_business_proposal_refinement_loop(
        self, mock_get_client: MagicMock
    ) -> None:
        """Test agentic loop for business proposal improvement."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_responses = [
            "We should build an app.",  # Vague proposal
            "False",  # Too vague
            "Include specific market analysis, target audience, revenue model, and competitive advantages.",
            "Create a comprehensive business proposal for a mobile app including market analysis, target audience, revenue model, and competitive advantages.",
            "Mobile Food Delivery App Proposal:\nMarket: $150B global food delivery market growing 11% annually\nTarget: Urban professionals aged 25-40\nRevenue: 15% commission + subscription model\nAdvantage: AI-powered recommendations and 30-min guarantee",
            "True",
        ]
        mock_client.ainvoke = AsyncMock()
        mock_client.ainvoke.side_effect = [
            MagicMock(content=response) for response in mock_responses
        ]

        results = await self._execute_agentic_loop(
            task="Create a business proposal for a new product",
            goals="Comprehensive proposal with market analysis and financials",
            max_iterations=3,
        )

        assert results["success"] is True
        assert "$150B" in results["final_result"]
        assert "Revenue:" in results["final_result"]

    async def _execute_agentic_loop(
        self,
        task: str,
        goals: str,
        max_iterations: int = 5,
        tool_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """Helper method to execute a complete agentic loop."""
        current_task = task
        iteration = 0
        success = False
        final_result = ""

        for iteration in range(max_iterations):
            # Execute task
            result = await llm_run(current_task, toolList=tool_list)
            final_result = result

            # Evaluate result
            evaluation = await llm_evaluate_results(
                current_task, result, goals, toolList=tool_list
            )

            if evaluation:
                success = True
                break

            # Get feedback and revise
            feedback = await llm_give_feedback(current_task, result, toolList=tool_list)
            current_task = await llm_revise_task(
                current_task, feedback, toolList=tool_list
            )

        return {
            "success": success,
            "iterations": iteration + 1,
            "final_result": final_result,
            "final_task": current_task,
        }
