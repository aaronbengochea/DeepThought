"""Unit tests for authentication utilities and endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from deepthought.api.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    verify_password,
)


class TestHashPassword:
    """Tests for hash_password function."""

    def test_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("testpassword")
        assert isinstance(result, str)

    def test_returns_bcrypt_hash(self):
        """Test that the returned hash starts with bcrypt prefix."""
        result = hash_password("testpassword")
        assert result.startswith("$2b$")

    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self):
        """Test that the same password with different salts produces different hashes."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_correct_password_returns_true(self):
        """Test that a correct password verifies successfully."""
        password = "mysecurepassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self):
        """Test that an incorrect password fails verification."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password(self):
        """Test verification with an empty password."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    @patch("deepthought.api.auth.get_settings")
    def test_returns_string(self, mock_settings):
        """Test that create_access_token returns a string."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})
        assert isinstance(token, str)

    @patch("deepthought.api.auth.get_settings")
    def test_token_contains_subject(self, mock_settings):
        """Test that the token payload contains the subject claim."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"

    @patch("deepthought.api.auth.get_settings")
    def test_token_contains_expiration(self, mock_settings):
        """Test that the token payload contains an expiration claim."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert "exp" in payload

    @patch("deepthought.api.auth.get_settings")
    def test_does_not_mutate_input(self, mock_settings):
        """Test that the original data dict is not mutated."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        data = {"sub": "user@example.com"}
        create_access_token(data)
        assert "exp" not in data


class TestDecodeAccessToken:
    """Tests for decode_access_token function."""

    @patch("deepthought.api.auth.get_settings")
    def test_decodes_valid_token(self, mock_settings):
        """Test that a valid token is decoded correctly."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"

    @patch("deepthought.api.auth.get_settings")
    def test_invalid_token_raises_value_error(self, mock_settings):
        """Test that an invalid token raises ValueError."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
        )
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token("invalid.token.here")

    @patch("deepthought.api.auth.get_settings")
    def test_wrong_secret_raises_value_error(self, mock_settings):
        """Test that a token signed with a different secret fails."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="secret-one",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})

        mock_settings.return_value = MagicMock(
            jwt_secret_key="secret-two",
            jwt_algorithm="HS256",
        )
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_access_token(token)


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @patch("deepthought.api.auth.get_settings")
    async def test_returns_user_for_valid_token(self, mock_settings):
        """Test that a valid token returns the user record."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "user@example.com"})

        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value={
            "pk": "user@example.com",
            "first_name": "Test",
            "last_name": "User",
        })

        user = await get_current_user(token=token, users_db=mock_db)
        assert user["pk"] == "user@example.com"
        mock_db.get_item.assert_called_once_with(pk="user@example.com")

    @patch("deepthought.api.auth.get_settings")
    async def test_invalid_token_raises_401(self, mock_settings):
        """Test that an invalid token raises 401."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
        )
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="bad.token.here", users_db=mock_db)
        assert exc_info.value.status_code == 401

    @patch("deepthought.api.auth.get_settings")
    async def test_token_without_sub_raises_401(self, mock_settings):
        """Test that a token without a sub claim raises 401."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"data": "no-sub-claim"})

        mock_db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, users_db=mock_db)
        assert exc_info.value.status_code == 401

    @patch("deepthought.api.auth.get_settings")
    async def test_user_not_found_raises_401(self, mock_settings):
        """Test that a valid token for a non-existent user raises 401."""
        mock_settings.return_value = MagicMock(
            jwt_secret_key="test-secret",
            jwt_algorithm="HS256",
            jwt_expiration_minutes=60,
        )
        token = create_access_token({"sub": "deleted@example.com"})

        mock_db = MagicMock()
        mock_db.get_item = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, users_db=mock_db)
        assert exc_info.value.status_code == 401
