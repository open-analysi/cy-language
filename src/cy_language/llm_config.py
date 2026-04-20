"""LLM configuration and provider management for Cy language.

This module handles LLM provider configuration, model selection,
and connection management for LLM-based functions.
"""

import os
from typing import Any

from pydantic import SecretStr


class LLMConfig:
    """Configuration manager for LLM providers and models."""

    def __init__(self) -> None:
        """Initialize LLM configuration with default settings."""
        self.provider = "openai"  # Default provider
        self.model = "gpt-4o"  # Default model
        self.api_key: str | None = None
        self.timeout = 30  # Default timeout in seconds
        self.max_tokens = 1000  # Default max tokens

        # Load configuration from environment
        self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Load OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Load optional configuration overrides
        self.provider = os.getenv("CY_LLM_PROVIDER", self.provider)
        self.model = os.getenv("CY_LLM_MODEL", self.model)

        # Load numeric settings with defaults
        try:
            self.timeout = int(os.getenv("CY_LLM_TIMEOUT", str(self.timeout)))
            self.max_tokens = int(os.getenv("CY_LLM_MAX_TOKENS", str(self.max_tokens)))
        except ValueError:
            # Keep defaults if environment values are invalid
            pass

    def get_client(self) -> Any:
        """Get the configured LLM client.

        Returns:
            Configured LangChain LLM client
        """
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI

            if not self.api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                )

            return ChatOpenAI(
                model=self.model,
                api_key=SecretStr(self.api_key),
                timeout=self.timeout,
                max_completion_tokens=self.max_tokens,
                temperature=0,  # Deterministic for better tool usage
            )
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def validate_configuration(self) -> bool:
        """Validate that the LLM configuration is valid.

        Returns:
            True if configuration is valid, False otherwise
        """
        if self.provider == "openai":
            # Check API key is available
            if not self.api_key:
                return False

            # Basic validation - key should be non-empty string
            return isinstance(self.api_key, str) and len(self.api_key.strip()) > 0

        return False


# Global configuration instance
llm_config = LLMConfig()
