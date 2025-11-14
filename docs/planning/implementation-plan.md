# Quality Agent - Phased Implementation Plan

> Comprehensive implementation plan with detailed phases, deliverables, and documentation requirements

**Last Updated**: 2025-11-14
**Status**: Phase 3 Complete - CrewAI Agents Operational
**Next Phase**: Phase 4 - Integration and Testing (Ongoing)

---

## Table of Contents

- [Overview](#overview)
- [Phase 0: Planning and Setup](#phase-0-planning-and-setup) ✓ Complete
- [Phase 1: Foundation and Core Infrastructure](#phase-1-foundation-and-core-infrastructure)
- [Phase 2: Webhook Receiver and Security](#phase-2-webhook-receiver-and-security)
- [Phase 3: CrewAI Agents Implementation](#phase-3-crewai-agents-implementation)
- [Phase 4: Integration and Testing](#phase-4-integration-and-testing)
- [Phase 5: Deployment and Operations](#phase-5-deployment-and-operations)
- [Phase 6: Storage and History](#phase-6-storage-and-history)
- [Phase 7: UI and Notifications](#phase-7-ui-and-notifications)
- [Phase 8: Advanced Features](#phase-8-advanced-features)
- [Documentation Maintenance Strategy](#documentation-maintenance-strategy)
- [Success Criteria](#success-criteria)

---

## Overview

### Project Goals

1. **Primary**: Build a production-ready webhook receiver that analyzes GitHub PRs for test coverage gaps
2. **Secondary**: Establish strong development practices (testing, documentation, code quality)
3. **Tertiary**: Create a scalable foundation for future enhancements

### Development Principles

- **Documentation-First**: Update documentation before or during implementation
- **Test-Driven**: Write tests before or alongside implementation
- **Security-First**: Implement security measures from the start
- **Incremental**: Each phase delivers working, deployable software
- **Quality Gates**: Pre-commit hooks enforce code quality standards

### Quality Standards

- **Code Coverage**: Minimum 80%, target 90%+
- **Type Coverage**: 100% (all functions must have type hints)
- **Documentation**: 100% (all public APIs must have docstrings)
- **Security**: Zero high-severity vulnerabilities (via bandit)
- **Performance**: Webhook response < 200ms, analysis completion < 30s

---

## Phase 0: Planning and Setup

**Status**: ✅ Complete
**Duration**: Day 1
**Goal**: Establish project structure, documentation, and development tooling

### Objectives

- [x] Create comprehensive project documentation
- [x] Define phased implementation plan
- [x] Set up development tooling and pre-commit hooks
- [x] Establish documentation maintenance strategy

### Deliverables

- [x] `Claude.md` - Complete project context and guidelines
- [x] `README.md` - Project overview and quick start guide
- [x] `IMPLEMENTATION_PLAN.md` - This file
- [x] `.pre-commit-config.yaml` - Pre-commit hooks configuration
- [x] `pyproject.toml` - Project dependencies and configuration
- [ ] `.gitignore` - Python and project-specific ignores
- [ ] `.env.example` - Environment variables template

### Documentation Created

- **Claude.md**: Project context, architecture, coding standards, testing requirements
- **README.md**: Quick start, installation, basic usage
- **IMPLEMENTATION_PLAN.md**: Detailed phased implementation plan

### Next Steps

→ Proceed to **Phase 1: Foundation and Core Infrastructure**

---

## Phase 1: Foundation and Core Infrastructure

**Status**: 🔄 Ready to Start
**Duration**: 2-3 days
**Goal**: Set up project structure, configuration management, and core dependencies

### Objectives

1. Initialize Python project with modern tooling (uv, pyproject.toml)
2. Create project directory structure
3. Set up configuration management with Pydantic Settings
4. Implement structured logging with contextual information
5. Set up testing framework and fixtures
6. Configure pre-commit hooks for code quality

### Tasks Breakdown

#### Task 1.1: Project Initialization
```bash
# Create project structure
mkdir -p app agents models tests/{unit,integration} docs deployment/k8s
touch app/__init__.py agents/__init__.py models/__init__.py tests/__init__.py
```

**Files to Create**:
- `pyproject.toml` - Dependencies, build config, tool settings
- `.gitignore` - Python, IDE, environment-specific files
- `.env.example` - Template for required environment variables
- `app/__init__.py` - Package initialization
- `agents/__init__.py` - Agent package initialization
- `models/__init__.py` - Models package initialization

**Dependencies to Add**:
```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "crewai>=0.1.0",
    "crewai-tools>=0.1.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.25.0",
    "PyGithub>=2.1.0",
    "structlog>=23.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "bandit>=1.7.5",
    "pre-commit>=3.5.0",
]
```

**Success Criteria**:
- [ ] Project installs cleanly with `uv sync`
- [ ] All package imports work correctly
- [ ] `.env.example` documents all required environment variables
- [ ] `uv.lock` is committed to git

#### Task 1.2: Configuration Management
**Files to Create**:
- `app/config.py` - Pydantic Settings-based configuration

**Implementation**:
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # GitHub Configuration
    github_webhook_secret: str = Field(description="GitHub webhook secret for signature verification")
    github_token: str = Field(description="GitHub personal access token")

    # Anthropic Configuration
    anthropic_api_key: str = Field(description="Anthropic API key for Claude")

    # Application Configuration
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")

settings = Settings()
```

**Success Criteria**:
- [ ] Configuration loads from `.env` file
- [ ] Missing required variables raise clear errors
- [ ] Type validation works correctly
- [ ] Default values work as expected

#### Task 1.3: Structured Logging
**Files to Create**:
- `app/logging_config.py` - Structured logging setup

**Implementation**:
```python
import structlog
from app.config import settings

def configure_logging() -> None:
    """Configure structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.environment == "development"
            else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Success Criteria**:
- [ ] Logs output in JSON format in production
- [ ] Logs output in readable format in development
- [ ] Log level is configurable via environment variable
- [ ] Context variables are included in all logs

#### Task 1.4: Testing Framework Setup
**Files to Create**:
- `tests/conftest.py` - Pytest configuration and fixtures
- `tests/unit/test_config.py` - Configuration tests
- `pytest.ini` or `pyproject.toml` pytest config

**Implementation** (`tests/conftest.py`):
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)

@pytest.fixture
def mock_github_webhook_payload():
    """Mock GitHub webhook payload for testing."""
    return {
        "action": "opened",
        "number": 123,
        "pull_request": {
            "id": 1,
            "title": "Test PR",
            "state": "open",
            # ... more fields
        }
    }
```

**Success Criteria**:
- [ ] `pytest` runs successfully (even with no tests)
- [ ] Fixtures are available to all tests
- [ ] Coverage reporting works (`pytest --cov`)
- [ ] Async tests work with `pytest-asyncio`

#### Task 1.5: Pre-commit Hooks Configuration
**Files to Create**:
- `.pre-commit-config.yaml` - Pre-commit hooks definition

**Implementation**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.5.0]
        args: [--strict, --ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, app, agents, models]

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-quick
        entry: pytest
        args: [tests/unit, -x, --tb=short]
        language: system
        pass_filenames: false
        always_run: true
```

**Success Criteria**:
- [ ] Pre-commit hooks install correctly
- [ ] `pre-commit run --all-files` passes
- [ ] Hooks run automatically on git commit
- [ ] Hooks can be skipped with `git commit --no-verify` if needed

### Documentation to Create/Update

#### New Documentation Files
1. **`docs/setup.md`** - Detailed setup instructions
   - Prerequisites and dependencies
   - Step-by-step installation
   - Configuration details
   - Troubleshooting common setup issues

2. **`docs/architecture.md`** - System architecture (initial version)
   - High-level component diagram
   - Technology stack details
   - Data flow overview
   - Design decisions and rationale

3. **`docs/development.md`** - Development workflow
   - Setting up development environment
   - Running tests
   - Code quality tools
   - Git workflow and branch strategy

#### Updates to Existing Files
- **README.md**: Add links to new documentation
- **Claude.md**: Update with any architecture decisions made during implementation

### Testing Requirements

#### Unit Tests
- `tests/unit/test_config.py` - Configuration loading and validation
- `tests/unit/test_logging.py` - Logging configuration and output format

**Minimum Coverage**: 90% for configuration and logging modules

### Code Quality Gates

All of the following must pass before Phase 1 is complete:
- [ ] `ruff check .` - No linting errors
- [ ] `ruff format .` - Code is properly formatted
- [ ] `mypy .` - No type errors (strict mode)
- [ ] `bandit -r app agents models` - No security issues
- [ ] `pytest tests/ --cov=app --cov-report=term-missing` - Tests pass with >90% coverage
- [ ] `pre-commit run --all-files` - All hooks pass

### Success Criteria

- [ ] Project structure is complete and organized
- [ ] Configuration management works with environment variables
- [ ] Structured logging is set up and working
- [ ] Testing framework is ready with basic fixtures
- [ ] Pre-commit hooks are configured and passing
- [ ] All documentation is created and up-to-date
- [ ] Code quality gates all pass

### Estimated Effort

- Setup and configuration: 4-6 hours
- Testing framework: 2-3 hours
- Documentation: 3-4 hours
- **Total**: 9-13 hours (1-2 days)

---

## Phase 2: Webhook Receiver and Security

**Status**: 🔜 Pending Phase 1
**Duration**: 3-4 days
**Goal**: Implement secure GitHub webhook receiver with signature verification

### Objectives

1. Create Pydantic models for GitHub webhook payloads
2. Implement HMAC signature verification
3. Build FastAPI webhook endpoint
4. Add security headers and rate limiting
5. Implement health check and metrics endpoints
6. Add comprehensive security tests

### Tasks Breakdown

#### Task 2.1: GitHub Webhook Models
**Files to Create**:
- `models/github.py` - Pydantic models for GitHub webhooks

**Models to Implement**:
```python
class GitHubUser(BaseModel):
    """GitHub user model."""
    login: str
    id: int
    avatar_url: str

class GitHubRepository(BaseModel):
    """GitHub repository model."""
    id: int
    name: str
    full_name: str
    owner: GitHubUser

class GitHubPullRequest(BaseModel):
    """GitHub pull request model."""
    id: int
    number: int
    title: str
    state: str
    user: GitHubUser
    head: dict
    base: dict
    # ... more fields

class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload model."""
    action: str
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
```

**Success Criteria**:
- [ ] Models match GitHub webhook payload structure
- [ ] All fields have appropriate types and validation
- [ ] Models handle optional fields correctly
- [ ] Documentation includes field descriptions

#### Task 2.2: Webhook Signature Verification
**Files to Create**:
- `app/security.py` - Security utilities for webhook verification

**Implementation**:
```python
import hmac
import hashlib
from typing import Optional

def verify_github_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str
) -> bool:
    """
    Verify GitHub webhook signature using HMAC SHA256.

    Uses constant-time comparison to prevent timing attacks.
    """
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = hmac.new(
        secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    received_signature = signature_header[7:]  # Remove "sha256=" prefix

    return hmac.compare_digest(expected_signature, received_signature)
```

**Success Criteria**:
- [ ] Signature verification works with valid signatures
- [ ] Invalid signatures are rejected
- [ ] Uses constant-time comparison
- [ ] Handles edge cases (missing header, wrong format)

#### Task 2.3: FastAPI Application Setup
**Files to Create**:
- `app/main.py` - FastAPI application initialization

**Implementation**:
```python
from fastapi import FastAPI
from app.logging_config import configure_logging
from app.webhook_receiver import router as webhook_router

configure_logging()

app = FastAPI(
    title="Quality Agent",
    description="AI-powered GitHub PR analysis service",
    version="0.1.0"
)

app.include_router(webhook_router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

**Success Criteria**:
- [ ] FastAPI application starts successfully
- [ ] OpenAPI docs are available at `/docs`
- [ ] Health check endpoint responds correctly

#### Task 2.4: Webhook Endpoint Implementation
**Files to Create**:
- `app/webhook_receiver.py` - GitHub webhook endpoint

**Implementation**:
```python
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.security import verify_github_signature
from app.config import settings
from models.github import GitHubWebhookPayload
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/webhook")

@router.post("/github")
async def receive_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive and process GitHub webhook events.

    Verifies HMAC signature and processes PR events asynchronously.
    """
    # Get signature from headers
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    if not verify_github_signature(body, signature, settings.github_webhook_secret):
        logger.warning("webhook_signature_verification_failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    payload = GitHubWebhookPayload.model_validate_json(body)

    logger.info(
        "webhook_received",
        action=payload.action,
        pr_number=payload.number,
        repository=payload.repository.full_name
    )

    # Process webhook asynchronously
    background_tasks.add_task(process_webhook, payload)

    return {"status": "accepted"}

async def process_webhook(payload: GitHubWebhookPayload):
    """Process webhook payload (placeholder for agent orchestration)."""
    logger.info("processing_webhook", pr_number=payload.number)
    # TODO: Trigger CrewAI agents in Phase 3
```

**Success Criteria**:
- [ ] Endpoint accepts POST requests
- [ ] Signature verification works correctly
- [ ] Invalid signatures are rejected with 401
- [ ] Valid webhooks return 200 immediately
- [ ] Processing happens asynchronously

#### Task 2.5: Security Headers and Middleware
**Files to Update**:
- `app/main.py` - Add security middleware

**Implementation**:
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.ngrok.io"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://github.com"],
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

**Success Criteria**:
- [ ] Security headers are added to responses
- [ ] CORS is configured for GitHub
- [ ] Trusted host middleware prevents host header attacks

### Documentation to Create/Update

#### New Documentation Files
1. **`docs/api.md`** - API documentation
   - Endpoint specifications
   - Request/response formats
   - Authentication and security
   - Error responses

2. **`docs/security.md`** - Security documentation
   - Webhook signature verification
   - Secret management
   - Security headers and middleware
   - Threat model and mitigations

#### Updates to Existing Files
- **README.md**: Update with webhook setup instructions
- **Claude.md**: Update security section with implementation details

### Testing Requirements

#### Unit Tests
- `tests/unit/test_security.py` - Signature verification
- `tests/unit/models/test_github.py` - GitHub models validation
- `tests/unit/test_webhook_receiver.py` - Webhook endpoint logic

#### Integration Tests
- `tests/integration/test_webhook_flow.py` - End-to-end webhook processing

**Test Cases**:
1. Valid webhook with correct signature → 200 OK
2. Valid webhook with invalid signature → 401 Unauthorized
3. Webhook with missing signature → 401 Unauthorized
4. Invalid JSON payload → 422 Unprocessable Entity
5. Malformed signature header → 401 Unauthorized
6. Replay attack (same payload twice) → Both accepted (idempotency tested later)

**Minimum Coverage**: 95% for security-critical code

### Code Quality Gates

- [ ] `ruff check .` - No linting errors
- [ ] `mypy .` - No type errors
- [ ] `bandit -r app` - No security issues (especially in security.py)
- [ ] `pytest tests/ --cov=app --cov-report=term-missing` - >95% coverage for webhook/security
- [ ] Manual test: Send test webhook from GitHub
- [ ] Manual test: Verify signature with invalid secret fails

### Success Criteria

- [ ] Webhook endpoint receives and verifies GitHub webhooks
- [ ] Signature verification is secure and tested
- [ ] FastAPI application is properly structured
- [ ] Security headers and middleware are configured
- [ ] Comprehensive tests cover all security scenarios
- [ ] Documentation is complete and accurate
- [ ] Manual testing with GitHub webhooks successful

### Estimated Effort

- Models and security: 4-6 hours
- Webhook endpoint: 4-5 hours
- Testing: 5-6 hours
- Documentation: 3-4 hours
- **Total**: 16-21 hours (2-3 days)

---

## Phase 3: CrewAI Agents Implementation

**Status**: ✅ Complete (2025-11-14)
**Duration**: 1 day (actual)
**Goal**: Implement three AI agents with CrewAI orchestration

### Objectives

1. ✅ Create Pydantic models for agent communication
2. ✅ Implement CodeAnalyzerAgent
3. ✅ Implement TestCoverageAgent
4. ✅ Implement TestPlannerAgent
5. ✅ Set up CrewAI orchestration
6. ✅ Integrate with webhook receiver
7. ✅ Test agent interactions end-to-end

### Tasks Breakdown

#### Task 3.1: Agent Communication Models
**Files to Create**:
- `models/analysis.py` - Models for inter-agent communication

**Models to Implement**:
```python
class CodeChange(BaseModel):
    """Represents a code change in a file."""
    file_path: str
    change_type: Literal["added", "modified", "deleted"]
    lines_added: int
    lines_removed: int
    functions_changed: list[str]
    impact_score: float = Field(ge=0.0, le=1.0)

class TestCoverageGap(BaseModel):
    """Represents a missing test scenario."""
    file_path: str
    function_name: str
    gap_description: str
    severity: Literal["low", "medium", "high", "critical"]
    suggested_test_cases: list[str]

class TestExecutionPlan(BaseModel):
    """Test execution plan with prioritized tests."""
    priority: Literal["critical", "high", "medium", "low"]
    test_files: list[str]
    estimated_duration: int  # seconds
    rationale: str

class AnalysisReport(BaseModel):
    """Complete analysis report."""
    pr_number: int
    repository: str
    code_changes: list[CodeChange]
    coverage_gaps: list[TestCoverageGap]
    execution_plan: TestExecutionPlan
    summary: str
    timestamp: datetime
```

**Success Criteria**:
- [ ] Models support all required agent communication
- [ ] Validation rules are appropriate
- [ ] Models are fully typed and documented
- [ ] JSON serialization works correctly

#### Task 3.2: CodeAnalyzerAgent
**Files to Create**:
- `agents/code_analyzer.py` - Code analysis agent

**Implementation**:
```python
from crewai import Agent, Task
from models.analysis import CodeChange

CODE_ANALYZER_PROMPT = """
You are an expert code analyst. Analyze the provided git diff and identify:

1. All changed files and classify them (source, test, config)
2. Functions or methods that were added, modified, or deleted
3. The nature of changes (feature, bugfix, refactor)
4. Potential impact areas and dependencies
5. Complexity of changes

For each changed file, assess the impact score (0.0-1.0) based on:
- Number of lines changed
- Complexity of logic changes
- Number of functions affected
- Critical path involvement

Output: A structured list of CodeChange objects in JSON format.
"""

def create_code_analyzer_agent() -> Agent:
    """Create the CodeAnalyzerAgent."""
    return Agent(
        role="Code Analyzer",
        goal="Analyze code changes from git diffs and identify impacted areas",
        backstory="Expert code analyst with deep understanding of software architecture",
        verbose=True,
        allow_delegation=False
    )

def create_code_analysis_task(agent: Agent, pr_diff: str) -> Task:
    """Create code analysis task."""
    return Task(
        description=f"{CODE_ANALYZER_PROMPT}\n\nGit Diff:\n{pr_diff}",
        agent=agent,
        expected_output="JSON array of CodeChange objects"
    )
```

**Success Criteria**:
- [ ] Agent analyzes git diffs correctly
- [ ] Outputs valid CodeChange models
- [ ] Handles various file types appropriately
- [ ] Impact scoring is reasonable

#### Task 3.3: TestCoverageAgent
**Files to Create**:
- `agents/test_coverage.py` - Test coverage analysis agent

**Implementation**:
```python
from crewai import Agent, Task
from models.analysis import CodeChange, TestCoverageGap

TEST_COVERAGE_PROMPT = """
You are a test coverage expert. Given the code changes, identify test coverage gaps:

1. For each changed function, determine if tests exist
2. Identify missing test scenarios (edge cases, error cases, integration)
3. Assess severity of each gap (critical, high, medium, low)
4. Suggest specific test cases to add

Consider:
- Unit test coverage for new/modified functions
- Integration tests for API endpoints
- Edge cases and error handling
- Regression tests for bug fixes

Output: A structured list of TestCoverageGap objects in JSON format.
"""

def create_test_coverage_agent() -> Agent:
    """Create the TestCoverageAgent."""
    return Agent(
        role="Test Coverage Analyst",
        goal="Identify test coverage gaps based on code changes",
        backstory="Expert in test-driven development and quality assurance",
        verbose=True,
        allow_delegation=False
    )

def create_test_coverage_task(
    agent: Agent,
    code_changes: list[CodeChange]
) -> Task:
    """Create test coverage analysis task."""
    changes_json = [c.model_dump() for c in code_changes]
    return Task(
        description=f"{TEST_COVERAGE_PROMPT}\n\nCode Changes:\n{changes_json}",
        agent=agent,
        expected_output="JSON array of TestCoverageGap objects"
    )
```

**Success Criteria**:
- [ ] Agent identifies relevant test gaps
- [ ] Outputs valid TestCoverageGap models
- [ ] Severity assessment is reasonable
- [ ] Suggested test cases are specific and actionable

#### Task 3.4: TestPlannerAgent
**Files to Create**:
- `agents/test_planner.py` - Test planning agent

**Implementation**:
```python
from crewai import Agent, Task
from models.analysis import TestCoverageGap, TestExecutionPlan

TEST_PLANNER_PROMPT = """
You are a test execution planning expert. Given the coverage gaps, create an intelligent test execution plan:

1. Prioritize tests based on severity and impact
2. Group related tests for efficient execution
3. Estimate execution time
4. Provide clear rationale for prioritization

Consider:
- Critical path tests should run first
- Group tests by module/feature
- Balance thoroughness with execution time
- Focus on high-risk areas

Output: A TestExecutionPlan object in JSON format.
"""

def create_test_planner_agent() -> Agent:
    """Create the TestPlannerAgent."""
    return Agent(
        role="Test Execution Planner",
        goal="Create optimized test execution plans based on coverage gaps",
        backstory="Expert in test strategy and risk-based testing",
        verbose=True,
        allow_delegation=False
    )

def create_test_planning_task(
    agent: Agent,
    coverage_gaps: list[TestCoverageGap]
) -> Task:
    """Create test planning task."""
    gaps_json = [g.model_dump() for g in coverage_gaps]
    return Task(
        description=f"{TEST_PLANNER_PROMPT}\n\nCoverage Gaps:\n{gaps_json}",
        agent=agent,
        expected_output="JSON TestExecutionPlan object"
    )
```

**Success Criteria**:
- [ ] Agent creates reasonable test plans
- [ ] Outputs valid TestExecutionPlan model
- [ ] Prioritization makes sense
- [ ] Execution time estimates are reasonable

#### Task 3.5: CrewAI Orchestration
**Files to Create**:
- `agents/crew.py` - CrewAI crew orchestration

**Implementation**:
```python
from crewai import Crew
from agents.code_analyzer import create_code_analyzer_agent, create_code_analysis_task
from agents.test_coverage import create_test_coverage_agent, create_test_coverage_task
from agents.test_planner import create_test_planner_agent, create_test_planning_task
from models.analysis import AnalysisReport
import structlog

logger = structlog.get_logger()

async def analyze_pr(pr_number: int, repository: str, pr_diff: str) -> AnalysisReport:
    """
    Orchestrate AI agents to analyze a pull request.

    Returns a complete AnalysisReport with code changes, coverage gaps,
    and test execution plan.
    """
    logger.info("starting_pr_analysis", pr_number=pr_number, repository=repository)

    # Create agents
    code_analyzer = create_code_analyzer_agent()
    test_coverage = create_test_coverage_agent()
    test_planner = create_test_planner_agent()

    # Create tasks
    analysis_task = create_code_analysis_task(code_analyzer, pr_diff)
    coverage_task = create_test_coverage_task(test_coverage, [])  # Will get input from previous
    planning_task = create_test_planning_task(test_planner, [])  # Will get input from previous

    # Create crew
    crew = Crew(
        agents=[code_analyzer, test_coverage, test_planner],
        tasks=[analysis_task, coverage_task, planning_task],
        verbose=True
    )

    # Execute crew
    result = crew.kickoff()

    logger.info("pr_analysis_complete", pr_number=pr_number)

    # Parse result into AnalysisReport
    # TODO: Parse crew output and create AnalysisReport

    return report
```

**Success Criteria**:
- [ ] Agents execute in correct order
- [ ] Data passes correctly between agents
- [ ] Crew execution completes successfully
- [ ] Results are parsed into AnalysisReport

#### Task 3.6: GitHub API Integration
**Files to Create**:
- `app/github_client.py` - GitHub API client

**Implementation**:
```python
from github import Github
from app.config import settings
import structlog

logger = structlog.get_logger()

class GitHubClient:
    """GitHub API client for fetching PR information."""

    def __init__(self):
        self.client = Github(settings.github_token)

    async def get_pr_diff(self, repository: str, pr_number: int) -> str:
        """Fetch the diff for a pull request."""
        repo = self.client.get_repo(repository)
        pr = repo.get_pull(pr_number)

        # Get diff from PR files
        files = pr.get_files()
        diff_parts = []

        for file in files:
            diff_parts.append(f"--- a/{file.filename}")
            diff_parts.append(f"+++ b/{file.filename}")
            if file.patch:
                diff_parts.append(file.patch)

        return "\n".join(diff_parts)
```

**Success Criteria**:
- [ ] Fetches PR diffs correctly
- [ ] Handles GitHub API rate limiting
- [ ] Error handling for missing PRs
- [ ] Logs API calls appropriately

#### Task 3.7: Integration with Webhook Receiver
**Files to Update**:
- `app/webhook_receiver.py` - Connect agents to webhook

**Implementation**:
```python
async def process_webhook(payload: GitHubWebhookPayload):
    """Process webhook payload with CrewAI agents."""
    logger.info("processing_webhook", pr_number=payload.number)

    # Fetch PR diff
    github_client = GitHubClient()
    pr_diff = await github_client.get_pr_diff(
        payload.repository.full_name,
        payload.number
    )

    # Run analysis
    report = await analyze_pr(
        pr_number=payload.number,
        repository=payload.repository.full_name,
        pr_diff=pr_diff
    )

    # TODO: Store report (Phase 6)
    logger.info(
        "analysis_complete",
        pr_number=payload.number,
        gaps_found=len(report.coverage_gaps)
    )
```

**Success Criteria**:
- [ ] Webhook triggers agent analysis
- [ ] PR diff is fetched and passed to agents
- [ ] Analysis completes successfully
- [ ] Results are logged

### Documentation to Create/Update

#### New Documentation Files
1. **`docs/agents.md`** - Comprehensive agent documentation
   - Agent roles and responsibilities
   - Prompt templates and tuning
   - Inter-agent communication
   - Performance characteristics
   - Troubleshooting agent issues

2. **`docs/testing-agents.md`** - Agent testing guide
   - Mocking LLM calls
   - Testing agent prompts
   - Validating agent outputs
   - Integration test patterns

#### Updates to Existing Files
- **Claude.md**: Update agent sections with actual implementations
- **README.md**: Update architecture diagram with agent details

### Testing Requirements

#### Unit Tests
- `tests/unit/models/test_analysis.py` - Analysis models
- `tests/unit/agents/test_code_analyzer.py` - CodeAnalyzerAgent (mocked LLM)
- `tests/unit/agents/test_test_coverage.py` - TestCoverageAgent (mocked LLM)
- `tests/unit/agents/test_test_planner.py` - TestPlannerAgent (mocked LLM)
- `tests/unit/test_github_client.py` - GitHub API client

#### Integration Tests
- `tests/integration/test_agent_orchestration.py` - Full agent pipeline
- `tests/integration/test_webhook_to_analysis.py` - End-to-end flow

**Test Data**:
- Sample PR diffs (small, medium, large)
- Various change types (feature, bugfix, refactor)
- Edge cases (no tests, all tests, mixed)

**Minimum Coverage**: 85% for agent modules (100% for models)

### Code Quality Gates

- [ ] All agents produce valid Pydantic models
- [ ] Agent prompts are well-documented
- [ ] Error handling for LLM failures
- [ ] Timeouts for long-running agent tasks
- [ ] Integration tests pass with mocked LLM
- [ ] Manual test with real PRs from missing-table repo

### Success Criteria

- [ ] Three agents are implemented and working
- [ ] Agents communicate via Pydantic models
- [ ] CrewAI orchestration works correctly
- [ ] GitHub API integration fetches PR diffs
- [ ] End-to-end flow from webhook to analysis works
- [ ] Comprehensive tests cover agent behavior
- [ ] Documentation is complete with examples

### Estimated Effort

- Models and agent implementation: 12-16 hours
- GitHub API integration: 4-5 hours
- Orchestration and integration: 6-8 hours
- Testing: 8-10 hours
- Documentation: 4-5 hours
- **Total**: 34-44 hours (5-7 days)

---

## Phase 4: Integration and Testing

**Status**: 🔜 Pending Phase 3
**Duration**: 3-4 days
**Goal**: Comprehensive testing, bug fixes, and polish

### Objectives

1. Achieve 90%+ code coverage
2. Comprehensive integration testing
3. Security testing and hardening
4. Performance testing and optimization
5. Error handling and resilience
6. Documentation review and updates

### Tasks Breakdown

#### Task 4.1: Code Coverage Improvement
**Goal**: Achieve 90%+ overall coverage

**Focus Areas**:
- Edge cases in signature verification
- Error paths in webhook processing
- Agent failure scenarios
- GitHub API error handling
- Configuration validation

**Success Criteria**:
- [ ] Overall coverage >90%
- [ ] Security-critical code at 100%
- [ ] All public APIs have tests
- [ ] Coverage report shows no major gaps

#### Task 4.2: Integration Testing
**Files to Create**:
- `tests/integration/test_full_workflow.py` - Complete workflow tests
- `tests/integration/test_error_scenarios.py` - Error handling tests

**Test Scenarios**:
1. Happy path: Valid webhook → Analysis → Report
2. Invalid signature → 401 Unauthorized
3. GitHub API failure → Graceful degradation
4. Agent timeout → Error logged, webhook still accepted
5. Malformed PR diff → Error handled gracefully
6. Empty PR (no changes) → Handled correctly

**Success Criteria**:
- [ ] All integration tests pass
- [ ] Error scenarios are handled gracefully
- [ ] No unhandled exceptions in logs

#### Task 4.3: Security Testing
**Files to Create**:
- `tests/security/test_signature_verification.py` - Security-focused tests
- `tests/security/test_injection.py` - Injection attack tests

**Security Test Cases**:
1. Signature verification timing attack resistance
2. Invalid HMAC formats handled securely
3. SQL injection attempts (if database added)
4. Command injection in PR diffs
5. XSS in PR titles/descriptions
6. Oversized payloads rejected
7. Replay attack detection (future)

**Success Criteria**:
- [ ] All security tests pass
- [ ] Bandit reports no high-severity issues
- [ ] Manual security review complete

#### Task 4.4: Performance Testing
**Files to Create**:
- `tests/performance/test_webhook_latency.py` - Performance tests

**Performance Benchmarks**:
- Webhook response time: <200ms (p95)
- Agent analysis time: <30s for typical PR
- Memory usage: <500MB under load
- Concurrent webhook handling: 10+ simultaneous

**Success Criteria**:
- [ ] Performance benchmarks met
- [ ] No memory leaks detected
- [ ] Concurrent requests handled correctly

#### Task 4.5: Error Handling and Resilience
**Improvements**:
- Retry logic for GitHub API calls
- Timeout handling for agent tasks
- Graceful degradation for agent failures
- Circuit breaker for external services (future)

**Success Criteria**:
- [ ] All error paths tested
- [ ] Logs include appropriate context
- [ ] No silent failures

### Documentation to Create/Update

#### New Documentation Files
1. **`docs/testing.md`** - Comprehensive testing guide
   - Test strategy overview
   - Running different test suites
   - Writing new tests
   - Coverage requirements
   - Performance benchmarks

2. **`docs/troubleshooting.md`** - Troubleshooting guide
   - Common issues and solutions
   - Log analysis
   - Performance debugging
   - GitHub API issues
   - Agent failures

#### Updates to Existing Files
- **README.md**: Update testing section
- **Claude.md**: Document error handling patterns
- **docs/api.md**: Document error responses

### Success Criteria

- [ ] Code coverage >90% overall
- [ ] All integration tests pass
- [ ] Security testing complete with no critical issues
- [ ] Performance benchmarks met
- [ ] Error handling is comprehensive
- [ ] Documentation is complete and accurate

### Estimated Effort

- Coverage improvement: 6-8 hours
- Integration testing: 6-8 hours
- Security testing: 4-5 hours
- Performance testing: 3-4 hours
- Documentation: 3-4 hours
- **Total**: 22-29 hours (3-4 days)

---

## Phase 5: Deployment and Operations

**Status**: 🔜 Pending Phase 4
**Duration**: 2-3 days
**Goal**: Production-ready deployment with Docker and k3s

### Objectives

1. Create production-ready Dockerfile
2. Set up docker-compose for local development
3. Create k3s deployment manifests
4. Configure environment-specific settings
5. Set up observability (logs, health checks)
6. Create deployment documentation
7. Perform deployment testing

### Tasks Breakdown

#### Task 5.1: Dockerfile Creation
**Files to Create**:
- `deployment/Dockerfile` - Multi-stage production build

**Implementation**:
```dockerfile
# Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app ./app
COPY agents ./agents
COPY models ./models

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Success Criteria**:
- [ ] Image builds successfully
- [ ] Image size is reasonable (<500MB)
- [ ] Multi-stage build minimizes final image size
- [ ] Health check works correctly
- [ ] Runs as non-root user

#### Task 5.2: Docker Compose Setup
**Files to Create**:
- `deployment/docker-compose.yml` - Local development setup

**Implementation**:
```yaml
version: '3.8'

services:
  quality-agent:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=development
    volumes:
      - ../app:/app/app
      - ../agents:/app/agents
      - ../models:/app/models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

**Success Criteria**:
- [ ] Services start successfully
- [ ] Environment variables are passed correctly
- [ ] Volume mounts work for development
- [ ] Health checks function properly

#### Task 5.3: Kubernetes Manifests
**Files to Create**:
- `deployment/k8s/deployment.yaml` - k3s deployment
- `deployment/k8s/service.yaml` - k3s service
- `deployment/k8s/secret.yaml.example` - Secret template

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quality-agent
  labels:
    app: quality-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quality-agent
  template:
    metadata:
      labels:
        app: quality-agent
    spec:
      containers:
      - name: quality-agent
        image: quality-agent:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: GITHUB_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: quality-agent-secrets
              key: github-webhook-secret
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: quality-agent-secrets
              key: github-token
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: quality-agent-secrets
              key: anthropic-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Success Criteria**:
- [ ] Deployment succeeds in k3s
- [ ] Service is accessible within cluster
- [ ] Health checks work correctly
- [ ] Resource limits are appropriate
- [ ] Secrets are properly mounted

#### Task 5.4: Environment Configuration
**Files to Update**:
- `.env.example` - Complete environment variable template
- `app/config.py` - Add environment-specific settings

**Environment-Specific Settings**:
- Development: Verbose logging, hot reload
- Staging: Production-like, debug logging
- Production: Optimized, INFO logging, security hardened

**Success Criteria**:
- [ ] Environment variables documented
- [ ] Settings vary appropriately by environment
- [ ] No hardcoded secrets in code

#### Task 5.5: Observability Setup
**Files to Update**:
- `app/main.py` - Add metrics endpoint (optional)
- `app/logging_config.py` - Production logging configuration

**Observability Features**:
- Structured JSON logging in production
- Request ID tracing
- Performance metrics
- Error tracking

**Success Criteria**:
- [ ] Logs are structured and parseable
- [ ] Health check endpoint is robust
- [ ] Metrics endpoint available (if implemented)

### Documentation to Create/Update

#### New Documentation Files
1. **`docs/deployment.md`** - Comprehensive deployment guide
   - Docker deployment
   - docker-compose deployment
   - k3s deployment
   - Secret management
   - Troubleshooting deployment issues

2. **`docs/operations.md`** - Operations runbook
   - Starting/stopping services
   - Viewing logs
   - Health monitoring
   - Scaling considerations
   - Backup and recovery (if applicable)

#### Updates to Existing Files
- **README.md**: Update deployment instructions
- **Claude.md**: Document deployment decisions

### Testing Requirements

#### Deployment Tests
- Build Docker image successfully
- Run container and verify health
- Deploy to k3s and verify accessibility
- Test with ngrok tunnel
- Send test webhook and verify processing

**Success Criteria**:
- [ ] All deployment methods tested
- [ ] Services accessible as expected
- [ ] Webhooks process correctly in deployed environment

### Success Criteria

- [ ] Docker image builds and runs correctly
- [ ] docker-compose setup works for development
- [ ] k3s deployment successful
- [ ] Environment configuration is complete
- [ ] Observability features functional
- [ ] Deployment documentation complete
- [ ] Manual deployment testing successful

### Estimated Effort

- Docker and docker-compose: 4-5 hours
- Kubernetes manifests: 3-4 hours
- Testing and troubleshooting: 4-5 hours
- Documentation: 3-4 hours
- **Total**: 14-18 hours (2-3 days)

---

## Phase 6: Storage and History

**Status**: 🔜 Future Phase
**Duration**: 3-4 days
**Goal**: Add persistent storage for analysis results

### Objectives

1. Choose database (SQLite for POC, PostgreSQL for production)
2. Implement database models and schema
3. Store analysis results
4. Query and retrieve historical analyses
5. Add analysis history endpoint to API

### Key Features

- Store all analysis reports
- Query by repository, PR number, date range
- Historical trend analysis
- Analysis comparison over time

### Documentation Required

- Database schema documentation
- API endpoints for querying history
- Migration guide (if schema changes)

### Estimated Effort: 20-25 hours (3-4 days)

---

## Phase 7: UI and Notifications

**Status**: 🔜 Future Phase
**Duration**: 5-7 days
**Goal**: Add user-facing features (dashboard, notifications)

### Objectives

1. Build simple web dashboard for viewing results
2. Add Slack/Discord notification integration
3. Post analysis summaries as GitHub PR comments
4. Email notifications (optional)

### Key Features

- Dashboard showing recent analyses
- Drill-down into specific PRs
- Notification configuration per repository
- GitHub PR comment integration

### Documentation Required

- Dashboard user guide
- Notification setup guide
- GitHub App setup (for PR comments)

### Estimated Effort: 35-45 hours (5-7 days)

---

## Phase 8: Advanced Features

**Status**: 🔜 Future Phase
**Duration**: Variable
**Goal**: Advanced capabilities and optimizations

### Possible Features

1. Multi-repository support with per-repo configuration
2. Custom test selection rules
3. Integration with test execution platforms (pytest, coverage.py)
4. Automatic test generation (experimental)
5. Performance optimizations and caching
6. Advanced analytics and reporting

### Documentation Required

- Feature-specific guides
- Configuration reference
- API updates

### Estimated Effort: Variable based on features selected

---

## Documentation Maintenance Strategy

### Documentation as Code

1. **Documentation Lives with Code**
   - All docs in `docs/` directory
   - Version controlled alongside code
   - Updated in the same PRs as code changes

2. **Documentation Review in PRs**
   - Every feature PR must include documentation updates
   - Documentation changes are part of "Definition of Done"
   - Reviewers check for documentation completeness

3. **Automated Documentation Checks**
   - Pre-commit hooks check for missing docstrings
   - CI checks for broken links in documentation
   - Spell-check on documentation files

### Documentation Types and Ownership

| Documentation Type | Location | Updated When | Owner |
|-------------------|----------|--------------|-------|
| API Docs | `docs/api.md` | New endpoints, schema changes | Backend developers |
| Agent Docs | `docs/agents.md` | Agent changes, prompt updates | AI/ML developers |
| Architecture | `docs/architecture.md` | Design changes, new components | Tech lead |
| Deployment | `docs/deployment.md` | Infrastructure changes | DevOps/Infrastructure |
| Testing | `docs/testing.md` | Test strategy changes | QA/Test engineers |
| Troubleshooting | `docs/troubleshooting.md` | New issues discovered | All developers |
| README | `README.md` | Major feature additions | Project maintainer |
| Claude Context | `Claude.md` | Standards, patterns change | Tech lead |

### Documentation Update Workflow

1. **Before Implementation**
   - Review existing documentation
   - Identify what needs updating
   - Create outline for new sections

2. **During Implementation**
   - Update code comments and docstrings
   - Draft documentation changes
   - Add examples and diagrams as needed

3. **In Pull Request**
   - Include documentation changes in same PR
   - Link documentation changes in PR description
   - Request documentation review

4. **After Merge**
   - Verify documentation builds correctly
   - Check links are working
   - Update changelog if applicable

### Documentation Quality Standards

1. **Completeness**
   - All public APIs documented
   - All configuration options explained
   - All deployment scenarios covered
   - Troubleshooting for common issues

2. **Clarity**
   - Use simple, direct language
   - Include examples and code snippets
   - Add diagrams for complex concepts
   - Define technical terms

3. **Accuracy**
   - Documentation matches code behavior
   - Examples are tested and working
   - Configuration values are correct
   - Links are valid

4. **Maintainability**
   - Documentation is DRY (Don't Repeat Yourself)
   - Use links to reference other docs
   - Keep sections focused and modular
   - Use templates for consistency

### Scheduled Documentation Reviews

1. **Weekly** (during active development)
   - Review documentation PRs
   - Update changelog
   - Fix reported issues

2. **Monthly**
   - Review all documentation for accuracy
   - Update outdated screenshots/examples
   - Check and fix broken links
   - Review and update troubleshooting guide

3. **Quarterly**
   - Complete documentation audit
   - Restructure if needed
   - Update architecture diagrams
   - Review and update Claude.md

### Documentation Templates

#### New Feature Documentation Template
```markdown
## Feature Name

### Overview
Brief description of what the feature does and why it exists.

### Configuration
List of configuration options and environment variables.

### Usage
Step-by-step guide with examples.

### API Reference
Endpoints, request/response formats (if applicable).

### Troubleshooting
Common issues and solutions.

### Related Documentation
Links to related docs.
```

#### API Endpoint Documentation Template
```markdown
### POST /endpoint/path

**Description**: What this endpoint does

**Authentication**: Required authentication

**Request**:
```json
{
  "field": "value"
}
```

**Response**:
```json
{
  "result": "value"
}
```

**Errors**:
- 400: Bad Request - Invalid input
- 401: Unauthorized - Missing/invalid auth

**Example**:
```bash
curl -X POST http://localhost:8000/endpoint/path \
  -H "Content-Type: application/json" \
  -d '{"field":"value"}'
```
```

### Documentation Tools

1. **Markdown Linting**: `markdownlint` for consistent formatting
2. **Link Checking**: `markdown-link-check` to find broken links
3. **Spell Checking**: `codespell` for catching typos
4. **Diagram Tool**: Mermaid for architecture diagrams
5. **API Docs**: FastAPI auto-generated docs for API reference

### Pre-commit Hook for Documentation

```yaml
# .pre-commit-config.yaml addition
- repo: https://github.com/markdownlint/markdownlint
  rev: v0.12.0
  hooks:
    - id: markdownlint
      args: [--fix]
      files: \.(md)$

- repo: local
  hooks:
    - id: check-docstrings
      name: Check docstrings
      entry: python scripts/check_docstrings.py
      language: system
      pass_filenames: false
```

---

## Success Criteria

### Phase-Level Success Criteria

Each phase is considered complete when:

1. **All tasks are completed** and deliverables are done
2. **All tests pass** with required coverage
3. **Code quality gates pass** (linting, typing, security)
4. **Documentation is complete** and reviewed
5. **Manual testing** has been performed successfully
6. **Code review** has been completed and approved

### Project-Level Success Criteria

The entire project is considered successful when:

1. **Phases 1-5 are complete** (POC is fully functional)
2. **System processes GitHub webhooks** end-to-end successfully
3. **AI agents analyze PRs** and generate useful insights
4. **Test coverage is >90%** overall
5. **Security testing passes** with no critical issues
6. **Deployment works** on Docker, docker-compose, and k3s
7. **Documentation is comprehensive** and up-to-date
8. **Real-world testing** with missing-table repository succeeds

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code Coverage | >90% | pytest --cov |
| Type Coverage | 100% | mypy strict mode |
| Security Issues | 0 critical, 0 high | bandit |
| Documentation Coverage | 100% public APIs | docstring checker |
| Test Pass Rate | 100% | pytest |
| Performance | <200ms webhook, <30s analysis | performance tests |
| Deployment Success | 100% | manual testing |

---

## Risk Management

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM API failures | High | Medium | Implement retries, fallbacks, graceful degradation |
| GitHub API rate limits | Medium | Medium | Implement caching, use GitHub App if needed |
| Agent hallucinations | Medium | Medium | Validate outputs against schemas, add confidence scores |
| Performance issues | Medium | Low | Performance testing in Phase 4, optimize as needed |
| Security vulnerabilities | High | Low | Security-first design, testing, regular audits |

### Schedule Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Phase overruns | Medium | Medium | Buffer time in estimates, prioritize ruthlessly |
| Scope creep | Medium | Medium | Strict phase boundaries, document future work separately |
| Testing takes longer | Low | Medium | Allocate sufficient time, start testing early |
| Documentation backlog | Medium | Low | Document as you go, enforce in PRs |

---

## Appendix

### Useful Commands Reference

```bash
# Development
uv sync                            # Sync all dependencies from lockfile
uv add package-name                # Add a dependency
uv add --dev package-name          # Add a dev dependency
uv run uvicorn app.main:app --reload  # Run development server
uv run pre-commit run --all-files  # Run all pre-commit hooks

# Testing
pytest tests/                      # Run all tests
pytest tests/unit/                 # Run unit tests only
pytest --cov=app --cov=agents      # Run with coverage
pytest -v -s                       # Verbose output with prints

# Code Quality
ruff check .                       # Lint code
ruff format .                      # Format code
mypy .                             # Type check
bandit -r app agents models        # Security scan

# Docker
docker build -t quality-agent:latest .                    # Build image
docker run -p 8000:8000 --env-file .env quality-agent    # Run container
docker-compose up --build                                 # Build and run with compose

# Kubernetes
kubectl apply -f deployment/k8s/                      # Deploy to k3s
kubectl get pods -l app=quality-agent                 # Check pod status
kubectl logs -f deployment/quality-agent              # View logs
kubectl delete -f deployment/k8s/                     # Remove deployment

# ngrok
ngrok http 8000                                       # Expose local server
```

### Phase Checklist Template

Use this checklist at the end of each phase:

- [ ] All tasks completed
- [ ] All tests passing
- [ ] Code coverage meets target
- [ ] Code quality gates pass
- [ ] Documentation complete
- [ ] Manual testing successful
- [ ] Code reviewed and approved
- [ ] Changes merged to main
- [ ] Phase retrospective completed
- [ ] Next phase planning done

---

**END OF IMPLEMENTATION PLAN**

*This is a living document. Update as the project evolves.*
