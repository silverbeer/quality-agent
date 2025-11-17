"""Pydantic models for metrics and DORA data.

This module defines data models for metrics API responses and DORA metrics snapshots.
Used for exposing metrics data via API endpoints (future enhancement).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PRMetrics(BaseModel):
    """Pull request metrics summary.

    Tracks PR activity and review times for a repository.
    """

    model_config = ConfigDict(frozen=True)

    repository: str = Field(description="Repository full name (e.g., 'owner/repo')")
    pr_opened_total: int = Field(ge=0, description="Total PRs opened")
    pr_closed_total: int = Field(ge=0, description="Total PRs closed")
    pr_merged_total: int = Field(ge=0, description="Total PRs merged")
    avg_review_time_hours: float | None = Field(
        default=None, description="Average review time in hours (creation to merge)"
    )
    p50_review_time_hours: float | None = Field(
        default=None, description="Median (p50) review time in hours"
    )
    p95_review_time_hours: float | None = Field(
        default=None, description="95th percentile review time in hours"
    )


class DeploymentMetrics(BaseModel):
    """Deployment metrics summary.

    Tracks deployment frequency and success rate.
    """

    model_config = ConfigDict(frozen=True)

    repository: str = Field(description="Repository full name")
    environment: Literal["production", "staging", "development"] = Field(
        description="Deployment environment"
    )
    total_deployments: int = Field(ge=0, description="Total number of deployments")
    successful_deployments: int = Field(
        ge=0, description="Number of successful deployments"
    )
    failed_deployments: int = Field(ge=0, description="Number of failed deployments")
    success_rate: float = Field(
        ge=0.0, le=1.0, description="Deployment success rate (0.0 to 1.0)"
    )
    deployments_per_day: float | None = Field(
        default=None, description="Average deployments per day"
    )


class DORAMetricsSnapshot(BaseModel):
    """Snapshot of DORA metrics at a point in time.

    Represents the four key DORA metrics:
    - Deployment Frequency: How often deployments occur
    - Lead Time for Changes: Time from PR creation to merge (proxy)
    - Change Failure Rate: Percentage of deployments that fail
    - Time to Restore Service: Time to recover from incidents
    """

    model_config = ConfigDict(frozen=True)

    repository: str = Field(description="Repository full name")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Snapshot timestamp (UTC)"
    )

    # Deployment Frequency
    deployment_frequency_per_day: float | None = Field(
        default=None, description="Average deployments per day (last 30 days)"
    )

    # Lead Time for Changes (PR review time as proxy)
    lead_time_p50_hours: float | None = Field(
        default=None,
        description="Median (p50) lead time in hours (PR creation to merge)",
    )
    lead_time_p95_hours: float | None = Field(
        default=None, description="95th percentile lead time in hours"
    )

    # Change Failure Rate
    change_failure_rate: float | None = Field(
        default=None,
        description="Percentage of deployments that fail (0.0 to 1.0)",
    )

    # Time to Restore Service
    mttr_p50_hours: float | None = Field(
        default=None,
        description="Median (p50) time to restore service in hours (future)",
    )
    mttr_p95_hours: float | None = Field(
        default=None, description="95th percentile time to restore in hours (future)"
    )


class MetricsHealth(BaseModel):
    """Health status of the metrics system.

    Used for monitoring and debugging metrics collection.
    """

    model_config = ConfigDict(frozen=True)

    metrics_enabled: bool = Field(description="Whether metrics collection is enabled")
    metrics_endpoint_available: bool = Field(
        description="Whether /metrics endpoint is accessible"
    )
    prometheus_format_valid: bool = Field(
        description="Whether metrics are in valid Prometheus format"
    )
    total_metrics_collected: int = Field(
        ge=0, description="Total number of metrics being tracked"
    )
    last_metric_recorded_at: datetime | None = Field(
        default=None, description="Timestamp of last metric recorded"
    )
