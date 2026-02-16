"""LLM provider factory using Google Gemini."""

from functools import lru_cache
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from deepthought.config import get_settings


def _create_google_llm(model: str, api_key: str, **kwargs: Any) -> BaseChatModel:
    """Create a Google Gemini LLM instance.

    Args:
        model: The Google model name (e.g., "gemini-2.0-flash", "gemini-1.5-pro").
        api_key: The Google API key.
        **kwargs: Additional arguments passed to ChatGoogleGenerativeAI.

    Returns:
        A ChatGoogleGenerativeAI instance.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=kwargs.get("temperature", 0.0),
        **kwargs,
    )


@lru_cache
def get_llm(model: str | None = None) -> BaseChatModel:
    """Get a Google Gemini LLM instance.

    Args:
        model: Override the configured model. If None, uses settings.llm_model.

    Returns:
        A ChatGoogleGenerativeAI instance.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    settings = get_settings()
    effective_model = model or settings.llm_model

    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY must be set")

    return _create_google_llm(
        model=effective_model,
        api_key=settings.google_api_key,
    )


def get_llm_with_tools(tools: list[Any]) -> BaseChatModel:
    """Get an LLM instance with tools bound.

    Args:
        tools: List of LangChain tools to bind to the LLM.

    Returns:
        A BaseChatModel with tools bound.
    """
    llm = get_llm()
    return llm.bind_tools(tools)
