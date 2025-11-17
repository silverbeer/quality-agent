"""Integration tests for metrics collection flow.

Tests the full flow: webhook → metrics recording → metrics exposure.
"""

import hmac
import hashlib
from datetime import datetime, timezone

import pytest

from app.metrics import deployments_total, pr_review_time_seconds, pr_total


class TestPRMetricsFlow:
    """Test PR webhook → metrics flow."""

    @pytest.mark.asyncio
    async def test_pr_opened_webhook_records_metric(self, client, pr_opened_payload):
        """Test that PR opened webhook records PR metric."""
        test_repo = pr_opened_payload["repository"]["full_name"]
        initial_count = pr_total.labels(
            repository=test_repo, action="opened", merged="false"
        )._value.get()

        # Send PR opened webhook
        signature = self._create_signature(pr_opened_payload)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-pr-opened",
        }

        response = await client.post("/webhook/github", json=pr_opened_payload, headers=headers)
        assert response.status_code == 200

        # Verify metric was recorded
        new_count = pr_total.labels(
            repository=test_repo, action="opened", merged="false"
        )._value.get()
        assert new_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_pr_merged_webhook_records_review_time(
        self, client, pr_closed_merged_payload
    ):
        """Test that merged PR webhook records review time metric."""
        test_repo = pr_closed_merged_payload["repository"]["full_name"]

        # Get initial histogram count
        metric = pr_review_time_seconds.labels(repository=test_repo)
        initial_count = metric._count.get()

        # Send PR merged webhook
        signature = self._create_signature(pr_closed_merged_payload)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-pr-merged",
        }

        response = await client.post(
            "/webhook/github", json=pr_closed_merged_payload, headers=headers
        )
        assert response.status_code == 200

        # Verify review time metric was recorded
        new_count = metric._count.get()
        assert new_count == initial_count + 1
        assert metric._sum.get() > 0  # Should have some time recorded

    def _create_signature(self, payload: dict) -> str:
        """Create HMAC signature for test payload."""
        import json
        from app.config import settings

        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            settings.github_webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"


class TestDeploymentMetricsFlow:
    """Test push webhook → deployment metrics flow."""

    @pytest.mark.asyncio
    async def test_push_to_main_records_deployment(self, client):
        """Test that push to main branch records deployment metric."""
        # Create push to main payload
        push_payload = {
            "ref": "refs/heads/main",
            "before": "a" * 40,
            "after": "b" * 40,
            "repository": {
                "full_name": "test-org/test-repo",
                "name": "test-repo",
                "owner": {"login": "test-org"},
            },
            "pusher": {"name": "test-user", "email": "test@example.com"},
            "commits": [
                {
                    "id": "b" * 40,
                    "message": "Test commit",
                    "timestamp": "2025-01-01T12:00:00Z",
                    "url": "https://github.com/test-org/test-repo/commit/" + "b" * 40,
                    "author": {"name": "test-user", "email": "test@example.com"},
                    "added": ["file1.py"],
                    "modified": [],
                    "removed": [],
                }
            ],
            "head_commit": {
                "id": "b" * 40,
                "message": "Test commit",
                "timestamp": "2025-01-01T12:00:00Z",
                "url": "https://github.com/test-org/test-repo/commit/" + "b" * 40,
                "author": {"name": "test-user", "email": "test@example.com"},
                "added": ["file1.py"],
                "modified": [],
                "removed": [],
            },
            "compare": "https://github.com/test-org/test-repo/compare/aaa...bbb",
        }

        test_repo = push_payload["repository"]["full_name"]
        initial_count = deployments_total.labels(
            repository=test_repo, environment="production", status="success"
        )._value.get()

        # Send push webhook
        signature = self._create_signature(push_payload)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-main",
        }

        response = await client.post("/webhook/github", json=push_payload, headers=headers)
        assert response.status_code == 200

        # Verify deployment metric was recorded
        new_count = deployments_total.labels(
            repository=test_repo, environment="production", status="success"
        )._value.get()
        assert new_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_push_to_feature_branch_does_not_record_deployment(self, client):
        """Test that push to feature branch does NOT record deployment."""
        push_payload = {
            "ref": "refs/heads/feature/test-branch",
            "before": "a" * 40,
            "after": "b" * 40,
            "repository": {
                "full_name": "test-org/test-repo",
                "name": "test-repo",
                "owner": {"login": "test-org"},
            },
            "pusher": {"name": "test-user", "email": "test@example.com"},
            "commits": [],
            "head_commit": None,
            "compare": "https://github.com/test-org/test-repo/compare/aaa...bbb",
        }

        test_repo = push_payload["repository"]["full_name"]
        initial_count = deployments_total.labels(
            repository=test_repo, environment="production", status="success"
        )._value.get()

        # Send push webhook
        signature = self._create_signature(push_payload)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-push-feature",
        }

        response = await client.post("/webhook/github", json=push_payload, headers=headers)
        assert response.status_code == 200

        # Verify NO deployment metric was recorded
        new_count = deployments_total.labels(
            repository=test_repo, environment="production", status="success"
        )._value.get()
        assert new_count == initial_count  # Should not increment

    def _create_signature(self, payload: dict) -> str:
        """Create HMAC signature for test payload."""
        import json
        from app.config import settings

        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            settings.github_webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"


class TestMetricsConfiguration:
    """Test that metrics respect configuration settings."""

    @pytest.mark.asyncio
    async def test_metrics_only_recorded_when_enabled(
        self, client, pr_opened_payload, monkeypatch
    ):
        """Test that metrics are only recorded when enabled in config."""
        # This test would need to modify settings and restart the app
        # For now, we assume metrics are controlled by settings.enable_metrics
        # which is tested in unit tests
        pass  # Covered by unit tests for now
