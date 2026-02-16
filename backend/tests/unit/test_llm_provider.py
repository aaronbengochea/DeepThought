"""Unit tests for LLM provider."""

from unittest.mock import patch, MagicMock

import pytest

from deepthought.llm.provider import get_llm, get_llm_with_tools


class TestGetLLM:
    """Tests for get_llm factory function."""

    @patch("deepthought.llm.provider.get_settings")
    @patch("deepthought.llm.provider._create_google_llm")
    def test_creates_google_llm(self, mock_create_google, mock_settings):
        """Test Google Gemini LLM creation."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_model="gemini-2.0-flash",
            google_api_key="test-google-key",
        )
        mock_llm = MagicMock()
        mock_create_google.return_value = mock_llm

        result = get_llm()

        mock_create_google.assert_called_once_with(
            model="gemini-2.0-flash",
            api_key="test-google-key",
        )
        assert result == mock_llm

    @patch("deepthought.llm.provider.get_settings")
    @patch("deepthought.llm.provider._create_google_llm")
    def test_override_model(self, mock_create_google, mock_settings):
        """Test overriding model via parameter."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_model="gemini-2.0-flash",
            google_api_key="test-google-key",
        )
        mock_llm = MagicMock()
        mock_create_google.return_value = mock_llm

        result = get_llm(model="gemini-1.5-pro")

        mock_create_google.assert_called_once_with(
            model="gemini-1.5-pro",
            api_key="test-google-key",
        )
        assert result == mock_llm

    @patch("deepthought.llm.provider.get_settings")
    def test_raises_error_for_missing_google_key(self, mock_settings):
        """Test error when Google API key is missing."""
        get_llm.cache_clear()

        mock_settings.return_value = MagicMock(
            llm_model="gemini-2.0-flash",
            google_api_key="",
        )

        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            get_llm()


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
