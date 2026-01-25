"""LLM provider factory for switching between Ollama and Anthropic."""

from enum import Enum
from functools import lru_cache
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from deepthought.config import get_settings


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


def _create_ollama_llm(model: str, base_url: str, **kwargs: Any) -> BaseChatModel:
    """Create an Ollama LLM instance.

    Args:
        model: The Ollama model name (e.g., "llama3.2", "mistral").
        base_url: The Ollama server URL (e.g., "http://localhost:11434").
        **kwargs: Additional arguments passed to ChatOllama.

    Returns:
        A ChatOllama instance.
    """
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=kwargs.get("temperature", 0.0),
        **kwargs,
    )


def _create_anthropic_llm(model: str, api_key: str, **kwargs: Any) -> BaseChatModel:
    """Create an Anthropic LLM instance.

    Args:
        model: The Anthropic model name (e.g., "claude-3-haiku-20240307").
        api_key: The Anthropic API key.
        **kwargs: Additional arguments passed to ChatAnthropic.

    Returns:
        A ChatAnthropic instance.
    """
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=model,
        api_key=api_key,
        temperature=kwargs.get("temperature", 0.0),
        **kwargs,
    )


@lru_cache
def get_llm(
    provider: LLMProvider | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Get an LLM instance based on configuration.

    This factory function returns a cached LLM instance based on the
    configured provider (Ollama or Anthropic). Settings are read from
    environment variables via the Settings class.

    Args:
        provider: Override the configured provider. If None, uses settings.
        model: Override the configured model. If None, uses settings.

    Returns:
        A BaseChatModel instance (ChatOllama or ChatAnthropic).

    Raises:
        ValueError: If the provider is not supported or required config is missing.

    Example:
        >>> llm = get_llm()  # Uses default from settings
        >>> llm = get_llm(provider=LLMProvider.OLLAMA, model="mistral")
    """
    settings = get_settings()

    # Use provided values or fall back to settings
    effective_provider = provider or LLMProvider(settings.llm_provider)
    effective_model = model or settings.llm_model

    if effective_provider == LLMProvider.OLLAMA:
        if not settings.ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL must be set when using Ollama provider")

        return _create_ollama_llm(
            model=effective_model,
            base_url=settings.ollama_base_url,
        )

    elif effective_provider == LLMProvider.ANTHROPIC:
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set when using Anthropic provider"
            )

        return _create_anthropic_llm(
            model=effective_model,
            api_key=settings.anthropic_api_key,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {effective_provider}")


def get_llm_with_tools(tools: list[Any]) -> BaseChatModel:
    """Get an LLM instance with tools bound.

    This is a convenience function that gets the default LLM and binds
    the provided tools to it for function calling.

    Args:
        tools: List of LangChain tools to bind to the LLM.

    Returns:
        A BaseChatModel with tools bound.

    Example:
        >>> from deepthought.tools import add_values, query_dynamodb
        >>> llm = get_llm_with_tools([add_values, query_dynamodb])
    """
    llm = get_llm()
    return llm.bind_tools(tools)
