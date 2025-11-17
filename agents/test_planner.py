"""TestPlannerAgent - Creates intelligent test execution plans.

This agent is responsible for:
1. Analyzing TestCoverageGap objects from TestCoverageAgent
2. Prioritizing test recommendations based on risk and impact
3. Creating specific test recommendations with clear reasoning
4. Estimating test execution times
5. Identifying critical paths and remaining risk areas
6. Producing a comprehensive TestExecutionPlan
"""

from typing import ClassVar

from crewai import LLM, Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from models.analysis import TestCoverageGap, TestExecutionPlan


class TestPrioritizerTool(BaseTool):
    """Tool for prioritizing test recommendations based on risk and impact.

    Determines which tests should be run first based on:
    - Risk level of coverage gaps
    - Business criticality
    - Test type (security > integration > unit)
    - Impact on critical paths
    """

    name: str = "test_prioritizer"
    description: str = (
        "Prioritizes tests based on risk level, business criticality, and impact. "
        "Returns priority levels: critical, high, medium, low."
    )

    def _run(
        self,
        gap_risk_level: str,
        test_type: str,
        file_path: str,
        functions_count: int,
    ) -> dict:
        """Determine priority for a test.

        Args:
            gap_risk_level: Risk level of the coverage gap (low/medium/high/critical)
            test_type: Type of test (unit/integration/security/e2e)
            file_path: Path to the file being tested
            functions_count: Number of functions being tested

        Returns:
            dict: Priority assessment
        """
        priority_score = 0

        # Base priority from gap risk level
        risk_scores = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25,
        }
        priority_score += risk_scores.get(gap_risk_level, 25)

        # Test type importance
        test_type_scores = {
            "security": 30,
            "integration": 20,
            "e2e": 15,
            "unit": 10,
            "performance": 5,
        }
        priority_score += test_type_scores.get(test_type, 10)

        # Critical file paths
        path_lower = file_path.lower()
        critical_keywords = ["auth", "login", "password", "payment", "security", "admin"]
        if any(keyword in path_lower for keyword in critical_keywords):
            priority_score += 20

        # More functions = potentially more complex
        if functions_count > 5:
            priority_score += 10
        elif functions_count > 10:
            priority_score += 15

        # Convert score to priority level
        if priority_score >= 120:
            priority = "critical"
        elif priority_score >= 85:
            priority = "high"
        elif priority_score >= 55:
            priority = "medium"
        else:
            priority = "low"

        return {
            "priority": priority,
            "priority_score": priority_score,
        }


class TestEstimatorTool(BaseTool):
    """Tool for estimating test execution duration.

    Provides rough estimates based on test type and complexity.
    """

    name: str = "test_estimator"
    description: str = (
        "Estimates test execution duration in seconds based on test type, "
        "complexity, and number of test cases."
    )

    # Base durations in seconds
    BASE_DURATIONS: ClassVar[dict] = {
        "unit": 2,
        "integration": 10,
        "e2e": 30,
        "security": 15,
        "performance": 60,
    }

    def _run(self, test_type: str, test_count: int = 1, is_complex: bool = False) -> dict:
        """Estimate test duration.

        Args:
            test_type: Type of test
            test_count: Number of test cases
            is_complex: Whether tests are complex

        Returns:
            dict: Duration estimate
        """
        base_duration = self.BASE_DURATIONS.get(test_type, 5)

        # Multiply by number of tests
        total_duration = base_duration * test_count

        # Complex tests take longer
        if is_complex:
            total_duration = int(total_duration * 1.5)

        # Add setup/teardown overhead
        overhead = 5 if test_type in ("integration", "e2e") else 1
        total_duration += overhead

        return {
            "estimated_duration_seconds": total_duration,
            "base_duration": base_duration,
            "test_count": test_count,
        }


class TestRecommenderTool(BaseTool):
    """Tool for generating specific test recommendations.

    Creates detailed test recommendations with file paths, test names,
    and clear reasoning.
    """

    name: str = "test_recommender"
    description: str = (
        "Generates specific test recommendations with test file paths, test names, "
        "and clear explanations of why each test is needed."
    )

    def _run(
        self,
        file_path: str,
        functions_without_tests: list[str],
        test_type: str,
        scenarios: list[str],
        existing_test_files: list[str],
    ) -> dict:
        """Generate test recommendations.

        Args:
            file_path: Source file path
            functions_without_tests: Functions needing tests
            test_type: Type of test to recommend
            scenarios: Missing test scenarios
            existing_test_files: Existing test files (if any)

        Returns:
            dict: Test recommendations
        """
        recommendations = []

        # Determine test file path
        if existing_test_files:
            test_file = existing_test_files[0]  # Use existing test file
        else:
            # Generate test file path based on source file
            test_file = self._generate_test_path(file_path)

        # Create recommendations for each function
        for func in functions_without_tests:
            test_name = f"test_{func}"

            # Create recommendation
            rec = {
                "test_file": test_file,
                "test_name": test_name,
                "test_type": test_type,
                "function_under_test": func,
            }
            recommendations.append(rec)

        # Add scenario-based recommendations
        for scenario in scenarios[:3]:  # Limit to top 3 scenarios
            test_name = f"test_{scenario.lower().replace(' ', '_').replace('/', '_')}"
            rec = {
                "test_file": test_file,
                "test_name": test_name,
                "test_type": test_type,
                "scenario": scenario,
            }
            recommendations.append(rec)

        return {
            "recommendations": recommendations,
            "test_file": test_file,
            "total_recommendations": len(recommendations),
        }

    def _generate_test_path(self, source_path: str) -> str:
        """Generate test file path from source file path.

        Args:
            source_path: Source file path

        Returns:
            str: Test file path
        """
        # Simple heuristic: replace source dir with test dir and add test_ prefix
        if source_path.startswith("app/"):
            # app/services/user.py -> tests/unit/services/test_user.py
            parts = source_path[4:].split("/")  # Remove "app/"
            filename = parts[-1]
            dirs = parts[:-1]

            # Determine if it's a test file name
            if filename.endswith(".py"):
                test_filename = f"test_{filename}"
            else:
                test_filename = f"test_{filename}.py"

            return f"tests/unit/{'/'.join(dirs)}/{test_filename}"

        if source_path.startswith("src/"):
            # src/components/Button.tsx -> tests/unit/components/Button.test.tsx
            parts = source_path[4:].split("/")
            filename = parts[-1]
            dirs = parts[:-1]

            base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "js")
            test_filename = f"{base}.test.{ext}"

            return f"tests/unit/{'/'.join(dirs)}/{test_filename}"

        # Generic fallback
        return f"tests/test_{source_path.replace('/', '_')}"


class CriticalPathIdentifier(BaseTool):
    """Tool for identifying critical code paths that need testing.

    Analyzes coverage gaps to determine which code paths are most critical
    for system functionality and reliability.
    """

    name: str = "critical_path_identifier"
    description: str = (
        "Identifies critical code paths based on coverage gaps, helping prioritize "
        "which areas of the codebase are most important for testing."
    )

    CRITICAL_PATTERNS: ClassVar[list] = [
        "authentication",
        "authorization",
        "payment",
        "transaction",
        "security",
        "data modification",
        "user management",
        "api endpoints",
    ]

    def _run(
        self,
        coverage_gaps: list[dict],  # Simplified dict representation
    ) -> dict:
        """Identify critical paths from coverage gaps.

        Args:
            coverage_gaps: List of coverage gap information

        Returns:
            dict: Critical path analysis
        """
        critical_paths = []
        risk_areas = []

        for gap in coverage_gaps:
            file_path = gap.get("file_path", "")
            risk_level = gap.get("risk_level", "low")
            functions = gap.get("functions_without_tests", [])

            path_lower = file_path.lower()
            func_names_lower = " ".join(functions).lower()

            # Check for critical patterns
            for pattern in self.CRITICAL_PATTERNS:
                if pattern in path_lower or pattern in func_names_lower:
                    critical_paths.append(f"{pattern.title()} ({file_path})")

            # High/critical risk areas are remaining risks
            if risk_level in ("high", "critical"):
                risk_areas.append(f"{file_path} - {risk_level} risk")

        return {
            "critical_paths": list(set(critical_paths)),
            "risk_areas_remaining": list(set(risk_areas)),
            "total_critical_paths": len(set(critical_paths)),
        }


def create_test_planner_agent(llm: LLM | None = None) -> Agent:
    """Create and configure the TestPlannerAgent.

    Args:
        llm: Optional LLM configuration (if not provided, uses default Claude)

    Returns:
        Agent: Configured CrewAI agent
    """
    # Initialize tools
    prioritizer = TestPrioritizerTool()
    estimator = TestEstimatorTool()
    recommender = TestRecommenderTool()
    path_identifier = CriticalPathIdentifier()

    # Create agent
    agent = Agent(
        role="Test Planning Strategist",
        goal=(
            "Create intelligent, prioritized test execution plans that maximize code quality "
            "and risk mitigation. Recommend specific tests to run, in priority order, with "
            "clear reasoning for why each test matters."
        ),
        backstory=(
            "You are a test strategy expert who excels at creating actionable test plans. "
            "You understand that testing resources are finite, so you prioritize ruthlessly "
            "based on risk, business impact, and code criticality. Your test plans are "
            "specific, practical, and focused on the tests that matter most. You provide "
            "clear reasoning so developers understand not just what to test, but why."
        ),
        tools=[prioritizer, estimator, recommender, path_identifier],
        llm=llm,  # Use provided LLM or None to use default from environment
        verbose=True,
        allow_delegation=False,
    )

    return agent


def create_test_planning_task(
    agent: Agent,
    coverage_gaps: list[TestCoverageGap],
    code_changes: list | None = None,
) -> Task:
    """Create a task for the TestPlannerAgent.

    Args:
        agent: The TestPlannerAgent
        coverage_gaps: Coverage gaps from TestCoverageAgent
        code_changes: Optional code changes for additional context

    Returns:
        Task: Configured CrewAI task
    """
    gaps_summary = "\n".join(
        [
            f"- {gap.file_path}: {len(gap.functions_without_tests)} functions, "
            f"{gap.risk_level} risk, scenarios: {', '.join(gap.scenarios_missing[:2])}"
            for gap in coverage_gaps
        ]
    )

    task = Task(
        description=f"""
Create a comprehensive test execution plan based on the following coverage gaps.

Coverage Gaps:
{gaps_summary}

Instructions:
1. For each coverage gap:
   - Use test_recommender to generate specific test recommendations with:
     * test_file path
     * test_name (specific test function/method name)
     * test_type (unit, integration, security, e2e)
   - Use test_prioritizer to determine priority (critical/high/medium/low) based on:
     * Gap risk level
     * Test type
     * File path criticality
     * Number of functions affected
   - Use test_estimator to estimate test duration
   - Create TestRecommendation objects with:
     * test_file
     * test_name
     * test_type
     * priority
     * reason (clear explanation: "Tests {function} which handles {critical_operation} - {risk_reason}")
     * estimated_duration
     * addresses_gap (reference to gap)

2. Use critical_path_identifier to identify:
   - Critical code paths covered by this plan
   - Risk areas that remain after these tests

3. Create a TestExecutionPlan with:
   - recommendations (sorted by priority: critical first, then high, medium, low)
   - estimated_total_duration (sum of all test durations)
   - parallel_execution_possible (true for independent unit tests)
   - summary (concise overview of the plan)
   - coverage_gaps_addressed (count)
   - new_tests_needed (count of tests that don't exist yet)
   - critical_paths_covered (from critical_path_identifier)
   - risk_areas_remaining (from critical_path_identifier)

Prioritize ruthlessly - focus on high-impact tests that cover critical gaps.
Be specific and actionable - developers should know exactly which tests to run/write.

Output: Return a complete TestExecutionPlan with prioritized recommendations.
""",
        agent=agent,
        expected_output=(
            "A complete TestExecutionPlan with prioritized test recommendations, duration estimates, "
            "critical path coverage, and a clear summary of what to test and why."
        ),
    )

    return task


class TestPlanningInput(BaseModel):
    """Input model for test planning."""

    coverage_gaps: list[TestCoverageGap] = Field(description="Coverage gaps to address")


class TestPlanningOutput(BaseModel):
    """Output model for test planning."""

    test_plan: TestExecutionPlan = Field(description="Complete test execution plan")
    total_recommendations: int = Field(description="Total test recommendations")
    critical_tests: int = Field(description="Number of critical priority tests")
    estimated_duration_minutes: float = Field(description="Estimated total duration in minutes")
