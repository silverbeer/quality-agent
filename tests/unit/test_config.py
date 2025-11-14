"""Tests for configuration management."""

import os
from typing import Generator

import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment() -> Generator[None, None, None]:
    """Isolate environment variables for each test.

    This fixture saves the current environment, yields to the test,
    then restores the original environment after the test completes.
    """
    # Save current environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestSettings:
    """Test suite for Settings configuration class."""

    def test_settings_loads_from_environment(self) -> None:
        """Test that settings load correctly from environment variables."""
        # Arrange & Act (environment set up in conftest.py)
        from app.config import settings

        # Assert
        assert settings.github_webhook_secret == "test_webhook_secret_12345"
        assert settings.github_token == "ghp_test_token_12345"
        assert settings.anthropic_api_key == "sk-ant-test_key_12345"
        assert settings.environment == "development"
        assert settings.log_level == "DEBUG"

    def test_settings_has_correct_defaults(self) -> None:
        """Test that optional settings have correct default values."""
        # Arrange & Act
        from app.config import settings

        # Assert
        assert settings.port == 8000
        assert settings.log_level == "DEBUG"  # Set in test environment
        assert settings.agent_timeout == 300
        assert settings.crewai_model == "claude-3-sonnet-20240229"
        assert settings.crewai_temperature == 0.7
        assert settings.crewai_max_tokens == 4096

    def test_port_validation_accepts_valid_range(self) -> None:
        """Test that port validation accepts valid port numbers."""
        # Arrange
        os.environ["PORT"] = "3000"

        # Act
        test_settings = Settings()

        # Assert
        assert test_settings.port == 3000

    def test_port_validation_rejects_below_1024(self) -> None:
        """Test that port validation rejects ports below 1024."""
        # Arrange
        os.environ["PORT"] = "80"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "greater than or equal to 1024" in str(exc_info.value)

    def test_port_validation_rejects_above_65535(self) -> None:
        """Test that port validation rejects ports above 65535."""
        # Arrange
        os.environ["PORT"] = "70000"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "less than or equal to 65535" in str(exc_info.value)

    def test_log_level_is_uppercased(self) -> None:
        """Test that log level is automatically uppercased."""
        # Arrange
        os.environ["LOG_LEVEL"] = "info"

        # Act
        test_settings = Settings()

        # Assert
        assert test_settings.log_level == "INFO"

    def test_log_level_validation_rejects_invalid(self) -> None:
        """Test that invalid log levels are rejected."""
        # Arrange
        os.environ["LOG_LEVEL"] = "INVALID"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "log_level" in str(exc_info.value).lower()

    def test_environment_validation_rejects_invalid(self) -> None:
        """Test that invalid environments are rejected."""
        # Arrange
        os.environ["ENVIRONMENT"] = "invalid"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "environment" in str(exc_info.value).lower()

    def test_secret_validation_rejects_empty_string(self) -> None:
        """Test that empty secrets are rejected."""
        # Arrange
        os.environ["GITHUB_WEBHOOK_SECRET"] = "  "  # Whitespace only

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "cannot be empty" in str(exc_info.value)

    def test_crewai_temperature_validation_rejects_out_of_range(self) -> None:
        """Test that temperature validation rejects values outside 0.0-1.0."""
        # Arrange
        os.environ["CREWAI_TEMPERATURE"] = "1.5"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "less than or equal to 1" in str(exc_info.value)

    def test_is_development_property(self) -> None:
        """Test is_development property returns correct value."""
        # Arrange
        os.environ["ENVIRONMENT"] = "development"
        test_settings = Settings()

        # Act & Assert
        assert test_settings.is_development is True
        assert test_settings.is_production is False

    def test_is_production_property(self) -> None:
        """Test is_production property returns correct value."""
        # Arrange
        os.environ["ENVIRONMENT"] = "production"
        test_settings = Settings()

        # Act & Assert
        assert test_settings.is_production is True
        assert test_settings.is_development is False

    def test_is_debug_enabled_in_development(self) -> None:
        """Test is_debug_enabled returns True in development."""
        # Arrange
        os.environ["ENVIRONMENT"] = "development"
        os.environ["DEBUG"] = "false"
        test_settings = Settings()

        # Act & Assert
        assert test_settings.is_debug_enabled is True  # Development overrides

    def test_is_debug_enabled_with_debug_flag(self) -> None:
        """Test is_debug_enabled returns True when debug flag is set."""
        # Arrange
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DEBUG"] = "true"
        test_settings = Settings()

        # Act & Assert
        assert test_settings.is_debug_enabled is True

    def test_is_debug_enabled_in_production_without_flag(self) -> None:
        """Test is_debug_enabled returns False in production without debug flag."""
        # Arrange
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DEBUG"] = "false"
        test_settings = Settings()

        # Act & Assert
        assert test_settings.is_debug_enabled is False
