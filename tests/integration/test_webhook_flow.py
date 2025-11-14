"""Integration tests for complete webhook processing flow.

These tests verify the entire webhook flow from GitHub delivery to processing,
including signature verification, payload parsing, and response handling.
"""

import hmac
import hashlib
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client for integration tests."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def github_webhook_secret() -> str:
    """Get GitHub webhook secret from settings."""
    from app.config import settings
    return settings.github_webhook_secret


@pytest.fixture
def sample_push_payload() -> dict:
    """Sample push webhook payload."""
    return {
        "ref": "refs/heads/main",
        "before": "a" * 40,
        "after": "b" * 40,
        "repository": {
            "id": 987654321,
            "name": "quality-agent",
            "full_name": "silverbeer/quality-agent",
            "html_url": "https://github.com/silverbeer/quality-agent",
            "description": "AI-powered GitHub webhook service",
            "private": False,
            "owner": {
                "login": "silverbeer",
                "id": 12345,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "html_url": "https://github.com/silverbeer",
                "type": "User",
            },
            "default_branch": "main",
        },
        "pusher": {
            "name": "silverbeer",
            "email": "test@example.com",
        },
        "sender": {
            "login": "silverbeer",
            "id": 12345,
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            "html_url": "https://github.com/silverbeer",
            "type": "User",
        },
        "commits": [
            {
                "id": "c" * 40,
                "message": "Add new feature",
                "timestamp": "2024-11-14T10:00:00Z",
                "url": "https://github.com/silverbeer/quality-agent/commit/cccccccc",
                "author": {
                    "name": "silverbeer",
                    "email": "test@example.com",
                },
                "added": ["new_file.py"],
                "removed": [],
                "modified": ["existing_file.py"],
            }
        ],
        "head_commit": {
            "id": "c" * 40,
            "message": "Add new feature",
            "timestamp": "2024-11-14T10:00:00Z",
            "url": "https://github.com/silverbeer/quality-agent/commit/cccccccc",
            "author": {
                "name": "silverbeer",
                "email": "test@example.com",
            },
            "added": ["new_file.py"],
            "removed": [],
            "modified": ["existing_file.py"],
        },
        "compare": "https://github.com/silverbeer/quality-agent/compare/aaaa...bbbb",
    }


@pytest.fixture
def sample_pr_opened_payload() -> dict:
    """Sample pull request opened webhook payload."""
    return {
        "action": "opened",
        "number": 456,
        "pull_request": {
            "id": 123456789,
            "number": 456,
            "state": "open",
            "title": "Add new feature for webhook testing",
            "body": "This PR adds webhook integration testing",
            "html_url": "https://github.com/silverbeer/quality-agent/pull/456",
            "diff_url": "https://github.com/silverbeer/quality-agent/pull/456.diff",
            "patch_url": "https://github.com/silverbeer/quality-agent/pull/456.patch",
            "created_at": "2024-11-14T10:00:00Z",
            "updated_at": "2024-11-14T10:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "user": {
                "login": "silverbeer",
                "id": 12345,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "html_url": "https://github.com/silverbeer",
                "type": "User",
            },
            "head": {
                "ref": "feature/webhook-integration",
                "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                "user": {
                    "login": "silverbeer",
                    "id": 12345,
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                    "html_url": "https://github.com/silverbeer",
                    "type": "User",
                },
                "label": "silverbeer:feature/webhook-integration",
            },
            "base": {
                "ref": "main",
                "sha": "b2c3d4e5f6789012345678901234567890abcdef",
                "user": {
                    "login": "silverbeer",
                    "id": 12345,
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                    "html_url": "https://github.com/silverbeer",
                    "type": "User",
                },
                "label": "silverbeer:main",
            },
            "merged": False,
            "mergeable": True,
            "draft": False,
            "additions": 125,
            "deletions": 32,
            "changed_files": 8,
        },
        "repository": {
            "id": 987654321,
            "name": "quality-agent",
            "full_name": "silverbeer/quality-agent",
            "html_url": "https://github.com/silverbeer/quality-agent",
            "description": "AI-powered GitHub webhook service",
            "private": False,
            "owner": {
                "login": "silverbeer",
                "id": 12345,
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "html_url": "https://github.com/silverbeer",
                "type": "User",
            },
            "default_branch": "main",
        },
        "sender": {
            "login": "silverbeer",
            "id": 12345,
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            "html_url": "https://github.com/silverbeer",
            "type": "User",
        },
    }


def compute_github_signature(payload: dict, secret: str) -> str:
    """Compute GitHub HMAC SHA-256 signature for payload.

    Args:
        payload: Webhook payload dictionary
        secret: Webhook secret

    Returns:
        str: Signature header value (sha256=<hash>)
    """
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


class TestWebhookIntegrationFlow:
    """Integration tests for complete webhook processing."""

    def test_full_webhook_flow_pr_opened(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test complete flow: PR opened → signature verification → processing."""
        # Arrange
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-12345",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"  # Background analysis
        assert data["pr_number"] == 456
        assert data["action"] == "opened"
        assert "message" in data
        assert data["message"] == "Pull request analysis started"
        assert data["delivery_id"] == "test-delivery-12345"

    def test_full_webhook_flow_pr_synchronized(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test complete flow: PR synchronized (updated) → processing."""
        # Arrange - modify payload for synchronize action
        sample_pr_opened_payload["action"] = "synchronize"
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-67890",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"  # Background analysis
        assert data["pr_number"] == 456
        assert data["action"] == "synchronize"
        assert data["message"] == "Pull request analysis started"
        assert data["delivery_id"] == "test-delivery-67890"

    def test_full_webhook_flow_pr_closed_merged(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test complete flow: PR closed (merged)."""
        # Arrange - modify payload for closed + merged
        sample_pr_opened_payload["action"] = "closed"
        sample_pr_opened_payload["pull_request"]["merged"] = True
        sample_pr_opened_payload["pull_request"]["state"] = "closed"
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-merge-123",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Closed action is not actionable (even if merged)
        assert data["status"] == "ignored"

    def test_full_webhook_flow_security_rejects_tampered_payload(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test security: Reject tampered payload (signature mismatch)."""
        # Arrange - compute signature for original payload
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)

        # Tamper with payload after signature
        sample_pr_opened_payload["number"] = 999  # Changed!

        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-tampered",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]

    def test_full_webhook_flow_rejects_replay_attack(
        self,
        client: TestClient,
        github_webhook_secret: str,
    ) -> None:
        """Test security: Signature from different payload doesn't work (replay attack)."""
        # Arrange - create signature for payload 1
        payload1 = {"action": "opened", "number": 1}
        signature1 = compute_github_signature(payload1, github_webhook_secret)

        # Try to use signature1 with different payload2
        payload2 = {"action": "opened", "number": 2}

        headers = {
            "X-Hub-Signature-256": signature1,  # Wrong signature!
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-replay",
            "Content-Type": "application/json",
        }

        # Act - send payload2 with signature1
        response = client.post(
            "/webhook/github",
            json=payload2,
            headers=headers,
        )

        # Assert
        assert response.status_code == 401

    def test_full_webhook_flow_handles_draft_pr(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test that draft PRs are processed (they are actionable)."""
        # Arrange - mark as draft
        sample_pr_opened_payload["pull_request"]["draft"] = True
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-draft",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Draft PRs with "opened" action should still be processed
        assert data["status"] == "processing"
        assert data["pr_number"] == 456
        assert data["action"] == "opened"
        assert data["delivery_id"] == "test-delivery-draft"

    def test_full_webhook_flow_ignores_labeled_action(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test that non-actionable actions (labeled) are ignored."""
        # Arrange
        sample_pr_opened_payload["action"] = "labeled"
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-labeled",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert "does not require analysis" in data["message"]


class TestWebhookErrorHandling:
    """Test error handling in webhook processing."""

    def test_webhook_handles_malformed_payload_gracefully(
        self,
        client: TestClient,
        github_webhook_secret: str,
    ) -> None:
        """Test that malformed payloads return 400 with helpful error."""
        # Arrange - payload missing required fields
        malformed_payload = {"action": "opened"}  # Missing number, pull_request, etc.
        signature = compute_github_signature(malformed_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-malformed",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=malformed_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid payload structure" in response.json()["detail"]

    def test_webhook_validates_sha_format(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_pr_opened_payload: dict,
    ) -> None:
        """Test that invalid SHA format is rejected."""
        # Arrange - invalid SHA (not 40 characters)
        sample_pr_opened_payload["pull_request"]["head"]["sha"] = "invalid"
        signature = compute_github_signature(sample_pr_opened_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-invalid-sha",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_pr_opened_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid payload structure" in response.json()["detail"]


class TestPushEventHandling:
    """Test push event (commit) webhook handling."""

    def test_push_event_accepted(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_push_payload: dict,
    ) -> None:
        """Test that push events are accepted and processed."""
        # Arrange
        signature = compute_github_signature(sample_push_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-123",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_push_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["message"] == "Push received"
        assert data["branch"] == "main"
        assert data["commits"] == 1

    def test_push_event_with_multiple_commits(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_push_payload: dict,
    ) -> None:
        """Test push event with multiple commits."""
        # Arrange - add more commits
        sample_push_payload["commits"].append({
            "id": "d" * 40,
            "message": "Second commit",
            "timestamp": "2024-11-14T10:01:00Z",
            "url": "https://github.com/silverbeer/quality-agent/commit/dddddddd",
            "author": {
                "name": "silverbeer",
                "email": "test@example.com",
            },
            "added": [],
            "removed": [],
            "modified": ["another_file.py"],
        })
        signature = compute_github_signature(sample_push_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-multi",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_push_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["commits"] == 2

    def test_push_event_ignores_tag_push(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_push_payload: dict,
    ) -> None:
        """Test that tag pushes are ignored."""
        # Arrange - change to tag ref
        sample_push_payload["ref"] = "refs/tags/v1.0.0"
        signature = compute_github_signature(sample_push_payload, github_webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-tag",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_push_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert "not a branch" in data["message"].lower()

    def test_push_event_requires_valid_signature(
        self,
        client: TestClient,
        github_webhook_secret: str,
        sample_push_payload: dict,
    ) -> None:
        """Test that push events also require signature verification."""
        # Arrange - invalid signature
        headers = {
            "X-Hub-Signature-256": "sha256=invalid_signature",
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-invalid",
            "Content-Type": "application/json",
        }

        # Act
        response = client.post(
            "/webhook/github",
            json=sample_push_payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 401
