"""TestCoverageAgent - Identifies test coverage gaps based on code changes.

This agent is responsible for:
1. Analyzing CodeChange objects from CodeAnalyzerAgent
2. Finding existing test files for changed source files
3. Identifying functions/classes without test coverage
4. Detecting missing test scenarios (edge cases, error handling, etc.)
5. Assessing risk levels for coverage gaps
6. Producing TestCoverageGap models for TestPlannerAgent
"""

from pathlib import Path
from typing import ClassVar

from crewai import LLM, Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from models.analysis import CodeChange, TestCoverageGap


class TestFileFinder(BaseTool):
    """Tool for finding test files related to source files.

    Searches for test files that correspond to changed source files using
    common naming conventions and directory structures.
    """

    name: str = "test_file_finder"
    description: str = (
        "Finds existing test files for a given source file. Looks for common "
        "test naming patterns like test_*, *_test.*, or files in test directories."
    )

    def _run(self, source_file: str, repo_path: str | None = None) -> dict:
        """Find test files for a given source file.

        Args:
            source_file: Path to source file
            repo_path: Optional path to repository root

        Returns:
            dict: Test file information
        """
        # If repo_path not provided, we can't actually search filesystem
        # In production, this would clone/access the repo
        # For now, we'll return patterns that WOULD be searched

        file_stem = Path(source_file).stem  # e.g., "user_service"
        file_dir = Path(source_file).parent

        # Common test file patterns
        patterns = [
            f"test_{file_stem}.py",
            f"{file_stem}_test.py",
            f"test_{file_stem}.js",
            f"{file_stem}.test.js",
            f"{file_stem}.test.ts",
            f"{file_stem}.spec.js",
            f"{file_stem}.spec.ts",
        ]

        # Common test directory patterns
        test_dirs = [
            file_dir / "tests",
            file_dir / "test",
            Path("tests") / file_dir,
            Path("test") / file_dir,
            file_dir.parent / "tests" / file_dir.name,
        ]

        # In real implementation, check filesystem
        # For now, return the patterns we would search
        return {
            "source_file": source_file,
            "potential_test_files": patterns,
            "test_directories": [str(d) for d in test_dirs],
            "found_tests": [],  # Would be populated from actual filesystem search
            "has_tests": False,  # Would be True if tests found
        }


class CoverageAnalyzerTool(BaseTool):
    """Tool for analyzing test coverage by comparing source and test code.

    Analyzes which functions/classes in the source file are covered by tests.
    """

    name: str = "coverage_analyzer"
    description: str = (
        "Analyzes test coverage by comparing source code functions/classes against "
        "test file contents. Identifies which code elements lack test coverage."
    )

    def _run(
        self,
        source_functions: list[str],
        source_classes: list[str],
        test_file_content: str | None = None,
    ) -> dict:
        """Analyze coverage for source code elements.

        Args:
            source_functions: Functions from source file
            source_classes: Classes from source file
            test_file_content: Content of test file (if exists)

        Returns:
            dict: Coverage analysis results
        """
        if not test_file_content:
            # No test file = no coverage
            return {
                "functions_tested": [],
                "functions_untested": source_functions,
                "classes_tested": [],
                "classes_untested": source_classes,
                "coverage_percentage": 0.0,
                "has_tests": False,
            }

        # Simple heuristic: check if function/class names appear in test file
        # Real implementation would use AST analysis or actual coverage tools
        test_content_lower = test_file_content.lower()

        functions_tested = [
            func for func in source_functions if func.lower() in test_content_lower
        ]
        functions_untested = [func for func in source_functions if func not in functions_tested]

        classes_tested = [cls for cls in source_classes if cls.lower() in test_content_lower]
        classes_untested = [cls for cls in source_classes if cls not in classes_tested]

        total_items = len(source_functions) + len(source_classes)
        tested_items = len(functions_tested) + len(classes_tested)
        coverage_pct = (tested_items / total_items * 100) if total_items > 0 else 0.0

        return {
            "functions_tested": functions_tested,
            "functions_untested": functions_untested,
            "classes_tested": classes_tested,
            "classes_untested": classes_untested,
            "coverage_percentage": round(coverage_pct, 2),
            "has_tests": len(functions_tested) + len(classes_tested) > 0,
        }


class RiskAssessorTool(BaseTool):
    """Tool for assessing risk level of test coverage gaps.

    Evaluates the risk based on:
    - Type of code (critical business logic vs. utility)
    - Complexity of changes
    - Number of untested items
    - File type and importance
    """

    name: str = "risk_assessor"
    description: str = (
        "Assesses the risk level (low, medium, high, critical) of test coverage gaps "
        "based on code complexity, file type, and business criticality."
    )

    # Keywords that indicate critical/high-risk code
    CRITICAL_KEYWORDS: ClassVar[list] = [
        "auth",
        "login",
        "password",
        "payment",
        "transaction",
        "security",
        "admin",
        "delete",
        "remove",
        "drop",
    ]

    HIGH_RISK_KEYWORDS: ClassVar[list] = [
        "user",
        "account",
        "database",
        "api",
        "service",
        "create",
        "update",
        "modify",
    ]

    def _run(
        self,
        file_path: str,
        functions_untested: list[str],
        classes_untested: list[str],
        lines_changed: int,
        complexity_impact: str,
    ) -> dict:
        """Assess risk level for coverage gap.

        Args:
            file_path: Path to source file
            functions_untested: Untested functions
            classes_untested: Untested classes
            lines_changed: Total lines changed
            complexity_impact: Complexity assessment (low/medium/high)

        Returns:
            dict: Risk assessment
        """
        risk_score = 0
        reasons = []

        # Check for critical keywords in file path or function names
        path_lower = file_path.lower()
        all_names_lower = " ".join(functions_untested + classes_untested).lower()

        if any(keyword in path_lower or keyword in all_names_lower for keyword in self.CRITICAL_KEYWORDS):
            risk_score += 40
            reasons.append("Contains critical business logic (auth, payment, security, etc.)")

        elif any(keyword in path_lower or keyword in all_names_lower for keyword in self.HIGH_RISK_KEYWORDS):
            risk_score += 25
            reasons.append("Contains important business logic (user, API, database operations)")

        # Number of untested items
        untested_count = len(functions_untested) + len(classes_untested)
        if untested_count > 10:
            risk_score += 25
            reasons.append(f"High number of untested items ({untested_count})")
        elif untested_count > 5:
            risk_score += 15
            reasons.append(f"Moderate number of untested items ({untested_count})")
        elif untested_count > 0:
            risk_score += 5

        # Lines changed
        if lines_changed > 200:
            risk_score += 20
            reasons.append(f"Large change ({lines_changed} lines)")
        elif lines_changed > 100:
            risk_score += 10
            reasons.append(f"Significant change ({lines_changed} lines)")

        # Complexity impact
        if complexity_impact == "high":
            risk_score += 15
            reasons.append("High complexity change")
        elif complexity_impact == "medium":
            risk_score += 8

        # Determine risk level from score
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 45:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasons": reasons,
        }


class ScenarioIdentifierTool(BaseTool):
    """Tool for identifying missing test scenarios.

    Suggests test scenarios that should exist based on code patterns:
    - Error handling
    - Edge cases
    - Boundary conditions
    - Integration points
    """

    name: str = "scenario_identifier"
    description: str = (
        "Identifies missing test scenarios like error handling, edge cases, "
        "boundary conditions, and integration tests based on code patterns."
    )

    def _run(self, file_path: str, functions: list[str], classes: list[str]) -> dict:
        """Identify missing test scenarios.

        Args:
            file_path: Source file path
            functions: Function names
            classes: Class names

        Returns:
            dict: Suggested test scenarios
        """
        scenarios = []
        test_types = []

        # Always recommend these basic scenarios
        scenarios.append("Happy path / successful execution")
        scenarios.append("Error handling and exception cases")
        test_types.append("unit")

        # Check for specific patterns
        all_names_lower = " ".join(functions + classes).lower()

        if "create" in all_names_lower or "add" in all_names_lower:
            scenarios.append("Duplicate creation / uniqueness constraints")
            scenarios.append("Invalid input validation")

        if "update" in all_names_lower or "modify" in all_names_lower:
            scenarios.append("Update non-existent entity")
            scenarios.append("Concurrent update conflicts")

        if "delete" in all_names_lower or "remove" in all_names_lower:
            scenarios.append("Delete non-existent entity")
            scenarios.append("Cascade delete effects")

        if "get" in all_names_lower or "fetch" in all_names_lower or "find" in all_names_lower:
            scenarios.append("Not found / empty result handling")
            scenarios.append("Pagination and filtering")

        if "auth" in all_names_lower or "login" in all_names_lower:
            scenarios.append("Invalid credentials")
            scenarios.append("Session expiration")
            scenarios.append("Permission/authorization checks")
            test_types.append("security")

        if "api" in file_path.lower() or "endpoint" in file_path.lower():
            scenarios.append("API input validation")
            scenarios.append("API error responses")
            test_types.append("integration")

        if "database" in file_path.lower() or "db" in file_path.lower() or "repo" in file_path.lower():
            scenarios.append("Database connection failures")
            scenarios.append("Transaction rollback")
            test_types.append("integration")

        # Add edge case scenarios
        scenarios.append("Boundary values (empty, null, maximum)")
        scenarios.append("Race conditions / concurrency")

        return {
            "missing_scenarios": list(set(scenarios)),
            "recommended_test_types": list(set(test_types)),
        }


def create_test_coverage_agent(llm: LLM | None = None) -> Agent:
    """Create and configure the TestCoverageAgent.

    Args:
        llm: Optional LLM configuration (if not provided, uses default Claude)

    Returns:
        Agent: Configured CrewAI agent
    """
    # Initialize tools
    test_finder = TestFileFinder()
    coverage_analyzer = CoverageAnalyzerTool()
    risk_assessor = RiskAssessorTool()
    scenario_identifier = ScenarioIdentifierTool()

    # Create agent
    agent = Agent(
        role="Test Coverage Analyst",
        goal=(
            "Analyze code changes to identify test coverage gaps, assess the risk of "
            "untested code, and recommend which areas need test coverage based on "
            "business criticality and change complexity."
        ),
        backstory=(
            "You are a quality assurance expert with extensive experience in test "
            "coverage analysis and risk assessment. You understand that not all code "
            "needs the same level of testing - you prioritize based on business impact, "
            "complexity, and criticality. You excel at finding gaps in test coverage "
            "and explaining why those gaps matter."
        ),
        tools=[test_finder, coverage_analyzer, risk_assessor, scenario_identifier],
        llm=llm,  # Use provided LLM or None to use default from environment
        verbose=True,
        allow_delegation=False,
    )

    return agent


def create_coverage_analysis_task(
    agent: Agent,
    code_changes: list[CodeChange],
) -> Task:
    """Create a task for the TestCoverageAgent.

    Args:
        agent: The TestCoverageAgent
        code_changes: List of code changes from CodeAnalyzerAgent

    Returns:
        Task: Configured CrewAI task
    """
    # Filter to only source files
    source_changes = [change for change in code_changes if change.is_source_file]

    changes_summary = "\n".join(
        [
            f"- {change.file_path}: {len(change.functions_changed)} functions, "
            f"{change.total_lines_changed} lines, {change.complexity_impact} complexity"
            for change in source_changes
        ]
    )

    task = Task(
        description=f"""
Analyze test coverage gaps for the following code changes and produce TestCoverageGap objects.

Source files changed:
{changes_summary}

For each source file change:
1. Use test_file_finder to locate existing test files
2. Use coverage_analyzer to determine which functions/classes lack tests
3. Use scenario_identifier to suggest missing test scenarios (error handling, edge cases, etc.)
4. Use risk_assessor to evaluate the risk level based on:
   - File path and function names (look for critical keywords: auth, payment, security, etc.)
   - Number of untested items
   - Lines changed
   - Complexity impact
5. Create a TestCoverageGap object for each significant gap with:
   - file_path
   - functions_without_tests
   - classes_without_tests
   - scenarios_missing (from scenario_identifier)
   - existing_test_files (if any)
   - partially_covered (true if some tests exist)
   - risk_level (low/medium/high/critical)
   - reason (clear explanation of why this is a gap and its risk)
   - recommended_test_types (unit, integration, security, etc.)

Prioritize gaps in critical areas (authentication, payments, data modification).
Focus on actionable gaps that meaningfully improve code quality and reliability.

Output: Return a structured list of TestCoverageGap data that can be serialized.
""",
        agent=agent,
        expected_output=(
            "A structured JSON-like list of test coverage gaps with file paths, untested items, "
            "risk levels, missing scenarios, and clear recommendations."
        ),
    )

    return task


class CoverageAnalysisInput(BaseModel):
    """Input model for coverage analysis."""

    code_changes: list[CodeChange] = Field(description="Code changes to analyze")


class CoverageAnalysisOutput(BaseModel):
    """Output model for coverage analysis."""

    coverage_gaps: list[TestCoverageGap] = Field(description="Identified coverage gaps")
    total_gaps: int = Field(description="Total number of gaps")
    critical_gaps: int = Field(description="Number of critical gaps")
    high_risk_gaps: int = Field(description="Number of high/critical risk gaps")
