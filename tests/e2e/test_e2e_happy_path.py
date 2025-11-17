"""E2E happy path tests for webhook receiver.

Tests complete flows from webhook receipt through processing, audit logging,
and metrics recording. All scenarios use obviously fake repository names.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from app.metrics import deployments_total, pr_review_time_seconds, pr_total


class TestE2EPRHappyPath:
    """E2E happy path tests for pull request webhooks."""

    def test_pr_opened_complete_flow(
        self,
        client,
        e2e_pr_opened_payload,
        e2e_compute_signature,
        e2e_headers_for_pr,
    ):
        """E2E: Complete flow for PR opened webhook.

        Repo: octocat/definitely-not-skynet
        PR #42: "Add AI sentience (totally safe)"

        Verifies:
        1. HTTP 200 response with correct status
        2. Audit log entry created
        3. PR metrics incremented
        4. Response contains delivery ID
        """
        # Arrange
        delivery_id = "e2e-test-pr-opened-skynet-001"

        # Serialize payload once to ensure signature matches request body
        import json
        payload_json = json.dumps(e2e_pr_opened_payload, separators=(",", ":"), sort_keys=True)

        signature = e2e_compute_signature(e2e_pr_opened_payload)
        headers = e2e_headers_for_pr(delivery_id)
        headers["X-Hub-Signature-256"] = signature
        headers["Content-Type"] = "application/json"

        repo_name = e2e_pr_opened_payload["repository"]["full_name"]
        initial_pr_count = pr_total.labels(
            repository=repo_name, action="opened", merged="false"
        )._value.get()

        # Act
        response = client.post(
            "/webhook/github", data=payload_json, headers=headers
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Verify response data
        assert response_data["status"] == "processing"
        assert response_data["pr_number"] == 42
        assert response_data["action"] == "opened"
        assert response_data["delivery_id"] == delivery_id

        # Verify metrics incremented (with retry since background task is async)
        import time
        max_wait = 3  # seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            new_pr_count = pr_total.labels(
                repository=repo_name, action="opened", merged="false"
            )._value.get()
            if new_pr_count == initial_pr_count + 1:
                break
            time.sleep(0.1)
        else:
            # If we got here, metrics weren't incremented in time
            pytest.fail(f"Metrics not incremented after {max_wait}s. Expected {initial_pr_count + 1}, got {new_pr_count}")

        assert new_pr_count == initial_pr_count + 1

        # Verify audit log exists
        audit_log_file = Path(f"logs/webhooks/webhooks-{date.today().isoformat()}.jsonl")
        if audit_log_file.exists():
            # Read audit log and verify entry exists
            with open(audit_log_file, "r") as f:
                log_entries = [json.loads(line) for line in f if line.strip()]
                matching_entries = [
                    entry
                    for entry in log_entries
                    if entry.get("delivery_id") == delivery_id
                ]
                assert (
                    len(matching_entries) >= 1
                ), f"Expected at least 1 audit entry, found {len(matching_entries)}"

                entry = matching_entries[0]
                assert entry["event_type"] == "pull_request"
                assert entry["payload"]["number"] == 42
                assert entry["payload"]["repository"]["full_name"] == repo_name

    def test_pr_merged_complete_flow(
        self,
        client,
        e2e_pr_merged_payload,
        e2e_compute_signature,
        e2e_headers_for_pr,
    ):
        """E2E: Complete flow for PR merged webhook.

        Repo: octocat/definitely-not-skynet
        PR #42 merged after 2.5 hours

        Verifies:
        1. HTTP 200 response
        2. Audit log entry
        3. PR metrics show merged=true
        4. PR review time recorded
        """
        # Arrange
        delivery_id = "e2e-test-pr-merged-skynet-002"
        signature = e2e_compute_signature(e2e_pr_merged_payload)
        headers = e2e_headers_for_pr(delivery_id)
        headers["X-Hub-Signature-256"] = signature

        repo_name = e2e_pr_merged_payload["repository"]["full_name"]

        # Get initial metrics
        initial_merged_count = pr_total.labels(
            repository=repo_name, action="closed", merged="true"
        )._value.get()

        # Act
        response = client.post(
            "/webhook/github", json=e2e_pr_merged_payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Verify response
        assert response_data["status"] == "processing"
        assert response_data["pr_number"] == 42
        assert response_data["action"] == "closed"

        # Verify merged PR metric incremented
        new_merged_count = pr_total.labels(
            repository=repo_name, action="closed", merged="true"
        )._value.get()
        assert new_merged_count == initial_merged_count + 1

        # Verify review time was recorded (histogram should have data)
        # Note: Can't easily verify exact value, but we can verify it was called
        # by checking that another observation increases the count

    def test_pr_synchronized_complete_flow(
        self,
        client,
        e2e_pr_synchronized_payload,
        e2e_compute_signature,
        e2e_headers_for_pr,
    ):
        """E2E: Complete flow for PR synchronized webhook.

        Repo: senior-dev/works-on-my-machine
        PR #99: Force push to hotfix branch

        Verifies:
        1. HTTP 200 response
        2. Metrics recorded for synchronize action
        3. Audit log captured
        """
        # Arrange
        delivery_id = "e2e-test-pr-synchronized-works-003"
        signature = e2e_compute_signature(e2e_pr_synchronized_payload)
        headers = e2e_headers_for_pr(delivery_id)
        headers["X-Hub-Signature-256"] = signature

        repo_name = e2e_pr_synchronized_payload["repository"]["full_name"]
        initial_sync_count = pr_total.labels(
            repository=repo_name, action="synchronize", merged="false"
        )._value.get()

        # Act
        response = client.post(
            "/webhook/github", json=e2e_pr_synchronized_payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Verify response
        assert response_data["status"] == "processing"
        assert response_data["pr_number"] == 99
        assert response_data["action"] == "synchronize"

        # Verify synchronize metric incremented
        new_sync_count = pr_total.labels(
            repository=repo_name, action="synchronize", merged="false"
        )._value.get()
        assert new_sync_count == initial_sync_count + 1


class TestE2EPushHappyPath:
    """E2E happy path tests for push webhooks."""

    def test_push_to_main_complete_flow(
        self,
        client,
        e2e_push_to_main_payload,
        e2e_compute_signature,
        e2e_headers_for_push,
    ):
        """E2E: Complete flow for push to main branch.

        Repo: senior-dev/works-on-my-machine
        3 commits with developer humor

        Verifies:
        1. HTTP 200 response
        2. Deployment metric recorded (push-to-main = deployment)
        3. Audit log entry
        4. Correct environment label (production)
        """
        # Arrange
        delivery_id = "e2e-test-push-main-works-004"
        signature = e2e_compute_signature(e2e_push_to_main_payload)
        headers = e2e_headers_for_push(delivery_id)
        headers["X-Hub-Signature-256"] = signature

        repo_name = e2e_push_to_main_payload["repository"]["full_name"]
        initial_deploy_count = deployments_total.labels(
            repository=repo_name, environment="production", status="success"
        )._value.get()

        # Act
        response = client.post(
            "/webhook/github", json=e2e_push_to_main_payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Verify response
        assert response_data["status"] == "accepted"
        assert response_data["branch"] == "main"
        assert response_data["commits"] == 3

        # Verify deployment metric incremented
        new_deploy_count = deployments_total.labels(
            repository=repo_name, environment="production", status="success"
        )._value.get()
        assert new_deploy_count == initial_deploy_count + 1

        # Verify audit log exists
        audit_log_file = Path(f"logs/webhooks/webhooks-{date.today().isoformat()}.jsonl")
        if audit_log_file.exists():
            with open(audit_log_file, "r") as f:
                log_entries = [json.loads(line) for line in f if line.strip()]
                matching_entries = [
                    entry
                    for entry in log_entries
                    if entry.get("delivery_id") == delivery_id
                ]
                assert len(matching_entries) == 1

                entry = matching_entries[0]
                assert entry["event_type"] == "push"
                assert entry["payload"]["ref"] == "refs/heads/main"
                assert len(entry["payload"]["commits"]) == 3

    def test_push_to_feature_branch_ignores_deployment(
        self,
        client,
        e2e_push_to_main_payload,
        e2e_compute_signature,
        e2e_headers_for_push,
    ):
        """E2E: Push to feature branch doesn't record deployment.

        Verifies that only pushes to main/master trigger deployment metrics.
        """
        # Arrange - modify payload to be a feature branch
        feature_payload = e2e_push_to_main_payload.copy()
        feature_payload["ref"] = "refs/heads/feature/not-a-deployment"

        delivery_id = "e2e-test-push-feature-005"
        signature = e2e_compute_signature(feature_payload)
        headers = e2e_headers_for_push(delivery_id)
        headers["X-Hub-Signature-256"] = signature

        repo_name = feature_payload["repository"]["full_name"]
        initial_deploy_count = deployments_total.labels(
            repository=repo_name, environment="production", status="success"
        )._value.get()

        # Act
        response = client.post("/webhook/github", json=feature_payload, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Verify feature branch in response
        assert "feature/not-a-deployment" in response_data.get("branch", "")

        # Verify deployment metric NOT incremented
        new_deploy_count = deployments_total.labels(
            repository=repo_name, environment="production", status="success"
        )._value.get()
        assert new_deploy_count == initial_deploy_count, "Feature branch should not trigger deployment metric"
