"""Quality Agent - Pydantic models package."""

from models.analysis import (
    AnalysisReport,
    ChangeType,
    CodeChange,
    FileType,
    TestCoverageGap,
    TestExecutionPlan,
    TestRecommendation,
)
from models.github import (
    Commit,
    GitHubRef,
    GitHubRepository,
    GitHubUser,
    PullRequest,
    PullRequestWebhookPayload,
    PushWebhookPayload,
    WebhookDeliveryInfo,
)
from models.metrics import (
    DeploymentMetrics,
    DORAMetricsSnapshot,
    MetricsHealth,
    PRMetrics,
)


__version__ = "0.1.0"

__all__ = [
    # GitHub models
    "Commit",
    "GitHubRef",
    "GitHubRepository",
    "GitHubUser",
    "PullRequest",
    "PullRequestWebhookPayload",
    "PushWebhookPayload",
    "WebhookDeliveryInfo",
    # Analysis models
    "AnalysisReport",
    "ChangeType",
    "CodeChange",
    "FileType",
    "TestCoverageGap",
    "TestExecutionPlan",
    "TestRecommendation",
    # Metrics models
    "DeploymentMetrics",
    "DORAMetricsSnapshot",
    "MetricsHealth",
    "PRMetrics",
]
