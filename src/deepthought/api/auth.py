"""Authentication utilities for password hashing, JWT management, and user resolution."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from deepthought.config import get_settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        password: The plaintext password to check.
        password_hash: The bcrypt hash to verify against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token with an expiration claim.

    Args:
        data: The payload data to encode in the token (e.g. {"sub": "user@example.com"}).

    Returns:
        The encoded JWT string.
    """
    settings = get_settings()

    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload["exp"] = expire

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        ValueError: If the token is invalid, expired, or cannot be decoded.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {e}")

    return payload
