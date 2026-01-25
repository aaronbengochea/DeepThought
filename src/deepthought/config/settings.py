"""Application settings with environment variable support."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "DeepThought"
    debug: bool = False
    log_level: str = "INFO"

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # DynamoDB
    dynamodb_table_name: str = "deepthought-calculations"
    dynamodb_endpoint_url: str | None = None  # For local DynamoDB

    # LLM Configuration
    llm_provider: str = "ollama"  # "ollama" or "anthropic"
    llm_model: str = "llama3.2"  # Model name (e.g., "llama3.2", "mistral", "claude-3-haiku-20240307")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Anthropic
    anthropic_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
