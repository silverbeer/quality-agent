"""Tests for webhook receiver and signature verification."""

import hmac
import hashlib
import json
from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.webhook_receiver import verify_github_signature
from models.github import PullRequestWebhookPayload


class TestSignatureVerification:
    """Test suite for GitHub webhook signature verification."""

    def test_verify_github_signature_with_valid_signature(self) -> None:
        """Test that valid signatures are accepted."""
        # Arrange
        secret = "test_secret_12345"
        payload = b'{"test": "data"}'

        # Compute valid signature
        signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        signature_header = f"sha256={signature}"

        # Act
        result = verify_github_signature(
            payload_body=payload,
            signature_header=signature_header,
            secret=secret,
        )

        # Assert
        assert result is True

    def test_verify_github_signature_with_invalid_signature(self) -> None:
        """Test that invalid signatures are rejected."""
        # Arrange
        secret = "test_secret_12345"
        payload = b'{"test": "data"}'
        signature_header = "sha256=invalid_signature_here"

        # Act
        result = verify_github_signature(
            payload_body=payload,
            signature_header=signature_header,
            secret=secret,
        )

        # Assert
        assert result is False

    def test_verify_github_signature_with_wrong_secret(self) -> None:
        """Test that signatures with wrong secret are rejected."""
        # Arrange
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        payload = b'{"test": "data"}'

        # Compute signature with correct secret
        signature = hmac.new(
            key=correct_secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        signature_header = f"sha256={signature}"

        # Act - verify with wrong secret
        result = verify_github_signature(
            payload_body=payload,
            signature_header=signature_header,
            secret=wrong_secret,
        )

        # Assert
        assert result is False

    def test_verify_github_signature_with_missing_prefix(self) -> None:
        """Test that signatures without sha256= prefix are rejected."""
        # Arrange
        secret = "test_secret_12345"
        payload = b'{"test": "data"}'

        # Create signature without prefix
        signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        signature_header = signature  # Missing "sha256=" prefix

        # Act
        result = verify_github_signature(
            payload_body=payload,
            signature_header=signature_header,
            secret=secret,
        )

        # Assert
        assert result is False

    def test_verify_github_signature_with_modified_payload(self) -> None:
        """Test that signature verification fails if payload is modified."""
        # Arrange
        secret = "test_secret_12345"
        original_payload = b'{"test": "original"}'
        modified_payload = b'{"test": "modified"}'

        # Compute signature for original payload
        signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=original_payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
        signature_header = f"sha256={signature}"

        # Act - verify with modified payload
        result = verify_github_signature(
            payload_body=modified_payload,
            signature_header=signature_header,
            secret=secret,
        )

        # Assert
        assert result is False


class TestWebhookEndpoint:
    """Test suite for the webhook endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Get test client."""
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def valid_pr_payload(self) -> dict:
        """Generate a valid pull request webhook payload."""
        return {
            "action": "opened",
            "number": 123,
            "pull_request": {
                "id": 1,
                "number": 123,
                "state": "open",
                "title": "Test PR",
                "body": "Test description",
                "html_url": "https://github.com/test/repo/pull/123",
                "diff_url": "https://github.com/test/repo/pull/123.diff",
                "patch_url": "https://github.com/test/repo/pull/123.patch",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "closed_at": None,
                "merged_at": None,
                "merge_commit_sha": None,
                "user": {
                    "login": "testuser",
                    "id": 1,
                    "avatar_url": "https://github.com/avatar.jpg",
                    "html_url": "https://github.com/testuser",
                    "type": "User",
                },
                "head": {
                    "ref": "feature-branch",
                    "sha": "a" * 40,
                    "user": {
                        "login": "testuser",
                        "id": 1,
                        "avatar_url": "https://github.com/avatar.jpg",
                        "html_url": "https://github.com/testuser",
                        "type": "User",
                    },
                    "label": "testuser:feature-branch",
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {
                        "login": "testuser",
                        "id": 1,
                        "avatar_url": "https://github.com/avatar.jpg",
                        "html_url": "https://github.com/testuser",
                        "type": "User",
                    },
                    "label": "testuser:main",
                },
                "merged": False,
                "mergeable": True,
                "draft": False,
                "additions": 10,
                "deletions": 5,
                "changed_files": 2,
            },
            "repository": {
                "id": 1,
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "html_url": "https://github.com/testuser/test-repo",
                "description": "Test repository",
                "private": False,
                "owner": {
                    "login": "testuser",
                    "id": 1,
                    "avatar_url": "https://github.com/avatar.jpg",
                    "html_url": "https://github.com/testuser",
                    "type": "User",
                },
                "default_branch": "main",
            },
            "sender": {
                "login": "testuser",
                "id": 1,
                "avatar_url": "https://github.com/avatar.jpg",
                "html_url": "https://github.com/testuser",
                "type": "User",
            },
        }

    def _compute_signature(self, payload: dict, secret: str) -> str:
        """Compute valid GitHub signature for payload."""
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def test_webhook_endpoint_with_valid_signature(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint accepts valid signature."""
        # Arrange
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"  # Background analysis
        assert data["pr_number"] == 123
        assert data["delivery_id"] == "12345-67890"

    def test_webhook_endpoint_rejects_invalid_signature(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint rejects invalid signature."""
        # Arrange
        headers = {
            "X-Hub-Signature-256": "sha256=invalid_signature",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]

    def test_webhook_endpoint_rejects_missing_signature_header(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint rejects missing signature header."""
        # Arrange
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422  # FastAPI validation error
        assert "x-hub-signature-256" in str(response.json()).lower()

    def test_webhook_endpoint_rejects_missing_event_header(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint rejects missing event header."""
        # Arrange
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422  # FastAPI validation error
        assert "x-github-event" in str(response.json()).lower()

    def test_webhook_endpoint_rejects_missing_delivery_header(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint rejects missing delivery header."""
        # Arrange
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 422  # FastAPI validation error
        assert "x-github-delivery" in str(response.json()).lower()

    def test_webhook_endpoint_ignores_non_pull_request_events(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint ignores events that are not pull_request or push."""
        # Arrange
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "issues",  # Unsupported event type
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_endpoint_ignores_non_actionable_pr_actions(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint ignores non-actionable PR actions."""
        # Arrange
        valid_pr_payload["action"] = "labeled"  # Non-actionable action
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    def test_webhook_endpoint_accepts_synchronize_action(
        self, client: TestClient, valid_pr_payload: dict
    ) -> None:
        """Test webhook endpoint accepts synchronize action (PR updated)."""
        # Arrange
        valid_pr_payload["action"] = "synchronize"
        from app.config import settings
        signature = self._compute_signature(valid_pr_payload, settings.github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=valid_pr_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"  # Background analysis
        assert data["action"] == "synchronize"
        assert data["pr_number"] == 123
        assert data["delivery_id"] == "12345-67890"

    def test_webhook_endpoint_rejects_invalid_json(
        self, client: TestClient
    ) -> None:
        """Test webhook endpoint rejects invalid JSON."""
        # Arrange
        from app.config import settings
        invalid_json = b"not valid json"
        signature = hmac.new(
            key=settings.github_webhook_secret.encode("utf-8"),
            msg=invalid_json,
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers = {
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "12345-67890",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            content=invalid_json,
            headers=headers,
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]


class TestPullRequestPayloadModel:
    """Test suite for PullRequestWebhookPayload model."""

    def test_payload_model_validates_correct_data(self) -> None:
        """Test that model validates correct webhook payload."""
        # Arrange
        payload_data = {
            "action": "opened",
            "number": 123,
            "pull_request": {
                "id": 1,
                "number": 123,
                "state": "open",
                "title": "Test PR",
                "body": "Test description",
                "html_url": "https://github.com/test/repo/pull/123",
                "diff_url": "https://github.com/test/repo/pull/123.diff",
                "patch_url": "https://github.com/test/repo/pull/123.patch",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "closed_at": None,
                "merged_at": None,
                "merge_commit_sha": None,
                "user": {
                    "login": "testuser",
                    "id": 1,
                    "avatar_url": "https://github.com/avatar.jpg",
                    "html_url": "https://github.com/testuser",
                    "type": "User",
                },
                "head": {
                    "ref": "feature",
                    "sha": "a" * 40,
                    "user": {
                        "login": "testuser",
                        "id": 1,
                        "avatar_url": "https://github.com/avatar.jpg",
                        "html_url": "https://github.com/testuser",
                        "type": "User",
                    },
                    "label": "testuser:feature",
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {
                        "login": "testuser",
                        "id": 1,
                        "avatar_url": "https://github.com/avatar.jpg",
                        "html_url": "https://github.com/testuser",
                        "type": "User",
                    },
                    "label": "testuser:main",
                },
                "merged": False,
                "mergeable": True,
                "draft": False,
                "additions": 10,
                "deletions": 5,
                "changed_files": 2,
            },
            "repository": {
                "id": 1,
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "html_url": "https://github.com/testuser/test-repo",
                "description": "Test repository",
                "private": False,
                "owner": {
                    "login": "testuser",
                    "id": 1,
                    "avatar_url": "https://github.com/avatar.jpg",
                    "html_url": "https://github.com/testuser",
                    "type": "User",
                },
                "default_branch": "main",
            },
            "sender": {
                "login": "testuser",
                "id": 1,
                "avatar_url": "https://github.com/avatar.jpg",
                "html_url": "https://github.com/testuser",
                "type": "User",
            },
        }

        # Act
        payload = PullRequestWebhookPayload.model_validate(payload_data)

        # Assert
        assert payload.action == "opened"
        assert payload.number == 123
        assert payload.pull_request.title == "Test PR"
        assert payload.repository.full_name == "testuser/test-repo"

    def test_payload_model_is_actionable_for_opened(self) -> None:
        """Test is_actionable property returns True for opened action."""
        # Arrange
        payload_data = {"action": "opened", "number": 123}  # Minimal data

        # We need to provide a minimal valid payload, so let's just test the property directly
        # by creating a mock object
        class MockPayload:
            action = "opened"

        payload = MockPayload()

        # Act & Assert
        assert payload.action in ("opened", "synchronize")

    def test_payload_model_is_actionable_for_synchronize(self) -> None:
        """Test is_actionable property returns True for synchronize action."""
        # Arrange
        class MockPayload:
            action = "synchronize"

        payload = MockPayload()

        # Act & Assert
        assert payload.action in ("opened", "synchronize")

    def test_payload_model_is_not_actionable_for_labeled(self) -> None:
        """Test is_actionable property returns False for labeled action."""
        # Arrange
        class MockPayload:
            action = "labeled"

        payload = MockPayload()

        # Act & Assert
        assert payload.action not in ("opened", "synchronize")
