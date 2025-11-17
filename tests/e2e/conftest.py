"""E2E test fixtures with obviously fake, humorous test data.

All fixtures use developer-humor themed repository names, commit messages,
and file names to make it crystal clear these are test scenarios.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings


@pytest.fixture
def e2e_skynet_repo():
    """Obviously fake AI project repository."""
    return {
        "id": 123456789,
        "name": "definitely-not-skynet",
        "full_name": "octocat/definitely-not-skynet",
        "owner": {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "type": "User",
        },
        "private": False,
        "html_url": "https://github.com/octocat/definitely-not-skynet",
        "description": "Totally harmless AI project. Nothing to see here.",
        "fork": False,
        "default_branch": "main",
    }


@pytest.fixture
def e2e_works_on_my_machine_repo():
    """Classic developer excuse repository."""
    return {
        "id": 987654321,
        "name": "works-on-my-machine",
        "full_name": "senior-dev/works-on-my-machine",
        "owner": {
            "login": "senior-dev",
            "id": 42,
            "avatar_url": "https://avatars.githubusercontent.com/u/42?v=4",
            "type": "User",
        },
        "private": False,
        "html_url": "https://github.com/senior-dev/works-on-my-machine",
        "description": "¯\\_(ツ)_/¯",
        "fork": False,
        "default_branch": "main",
    }


@pytest.fixture
def e2e_pr_opened_payload(e2e_skynet_repo):
    """E2E: PR opened in definitely-not-skynet.

    PR #42: "Add AI sentience (totally safe)"
    Files: god_class.py, spaghetti_code.py, test_that_always_passes.py
    """
    # Use fixed timestamps for consistent signatures
    created_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    return {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 111111111,
            "number": 42,
            "state": "open",
            "locked": False,
            "title": "Add AI sentience (totally safe)",
            "user": {
                "login": "senior-dev",
                "id": 42,
                "type": "User",
            },
            "body": "## Summary\n\nAdding self-awareness to the AI. What could possibly go wrong?\n\n## Checklist\n- [x] Code compiles\n- [ ] Tests (TODO: write these someday)\n- [ ] Documentation (lol)\n\nYOLO 🚀",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "head": {
                "label": "senior-dev:feature/add-sentience",
                "ref": "feature/add-sentience",
                "sha": "a" * 40,
                "user": {"login": "senior-dev"},
            },
            "base": {
                "label": "octocat:main",
                "ref": "main",
                "sha": "b" * 40,
                "user": {"login": "octocat"},
            },
            "merged": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "draft": False,
            "commits": 3,
            "additions": 750,
            "deletions": 200,
            "changed_files": 3,
        },
        "repository": e2e_skynet_repo,
        "sender": {
            "login": "senior-dev",
            "id": 42,
            "type": "User",
        },
    }


@pytest.fixture
def e2e_pr_synchronized_payload(e2e_works_on_my_machine_repo):
    """E2E: PR synchronized (force push) in works-on-my-machine.

    PR #99: "Fix production bug (introduce 3 more)"
    """
    # Use fixed timestamps for consistent signatures
    created_at = datetime(2025, 1, 14, 10, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)

    return {
        "action": "synchronize",
        "number": 99,
        "before": "c" * 40,
        "after": "d" * 40,
        "pull_request": {
            "id": 222222222,
            "number": 99,
            "state": "open",
            "locked": False,
            "title": "Fix production bug (probably introduce 3 more)",
            "user": {
                "login": "intern",
                "id": 999,
                "type": "User",
            },
            "body": "Hotfix for prod. Tested on my machine. Deploy on Friday?",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "head": {
                "label": "intern:hotfix/friday-deploy",
                "ref": "hotfix/friday-deploy",
                "sha": "d" * 40,
                "user": {"login": "intern"},
            },
            "base": {
                "label": "senior-dev:main",
                "ref": "main",
                "sha": "e" * 40,
                "user": {"login": "senior-dev"},
            },
            "merged": False,
            "mergeable": True,
            "mergeable_state": "unstable",
            "draft": False,
            "commits": 5,
            "additions": 150,
            "deletions": 50,
            "changed_files": 2,
        },
        "repository": e2e_works_on_my_machine_repo,
        "sender": {
            "login": "intern",
            "id": 999,
            "type": "User",
        },
    }


@pytest.fixture
def e2e_pr_merged_payload(e2e_skynet_repo):
    """E2E: PR merged in definitely-not-skynet.

    PR #42 merged after 2.5 hours of "review"
    """
    # Use fixed timestamps for consistent signatures (2.5 hour review time)
    created_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
    merged_at = datetime(2025, 1, 15, 12, 30, 0, tzinfo=timezone.utc)

    return {
        "action": "closed",
        "number": 42,
        "pull_request": {
            "id": 111111111,
            "number": 42,
            "state": "closed",
            "locked": False,
            "title": "Add AI sentience (totally safe)",
            "user": {
                "login": "senior-dev",
                "id": 42,
                "type": "User",
            },
            "body": "## Summary\n\nAdding self-awareness to the AI. What could possibly go wrong?\n\nYOLO 🚀",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": merged_at.isoformat(),
            "merged_at": merged_at.isoformat(),
            "merge_commit_sha": "f" * 40,
            "head": {
                "label": "senior-dev:feature/add-sentience",
                "ref": "feature/add-sentience",
                "sha": "a" * 40,
                "user": {"login": "senior-dev"},
            },
            "base": {
                "label": "octocat:main",
                "ref": "main",
                "sha": "b" * 40,
                "user": {"login": "octocat"},
            },
            "merged": True,
            "merged_by": {
                "login": "octocat",
                "id": 1,
                "type": "User",
            },
            "mergeable": None,
            "mergeable_state": "unknown",
            "draft": False,
            "commits": 3,
            "additions": 750,
            "deletions": 200,
            "changed_files": 3,
        },
        "repository": e2e_skynet_repo,
        "sender": {
            "login": "senior-dev",
            "id": 42,
            "type": "User",
        },
    }


@pytest.fixture
def e2e_push_to_main_payload(e2e_works_on_my_machine_repo):
    """E2E: Push to main branch (deployment simulation).

    3 commits with developer humor
    """
    return {
        "ref": "refs/heads/main",
        "before": "1" * 40,
        "after": "2" * 40,
        "repository": e2e_works_on_my_machine_repo,
        "pusher": {
            "name": "senior-dev",
            "email": "senior-dev@example.com",
        },
        "sender": {
            "login": "senior-dev",
            "id": 42,
            "type": "User",
        },
        "commits": [
            {
                "id": "a1b2c3d4" + "0" * 32,
                "tree_id": "tree123",
                "distinct": True,
                "message": "WIP: this compiles, shipping it",
                "timestamp": "2025-01-15T10:00:00Z",
                "url": "https://github.com/senior-dev/works-on-my-machine/commit/a1b2c3d4",
                "author": {
                    "name": "Senior Dev",
                    "email": "senior@example.com",
                    "username": "senior-dev",
                },
                "committer": {
                    "name": "Senior Dev",
                    "email": "senior@example.com",
                    "username": "senior-dev",
                },
                "added": ["src/new_feature.py"],
                "removed": [],
                "modified": ["src/main.py"],
            },
            {
                "id": "e5f6g7h8" + "0" * 32,
                "tree_id": "tree456",
                "distinct": True,
                "message": "Fixed bug (introduced 3 more)",
                "timestamp": "2025-01-15T11:00:00Z",
                "url": "https://github.com/senior-dev/works-on-my-machine/commit/e5f6g7h8",
                "author": {
                    "name": "Intern",
                    "email": "intern@example.com",
                    "username": "intern",
                },
                "committer": {
                    "name": "Intern",
                    "email": "intern@example.com",
                    "username": "intern",
                },
                "added": [],
                "removed": ["legacy/spaghetti_code.py"],
                "modified": ["src/bugfix.py"],
            },
            {
                "id": "i9j0k1l2" + "0" * 32,
                "tree_id": "tree789",
                "distinct": True,
                "message": "TODO: add tests (narrator: they never did)",
                "timestamp": "2025-01-15T12:00:00Z",
                "url": "https://github.com/senior-dev/works-on-my-machine/commit/i9j0k1l2",
                "author": {
                    "name": "PM",
                    "email": "pm@example.com",
                    "username": "pm-user",
                },
                "committer": {
                    "name": "PM",
                    "email": "pm@example.com",
                    "username": "pm-user",
                },
                "added": ["docs/README.md"],
                "removed": [],
                "modified": [],
            },
        ],
        "head_commit": {
            "id": "2" * 40,
            "tree_id": "tree789",
            "distinct": True,
            "message": "TODO: add tests (narrator: they never did)",
            "timestamp": "2025-01-15T12:00:00Z",
            "url": f"https://github.com/senior-dev/works-on-my-machine/commit/{'2' * 40}",
            "author": {
                "name": "PM",
                "email": "pm@example.com",
                "username": "pm-user",
            },
            "committer": {
                "name": "PM",
                "email": "pm@example.com",
                "username": "pm-user",
            },
            "added": ["docs/README.md"],
            "removed": [],
            "modified": [],
        },
        "compare": f"https://github.com/senior-dev/works-on-my-machine/compare/{'1' * 12}...{'2' * 12}",
    }


@pytest.fixture
def e2e_compute_signature():
    """Helper function to compute HMAC signature for e2e tests."""

    def _compute(payload: dict) -> str:
        """Compute valid GitHub webhook signature.

        Args:
            payload: Webhook payload dictionary

        Returns:
            str: Signature in format "sha256=<hex_digest>"
        """
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            settings.github_webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    return _compute


@pytest.fixture
def e2e_headers_for_pr():
    """Standard headers for PR webhook e2e tests."""
    return lambda delivery_id: {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Hookshot/test",
    }


@pytest.fixture
def e2e_headers_for_push():
    """Standard headers for push webhook e2e tests."""
    return lambda delivery_id: {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Hookshot/test",
    }
