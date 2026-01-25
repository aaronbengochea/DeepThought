"""Unit tests for LLM provider abstraction."""

from unittest.mock import patch, MagicMock

import pytest

from deepthought.llm.provider import LLMProvider, get_llm, get_llm_with_tools


class TestLLMProvider:
    """Tests for LLMProvider enum."""

    def test_ollama_value(self):
        """Test OLLAMA enum value."""
        assert LLMProvider.OLLAMA.value == "ollama"

    def test_anthropic_value(self):
        """Test ANTHROPIC enum value."""
        assert LLMProvider.ANTHROPIC.value == "anthropic"

    def test_from_string(self):
        """Test creating enum from string."""
        assert LLMProvider("ollama") == LLMProvider.OLLAMA
        assert LLMProvider("anthropic") == LLMProvider.ANTHROPIC


class TestGetLLM:
    """Tests for get_llm factory function."""

    @patch("deepthought.llm.provider.get_settings")
    @patch("deepthought.llm.provider._create_ollama_llm")
    def test_creates_ollama_by_default(self, mock_create_ollama, mock_settings):
        """Test default provider is Ollama."""
        # Clear the cache
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_provider="ollama",
            llm_model="llama3.2",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key="",
        )
        mock_llm = MagicMock()
        mock_create_ollama.return_value = mock_llm

        result = get_llm()

        mock_create_ollama.assert_called_once_with(
            model="llama3.2",
            base_url="http://localhost:11434",
        )
        assert result == mock_llm

    @patch("deepthought.llm.provider.get_settings")
    @patch("deepthought.llm.provider._create_anthropic_llm")
    def test_creates_anthropic_when_configured(self, mock_create_anthropic, mock_settings):
        """Test Anthropic provider when configured."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_provider="anthropic",
            llm_model="claude-3-haiku-20240307",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key="sk-test-key",
        )
        mock_llm = MagicMock()
        mock_create_anthropic.return_value = mock_llm

        result = get_llm()

        mock_create_anthropic.assert_called_once_with(
            model="claude-3-haiku-20240307",
            api_key="sk-test-key",
        )
        assert result == mock_llm

    @patch("deepthought.llm.provider.get_settings")
    def test_raises_error_for_missing_ollama_url(self, mock_settings):
        """Test error when Ollama URL is missing."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_provider="ollama",
            llm_model="llama3.2",
            ollama_base_url="",  # Missing
            anthropic_api_key="",
        )

        with pytest.raises(ValueError, match="OLLAMA_BASE_URL"):
            get_llm()

    @patch("deepthought.llm.provider.get_settings")
    def test_raises_error_for_missing_anthropic_key(self, mock_settings):
        """Test error when Anthropic API key is missing."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_provider="anthropic",
            llm_model="claude-3-haiku-20240307",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key="",  # Missing
        )

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_llm()

    @patch("deepthought.llm.provider.get_settings")
    @patch("deepthought.llm.provider._create_ollama_llm")
    def test_override_provider(self, mock_create_ollama, mock_settings):
        """Test overriding provider via parameter."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_provider="anthropic",  # Default to Anthropic
            llm_model="claude-3-haiku-20240307",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key="sk-test-key",
        )
        mock_llm = MagicMock()
        mock_create_ollama.return_value = mock_llm

        # Override to Ollama
        result = get_llm(provider=LLMProvider.OLLAMA, model="mistral")

        mock_create_ollama.assert_called_once_with(
            model="mistral",
            base_url="http://localhost:11434",
        )


class TestGetLLMWithTools:
    """Tests for get_llm_with_tools function."""

    @patch("deepthought.llm.provider.get_llm")
    def test_binds_tools_to_llm(self, mock_get_llm):
        """Test tools are bound to the LLM."""
        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_get_llm.return_value = mock_llm

        tools = [MagicMock(), MagicMock()]
        result = get_llm_with_tools(tools)

        mock_llm.bind_tools.assert_called_once_with(tools)
        assert result == mock_llm_with_tools
