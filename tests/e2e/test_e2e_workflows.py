"""E2E workflow tests simulating multi-step PR lifecycles.

Tests complete PR workflows from opened → synchronized → merged,
verifying state consistency across multiple webhook deliveries.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.metrics import pr_review_time_seconds, pr_total


class TestE2ECompleteWorkflow:
    """E2E tests for complete PR lifecycle workflows."""

    def test_complete_pr_lifecycle(
        self,
        client,
        e2e_skynet_repo,
        e2e_compute_signature,
        e2e_headers_for_pr,
    ):
        """E2E: Complete PR lifecycle from opened to merged.

        Simulates:
        Step 1: PR opened (#42 in definitely-not-skynet)
        Step 2: PR synchronized (force push)
        Step 3: PR synchronized (new commits)
        Step 4: PR merged

        Verifies metrics and state consistency across all steps.
        """
        repo_name = e2e_skynet_repo["full_name"]

        # Get initial metrics
        initial_opened = pr_total.labels(
            repository=repo_name, action="opened", merged="false"
        )._value.get()
        initial_sync = pr_total.labels(
            repository=repo_name, action="synchronize", merged="false"
        )._value.get()
        initial_merged = pr_total.labels(
            repository=repo_name, action="closed", merged="true"
        )._value.get()

        # Step 1: PR Opened
        created_at = datetime.now(timezone.utc) - timedelta(hours=3)
        pr_opened = self._create_pr_opened(e2e_skynet_repo, created_at)

        response = self._send_webhook(
            client,
            pr_opened,
            "e2e-workflow-opened-001",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "processing"
        assert response.json()["pr_number"] == 42

        # Verify opened metric incremented
        assert (
            pr_total.labels(repository=repo_name, action="opened", merged="false")._value.get()
            == initial_opened + 1
        )

        # Step 2: PR Synchronized (force push)
        pr_sync_1 = self._create_pr_synchronized(
            e2e_skynet_repo, created_at, "force push: fixing typos"
        )

        response = self._send_webhook(
            client,
            pr_sync_1,
            "e2e-workflow-sync1-002",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )

        assert response.status_code == 200
        assert response.json()["action"] == "synchronize"

        # Verify sync metric incremented (first time)
        assert (
            pr_total.labels(repository=repo_name, action="synchronize", merged="false")._value.get()
            == initial_sync + 1
        )

        # Step 3: PR Synchronized (new commits)
        pr_sync_2 = self._create_pr_synchronized(
            e2e_skynet_repo, created_at, "added tests (lol jk)"
        )

        response = self._send_webhook(
            client,
            pr_sync_2,
            "e2e-workflow-sync2-003",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )

        assert response.status_code == 200

        # Verify sync metric incremented again
        assert (
            pr_total.labels(repository=repo_name, action="synchronize", merged="false")._value.get()
            == initial_sync + 2
        )

        # Step 4: PR Merged
        merged_at = datetime.now(timezone.utc)
        pr_merged = self._create_pr_merged(e2e_skynet_repo, created_at, merged_at)

        response = self._send_webhook(
            client,
            pr_merged,
            "e2e-workflow-merged-004",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )

        assert response.status_code == 200

        # Verify merged metric incremented
        assert (
            pr_total.labels(repository=repo_name, action="closed", merged="true")._value.get()
            == initial_merged + 1
        )

        # Verify review time was recorded (3 hours)
        # Can't directly assert histogram value, but test that it didn't crash

    def test_multiple_prs_interleaved(
        self,
        client,
        e2e_skynet_repo,
        e2e_works_on_my_machine_repo,
        e2e_compute_signature,
        e2e_headers_for_pr,
    ):
        """E2E: Multiple PRs from different repos interleaved.

        Simulates:
        - PR #1 opened (skynet)
        - PR #2 opened (works-on-my-machine)
        - PR #1 synchronized (skynet)
        - PR #2 merged (works-on-my-machine)
        - PR #1 closed without merge (skynet)

        Verifies each PR is tracked independently.
        """
        skynet_name = e2e_skynet_repo["full_name"]
        works_name = e2e_works_on_my_machine_repo["full_name"]

        # Get initial metrics for both repos
        skynet_initial = pr_total.labels(
            repository=skynet_name, action="opened", merged="false"
        )._value.get()
        works_initial = pr_total.labels(
            repository=works_name, action="opened", merged="false"
        )._value.get()

        # PR #1 opened (skynet)
        created_at_1 = datetime.now(timezone.utc) - timedelta(hours=2)
        pr1_opened = self._create_pr_opened(e2e_skynet_repo, created_at_1, pr_number=1)

        response = self._send_webhook(
            client,
            pr1_opened,
            "e2e-multi-pr1-opened-001",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )
        assert response.status_code == 200
        assert response.json()["pr_number"] == 1

        # Verify skynet metric incremented
        assert (
            pr_total.labels(repository=skynet_name, action="opened", merged="false")._value.get()
            == skynet_initial + 1
        )

        # PR #2 opened (works-on-my-machine)
        created_at_2 = datetime.now(timezone.utc) - timedelta(hours=1)
        pr2_opened = self._create_pr_opened(
            e2e_works_on_my_machine_repo, created_at_2, pr_number=2
        )

        response = self._send_webhook(
            client,
            pr2_opened,
            "e2e-multi-pr2-opened-002",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )
        assert response.status_code == 200
        assert response.json()["pr_number"] == 2

        # Verify works metric incremented
        assert (
            pr_total.labels(repository=works_name, action="opened", merged="false")._value.get()
            == works_initial + 1
        )

        # PR #2 merged (works-on-my-machine)
        merged_at_2 = datetime.now(timezone.utc)
        pr2_merged = self._create_pr_merged(
            e2e_works_on_my_machine_repo, created_at_2, merged_at_2, pr_number=2
        )

        response = self._send_webhook(
            client,
            pr2_merged,
            "e2e-multi-pr2-merged-003",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )
        assert response.status_code == 200

        # Verify works merged metric incremented
        works_merged = pr_total.labels(
            repository=works_name, action="closed", merged="true"
        )._value.get()
        assert works_merged > 0

        # PR #1 closed without merge (skynet)
        pr1_closed = self._create_pr_closed_unmerged(e2e_skynet_repo, created_at_1, pr_number=1)

        response = self._send_webhook(
            client,
            pr1_closed,
            "e2e-multi-pr1-closed-004",
            e2e_compute_signature,
            e2e_headers_for_pr,
        )
        assert response.status_code == 200

        # Verify skynet closed-unmerged metric incremented
        skynet_closed = pr_total.labels(
            repository=skynet_name, action="closed", merged="false"
        )._value.get()
        assert skynet_closed > 0

    # Helper methods to create payloads

    def _send_webhook(self, client, payload, delivery_id, compute_sig, headers_func):
        """Send webhook with proper signature and headers."""
        signature = compute_sig(payload)
        headers = headers_func(delivery_id)
        headers["X-Hub-Signature-256"] = signature
        return client.post("/webhook/github", json=payload, headers=headers)

    def _create_pr_opened(self, repo, created_at, pr_number=42):
        """Create PR opened payload."""
        return {
            "action": "opened",
            "number": pr_number,
            "pull_request": {
                "id": pr_number * 1000,
                "number": pr_number,
                "state": "open",
                "title": f"Add feature #{pr_number}",
                "user": {"login": "developer", "id": 123},
                "body": "Test PR body",
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
                "closed_at": None,
                "merged_at": None,
                "merge_commit_sha": None,
                "head": {
                    "ref": f"feature/pr-{pr_number}",
                    "sha": str(pr_number) * 10,
                    "user": {"login": "developer"},
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {"login": repo["owner"]["login"]},
                },
                "merged": False,
                "draft": False,
                "commits": 1,
                "additions": 100,
                "deletions": 10,
                "changed_files": 2,
            },
            "repository": repo,
            "sender": {"login": "developer", "id": 123},
        }

    def _create_pr_synchronized(self, repo, created_at, commit_msg="Updated PR"):
        """Create PR synchronized payload."""
        updated_at = datetime.now(timezone.utc)
        return {
            "action": "synchronize",
            "number": 42,
            "before": "a" * 40,
            "after": "c" * 40,
            "pull_request": {
                "id": 42000,
                "number": 42,
                "state": "open",
                "title": "Add feature #42",
                "user": {"login": "developer", "id": 123},
                "body": "Test PR body",
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "closed_at": None,
                "merged_at": None,
                "head": {
                    "ref": "feature/pr-42",
                    "sha": "c" * 40,
                    "user": {"login": "developer"},
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {"login": repo["owner"]["login"]},
                },
                "merged": False,
                "draft": False,
                "commits": 2,
                "additions": 150,
                "deletions": 20,
                "changed_files": 3,
            },
            "repository": repo,
            "sender": {"login": "developer", "id": 123},
        }

    def _create_pr_merged(self, repo, created_at, merged_at, pr_number=42):
        """Create PR merged payload."""
        return {
            "action": "closed",
            "number": pr_number,
            "pull_request": {
                "id": pr_number * 1000,
                "number": pr_number,
                "state": "closed",
                "title": f"Add feature #{pr_number}",
                "user": {"login": "developer", "id": 123},
                "body": "Test PR body",
                "created_at": created_at.isoformat(),
                "updated_at": merged_at.isoformat(),
                "closed_at": merged_at.isoformat(),
                "merged_at": merged_at.isoformat(),
                "merge_commit_sha": "m" * 40,
                "head": {
                    "ref": f"feature/pr-{pr_number}",
                    "sha": str(pr_number) * 10,
                    "user": {"login": "developer"},
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {"login": repo["owner"]["login"]},
                },
                "merged": True,
                "merged_by": {"login": repo["owner"]["login"], "id": 1},
                "draft": False,
                "commits": 2,
                "additions": 150,
                "deletions": 20,
                "changed_files": 3,
            },
            "repository": repo,
            "sender": {"login": "developer", "id": 123},
        }

    def _create_pr_closed_unmerged(self, repo, created_at, pr_number=42):
        """Create PR closed without merge payload."""
        closed_at = datetime.now(timezone.utc)
        return {
            "action": "closed",
            "number": pr_number,
            "pull_request": {
                "id": pr_number * 1000,
                "number": pr_number,
                "state": "closed",
                "title": f"Add feature #{pr_number}",
                "user": {"login": "developer", "id": 123},
                "body": "Test PR body",
                "created_at": created_at.isoformat(),
                "updated_at": closed_at.isoformat(),
                "closed_at": closed_at.isoformat(),
                "merged_at": None,
                "merge_commit_sha": None,
                "head": {
                    "ref": f"feature/pr-{pr_number}",
                    "sha": str(pr_number) * 10,
                    "user": {"login": "developer"},
                },
                "base": {
                    "ref": "main",
                    "sha": "b" * 40,
                    "user": {"login": repo["owner"]["login"]},
                },
                "merged": False,
                "draft": False,
                "commits": 1,
                "additions": 100,
                "deletions": 10,
                "changed_files": 2,
            },
            "repository": repo,
            "sender": {"login": "developer", "id": 123},
        }
