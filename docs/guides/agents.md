# Agent Architecture

> AI agent design, implementation, and orchestration using CrewAI

**Status**: ✅ Complete (Phase 3)
**Last Updated**: 2025-11-14

## Overview

Quality Agent uses three specialized AI agents orchestrated by CrewAI to analyze GitHub pull requests and generate intelligent test execution plans. Each agent has a specific role, uses custom tools, and produces structured Pydantic models for inter-agent communication.

### Agent Pipeline

```
GitHub PR Event
    ↓
Webhook Receiver (signature verification)
    ↓
Background Task (async processing)
    ↓
┌─────────────────────────────────────────┐
│  QualityAnalysisCrew                    │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  1. CodeAnalyzerAgent             │ │
│  │     - Fetches PR diff             │ │
│  │     - Parses file changes         │ │
│  │     - Detects functions/classes   │ │
│  │     - Assesses complexity         │ │
│  │     Output: CodeChange[]          │ │
│  └──────────┬────────────────────────┘ │
│             ↓                           │
│  ┌───────────────────────────────────┐ │
│  │  2. TestCoverageAgent             │ │
│  │     - Finds existing tests        │ │
│  │     - Identifies untested code    │ │
│  │     - Assesses risk levels        │ │
│  │     - Suggests scenarios          │ │
│  │     Output: TestCoverageGap[]     │ │
│  └──────────┬────────────────────────┘ │
│             ↓                           │
│  ┌───────────────────────────────────┐ │
│  │  3. TestPlannerAgent              │ │
│  │     - Prioritizes tests           │ │
│  │     - Creates recommendations     │ │
│  │     - Estimates durations         │ │
│  │     - Identifies critical paths   │ │
│  │     Output: TestExecutionPlan     │ │
│  └──────────┬────────────────────────┘ │
│             ↓                           │
│       AnalysisReport                    │
└─────────────────────────────────────────┘
    ↓
Structured Logging
```

## Data Models

All agents communicate using type-safe Pydantic models defined in `models/analysis.py`:

### CodeChange
Represents a code change in a file with metadata about the change.

**Fields**:
- `file_path`: Path to changed file
- `change_type`: `added`, `modified`, `deleted`, or `renamed`
- `file_type`: `source`, `test`, `config`, `documentation`, or `other`
- `functions_changed`: List of function names
- `classes_changed`: List of class names
- `lines_added`, `lines_deleted`: Line count metrics
- `complexity_impact`: `low`, `medium`, or `high`
- `imports_added`: New dependencies
- `related_files`: Files potentially affected
- `key_changes`: Brief description

### TestCoverageGap
Represents missing test coverage with risk assessment.

**Fields**:
- `file_path`: Source file with gap
- `functions_without_tests`: Untested functions
- `classes_without_tests`: Untested classes
- `scenarios_missing`: Missing test scenarios (e.g., "error handling")
- `existing_test_files`: Current test files
- `partially_covered`: True if some tests exist
- `risk_level`: `low`, `medium`, `high`, or `critical`
- `reason`: Explanation of gap and risk
- `recommended_test_types`: Types of tests needed

### TestRecommendation
Specific test recommendation with priority.

**Fields**:
- `test_file`: Where test should be added
- `test_name`: Specific test function name
- `test_type`: `unit`, `integration`, `e2e`, `security`, or `performance`
- `priority`: `critical`, `high`, `medium`, or `low`
- `reason`: Why this test is important
- `estimated_duration`: Test duration in seconds
- `addresses_gap`: Reference to coverage gap

### TestExecutionPlan
Complete test execution plan with prioritized recommendations.

**Fields**:
- `recommendations`: Ordered list of TestRecommendation (highest priority first)
- `estimated_total_duration`: Total duration in seconds
- `parallel_execution_possible`: Whether tests can run in parallel
- `summary`: Brief plan overview
- `coverage_gaps_addressed`: Number of gaps addressed
- `new_tests_needed`: Number of new tests to write
- `critical_paths_covered`: Critical code paths being tested
- `risk_areas_remaining`: Areas still lacking coverage

### AnalysisReport
Final comprehensive analysis report.

**Fields**:
- `pr_number`, `repository`, `pr_url`, `commit_sha`: PR context
- `analysis_timestamp`, `duration_seconds`: Timing info
- `code_changes`: All identified code changes
- `coverage_gaps`: All identified coverage gaps
- `test_plan`: Complete test execution plan
- `status`: `completed`, `partial`, or `failed`
- `errors`: Any errors encountered
- `total_files_changed`, `total_lines_changed`: Metrics
- `risk_score`: Overall risk (`low`, `medium`, `high`, `critical`)

## CodeAnalyzerAgent

**Location**: `agents/code_analyzer.py`

### Role
Analyzes git diffs from GitHub PRs to identify changed files, functions, classes, and assess change complexity.

### Tools

1. **DiffParserTool** (`diff_parser`)
   - Fetches PR diff from GitHub
   - Parses diff into structured file changes
   - Counts lines added/deleted
   - Detects file operations (added, modified, deleted, renamed)

2. **FunctionDetectorTool** (`function_detector`)
   - Detects changed functions and classes using regex
   - Supports Python, JavaScript, TypeScript, Java, Go
   - Language-specific patterns for accurate detection

3. **FileClassifierTool** (`file_classifier`)
   - Classifies files by type (source, test, config, docs, other)
   - Path-based heuristics (e.g., `/tests/`, `test_*.py`)
   - Extension-based detection (`.py`, `.js`, `.md`)

### Configuration
```python
agent = Agent(
    role="Code Change Analyzer",
    goal="Analyze git diffs from pull requests to identify all code changes...",
    backstory="Expert software engineer with deep knowledge of multiple languages...",
    tools=[diff_parser, function_detector, file_classifier],
    verbose=True,
    allow_delegation=False,
)
```

### Input
- `PullRequestWebhookPayload`: GitHub webhook payload with PR info
- `github_token`: Optional GitHub API token

### Output
- `list[CodeChange]`: Structured code changes

### Language Support
- **Python**: Functions (`def`/`async def`), classes
- **JavaScript/TypeScript**: Functions, arrow functions, classes
- **Java**: Methods, classes
- **Go**: Functions, structs
- **Vue.js**: Treated as JavaScript

### Complexity Assessment
Determines `complexity_impact` based on:
- Lines changed (more lines = higher complexity)
- Number of functions/classes affected
- File type (source code is higher impact than config)

## TestCoverageAgent

**Location**: `agents/test_coverage.py`

### Role
Identifies test coverage gaps by analyzing code changes and finding existing tests.

### Tools

1. **TestFileFinder** (`test_file_finder`)
   - Searches for existing test files
   - Common patterns: `test_*.py`, `*_test.py`, `*.test.js`, `*.spec.ts`
   - Checks test directories: `tests/`, `test/`

2. **CoverageAnalyzerTool** (`coverage_analyzer`)
   - Compares source functions/classes against test file content
   - Identifies untested code elements
   - Calculates coverage percentage
   - Heuristic: checks if names appear in test files

3. **RiskAssessorTool** (`risk_assessor`)
   - Assesses risk level of coverage gaps
   - Critical keywords: `auth`, `login`, `password`, `payment`, `security`
   - High-risk keywords: `user`, `account`, `database`, `api`
   - Factors: lines changed, number of untested items, complexity

4. **ScenarioIdentifierTool** (`scenario_identifier`)
   - Suggests missing test scenarios
   - Pattern detection: `create` → test duplicates, invalid input
   - Pattern detection: `delete` → test non-existent, cascades
   - Always recommends: error handling, edge cases, boundary values

### Configuration
```python
agent = Agent(
    role="Test Coverage Analyst",
    goal="Analyze code changes to identify test coverage gaps...",
    backstory="Quality assurance expert with extensive experience...",
    tools=[test_finder, coverage_analyzer, risk_assessor, scenario_identifier],
    verbose=True,
    allow_delegation=False,
)
```

### Input
- `list[CodeChange]`: Code changes from CodeAnalyzerAgent

### Output
- `list[TestCoverageGap]`: Identified coverage gaps with risk assessment

### Risk Levels
- **Critical (70+ score)**: Auth/payment/security code without tests
- **High (45-69 score)**: Important business logic, many untested items
- **Medium (20-44 score)**: Moderate risk, some untested code
- **Low (< 20 score)**: Minor gaps, low impact

## TestPlannerAgent

**Location**: `agents/test_planner.py`

### Role
Creates intelligent, prioritized test execution plans based on coverage gaps.

### Tools

1. **TestPrioritizerTool** (`test_prioritizer`)
   - Determines test priority based on:
     * Gap risk level (critical/high/medium/low)
     * Test type (security > integration > unit)
     * File path criticality
     * Number of functions being tested
   - Returns priority score and level

2. **TestEstimatorTool** (`test_estimator`)
   - Estimates test duration by type:
     * Unit: 2 seconds base
     * Integration: 10 seconds base
     * E2E: 30 seconds base
     * Security: 15 seconds base
   - Adjusts for complexity and test count

3. **TestRecommenderTool** (`test_recommender`)
   - Generates specific test recommendations
   - Creates test file paths (e.g., `tests/unit/services/test_user.py`)
   - Names test functions (e.g., `test_update_user_with_timestamp`)
   - Provides clear reasoning for each test

4. **CriticalPathIdentifier** (`critical_path_identifier`)
   - Identifies critical code paths: authentication, payment, transactions
   - Highlights risk areas that remain after testing
   - Helps prioritize what matters most

### Configuration
```python
agent = Agent(
    role="Test Planning Strategist",
    goal="Create intelligent, prioritized test execution plans...",
    backstory="Test strategy expert who excels at creating actionable test plans...",
    tools=[prioritizer, estimator, recommender, path_identifier],
    verbose=True,
    allow_delegation=False,
)
```

### Input
- `list[TestCoverageGap]`: Coverage gaps from TestCoverageAgent
- `list[CodeChange]`: Optional code changes for context

### Output
- `TestExecutionPlan`: Complete prioritized test plan

### Priority Scoring
Priority determined by multiple factors:
- **Base score**: From gap risk level (25-100)
- **Test type bonus**: Security (+30), Integration (+20), Unit (+10)
- **Critical path bonus**: Auth/payment files (+20)
- **Complexity bonus**: Many functions (+10-15), large changes (+10-20)

**Final priority tiers**:
- **Critical**: Score ≥ 120
- **High**: Score 85-119
- **Medium**: Score 55-84
- **Low**: Score < 55

## CrewAI Orchestration

**Location**: `agents/crew.py`

### QualityAnalysisCrew Class

Orchestrates the three-agent pipeline and handles data flow between agents.

```python
class QualityAnalysisCrew:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.code_analyzer = create_code_analyzer_agent(github_token)
        self.coverage_analyzer = create_test_coverage_agent()
        self.test_planner = create_test_planner_agent()

    def analyze_pull_request(self, webhook_payload: PullRequestWebhookPayload) -> AnalysisReport:
        # Stage 1: Code Analysis
        code_changes = self._run_code_analysis(webhook_payload)

        # Stage 2: Coverage Analysis
        coverage_gaps = self._run_coverage_analysis(code_changes)

        # Stage 3: Test Planning
        test_plan = self._run_test_planning(coverage_gaps, code_changes)

        # Create final report
        return self._create_full_report(webhook_payload, code_changes, coverage_gaps, test_plan)
```

### Sequential Processing

Agents run sequentially, each building on the previous agent's output:
1. **CodeAnalyzerAgent** analyzes diff → produces `CodeChange[]`
2. **TestCoverageAgent** uses `CodeChange[]` → produces `TestCoverageGap[]`
3. **TestPlannerAgent** uses `TestCoverageGap[]` → produces `TestExecutionPlan`

### Error Handling

- Exceptions caught at each stage
- Logs errors with context (PR number, delivery ID, error message)
- Returns `AnalysisReport` with `status="failed"` on error
- Handles edge cases:
  * No source code changes → returns minimal report
  * No coverage gaps → returns report with no recommendations
  * Analysis timeout → returns partial results

### Logging

Structured logging throughout pipeline:
```python
logger.info("stage_1_starting", stage="code_analysis")
logger.info("stage_1_completed", stage="code_analysis", changes_found=len(code_changes))
logger.error("analysis_failed", pr_number=pr_number, error=str(e))
```

## Integration with Webhook Receiver

**Location**: `app/webhook_receiver.py`

### Background Task Processing

Analysis runs asynchronously using FastAPI's `BackgroundTasks`:

```python
async def run_pr_analysis(payload: PullRequestWebhookPayload, delivery_id: str) -> None:
    """Run PR analysis in background."""
    report = analyze_pull_request(webhook_payload=payload, github_token=settings.github_token)
    logger.info("analysis_completed", **report.to_summary_dict())

async def process_pull_request_webhook(
    payload: PullRequestWebhookPayload,
    delivery_info: WebhookDeliveryInfo,
    background_tasks: BackgroundTasks,
) -> dict:
    """Process PR webhook and queue analysis."""
    if payload.is_actionable:
        background_tasks.add_task(run_pr_analysis, payload, delivery_info.delivery_id)
        return {"status": "processing", "pr_number": payload.number}
```

### Response Flow

1. GitHub sends webhook → FastAPI receives request
2. Signature verified → Payload validated
3. Background task queued → **200 OK response immediately**
4. Analysis runs asynchronously → Results logged
5. Future: Results posted to GitHub PR or stored in database

## Usage Example

```python
from agents import analyze_pull_request
from models import PullRequestWebhookPayload

# Parse webhook
payload = PullRequestWebhookPayload.model_validate(webhook_data)

# Run analysis
report = analyze_pull_request(webhook_payload=payload, github_token="ghp_...")

# Access results
print(f"Found {len(report.coverage_gaps)} coverage gaps")
print(f"Risk score: {report.risk_score}")
print(f"Critical tests: {len(report.test_plan.critical_tests)}")

# Get summary
summary = report.to_summary_dict()
# {
#   "pr_number": 123,
#   "status": "completed",
#   "coverage_gaps": 5,
#   "critical_gaps": 2,
#   "total_test_recommendations": 12,
#   "risk_score": "high",
#   ...
# }
```

## Testing Agents

### Unit Testing Approach

Mock agent tools and verify logic:

```python
from unittest.mock import Mock
from agents.code_analyzer import DiffParserTool

def test_diff_parser_counts_lines():
    tool = DiffParserTool()
    result = tool._run(diff_url="http://test.com/diff", github_token=None)
    # Assertions on result structure
```

### Integration Testing

Test full agent pipeline with mock LLM responses:

```python
@mock.patch('agents.crew.Crew.kickoff')
def test_full_analysis_pipeline(mock_kickoff):
    mock_kickoff.return_value = mock_agent_output
    crew = QualityAnalysisCrew(github_token="test")
    report = crew.analyze_pull_request(test_payload)
    assert report.status == "completed"
```

### Current Test Coverage

- **Overall**: 51.61% (new agent code needs tests)
- **Models**: 85-98% (well tested)
- **Webhook receiver**: 91% (excellent)
- **Agent modules**: 19-27% (need unit tests)

**Goal**: Bring agent coverage to 80%+ with comprehensive tool tests.

## Performance Considerations

### Analysis Duration
- **Target**: < 30 seconds per PR
- **Current**: Depends on LLM response time and diff size
- **Optimization**: Caching, parallel tool execution (future)

### Token Usage
- Focused prompts minimize token usage
- Structured output reduces parsing complexity
- Future: Implement token usage tracking and optimization

### Scalability
- Background processing prevents webhook timeout
- Stateless agents allow horizontal scaling
- Future: Message queue for high-volume processing

## Future Enhancements

### Phase 4+
- [ ] Agent output parsing (currently using mock data)
- [ ] Real-time agent result streaming
- [ ] Agent performance metrics
- [ ] Custom agent configuration per repository
- [ ] Agent learning from past analyses
- [ ] Multi-model support (GPT, Claude, local models)

---

**Last Updated**: 2025-11-14
**Phase**: Phase 3 Complete
**Module Files**: `agents/code_analyzer.py`, `agents/test_coverage.py`, `agents/test_planner.py`, `agents/crew.py`
**Data Models**: `models/analysis.py`
