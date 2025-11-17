"""Configuration management using Pydantic Settings.

This module provides type-safe configuration loading from environment variables.
All settings are validated at startup to fail fast if misconfigured.
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All required settings must be provided via environment variables or .env file.
    Optional settings have sensible defaults.

    Example:
        ```python
        from app.config import settings

        print(settings.port)  # 8000
        print(settings.environment)  # "development"
        ```
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # GitHub Configuration
    github_webhook_secret: str = Field(
        description="GitHub webhook secret for HMAC signature verification"
    )
    github_token: str = Field(
        description="GitHub personal access token for API access"
    )

    # Anthropic Configuration
    anthropic_api_key: str = Field(
        description="Anthropic API key for Claude (used by CrewAI agents)"
    )

    # Application Configuration
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port number"
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment name (affects logging format and behaviors)"
    )

    # Development/Debug Settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, detailed errors)"
    )

    # Webhook Audit Logging
    enable_webhook_audit: bool = Field(
        default=True,
        description="Enable audit logging of all webhook requests"
    )

    webhook_audit_dir: str = Field(
        default="logs/webhooks",
        description="Directory to store webhook audit logs"
    )

    webhook_audit_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retain webhook audit logs"
    )

    # Metrics Configuration
    enable_metrics: bool = Field(
        default=False,
        description="Enable Prometheus metrics endpoint at /metrics"
    )

    metrics_include_default: bool = Field(
        default=True,
        description="Include default HTTP metrics (request count, duration, etc.)"
    )

    # Agent Configuration (optional, with defaults)
    agent_timeout: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Agent execution timeout in seconds"
    )

    crewai_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="CrewAI model to use for agents"
    )

    crewai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="CrewAI temperature (0.0=deterministic, 1.0=creative)"
    )

    crewai_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=100000,
        description="Maximum tokens for agent responses"
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def uppercase_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase.

        Runs before type validation so lowercase values can be uppercased.
        """
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("github_webhook_secret", "github_token", "anthropic_api_key")
    @classmethod
    def validate_secret_not_empty(cls, v: str, info) -> str:
        """Ensure secrets are not empty strings."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug or self.is_development


# Global settings instance
# This is loaded once at module import and reused throughout the application
settings = Settings()
