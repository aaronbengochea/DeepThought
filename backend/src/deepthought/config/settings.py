"""Application settings with environment variable support."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Application
    app_name: str = "DeepThought"
    debug: bool = False
    log_level: str = "INFO"

    # AWS
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str

    # DynamoDB
    dynamodb_endpoint_url: str
    dc_dynamodb_endpoint: str

    # LLM Configuration
    llm_model: str

    # Google Gemini
    google_api_key: str

    # DynamoDB Tables
    dynamodb_users_table: str
    dynamodb_pairs_table: str
    dynamodb_logs_table: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # Test Seed Data
    test_user_password: str = ""

    # CORS
    cors_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
