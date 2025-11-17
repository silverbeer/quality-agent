"""DORA metrics collection using Prometheus.

This module defines DORA (DevOps Research and Assessment) metrics:
- Deployment Frequency: How often deployments to production occur
- Lead Time for Changes: Time from PR creation to merge (proxy for commit to deploy)
- Change Failure Rate: Percentage of deployments that fail (future)
- Time to Restore Service: Time to recover from incidents (future)

Metrics are exposed via the /metrics endpoint and scraped by Prometheus.

Reference: https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance
"""

from prometheus_client import Counter, Histogram

# ==============================================================================
# Pull Request Metrics
# ==============================================================================

pr_total = Counter(
    "pr_total",
    "Total number of pull requests",
    ["repository", "action", "merged"],
)
"""
Total number of pull request events.

Labels:
- repository: Repository full name (e.g., "org/repo")
- action: PR action (opened, closed, synchronize)
- merged: Whether PR was merged ("true" or "false")

Examples:
- pr_total{repository="org/repo",action="opened",merged="false"} 25
- pr_total{repository="org/repo",action="closed",merged="true"} 20
"""

pr_review_time_seconds = Histogram(
    "pr_review_time_seconds",
    "Time from PR creation to merge (lead time proxy)",
    ["repository"],
    buckets=[
        300,  # 5 minutes
        900,  # 15 minutes
        3600,  # 1 hour
        7200,  # 2 hours
        14400,  # 4 hours
        43200,  # 12 hours
        86400,  # 1 day
        172800,  # 2 days
        604800,  # 1 week
    ],
)
"""
Histogram of PR review time (creation to merge).

This is a proxy for "Lead Time for Changes" - the full metric would be
commit creation to production deployment, but we start with PR metrics
since deployment webhooks aren't configured yet.

Labels:
- repository: Repository full name

Buckets: 5min, 15min, 1h, 2h, 4h, 12h, 1d, 2d, 1w

Use in Grafana:
- Median (p50): histogram_quantile(0.50, rate(pr_review_time_seconds_bucket[5m]))
- 95th percentile: histogram_quantile(0.95, rate(pr_review_time_seconds_bucket[5m]))
"""

# ==============================================================================
# Deployment Metrics
# ==============================================================================

deployments_total = Counter(
    "deployments_total",
    "Total number of deployments",
    ["repository", "environment", "status"],
)
"""
Total number of deployment events.

Currently uses push-to-main as a deployment proxy. Will be enhanced when
deployment webhooks are configured.

Labels:
- repository: Repository full name
- environment: Deployment environment (production, staging, development)
- status: Deployment status (success, failure)

Examples:
- deployments_total{repository="org/repo",environment="production",status="success"} 47

Use in Grafana for Deployment Frequency:
- rate(deployments_total{environment="production",status="success"}[1d])
"""

# ==============================================================================
# Change Failure Rate Metrics (Future)
# ==============================================================================

# Note: Change Failure Rate is calculated from deployments_total:
# CFR = deployments_total{status="failure"} / deployments_total{status="*"}
#
# In Grafana:
# rate(deployments_total{status="failure"}[1d]) /
# rate(deployments_total[1d])

# ==============================================================================
# Time to Restore Service Metrics (Future)
# ==============================================================================

incident_recovery_time_seconds = Histogram(
    "incident_recovery_time_seconds",
    "Time to restore service after incident",
    ["repository", "incident_type"],
    buckets=[
        60,  # 1 minute
        300,  # 5 minutes
        900,  # 15 minutes
        3600,  # 1 hour
        7200,  # 2 hours
        21600,  # 6 hours
        86400,  # 1 day
    ],
)
"""
Histogram of incident recovery time.

Future enhancement - requires issue webhooks or deployment status webhooks
to track incidents and their resolution.

Labels:
- repository: Repository full name
- incident_type: Type of incident (deployment_failure, hotfix, rollback)

Buckets: 1min, 5min, 15min, 1h, 2h, 6h, 1d
"""

# ==============================================================================
# Helper Functions
# ==============================================================================


def record_pr_event(repository: str, action: str, merged: bool) -> None:
    """Record a pull request event.

    Args:
        repository: Repository full name (e.g., "owner/repo")
        action: PR action (opened, closed, synchronize)
        merged: Whether the PR was merged (True/False)
    """
    pr_total.labels(
        repository=repository, action=action, merged=str(merged).lower()
    ).inc()


def record_pr_review_time(repository: str, review_time_seconds: float) -> None:
    """Record PR review time (creation to merge).

    Args:
        repository: Repository full name
        review_time_seconds: Time in seconds from PR creation to merge
    """
    pr_review_time_seconds.labels(repository=repository).observe(review_time_seconds)


def record_deployment(
    repository: str, environment: str = "production", success: bool = True
) -> None:
    """Record a deployment event.

    Currently uses push-to-main as deployment proxy. Will be enhanced when
    deployment webhooks are configured.

    Args:
        repository: Repository full name
        environment: Deployment environment (default: production)
        success: Whether deployment succeeded (default: True)
    """
    status = "success" if success else "failure"
    deployments_total.labels(
        repository=repository, environment=environment, status=status
    ).inc()


def record_incident_recovery(
    repository: str, incident_type: str, recovery_time_seconds: float
) -> None:
    """Record incident recovery time.

    Future enhancement - requires incident tracking webhooks.

    Args:
        repository: Repository full name
        incident_type: Type of incident (deployment_failure, hotfix, rollback)
        recovery_time_seconds: Time to restore service in seconds
    """
    incident_recovery_time_seconds.labels(
        repository=repository, incident_type=incident_type
    ).observe(recovery_time_seconds)
