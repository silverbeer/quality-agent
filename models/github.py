"""GitHub webhook payload models.

Pydantic models for GitHub webhook payloads, specifically for pull request events.
These models provide type-safe parsing and validation of incoming webhook data.

Reference: https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class GitHubUser(BaseModel):
    """GitHub user information."""

    login: str = Field(description="GitHub username")
    id: int = Field(description="GitHub user ID")
    avatar_url: HttpUrl = Field(description="User avatar URL")
    html_url: HttpUrl = Field(description="User profile URL")
    type: str = Field(description="User type (User, Bot, etc.)")


class GitHubRepository(BaseModel):
    """GitHub repository information."""

    id: int = Field(description="Repository ID")
    name: str = Field(description="Repository name")
    full_name: str = Field(description="Full repository name (owner/repo)")
    html_url: HttpUrl = Field(description="Repository URL")
    description: str | None = Field(default=None, description="Repository description")
    private: bool = Field(description="Whether repository is private")
    owner: GitHubUser = Field(description="Repository owner")
    default_branch: str = Field(description="Default branch name")


class GitHubRef(BaseModel):
    """Git reference (branch/commit) information."""

    ref: str = Field(description="Branch name")
    sha: str = Field(description="Commit SHA", min_length=40, max_length=40)
    repo: GitHubRepository | None = Field(default=None, description="Repository info")
    user: GitHubUser = Field(description="User who owns the ref")
    label: str = Field(description="Label for the ref (owner:branch)")


class PullRequest(BaseModel):
    """GitHub pull request data."""

    id: int = Field(description="Pull request ID")
    number: int = Field(description="Pull request number")
    state: Literal["open", "closed"] = Field(description="PR state")
    title: str = Field(description="PR title")
    body: str | None = Field(default=None, description="PR description body")
    html_url: HttpUrl = Field(description="PR URL")
    diff_url: HttpUrl = Field(description="Diff URL")
    patch_url: HttpUrl = Field(description="Patch URL")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    closed_at: datetime | None = Field(default=None, description="Close timestamp")
    merged_at: datetime | None = Field(default=None, description="Merge timestamp")
    merge_commit_sha: str | None = Field(default=None, description="Merge commit SHA")
    user: GitHubUser = Field(description="PR author")
    head: GitHubRef = Field(description="Head branch (source)")
    base: GitHubRef = Field(description="Base branch (target)")
    merged: bool = Field(description="Whether PR is merged")
    mergeable: bool | None = Field(default=None, description="Whether PR is mergeable")
    draft: bool = Field(default=False, description="Whether PR is a draft")
    additions: int = Field(ge=0, description="Number of lines added")
    deletions: int = Field(ge=0, description="Number of lines deleted")
    changed_files: int = Field(ge=0, description="Number of files changed")


class PullRequestWebhookPayload(BaseModel):
    """GitHub pull request webhook payload.

    This is the complete payload sent by GitHub when a pull request event occurs.
    Supports actions: opened, synchronize, closed, reopened, edited, etc.

    Example:
        ```python
        payload = PullRequestWebhookPayload.model_validate(request_json)
        if payload.action == "opened":
            pr_number = payload.pull_request.number
            pr_title = payload.pull_request.title
        ```
    """

    action: Literal[
        "opened",
        "closed",
        "reopened",
        "synchronize",
        "edited",
        "assigned",
        "unassigned",
        "labeled",
        "unlabeled",
        "review_requested",
        "review_request_removed",
        "ready_for_review",
        "converted_to_draft",
    ] = Field(description="Action that triggered the webhook")

    number: int = Field(description="Pull request number")
    pull_request: PullRequest = Field(description="Pull request data")
    repository: GitHubRepository = Field(description="Repository data")
    sender: GitHubUser = Field(description="User who triggered the event")

    @property
    def is_actionable(self) -> bool:
        """Check if this webhook event requires analysis.

        We only analyze PRs when they are opened or updated (synchronized).
        Other actions like labels, assignments, etc. are ignored.

        Returns:
            bool: True if we should analyze this PR.
        """
        return self.action in ("opened", "synchronize")

    @property
    def is_merged(self) -> bool:
        """Check if this PR was merged (vs. closed without merging).

        Returns:
            bool: True if PR was merged.
        """
        return self.action == "closed" and self.pull_request.merged

    @property
    def pr_url(self) -> str:
        """Get the pull request URL as a string.

        Returns:
            str: GitHub PR URL.
        """
        return str(self.pull_request.html_url)

    @property
    def diff_url(self) -> str:
        """Get the diff URL for this PR.

        Returns:
            str: GitHub diff URL.
        """
        return str(self.pull_request.diff_url)

    @property
    def repo_full_name(self) -> str:
        """Get the full repository name (owner/repo).

        Returns:
            str: Full repository name.
        """
        return self.repository.full_name


class Commit(BaseModel):
    """Git commit information."""

    id: str = Field(description="Commit SHA", min_length=40, max_length=40)
    message: str = Field(description="Commit message")
    timestamp: datetime = Field(description="Commit timestamp")
    url: HttpUrl = Field(description="Commit URL")
    author: dict = Field(description="Commit author info")
    added: list[str] = Field(default_factory=list, description="Added files")
    removed: list[str] = Field(default_factory=list, description="Removed files")
    modified: list[str] = Field(default_factory=list, description="Modified files")


class PushWebhookPayload(BaseModel):
    """GitHub push webhook payload.

    This is the payload sent by GitHub when commits are pushed to a branch.

    Example:
        ```python
        payload = PushWebhookPayload.model_validate(request_json)
        branch = payload.ref.split('/')[-1]  # Extract branch name
        commits = payload.commits
        ```
    """

    ref: str = Field(description="Full git ref (e.g., refs/heads/main)")
    before: str = Field(description="SHA before push", min_length=40, max_length=40)
    after: str = Field(description="SHA after push", min_length=40, max_length=40)
    repository: GitHubRepository = Field(description="Repository data")
    pusher: dict = Field(description="User who pushed the commits")
    sender: GitHubUser = Field(description="User who triggered the event")
    commits: list[Commit] = Field(description="List of commits in this push")
    head_commit: Commit | None = Field(default=None, description="Most recent commit")
    compare: HttpUrl = Field(description="URL to compare changes")

    @property
    def branch_name(self) -> str:
        """Extract branch name from ref.

        Returns:
            str: Branch name (e.g., "main" from "refs/heads/main")
        """
        return self.ref.split("/")[-1]

    @property
    def is_branch_push(self) -> bool:
        """Check if this is a branch push (not a tag).

        Returns:
            bool: True if pushing to a branch.
        """
        return self.ref.startswith("refs/heads/")

    @property
    def repo_full_name(self) -> str:
        """Get the full repository name (owner/repo).

        Returns:
            str: Full repository name.
        """
        return self.repository.full_name

    @property
    def commit_count(self) -> int:
        """Get number of commits in this push.

        Returns:
            int: Number of commits.
        """
        return len(self.commits)


class WebhookDeliveryInfo(BaseModel):
    """Information about webhook delivery for logging/debugging.

    Not part of the webhook payload itself, but useful for tracking
    webhook processing internally.
    """

    delivery_id: str = Field(description="GitHub webhook delivery ID (from headers)")
    event_type: str = Field(description="GitHub event type (from headers)")
    signature: str = Field(description="GitHub signature (from headers)")
    received_at: datetime = Field(
        default_factory=datetime.utcnow, description="When webhook was received"
    )
    payload_size: int = Field(ge=0, description="Payload size in bytes")
