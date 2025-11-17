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


def _build_user(login: str, user_id: int) -> dict:
    """Build complete GitHub user object with all required fields."""
    return {
        "login": login,
        "id": user_id,
        "node_id": f"U_kgDO{user_id}",
        "avatar_url": f"https://avatars.githubusercontent.com/u/{user_id}?v=4",
        "gravatar_id": "",
        "url": f"https://api.github.com/users/{login}",
        "html_url": f"https://github.com/{login}",
        "followers_url": f"https://api.github.com/users/{login}/followers",
        "following_url": f"https://api.github.com/users/{login}/following{{/other_user}}",
        "gists_url": f"https://api.github.com/users/{login}/gists{{/gist_id}}",
        "starred_url": f"https://api.github.com/users/{login}/starred{{/owner}}{{/repo}}",
        "subscriptions_url": f"https://api.github.com/users/{login}/subscriptions",
        "organizations_url": f"https://api.github.com/users/{login}/orgs",
        "repos_url": f"https://api.github.com/users/{login}/repos",
        "events_url": f"https://api.github.com/users/{login}/events{{/privacy}}",
        "received_events_url": f"https://api.github.com/users/{login}/received_events",
        "type": "User",
        "user_view_type": "public",
        "site_admin": False,
    }


def _build_repo(
    repo_id: int,
    owner_login: str,
    owner_id: int,
    repo_name: str,
    description: str,
    default_branch: str = "main",
) -> dict:
    """Build complete GitHub repository object with all required fields."""
    full_name = f"{owner_login}/{repo_name}"
    owner = _build_user(owner_login, owner_id)

    return {
        "id": repo_id,
        "node_id": f"R_kgDO{repo_id}",
        "name": repo_name,
        "full_name": full_name,
        "private": False,
        "owner": owner,
        "html_url": f"https://github.com/{full_name}",
        "description": description,
        "fork": False,
        "url": f"https://api.github.com/repos/{full_name}",
        "forks_url": f"https://api.github.com/repos/{full_name}/forks",
        "keys_url": f"https://api.github.com/repos/{full_name}/keys{{/key_id}}",
        "collaborators_url": f"https://api.github.com/repos/{full_name}/collaborators{{/collaborator}}",
        "teams_url": f"https://api.github.com/repos/{full_name}/teams",
        "hooks_url": f"https://api.github.com/repos/{full_name}/hooks",
        "issue_events_url": f"https://api.github.com/repos/{full_name}/issues/events{{/number}}",
        "events_url": f"https://api.github.com/repos/{full_name}/events",
        "assignees_url": f"https://api.github.com/repos/{full_name}/assignees{{/user}}",
        "branches_url": f"https://api.github.com/repos/{full_name}/branches{{/branch}}",
        "tags_url": f"https://api.github.com/repos/{full_name}/tags",
        "blobs_url": f"https://api.github.com/repos/{full_name}/git/blobs{{/sha}}",
        "git_tags_url": f"https://api.github.com/repos/{full_name}/git/tags{{/sha}}",
        "git_refs_url": f"https://api.github.com/repos/{full_name}/git/refs{{/sha}}",
        "trees_url": f"https://api.github.com/repos/{full_name}/git/trees{{/sha}}",
        "statuses_url": f"https://api.github.com/repos/{full_name}/statuses/{{sha}}",
        "languages_url": f"https://api.github.com/repos/{full_name}/languages",
        "stargazers_url": f"https://api.github.com/repos/{full_name}/stargazers",
        "contributors_url": f"https://api.github.com/repos/{full_name}/contributors",
        "subscribers_url": f"https://api.github.com/repos/{full_name}/subscribers",
        "subscription_url": f"https://api.github.com/repos/{full_name}/subscription",
        "commits_url": f"https://api.github.com/repos/{full_name}/commits{{/sha}}",
        "git_commits_url": f"https://api.github.com/repos/{full_name}/git/commits{{/sha}}",
        "comments_url": f"https://api.github.com/repos/{full_name}/comments{{/number}}",
        "issue_comment_url": f"https://api.github.com/repos/{full_name}/issues/comments{{/number}}",
        "contents_url": f"https://api.github.com/repos/{full_name}/contents/{{+path}}",
        "compare_url": f"https://api.github.com/repos/{full_name}/compare/{{base}}...{{head}}",
        "merges_url": f"https://api.github.com/repos/{full_name}/merges",
        "archive_url": f"https://api.github.com/repos/{full_name}/{{archive_format}}{{/ref}}",
        "downloads_url": f"https://api.github.com/repos/{full_name}/downloads",
        "issues_url": f"https://api.github.com/repos/{full_name}/issues{{/number}}",
        "pulls_url": f"https://api.github.com/repos/{full_name}/pulls{{/number}}",
        "milestones_url": f"https://api.github.com/repos/{full_name}/milestones{{/number}}",
        "notifications_url": f"https://api.github.com/repos/{full_name}/notifications{{?since,all,participating}}",
        "labels_url": f"https://api.github.com/repos/{full_name}/labels{{/name}}",
        "releases_url": f"https://api.github.com/repos/{full_name}/releases{{/id}}",
        "deployments_url": f"https://api.github.com/repos/{full_name}/deployments",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-15T00:00:00Z",
        "pushed_at": "2025-01-15T10:00:00Z",
        "git_url": f"git://github.com/{full_name}.git",
        "ssh_url": f"git@github.com:{full_name}.git",
        "clone_url": f"https://github.com/{full_name}.git",
        "svn_url": f"https://github.com/{full_name}",
        "homepage": None,
        "size": 1337,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": "Python",
        "has_issues": True,
        "has_projects": True,
        "has_downloads": True,
        "has_wiki": True,
        "has_pages": False,
        "has_discussions": False,
        "forks_count": 0,
        "mirror_url": None,
        "archived": False,
        "disabled": False,
        "open_issues_count": 1,
        "license": None,
        "allow_forking": True,
        "is_template": False,
        "web_commit_signoff_required": False,
        "topics": [],
        "visibility": "public",
        "forks": 0,
        "open_issues": 1,
        "watchers": 0,
        "default_branch": default_branch,
        "allow_squash_merge": True,
        "allow_merge_commit": True,
        "allow_rebase_merge": True,
        "allow_auto_merge": False,
        "delete_branch_on_merge": False,
        "allow_update_branch": False,
        "use_squash_pr_title_as_default": False,
        "squash_merge_commit_message": "COMMIT_MESSAGES",
        "squash_merge_commit_title": "COMMIT_OR_PR_TITLE",
        "merge_commit_message": "PR_TITLE",
        "merge_commit_title": "MERGE_MESSAGE",
    }


@pytest.fixture
def e2e_skynet_repo():
    """Obviously fake AI project repository."""
    return _build_repo(
        repo_id=123456789,
        owner_login="octocat",
        owner_id=1,
        repo_name="definitely-not-skynet",
        description="Totally harmless AI project. Nothing to see here.",
    )


@pytest.fixture
def e2e_works_on_my_machine_repo():
    """Classic developer excuse repository."""
    return _build_repo(
        repo_id=987654321,
        owner_login="senior-dev",
        owner_id=42,
        repo_name="works-on-my-machine",
        description="¯\\_(ツ)_/¯",
    )


@pytest.fixture
def e2e_pr_opened_payload(e2e_skynet_repo):
    """E2E: PR opened in definitely-not-skynet.

    PR #42: "Add AI sentience (totally safe)"
    Files: god_class.py, spaghetti_code.py, test_that_always_passes.py
    """
    # Use fixed timestamps for consistent signatures
    created_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    full_name = e2e_skynet_repo["full_name"]
    pr_number = 42
    head_sha = "a" * 40
    base_sha = "b" * 40

    # Build users
    pr_author = _build_user("senior-dev", 42)
    repo_owner = _build_user("octocat", 1)

    return {
        "action": "opened",
        "number": pr_number,
        "pull_request": {
            "url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}",
            "id": 111111111,
            "node_id": "PR_kwDO111111",
            "html_url": f"https://github.com/{full_name}/pull/{pr_number}",
            "diff_url": f"https://github.com/{full_name}/pull/{pr_number}.diff",
            "patch_url": f"https://github.com/{full_name}/pull/{pr_number}.patch",
            "issue_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}",
            "number": pr_number,
            "state": "open",
            "locked": False,
            "title": "Add AI sentience (totally safe)",
            "user": pr_author,
            "body": "## Summary\n\nAdding self-awareness to the AI. What could possibly go wrong?\n\n## Checklist\n- [x] Code compiles\n- [ ] Tests (TODO: write these someday)\n- [ ] Documentation (lol)\n\nYOLO 🚀",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "assignee": None,
            "assignees": [],
            "requested_reviewers": [],
            "requested_teams": [],
            "labels": [],
            "milestone": None,
            "draft": False,
            "commits_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits",
            "review_comments_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments",
            "review_comment_url": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}",
            "comments_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments",
            "statuses_url": f"https://api.github.com/repos/{full_name}/statuses/{head_sha}",
            "head": {
                "label": "senior-dev:feature/add-sentience",
                "ref": "feature/add-sentience",
                "sha": head_sha,
                "user": pr_author,
                "repo": _build_repo(
                    repo_id=987654321,
                    owner_login="senior-dev",
                    owner_id=42,
                    repo_name="definitely-not-skynet",
                    description="Fork of skynet for testing",
                ),
            },
            "base": {
                "label": "octocat:main",
                "ref": "main",
                "sha": base_sha,
                "user": repo_owner,
                "repo": e2e_skynet_repo,
            },
            "_links": {
                "self": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}"},
                "html": {"href": f"https://github.com/{full_name}/pull/{pr_number}"},
                "issue": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}"},
                "comments": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments"},
                "review_comments": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments"},
                "review_comment": {"href": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}"},
                "commits": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits"},
                "statuses": {"href": f"https://api.github.com/repos/{full_name}/statuses/{head_sha}"},
            },
            "author_association": "CONTRIBUTOR",
            "auto_merge": None,
            "active_lock_reason": None,
            "merged": False,
            "mergeable": True,
            "rebaseable": None,
            "mergeable_state": "clean",
            "merged_by": None,
            "comments": 0,
            "review_comments": 0,
            "maintainer_can_modify": False,
            "commits": 3,
            "additions": 750,
            "deletions": 200,
            "changed_files": 3,
        },
        "repository": e2e_skynet_repo,
        "sender": pr_author,
    }


@pytest.fixture
def e2e_pr_synchronized_payload(e2e_works_on_my_machine_repo):
    """E2E: PR synchronized (force push) in works-on-my-machine.

    PR #99: "Fix production bug (introduce 3 more)"
    """
    # Use fixed timestamps for consistent signatures
    created_at = datetime(2025, 1, 14, 10, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)

    full_name = e2e_works_on_my_machine_repo["full_name"]
    pr_number = 99
    before_sha = "c" * 40
    after_sha = "d" * 40
    base_sha = "e" * 40

    # Build users
    intern = _build_user("intern", 999)
    senior_dev = _build_user("senior-dev", 42)

    return {
        "action": "synchronize",
        "number": pr_number,
        "before": before_sha,
        "after": after_sha,
        "pull_request": {
            "url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}",
            "id": 222222222,
            "node_id": "PR_kwDO222222",
            "html_url": f"https://github.com/{full_name}/pull/{pr_number}",
            "diff_url": f"https://github.com/{full_name}/pull/{pr_number}.diff",
            "patch_url": f"https://github.com/{full_name}/pull/{pr_number}.patch",
            "issue_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}",
            "number": pr_number,
            "state": "open",
            "locked": False,
            "title": "Fix production bug (probably introduce 3 more)",
            "user": intern,
            "body": "Hotfix for prod. Tested on my machine. Deploy on Friday?",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "assignee": None,
            "assignees": [],
            "requested_reviewers": [],
            "requested_teams": [],
            "labels": [],
            "milestone": None,
            "draft": False,
            "commits_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits",
            "review_comments_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments",
            "review_comment_url": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}",
            "comments_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments",
            "statuses_url": f"https://api.github.com/repos/{full_name}/statuses/{after_sha}",
            "head": {
                "label": "intern:hotfix/friday-deploy",
                "ref": "hotfix/friday-deploy",
                "sha": after_sha,
                "user": intern,
                "repo": _build_repo(
                    repo_id=888888888,
                    owner_login="intern",
                    owner_id=999,
                    repo_name="works-on-my-machine",
                    description="Intern's fork (YOLO commits)",
                ),
            },
            "base": {
                "label": "senior-dev:main",
                "ref": "main",
                "sha": base_sha,
                "user": senior_dev,
                "repo": e2e_works_on_my_machine_repo,
            },
            "_links": {
                "self": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}"},
                "html": {"href": f"https://github.com/{full_name}/pull/{pr_number}"},
                "issue": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}"},
                "comments": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments"},
                "review_comments": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments"},
                "review_comment": {"href": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}"},
                "commits": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits"},
                "statuses": {"href": f"https://api.github.com/repos/{full_name}/statuses/{after_sha}"},
            },
            "author_association": "CONTRIBUTOR",
            "auto_merge": None,
            "active_lock_reason": None,
            "merged": False,
            "mergeable": True,
            "rebaseable": None,
            "mergeable_state": "unstable",
            "merged_by": None,
            "comments": 0,
            "review_comments": 0,
            "maintainer_can_modify": False,
            "commits": 5,
            "additions": 150,
            "deletions": 50,
            "changed_files": 2,
        },
        "repository": e2e_works_on_my_machine_repo,
        "sender": intern,
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

    full_name = e2e_skynet_repo["full_name"]
    pr_number = 42
    head_sha = "a" * 40
    base_sha = "b" * 40
    merge_sha = "f" * 40

    # Build users
    pr_author = _build_user("senior-dev", 42)
    repo_owner = _build_user("octocat", 1)

    return {
        "action": "closed",
        "number": pr_number,
        "pull_request": {
            "url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}",
            "id": 111111111,
            "node_id": "PR_kwDO111111",
            "html_url": f"https://github.com/{full_name}/pull/{pr_number}",
            "diff_url": f"https://github.com/{full_name}/pull/{pr_number}.diff",
            "patch_url": f"https://github.com/{full_name}/pull/{pr_number}.patch",
            "issue_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}",
            "number": pr_number,
            "state": "closed",
            "locked": False,
            "title": "Add AI sentience (totally safe)",
            "user": pr_author,
            "body": "## Summary\n\nAdding self-awareness to the AI. What could possibly go wrong?\n\nYOLO 🚀",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "closed_at": merged_at.isoformat(),
            "merged_at": merged_at.isoformat(),
            "merge_commit_sha": merge_sha,
            "assignee": None,
            "assignees": [],
            "requested_reviewers": [],
            "requested_teams": [],
            "labels": [],
            "milestone": None,
            "draft": False,
            "commits_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits",
            "review_comments_url": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments",
            "review_comment_url": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}",
            "comments_url": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments",
            "statuses_url": f"https://api.github.com/repos/{full_name}/statuses/{head_sha}",
            "head": {
                "label": "senior-dev:feature/add-sentience",
                "ref": "feature/add-sentience",
                "sha": head_sha,
                "user": pr_author,
                "repo": _build_repo(
                    repo_id=987654321,
                    owner_login="senior-dev",
                    owner_id=42,
                    repo_name="definitely-not-skynet",
                    description="Fork of skynet for testing",
                ),
            },
            "base": {
                "label": "octocat:main",
                "ref": "main",
                "sha": base_sha,
                "user": repo_owner,
                "repo": e2e_skynet_repo,
            },
            "_links": {
                "self": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}"},
                "html": {"href": f"https://github.com/{full_name}/pull/{pr_number}"},
                "issue": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}"},
                "comments": {"href": f"https://api.github.com/repos/{full_name}/issues/{pr_number}/comments"},
                "review_comments": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/comments"},
                "review_comment": {"href": f"https://api.github.com/repos/{full_name}/pulls/comments{{/number}}"},
                "commits": {"href": f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/commits"},
                "statuses": {"href": f"https://api.github.com/repos/{full_name}/statuses/{head_sha}"},
            },
            "author_association": "CONTRIBUTOR",
            "auto_merge": None,
            "active_lock_reason": None,
            "merged": True,
            "mergeable": None,
            "rebaseable": None,
            "mergeable_state": "unknown",
            "merged_by": repo_owner,
            "comments": 0,
            "review_comments": 0,
            "maintainer_can_modify": False,
            "commits": 3,
            "additions": 750,
            "deletions": 200,
            "changed_files": 3,
        },
        "repository": e2e_skynet_repo,
        "sender": pr_author,
    }


@pytest.fixture
def e2e_push_to_main_payload(e2e_works_on_my_machine_repo):
    """E2E: Push to main branch (deployment simulation).

    3 commits with developer humor
    """
    senior_dev = _build_user("senior-dev", 42)

    return {
        "ref": "refs/heads/main",
        "before": "1" * 40,
        "after": "2" * 40,
        "repository": e2e_works_on_my_machine_repo,
        "pusher": {
            "name": "senior-dev",
            "email": "senior-dev@example.com",
        },
        "sender": senior_dev,
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
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
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
