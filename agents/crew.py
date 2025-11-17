"""CrewAI orchestration for the quality analysis pipeline.

This module coordinates the three-agent pipeline:
1. CodeAnalyzerAgent: Analyzes git diffs and identifies code changes
2. TestCoverageAgent: Identifies test coverage gaps
3. TestPlannerAgent: Creates intelligent test execution plans

The crew executes these agents sequentially, passing data between them
to produce a comprehensive AnalysisReport.
"""

import time
from datetime import datetime

import structlog
from crewai import LLM, Crew, Process

from agents.code_analyzer import create_code_analysis_task, create_code_analyzer_agent
from agents.test_coverage import create_coverage_analysis_task, create_test_coverage_agent
from agents.test_planner import create_test_planner_agent, create_test_planning_task
from app.config import settings
from models.analysis import (
    AnalysisReport,
    ChangeType,
    CodeChange,
    FileType,
    TestCoverageGap,
    TestExecutionPlan,
    TestRecommendation,
)
from models.github import PullRequestWebhookPayload


logger = structlog.get_logger()


class QualityAnalysisCrew:
    """Orchestrates the quality analysis crew.

    This class manages the CrewAI agents and their execution pipeline,
    converting between agent outputs and Pydantic models.
    """

    def __init__(self, github_token: str | None = None):
        """Initialize the crew with agents.

        Args:
            github_token: Optional GitHub API token for fetching diffs
        """
        self.github_token = github_token

        # Create LLM configuration for Claude/Anthropic
        # This ensures all agents use Claude instead of defaulting to OpenAI
        self.llm = LLM(
            model=f"anthropic/{settings.crewai_model}",
            api_key=settings.anthropic_api_key,
            temperature=settings.crewai_temperature,
            max_tokens=settings.crewai_max_tokens,
        )

        # Create agents with Claude LLM
        self.code_analyzer = create_code_analyzer_agent(github_token, llm=self.llm)
        self.coverage_analyzer = create_test_coverage_agent(llm=self.llm)
        self.test_planner = create_test_planner_agent(llm=self.llm)

        logger.info(
            "quality_crew_initialized",
            agents=["CodeAnalyzer", "CoverageAnalyzer", "TestPlanner"],
            llm_model=settings.crewai_model,
            llm_provider="anthropic",
        )

    def analyze_pull_request(
        self, webhook_payload: PullRequestWebhookPayload
    ) -> AnalysisReport:
        """Run the complete analysis pipeline on a pull request.

        Args:
            webhook_payload: GitHub webhook payload with PR information

        Returns:
            AnalysisReport: Complete analysis results

        Raises:
            Exception: If analysis fails at any stage
        """
        start_time = time.time()
        pr_number = webhook_payload.number
        repo = webhook_payload.repo_full_name

        logger.info(
            "analysis_started",
            pr_number=pr_number,
            repository=repo,
            commit_sha=webhook_payload.pull_request.head.sha,
        )

        try:
            # Stage 1: Code Analysis
            logger.info("stage_1_starting", stage="code_analysis")
            code_changes = self._run_code_analysis(webhook_payload)
            logger.info(
                "stage_1_completed",
                stage="code_analysis",
                changes_found=len(code_changes),
            )

            # If no source code changes, return early with minimal report
            source_changes = [c for c in code_changes if c.is_source_file]
            if not source_changes:
                logger.info(
                    "no_source_changes",
                    pr_number=pr_number,
                    total_changes=len(code_changes),
                )
                return self._create_minimal_report(webhook_payload, code_changes, start_time)

            # Stage 2: Coverage Analysis
            logger.info("stage_2_starting", stage="coverage_analysis")
            coverage_gaps = self._run_coverage_analysis(code_changes)
            logger.info(
                "stage_2_completed",
                stage="coverage_analysis",
                gaps_found=len(coverage_gaps),
            )

            # If no coverage gaps, return report without test plan
            if not coverage_gaps:
                logger.info("no_coverage_gaps", pr_number=pr_number)
                return self._create_report_no_gaps(
                    webhook_payload, code_changes, start_time
                )

            # Stage 3: Test Planning
            logger.info("stage_3_starting", stage="test_planning")
            test_plan = self._run_test_planning(coverage_gaps, code_changes)
            logger.info(
                "stage_3_completed",
                stage="test_planning",
                recommendations=test_plan.total_tests,
            )

            # Create final report
            duration = time.time() - start_time
            report = self._create_full_report(
                webhook_payload,
                code_changes,
                coverage_gaps,
                test_plan,
                duration,
            )

            logger.info(
                "analysis_completed",
                pr_number=pr_number,
                duration_seconds=round(duration, 2),
                status=report.status,
            )

            return report

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "analysis_failed",
                pr_number=pr_number,
                error=str(e),
                duration_seconds=round(duration, 2),
            )

            # Return failed report
            return self._create_failed_report(webhook_payload, str(e), duration)

    def _run_code_analysis(
        self, webhook_payload: PullRequestWebhookPayload
    ) -> list[CodeChange]:
        """Run the code analysis stage.

        Args:
            webhook_payload: GitHub webhook payload

        Returns:
            list[CodeChange]: Identified code changes
        """
        task = create_code_analysis_task(
            self.code_analyzer, webhook_payload, self.github_token
        )

        crew = Crew(
            agents=[self.code_analyzer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # Parse result into CodeChange objects
        # CrewAI returns result as string, need to parse
        return self._parse_code_changes(result)

    def _run_coverage_analysis(self, code_changes: list[CodeChange]) -> list[TestCoverageGap]:
        """Run the coverage analysis stage.

        Args:
            code_changes: Code changes from previous stage

        Returns:
            list[TestCoverageGap]: Identified coverage gaps
        """
        task = create_coverage_analysis_task(self.coverage_analyzer, code_changes)

        crew = Crew(
            agents=[self.coverage_analyzer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # Parse result into TestCoverageGap objects
        return self._parse_coverage_gaps(result)

    def _run_test_planning(
        self,
        coverage_gaps: list[TestCoverageGap],
        code_changes: list[CodeChange],
    ) -> TestExecutionPlan:
        """Run the test planning stage.

        Args:
            coverage_gaps: Coverage gaps from previous stage
            code_changes: Code changes for context

        Returns:
            TestExecutionPlan: Test execution plan
        """
        task = create_test_planning_task(self.test_planner, coverage_gaps, code_changes)

        crew = Crew(
            agents=[self.test_planner],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # Parse result into TestExecutionPlan
        return self._parse_test_plan(result)

    def _parse_code_changes(self, result: str) -> list[CodeChange]:
        """Parse agent output into CodeChange models.

        Args:
            result: Raw agent output

        Returns:
            list[CodeChange]: Parsed code changes
        """
        # For now, create mock data - in production, would parse agent output
        # The agents should return structured JSON that we can parse
        logger.warning("using_mock_code_changes", reason="parsing not yet implemented")

        return [
            CodeChange(
                file_path="app/services/user.py",
                change_type=ChangeType.MODIFIED,
                file_type=FileType.SOURCE,
                functions_changed=["create_user", "update_user"],
                classes_changed=["UserService"],
                lines_added=45,
                lines_deleted=12,
                complexity_impact="medium",
                imports_added=["from datetime import datetime"],
                related_files=["app/models/user.py", "app/api/endpoints/users.py"],
                key_changes="Added timestamp tracking to user creation and updates",
            )
        ]

    def _parse_coverage_gaps(self, result: str) -> list[TestCoverageGap]:
        """Parse agent output into TestCoverageGap models.

        Args:
            result: Raw agent output

        Returns:
            list[TestCoverageGap]: Parsed coverage gaps
        """
        logger.warning("using_mock_coverage_gaps", reason="parsing not yet implemented")

        return [
            TestCoverageGap(
                file_path="app/services/user.py",
                functions_without_tests=["update_user"],
                classes_without_tests=[],
                scenarios_missing=[
                    "Error handling for invalid user data",
                    "Concurrent update conflicts",
                    "Timestamp validation",
                ],
                existing_test_files=["tests/unit/services/test_user.py"],
                partially_covered=True,
                risk_level="high",
                reason="User data modification without complete test coverage for new timestamp logic",
                recommended_test_types=["unit", "integration"],
            )
        ]

    def _parse_test_plan(self, result: str) -> TestExecutionPlan:
        """Parse agent output into TestExecutionPlan model.

        Args:
            result: Raw agent output

        Returns:
            TestExecutionPlan: Parsed test plan
        """
        logger.warning("using_mock_test_plan", reason="parsing not yet implemented")

        return TestExecutionPlan(
            recommendations=[
                TestRecommendation(
                    test_file="tests/unit/services/test_user.py",
                    test_name="test_update_user_with_timestamp",
                    test_type="unit",
                    priority="high",
                    reason="Tests update_user function which handles user data modification - high risk due to data integrity concerns",
                    estimated_duration=5,
                    addresses_gap="app/services/user.py",
                ),
                TestRecommendation(
                    test_file="tests/unit/services/test_user.py",
                    test_name="test_update_user_invalid_data",
                    test_type="unit",
                    priority="high",
                    reason="Tests error handling for invalid user data - critical for data validation",
                    estimated_duration=3,
                    addresses_gap="app/services/user.py",
                ),
            ],
            estimated_total_duration=8,
            parallel_execution_possible=True,
            summary="Run 2 high-priority unit tests covering user service timestamp changes",
            coverage_gaps_addressed=1,
            new_tests_needed=2,
            critical_paths_covered=["User Management (app/services/user.py)"],
            risk_areas_remaining=[],
        )

    def _create_full_report(
        self,
        webhook_payload: PullRequestWebhookPayload,
        code_changes: list[CodeChange],
        coverage_gaps: list[TestCoverageGap],
        test_plan: TestExecutionPlan,
        duration: float,
    ) -> AnalysisReport:
        """Create a complete analysis report.

        Args:
            webhook_payload: Original webhook payload
            code_changes: Identified code changes
            coverage_gaps: Identified coverage gaps
            test_plan: Test execution plan
            duration: Analysis duration in seconds

        Returns:
            AnalysisReport: Complete report
        """
        # Calculate metrics
        total_lines = sum(c.total_lines_changed for c in code_changes)

        # Determine overall risk score
        if any(g.risk_level == "critical" for g in coverage_gaps):
            risk_score = "critical"
        elif any(g.risk_level == "high" for g in coverage_gaps):
            risk_score = "high"
        elif any(g.risk_level == "medium" for g in coverage_gaps):
            risk_score = "medium"
        else:
            risk_score = "low"

        return AnalysisReport(
            pr_number=webhook_payload.number,
            repository=webhook_payload.repo_full_name,
            pr_url=webhook_payload.pr_url,
            commit_sha=webhook_payload.pull_request.head.sha,
            analysis_timestamp=datetime.utcnow(),
            duration_seconds=round(duration, 2),
            code_changes=code_changes,
            coverage_gaps=coverage_gaps,
            test_plan=test_plan,
            status="completed",
            errors=[],
            total_files_changed=len(code_changes),
            total_lines_changed=total_lines,
            risk_score=risk_score,
        )

    def _create_minimal_report(
        self,
        webhook_payload: PullRequestWebhookPayload,
        code_changes: list[CodeChange],
        start_time: float,
    ) -> AnalysisReport:
        """Create a minimal report when no source changes found.

        Args:
            webhook_payload: Original webhook payload
            code_changes: All code changes (non-source)
            start_time: Analysis start time

        Returns:
            AnalysisReport: Minimal report
        """
        duration = time.time() - start_time

        return AnalysisReport(
            pr_number=webhook_payload.number,
            repository=webhook_payload.repo_full_name,
            pr_url=webhook_payload.pr_url,
            commit_sha=webhook_payload.pull_request.head.sha,
            analysis_timestamp=datetime.utcnow(),
            duration_seconds=round(duration, 2),
            code_changes=code_changes,
            coverage_gaps=[],
            test_plan=TestExecutionPlan(
                recommendations=[],
                summary="No source code changes detected - no test recommendations",
                coverage_gaps_addressed=0,
                new_tests_needed=0,
            ),
            status="completed",
            total_files_changed=len(code_changes),
            total_lines_changed=sum(c.total_lines_changed for c in code_changes),
            risk_score="low",
        )

    def _create_report_no_gaps(
        self,
        webhook_payload: PullRequestWebhookPayload,
        code_changes: list[CodeChange],
        start_time: float,
    ) -> AnalysisReport:
        """Create a report when no coverage gaps found.

        Args:
            webhook_payload: Original webhook payload
            code_changes: Code changes
            start_time: Analysis start time

        Returns:
            AnalysisReport: Report with no gaps
        """
        duration = time.time() - start_time

        return AnalysisReport(
            pr_number=webhook_payload.number,
            repository=webhook_payload.repo_full_name,
            pr_url=webhook_payload.pr_url,
            commit_sha=webhook_payload.pull_request.head.sha,
            analysis_timestamp=datetime.utcnow(),
            duration_seconds=round(duration, 2),
            code_changes=code_changes,
            coverage_gaps=[],
            test_plan=TestExecutionPlan(
                recommendations=[],
                summary="All code changes have adequate test coverage",
                coverage_gaps_addressed=0,
                new_tests_needed=0,
            ),
            status="completed",
            total_files_changed=len(code_changes),
            total_lines_changed=sum(c.total_lines_changed for c in code_changes),
            risk_score="low",
        )

    def _create_failed_report(
        self,
        webhook_payload: PullRequestWebhookPayload,
        error_message: str,
        duration: float,
    ) -> AnalysisReport:
        """Create a failed analysis report.

        Args:
            webhook_payload: Original webhook payload
            error_message: Error message
            duration: Analysis duration

        Returns:
            AnalysisReport: Failed report
        """
        return AnalysisReport(
            pr_number=webhook_payload.number,
            repository=webhook_payload.repo_full_name,
            pr_url=webhook_payload.pr_url,
            commit_sha=webhook_payload.pull_request.head.sha,
            analysis_timestamp=datetime.utcnow(),
            duration_seconds=round(duration, 2),
            code_changes=[],
            coverage_gaps=[],
            test_plan=TestExecutionPlan(
                recommendations=[],
                summary="Analysis failed - see errors",
                coverage_gaps_addressed=0,
                new_tests_needed=0,
            ),
            status="failed",
            errors=[error_message],
            total_files_changed=0,
            total_lines_changed=0,
            risk_score=None,
        )


# Convenience function for easy import
def analyze_pull_request(
    webhook_payload: PullRequestWebhookPayload,
    github_token: str | None = None,
) -> AnalysisReport:
    """Analyze a pull request using the quality analysis crew.

    This is the main entry point for running the analysis pipeline.

    Args:
        webhook_payload: GitHub webhook payload
        github_token: Optional GitHub API token

    Returns:
        AnalysisReport: Complete analysis results

    Example:
        ```python
        from agents.crew import analyze_pull_request
        from models import PullRequestWebhookPayload

        payload = PullRequestWebhookPayload.model_validate(webhook_data)
        report = analyze_pull_request(payload, github_token="ghp_...")

        print(f"Found {len(report.coverage_gaps)} coverage gaps")
        print(f"Risk score: {report.risk_score}")
        ```
    """
    crew = QualityAnalysisCrew(github_token)
    return crew.analyze_pull_request(webhook_payload)
