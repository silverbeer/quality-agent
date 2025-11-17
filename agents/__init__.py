"""Quality Agent - CrewAI agents package."""

from agents.code_analyzer import (
    create_code_analysis_task,
    create_code_analyzer_agent,
)
from agents.crew import QualityAnalysisCrew, analyze_pull_request
from agents.test_coverage import (
    create_coverage_analysis_task,
    create_test_coverage_agent,
)
from agents.test_planner import (
    create_test_planner_agent,
    create_test_planning_task,
)


__version__ = "0.1.0"

__all__ = [
    # Main entry point
    "analyze_pull_request",
    "QualityAnalysisCrew",
    # Individual agents
    "create_code_analyzer_agent",
    "create_test_coverage_agent",
    "create_test_planner_agent",
    # Tasks
    "create_code_analysis_task",
    "create_coverage_analysis_task",
    "create_test_planning_task",
]
