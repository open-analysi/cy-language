"""LLM-based functions for the Cy language.

This module implements LLM-powered functions for agentic execution loops
using LangChain as the underlying framework.

NOTE: These functions are NOT registered with default_registry by default.
They are available for testing purposes but should not be exposed to end users
of the Cy language library. Tests can manually register them if needed.
"""

from collections.abc import Callable
from typing import Any

from langchain_openai import ChatOpenAI

from cy_language.ui.tools import ToolRegistry, register_tool_with_alias

# Create a separate registry for LLM functions (for testing only)
llm_registry = ToolRegistry()


@register_tool_with_alias(
    llm_registry,
    "llm_run",
    "llm::run",
    "Execute a prompt with an LLM and return the response",
)
async def llm_run(
    prompt: str, toolList: list[str] | None = None, useContext: bool = True
) -> str:
    """Execute a prompt with an LLM that can use available tools.

    Args:
        prompt: The prompt to send to the LLM
        toolList: List of tool names the LLM can use (None = all available tools)
        useContext: Whether to include available context in the prompt

    Returns:
        The LLM's response as a string, potentially using the provided tools
    """
    from cy_language.llm_config import llm_config

    # Handle edge cases
    if not prompt:
        prompt = "Please provide a helpful response."

    # Get LLM client
    try:
        client = llm_config.get_client()
    except Exception as e:
        raise Exception(f"LLM configuration error: {e!s}")

    # If no tools specified, fall back to basic text generation
    if not toolList:
        return await _basic_llm_call(client, prompt, useContext)

    # Use LangChain agent with tools
    try:
        return await _llm_call_with_tools(client, prompt, toolList, useContext)
    except Exception as e:
        print(f"Warning: Tool integration failed ({e}), falling back to basic LLM call")
        return await _basic_llm_call(client, prompt, useContext)


async def _basic_llm_call(client: ChatOpenAI, prompt: str, useContext: bool) -> str:
    """Basic LLM call without tools."""
    final_prompt = prompt

    if useContext:
        context_info = (
            "You are a helpful AI assistant integrated into the "
            "Cy programming language."
        )
        final_prompt = f"{context_info}\n\nUser request: {final_prompt}"

    try:
        response = await client.ainvoke(final_prompt)
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
    except Exception as e:
        raise Exception(f"LLM execution error: {e!s}")


async def _llm_call_with_tools(
    client: ChatOpenAI, prompt: str, toolList: list[str], useContext: bool
) -> str:
    """LLM call with tool access using LangChain agents."""
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain.tools import tool
    from langchain_core.prompts import ChatPromptTemplate

    # Get available tools from the global context
    available_tools = _get_available_tools()

    # Filter tools based on toolList
    selected_tools = {}
    for tool_name in toolList:
        if tool_name in available_tools:
            selected_tools[tool_name] = available_tools[tool_name]
        else:
            print(f"Warning: Requested tool '{tool_name}' not found in available tools")

    if not selected_tools:
        print("Warning: No valid tools found, falling back to basic LLM call")
        return await _basic_llm_call(client, prompt, useContext)

    # Create LangChain tools
    langchain_tools = []
    for tool_name, tool_func in selected_tools.items():
        # Create a wrapper function that preserves the original function
        def create_tool_wrapper(name: str, func: Callable) -> Callable:
            @tool(description=f"Tool: {name}")
            def tool_wrapper(*args: Any, **kwargs: Any) -> str:
                try:
                    result = func(*args, **kwargs)
                    return str(result)
                except Exception as e:
                    return f"Error calling {name}: {e!s}"

            return tool_wrapper

        langchain_tools.append(create_tool_wrapper(tool_name, tool_func))

    # Create agent prompt
    system_message = (
        "You are a helpful AI assistant integrated into the Cy programming language. "
        "You have access to tools that can help you complete tasks. "
        "Use the available tools when they would be helpful for answering the user's question. "
        f"Available tools: {', '.join(selected_tools.keys())}"
    )

    if useContext:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
    else:
        prompt_template = ChatPromptTemplate.from_messages(
            [("human", "{input}"), ("placeholder", "{agent_scratchpad}")]
        )

    # Create and run agent
    agent = create_tool_calling_agent(client, langchain_tools, prompt_template)  # type: ignore[arg-type]
    agent_executor = AgentExecutor(agent=agent, tools=langchain_tools, verbose=False)  # type: ignore[arg-type]

    response = await agent_executor.ainvoke({"input": prompt})

    if isinstance(response, dict) and "output" in response:
        return str(response["output"])
    return str(response)


def _get_available_tools() -> dict:
    """Get all available tools from the current Cy runtime context.

    Note: In async-only architecture (v0.2.0), MCP tools are not available
    within sync LLM functions. MCP tools are only accessible through the
    main async execution path (run_async).
    """
    # Return only LLM registry tools - MCP tools require async context
    return llm_registry.get_tools_dict().copy()


@register_tool_with_alias(
    llm_registry,
    "llm_evaluate_results",
    "llm::evaluate_results",
    "Use LLM to evaluate if results meet goals",
)
async def llm_evaluate_results(
    prompt: str,
    results: str,
    goals: str,
    toolList: list[str] | None = None,
    useContext: bool = True,
) -> bool:
    """Use an LLM to evaluate if results are satisfactory based on goals.

    Args:
        prompt: The original prompt that was executed
        results: The results to evaluate
        goals: The goals/criteria for evaluation
        toolList: List of tool names the LLM can use (None = all available tools)
        useContext: Whether to include available context in the prompt

    Returns:
        True if results meet the goals, False otherwise
    """
    evaluation_prompt = f"""Evaluate if the following results meet the specified goals.

Original prompt: {prompt}

Results to evaluate: {results}

Goals/Criteria: {goals}

Answer only with "True" if the results meet the goals, or "False" if they
don't. No other text."""

    try:
        response = await llm_run(
            evaluation_prompt, toolList=toolList, useContext=useContext
        )

        # Parse boolean from response
        response_lower = response.strip().lower()

        if response_lower in ["true", "yes", "1"]:
            return True
        if response_lower in ["false", "no", "0"]:
            return False
        # Default to False for unclear responses
        return False

    except Exception:
        # Default to False on error
        return False


@register_tool_with_alias(
    llm_registry,
    "llm_give_feedback",
    "llm::give_feedback",
    "Get LLM feedback on how to improve results",
)
async def llm_give_feedback(
    prompt: str,
    results: str,
    toolList: list[str] | None = None,
    useContext: bool = True,
) -> str:
    """Get feedback from an LLM on how to improve the results.

    Args:
        prompt: The original prompt that was executed
        results: The results to give feedback on
        toolList: List of tool names the LLM can use (None = all available tools)
        useContext: Whether to include available context in the prompt

    Returns:
        Feedback string on how to improve the results
    """
    feedback_prompt = f"""Provide constructive feedback on how to improve the following results.

Original prompt: {prompt}

Current results: {results}

Please provide specific, actionable feedback on how to make the results
better. Focus on what could be added, improved, or changed."""

    try:
        return str(
            await llm_run(feedback_prompt, toolList=toolList, useContext=useContext)
        )
    except Exception as e:
        return f"Unable to generate feedback: {e!s}"


@register_tool_with_alias(
    llm_registry,
    "llm_revise_task",
    "llm::revise_task",
    "Use LLM to revise a prompt based on feedback",
)
async def llm_revise_task(
    prompt: str,
    feedback: str,
    toolList: list[str] | None = None,
    useContext: bool = True,
) -> str:
    """Revise a prompt based on feedback to improve it.

    Args:
        prompt: The original prompt to revise
        feedback: Feedback on how to improve the prompt
        toolList: List of tool names the LLM can use (None = all available tools)
        useContext: Whether to include available context in the prompt

    Returns:
        The revised prompt incorporating the feedback
    """
    revision_prompt = f"""Revise the following prompt based on the provided feedback.

Original prompt: {prompt}

Feedback: {feedback}

Please provide an improved version of the prompt that addresses the
feedback. Return only the revised prompt."""

    try:
        return str(
            await llm_run(revision_prompt, toolList=toolList, useContext=useContext)
        )
    except Exception as e:
        return f"Unable to revise prompt: {e!s}"
