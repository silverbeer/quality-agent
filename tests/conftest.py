"""Pytest configuration and shared fixtures.

This module provides test fixtures that are available to all tests in the suite.
Fixtures are automatically discovered by pytest.
"""

import os
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Set test environment variables at module import time
# This ensures they're available before any application code is imported
os.environ.update({
    "GITHUB_WEBHOOK_SECRET": "test_webhook_secret_12345",
    "GITHUB_TOKEN": "ghp_test_token_12345",
    "ANTHROPIC_API_KEY": "sk-ant-test_key_12345",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "DEBUG",
    "DEBUG": "true",
})


@pytest.fixture(scope="session", autouse=True)
def test_environment() -> Generator[None, None, None]:
    """Set up test environment variables.

    This fixture runs once per test session and sets up required environment
    variables for testing. It automatically restores the original environment
    after tests complete.

    Yields:
        None
    """
    # Store original environment
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ.update({
        "GITHUB_WEBHOOK_SECRET": "test_webhook_secret_12345",
        "GITHUB_TOKEN": "ghp_test_token_12345",
        "ANTHROPIC_API_KEY": "sk-ant-test_key_12345",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true",
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture.

    Provides a test client for making HTTP requests to the application
    without running a real server.

    Returns:
        TestClient instance

    Example:
        ```python
        def test_health_check(client):
            response = client.get("/health")
            assert response.status_code == 200
        ```
    """
    # Import here to ensure test environment is set up first
    from app.main import app

    return TestClient(app)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock settings fixture.

    Provides a mock settings object for tests that need to override configuration.

    Returns:
        Mock settings object

    Example:
        ```python
        def test_with_mock_settings(mock_settings):
            mock_settings.port = 9000
            mock_settings.environment = "production"
            # ... test code
        ```
    """
    mock = MagicMock()
    mock.port = 8000
    mock.log_level = "INFO"
    mock.environment = "development"
    mock.debug = True
    mock.github_webhook_secret = "test_secret"
    mock.github_token = "test_token"
    mock.anthropic_api_key = "test_key"
    mock.agent_timeout = 300
    mock.crewai_model = "claude-3-sonnet-20240229"
    mock.crewai_temperature = 0.7
    mock.crewai_max_tokens = 4096
    mock.is_development = True
    mock.is_production = False
    mock.is_debug_enabled = True
    return mock


@pytest.fixture
def sample_github_webhook_payload() -> dict:
    """Sample GitHub webhook payload for pull request events.

    Returns:
        Dictionary representing a GitHub webhook payload

    Example:
        ```python
        def test_webhook(client, sample_github_webhook_payload):
            response = client.post(
                "/webhook/github",
                json=sample_github_webhook_payload
            )
        ```
    """
    return {
        "action": "opened",
        "number": 123,
        "pull_request": {
            "id": 1,
            "number": 123,
            "title": "Add new feature",
            "state": "open",
            "user": {
                "login": "testuser",
                "id": 1,
                "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            },
            "head": {
                "ref": "feature/new-feature",
                "sha": "abc123def456",
            },
            "base": {
                "ref": "main",
                "sha": "def456abc123",
            },
        },
        "repository": {
            "id": 1,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "owner": {
                "login": "testuser",
                "id": 1,
            },
        },
    }


@pytest.fixture
def valid_github_signature() -> str:
    """Valid GitHub webhook signature for testing.

    This signature corresponds to the test webhook secret and payload.

    Returns:
        HMAC SHA-256 signature string

    Example:
        ```python
        def test_signature_verification(valid_github_signature):
            headers = {"X-Hub-Signature-256": valid_github_signature}
            # ... test code
        ```
    """
    # This will be calculated based on the actual payload in webhook tests
    return "sha256=test_signature_placeholder"
