"""Analysis models for agent communication.

Pydantic models used for data exchange between CrewAI agents:
- CodeAnalyzerAgent outputs CodeChange models
- TestCoverageAgent outputs TestCoverageGap models
- TestPlannerAgent outputs TestExecutionPlan model
- Final output is AnalysisReport

These models provide type-safe, validated data structures for the agent pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChangeType(str, Enum):
    """Type of code change operation."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class FileType(str, Enum):
    """Type of file in the codebase."""

    SOURCE = "source"  # Production code
    TEST = "test"  # Test files
    CONFIG = "config"  # Configuration files
    DOCUMENTATION = "documentation"  # Docs/README
    OTHER = "other"  # Other files


class CodeChange(BaseModel):
    """Represents a code change identified by CodeAnalyzerAgent.

    Example:
        ```python
        change = CodeChange(
            file_path="app/services/user.py",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.SOURCE,
            functions_changed=["create_user", "update_user"],
            lines_added=45,
            lines_deleted=12,
            complexity_impact="medium"
        )
        ```
    """

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    file_path: str = Field(description="Path to the changed file relative to repo root")
    change_type: ChangeType = Field(description="Type of change operation")
    file_type: FileType = Field(description="Classification of file type")

    # Function/class level changes
    functions_changed: list[str] = Field(
        default_factory=list,
        description="List of function/method names that were changed",
    )
    classes_changed: list[str] = Field(
        default_factory=list, description="List of class names that were changed"
    )

    # Quantitative metrics
    lines_added: int = Field(ge=0, description="Number of lines added")
    lines_deleted: int = Field(ge=0, description="Number of lines deleted")

    # Impact assessment
    complexity_impact: Literal["low", "medium", "high"] = Field(
        description="Estimated complexity/risk impact of this change"
    )

    # Optional: dependencies and relationships
    imports_added: list[str] = Field(
        default_factory=list, description="New imports/dependencies added"
    )
    related_files: list[str] = Field(
        default_factory=list,
        description="Other files that may be affected by this change",
    )

    # Code snippets for context (optional, for LLM analysis)
    key_changes: str | None = Field(
        default=None,
        description="Brief description or snippet of key changes",
        max_length=500,
    )

    @property
    def total_lines_changed(self) -> int:
        """Calculate total lines changed (added + deleted).

        Returns:
            int: Total number of lines changed.
        """
        return self.lines_added + self.lines_deleted

    @property
    def is_test_file(self) -> bool:
        """Check if this is a test file.

        Returns:
            bool: True if this is a test file.
        """
        return self.file_type == FileType.TEST

    @property
    def is_source_file(self) -> bool:
        """Check if this is a source code file.

        Returns:
            bool: True if this is source code.
        """
        return self.file_type == FileType.SOURCE


class TestCoverageGap(BaseModel):
    """Represents a test coverage gap identified by TestCoverageAgent.

    Example:
        ```python
        gap = TestCoverageGap(
            file_path="app/services/user.py",
            functions_without_tests=["update_user"],
            risk_level="high",
            reason="Critical user data modification without test coverage"
        )
        ```
    """

    model_config = ConfigDict(frozen=True)

    # Reference to source file
    file_path: str = Field(description="Path to source file with coverage gap")
    related_change: str | None = Field(
        default=None,
        description="Reference to the CodeChange that revealed this gap",
    )

    # Coverage gap details
    functions_without_tests: list[str] = Field(
        description="Functions/methods lacking test coverage"
    )
    classes_without_tests: list[str] = Field(
        default_factory=list, description="Classes lacking test coverage"
    )
    scenarios_missing: list[str] = Field(
        default_factory=list,
        description="Test scenarios that should exist but don't (e.g., 'error handling', 'edge cases')",
    )

    # Existing test info
    existing_test_files: list[str] = Field(
        default_factory=list,
        description="Test files that already exist for this module",
    )
    partially_covered: bool = Field(
        default=False,
        description="True if some tests exist but coverage is incomplete",
    )

    # Risk assessment
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        description="Risk level of this coverage gap"
    )
    reason: str = Field(
        description="Explanation of why this is a coverage gap and its risk",
        max_length=500,
    )

    # Recommendations
    recommended_test_types: list[str] = Field(
        default_factory=list,
        description="Types of tests recommended (e.g., 'unit', 'integration', 'edge-case')",
    )

    @property
    def total_untested_items(self) -> int:
        """Count total untested functions and classes.

        Returns:
            int: Total number of untested items.
        """
        return len(self.functions_without_tests) + len(self.classes_without_tests)

    @property
    def is_critical(self) -> bool:
        """Check if this gap is critical priority.

        Returns:
            bool: True if risk level is critical.
        """
        return self.risk_level == "critical"

    @property
    def is_high_risk(self) -> bool:
        """Check if this gap is high or critical risk.

        Returns:
            bool: True if risk level is high or critical.
        """
        return self.risk_level in ("high", "critical")


class TestRecommendation(BaseModel):
    """A specific test recommendation with priority and details."""

    model_config = ConfigDict(frozen=True)

    test_file: str = Field(description="Test file path where test should be added/run")
    test_name: str = Field(description="Specific test function/method name")
    test_type: Literal["unit", "integration", "e2e", "security", "performance"] = Field(
        description="Type of test"
    )
    priority: Literal["critical", "high", "medium", "low"] = Field(
        description="Priority for running this test"
    )
    reason: str = Field(
        description="Why this test is important based on code changes",
        max_length=500,
    )
    estimated_duration: int | None = Field(
        default=None, description="Estimated test duration in seconds", ge=0
    )

    # Coverage gap reference
    addresses_gap: str | None = Field(
        default=None,
        description="Reference to TestCoverageGap this test addresses",
    )

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical priority test.

        Returns:
            bool: True if priority is critical.
        """
        return self.priority == "critical"

    @property
    def is_high_priority(self) -> bool:
        """Check if this is high or critical priority.

        Returns:
            bool: True if priority is high or critical.
        """
        return self.priority in ("critical", "high")


class TestExecutionPlan(BaseModel):
    """Complete test execution plan from TestPlannerAgent.

    This is the final output that tells us which tests to run and in what order.

    Example:
        ```python
        plan = TestExecutionPlan(
            recommendations=[rec1, rec2, rec3],
            estimated_total_duration=180,
            summary="Run 15 high-priority tests covering user service changes"
        )
        ```
    """

    model_config = ConfigDict(frozen=True)

    # Test recommendations in priority order
    recommendations: list[TestRecommendation] = Field(
        description="Ordered list of test recommendations (highest priority first)"
    )

    # Execution metadata
    estimated_total_duration: int | None = Field(
        default=None, description="Total estimated duration in seconds", ge=0
    )
    parallel_execution_possible: bool = Field(
        default=False,
        description="Whether tests can be run in parallel",
    )

    # Summary and insights
    summary: str = Field(
        description="Brief summary of the test plan",
        max_length=500,
    )
    coverage_gaps_addressed: int = Field(
        ge=0,
        description="Number of coverage gaps this plan addresses",
    )
    new_tests_needed: int = Field(
        ge=0,
        description="Number of new tests that need to be written",
    )

    # Risk mitigation
    critical_paths_covered: list[str] = Field(
        default_factory=list,
        description="Critical code paths that will be tested",
    )
    risk_areas_remaining: list[str] = Field(
        default_factory=list,
        description="Risk areas that still lack coverage after this plan",
    )

    @property
    def total_tests(self) -> int:
        """Get total number of test recommendations.

        Returns:
            int: Total test count.
        """
        return len(self.recommendations)

    @property
    def critical_tests(self) -> list[TestRecommendation]:
        """Get only critical priority tests.

        Returns:
            list[TestRecommendation]: Critical tests.
        """
        return [rec for rec in self.recommendations if rec.is_critical]

    @property
    def high_priority_tests(self) -> list[TestRecommendation]:
        """Get high and critical priority tests.

        Returns:
            list[TestRecommendation]: High and critical tests.
        """
        return [rec for rec in self.recommendations if rec.is_high_priority]

    @property
    def has_critical_tests(self) -> bool:
        """Check if plan includes any critical tests.

        Returns:
            bool: True if critical tests exist.
        """
        return len(self.critical_tests) > 0


class AnalysisReport(BaseModel):
    """Final analysis report combining all agent outputs.

    This is the complete result from the CrewAI pipeline that gets
    returned to the webhook caller and/or stored for future reference.

    Example:
        ```python
        report = AnalysisReport(
            pr_number=123,
            repository="owner/repo",
            analysis_timestamp=datetime.utcnow(),
            code_changes=[change1, change2],
            coverage_gaps=[gap1, gap2],
            test_plan=plan,
            status="completed"
        )
        ```
    """

    model_config = ConfigDict(frozen=False)  # Allow mutation for status updates

    # PR context
    pr_number: int = Field(description="Pull request number")
    repository: str = Field(description="Repository full name (owner/repo)")
    pr_url: str = Field(description="GitHub PR URL")
    commit_sha: str = Field(description="Commit SHA that was analyzed")

    # Timestamps
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When analysis was performed",
    )
    duration_seconds: float | None = Field(
        default=None, description="How long analysis took", ge=0
    )

    # Agent outputs
    code_changes: list[CodeChange] = Field(
        description="All code changes identified by CodeAnalyzerAgent"
    )
    coverage_gaps: list[TestCoverageGap] = Field(
        description="Coverage gaps identified by TestCoverageAgent"
    )
    test_plan: TestExecutionPlan = Field(
        description="Test execution plan from TestPlannerAgent"
    )

    # Status and errors
    status: Literal["completed", "partial", "failed"] = Field(
        default="completed",
        description="Analysis completion status",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Any errors encountered during analysis",
    )

    # High-level metrics
    total_files_changed: int = Field(ge=0, description="Total files changed in PR")
    total_lines_changed: int = Field(ge=0, description="Total lines changed (add + del)")
    risk_score: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None,
        description="Overall risk score for this PR",
    )

    @property
    def has_critical_gaps(self) -> bool:
        """Check if any critical coverage gaps exist.

        Returns:
            bool: True if critical gaps found.
        """
        return any(gap.is_critical for gap in self.coverage_gaps)

    @property
    def has_high_risk_gaps(self) -> bool:
        """Check if any high or critical gaps exist.

        Returns:
            bool: True if high/critical gaps found.
        """
        return any(gap.is_high_risk for gap in self.coverage_gaps)

    @property
    def is_successful(self) -> bool:
        """Check if analysis completed successfully.

        Returns:
            bool: True if status is completed.
        """
        return self.status == "completed"

    @property
    def source_files_changed(self) -> list[CodeChange]:
        """Get only source code changes (exclude tests, docs, config).

        Returns:
            list[CodeChange]: Source code changes.
        """
        return [change for change in self.code_changes if change.is_source_file]

    @property
    def test_files_changed(self) -> list[CodeChange]:
        """Get only test file changes.

        Returns:
            list[CodeChange]: Test file changes.
        """
        return [change for change in self.code_changes if change.is_test_file]

    def to_summary_dict(self) -> dict:
        """Create a concise summary dict for API responses or logging.

        Returns:
            dict: Summary of key metrics and results.
        """
        return {
            "pr_number": self.pr_number,
            "repository": self.repository,
            "status": self.status,
            "total_changes": len(self.code_changes),
            "source_files_changed": len(self.source_files_changed),
            "test_files_changed": len(self.test_files_changed),
            "coverage_gaps": len(self.coverage_gaps),
            "critical_gaps": len([g for g in self.coverage_gaps if g.is_critical]),
            "total_test_recommendations": self.test_plan.total_tests,
            "critical_tests": len(self.test_plan.critical_tests),
            "risk_score": self.risk_score,
            "duration_seconds": self.duration_seconds,
        }
