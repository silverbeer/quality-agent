# Quality Agent - Claude Context File

## Project Overview

**Quality Agent** is an AI-powered webhook receiver service that analyzes GitHub pull requests to identify test coverage gaps and generate intelligent test execution plans. Built with CrewAI agent orchestration, it provides automated quality analysis for the "missing-table" youth soccer league management application.

### Purpose
- Receive GitHub webhook events for PR activities (opened, synchronize, closed)
- Analyze code changes using AI agents to identify test coverage gaps
- Generate intelligent test execution plans based on code changes
- Provide actionable insights to improve code quality and test coverage

### Target Application
The primary target is **missing-table**, a youth soccer league management web app:
- **Frontend**: Vue.js
- **Backend**: FastAPI
- **Database**: Supabase
- **Deployment**: GCP GKE Autopilot (prod), k3s (local)

---

## Architecture

### Technology Stack
- **Framework**: FastAPI (async Python web framework)
- **AI Orchestration**: CrewAI with Claude (Anthropic)
- **Data Models**: Pydantic v2 (type-safe data validation)
- **GitHub Integration**: PyGithub + webhook verification
- **Deployment**: Docker + k3s (local), ngrok for webhook tunneling
- **Package Management**: uv (modern Python package manager)

### Core Components

```
quality-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── webhook_receiver.py  # GitHub webhook endpoint
│   └── config.py            # Configuration management
├── agents/
│   ├── __init__.py
│   ├── code_analyzer.py     # CodeAnalyzerAgent
│   ├── test_coverage.py     # TestCoverageAgent
│   ├── test_planner.py      # TestPlannerAgent
│   └── crew.py              # CrewAI orchestration
├── models/
│   ├── __init__.py
│   ├── github.py            # GitHub webhook payloads
│   ├── analysis.py          # Analysis data models
│   └── reports.py           # Report generation models
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── agents.md
│   └── deployment.md
└── deployment/
    ├── Dockerfile
    ├── docker-compose.yml
    └── k8s/
```

### Agent Architecture

#### 1. CodeAnalyzerAgent
**Role**: Analyze git diffs and identify changed files, functions, and code patterns
**Input**: `GitHubWebhookPayload` with PR information
**Output**: `CodeChange` models with detailed change analysis
**Tools**: Git diff parsing, AST analysis, pattern matching

#### 2. TestCoverageAgent
**Role**: Identify existing tests and coverage gaps based on code changes
**Input**: `CodeChange` models from CodeAnalyzerAgent
**Output**: `TestCoverageGap` models with missing test scenarios
**Tools**: Test file discovery, coverage analysis, dependency mapping

#### 3. TestPlannerAgent
**Role**: Create intelligent, prioritized test execution plans
**Input**: `TestCoverageGap` models from TestCoverageAgent
**Output**: `TestExecutionPlan` with recommended tests and priorities
**Tools**: Risk assessment, test prioritization, execution planning

### Data Flow

```
GitHub PR Event
    ↓
Webhook Receiver (signature verification)
    ↓
Parse webhook payload → GitHubWebhookPayload
    ↓
CrewAI Orchestration
    ↓
CodeAnalyzerAgent → CodeChange[]
    ↓
TestCoverageAgent → TestCoverageGap[]
    ↓
TestPlannerAgent → TestExecutionPlan
    ↓
Generate AnalysisReport
    ↓
Store/Return results
```

---

## Modern Python Tooling - NO PIP POLICY

**CRITICAL**: This project uses **modern Python tooling with uv**. We do NOT use pip, requirements.txt, or pip-style workflows.

### Python Version: 3.13.x

We target **Python 3.13.x specifically** (`requires-python = ">=3.13,<3.14"`):
- ✅ Modern Python features and performance
- ✅ Full ecosystem compatibility (all major packages have wheels)
- ❌ Python 3.14+ not yet supported (waiting for ecosystem to catch up)

**Why not 3.14?** Many dependencies (like `onnxruntime` from CrewAI) don't yet have wheels for Python 3.14. We'll upgrade when the ecosystem is ready.

### Package Management: uv Only

**Use uv commands exclusively**:
```bash
# ✅ CORRECT - Modern uv commands
uv sync                          # Install/sync all dependencies (replaces pip install)
uv add package-name              # Add a dependency (replaces pip install package-name)
uv add --dev package-name        # Add a dev dependency
uv remove package-name           # Remove a dependency
uv lock                          # Update lockfile after manual pyproject.toml edits
uv tree                          # Show dependency tree

# ❌ NEVER USE - Legacy pip commands
pip install -e ".[dev]"          # DEPRECATED - use uv sync
pip install package-name         # DEPRECATED - use uv add
pip freeze > requirements.txt    # DEPRECATED - use uv.lock
pip install -r requirements.txt  # DEPRECATED - use uv sync
```

### Modern Workflow

1. **Initial setup**:
   ```bash
   uv venv                    # Create virtual environment
   source .venv/bin/activate  # Activate (or use uv run)
   uv sync                    # Install all dependencies from lockfile
   ```

2. **Add a new dependency**:
   ```bash
   uv add fastapi             # Automatically updates pyproject.toml AND uv.lock
   ```

3. **Add a dev dependency**:
   ```bash
   uv add --dev pytest        # Adds to [project.optional-dependencies.dev]
   ```

4. **Remove a dependency**:
   ```bash
   uv remove package-name     # Updates pyproject.toml and uv.lock
   ```

5. **Sync environment** (after git pull, branch switch, etc.):
   ```bash
   uv sync                    # Ensures your env matches uv.lock exactly
   ```

6. **Run commands** (without activating venv):
   ```bash
   uv run pytest              # Runs pytest in project's venv
   uv run uvicorn app.main:app --reload
   ```

### Lockfile Management

- **`uv.lock`**: MUST be committed to git (ensures reproducible builds)
- Automatically updated by `uv add`, `uv remove`, `uv sync`
- Manually update: `uv lock` (after editing pyproject.toml directly)
- Never edit `uv.lock` manually

### Why uv, Not pip?

1. **10-100x faster** than pip
2. **Lockfile-based** - reproducible builds across all environments
3. **Modern resolver** - better dependency resolution
4. **Built-in virtual env management** - no need for separate venv/virtualenv
5. **Cargo/npm-style workflow** - industry standard approach
6. **No requirements.txt** - everything in pyproject.toml + uv.lock

### Migration from pip (For Reference Only)

| Legacy (pip) | Modern (uv) |
|-------------|-------------|
| `pip install -e ".[dev]"` | `uv sync` |
| `pip install package` | `uv add package` |
| `pip install package --dev` | `uv add --dev package` |
| `pip uninstall package` | `uv remove package` |
| `pip freeze > requirements.txt` | `uv lock` (creates uv.lock) |
| `pip install -r requirements.txt` | `uv sync` |
| `pip list` | `uv tree` or `uv pip list` |
| `python script.py` | `uv run python script.py` |

### Enforcement

- **Documentation**: Only uv commands in all docs
- **CI/CD**: Use `uv sync` in all pipelines
- **Code Review**: Reject any pip references
- **No requirements.txt**: If someone creates one, reject the PR

---

## Code Standards

### Python Style
- **PEP 8** compliance with modern typing (Python 3.13.x)
- **Type hints** on all functions and class methods
- **Docstrings** using Google style for all public APIs
- **Max line length**: 100 characters
- **Import order**: stdlib → third-party → local (sorted alphabetically)

### Pydantic Models
- Use Pydantic v2 syntax with `ConfigDict`
- Include field descriptions using `Field(description="...")`
- Validate all external inputs at the boundary
- Use strict types where possible
- Example:
  ```python
  from pydantic import BaseModel, Field, ConfigDict

  class CodeChange(BaseModel):
      model_config = ConfigDict(frozen=True, strict=True)

      file_path: str = Field(description="Path to the changed file")
      change_type: Literal["added", "modified", "deleted"] = Field(
          description="Type of change operation"
      )
      lines_changed: int = Field(gt=0, description="Number of lines changed")
  ```

### Async Patterns
- Use `async def` for all I/O-bound operations
- Prefer `httpx.AsyncClient` over synchronous requests
- Use `asyncio.gather()` for concurrent operations
- Handle exceptions at appropriate levels with structured logging

### Error Handling
- Use custom exception classes inheriting from `Exception`
- Log errors with context using structured logging
- Return appropriate HTTP status codes
- Never expose internal errors to external clients

---

## Testing Standards

### Coverage Requirements
- **Minimum**: 80% overall code coverage
- **Target**: 90%+ for critical paths (webhook verification, agent orchestration)
- **100%** for security-critical code (signature verification, input validation)

### Test Structure
```python
# tests/unit/test_webhook_receiver.py
import pytest
from unittest.mock import AsyncMock, patch

class TestWebhookReceiver:
    """Test suite for GitHub webhook receiver."""

    async def test_valid_signature_accepted(self, client, valid_payload):
        """Test that webhooks with valid signatures are accepted."""
        # Arrange
        headers = {"X-Hub-Signature-256": "sha256=..."}

        # Act
        response = await client.post("/webhook/github", json=valid_payload, headers=headers)

        # Assert
        assert response.status_code == 200
```

### Test Categories
1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test agent interactions and API endpoints
3. **Security Tests**: Test webhook verification, input validation
4. **Contract Tests**: Validate Pydantic models match GitHub API schemas

### Fixtures
- Use `pytest` fixtures for common test data
- Store fixtures in `tests/conftest.py` for reuse
- Mock external services (GitHub API, LLM calls) in tests

---

## Security Considerations

### Webhook Security
1. **Signature Verification**: Always verify `X-Hub-Signature-256` header
2. **HMAC Validation**: Use constant-time comparison for HMAC
3. **Rate Limiting**: Implement rate limiting on webhook endpoint
4. **Input Validation**: Validate all webhook payloads against Pydantic models

### Secret Management
- Store secrets in environment variables, never in code
- Use `.env` files locally (never commit `.env` files)
- In k3s: use Kubernetes secrets
- Required secrets:
  - `GITHUB_WEBHOOK_SECRET`: For webhook signature verification
  - `GITHUB_TOKEN`: For GitHub API access (read-only scope)
  - `ANTHROPIC_API_KEY`: For Claude API access

### API Security
- No authentication on webhook endpoint (GitHub signature is sufficient)
- Health check endpoint should be unauthenticated
- Consider adding API key for future admin endpoints

---

## Agent Development Guidelines

### CrewAI Best Practices
1. **Agent Design**: Each agent should have a single, clear responsibility
2. **Model Passing**: Use Pydantic models for all inter-agent communication
3. **Prompt Engineering**: Keep prompts focused and explicit about expected output format
4. **Tool Usage**: Provide agents with specific, purpose-built tools
5. **Error Recovery**: Implement retry logic and graceful degradation

### Agent Prompt Template
```python
CODE_ANALYZER_PROMPT = """
You are a code analysis expert. Your role is to analyze git diffs and identify:
1. Changed files and their types (source code, tests, config)
2. Functions/methods that were added, modified, or deleted
3. Potential impact areas and dependencies

Output Format: Provide a structured list of CodeChange objects.

Focus on actionable insights that will help identify test coverage gaps.
"""
```

### Testing Agents
- Mock LLM calls in tests using `unittest.mock`
- Test agent prompts separately from CrewAI orchestration
- Validate output models against expected schemas
- Test error handling and edge cases

---

## Documentation Standards

### Code Documentation
- **Docstrings**: Required for all public functions, classes, and modules
- **Comments**: Use inline comments for complex logic or non-obvious decisions
- **Type hints**: Required for all function parameters and return values

### Documentation Files
All documentation lives in `docs/` directory with organized structure:

**Planning** (`docs/planning/`):
- `implementation-plan.md`: Phased implementation plan (8 phases)
- `decisions/`: Architecture Decision Records (ADRs)

**Guides** (`docs/guides/`):
- `getting-started.md`: Installation and setup
- `development.md`: Development workflow and best practices
- `testing.md`: Testing strategy and requirements
- `deployment.md`: Deployment procedures
- `api.md`: API endpoints and schemas
- `agents.md`: Agent architecture and prompts
- `troubleshooting.md`: Common issues and solutions

**Reference** (`docs/reference/`):
- `architecture.md`: System design and components
- `security.md`: Security design and best practices
- `configuration.md`: Configuration options
- `environment-variables.md`: Environment variable reference
- `dependencies.md`: Dependencies and versions

**Navigation**: `docs/README.md` provides complete documentation index

### Documentation Maintenance
- **Update docs with code changes**: Documentation PRs should accompany feature PRs
- **Review during PR**: Documentation is part of the definition of done
- **Quarterly reviews**: Schedule documentation audits each quarter
- **Automation**: Use pre-commit hooks to check for missing docstrings

### README Standards
- Keep README concise (< 200 lines)
- Link to detailed docs in `docs/` directory
- Include quick start guide
- Add badges for build status, coverage, version

---

## Development Workflow

### Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and sync dependencies
uv venv
source .venv/bin/activate  # Or use: uv run <command>
uv sync                    # Install all dependencies from lockfile

# Install pre-commit hooks
uv run pre-commit install
```

### Pre-commit Hooks
Quality gates enforced on every commit:
1. **ruff**: Linting and formatting (replaces flake8, black, isort)
2. **mypy**: Static type checking
3. **bandit**: Security vulnerability scanning
4. **pytest**: Run fast unit tests
5. **check-docstrings**: Ensure all public APIs have docstrings

### Git Workflow
- **Branch naming**: `feature/description`, `fix/description`, `docs/description`
- **Commit messages**: Conventional commits format
  - `feat: add webhook signature verification`
  - `fix: handle missing PR files gracefully`
  - `docs: update agent architecture diagram`
  - `test: add coverage tests for TestPlannerAgent`
- **PR requirements**:
  - All tests passing
  - Coverage maintained or improved
  - Documentation updated
  - Pre-commit hooks passing

---

## Configuration Management

### Environment Variables
```bash
# Required
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_TOKEN=ghp_your_github_token
ANTHROPIC_API_KEY=sk-ant-your_key

# Optional
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Configuration Loading
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_webhook_secret: str
    github_token: str
    anthropic_api_key: str
    port: int = 8000
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

---

## Logging Standards

### Structured Logging
Use `structlog` for all logging:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "webhook_received",
    event="pull_request",
    action="opened",
    pr_number=123,
    repository="org/repo"
)
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (webhook received, agent started)
- **WARNING**: Warning messages (rate limit approaching, retry attempted)
- **ERROR**: Error messages that need attention (webhook verification failed)
- **CRITICAL**: Critical errors requiring immediate action

---

## Deployment

### Local Development
```bash
# Run with uvicorn
uvicorn app.main:app --reload --port 8000

# Run with docker-compose
docker-compose up --build

# Expose with ngrok
ngrok http 8000
```

### k3s Deployment
```bash
# Build and load image
docker build -t quality-agent:latest .
docker save quality-agent:latest | sudo k3s ctr images import -

# Apply manifests
kubectl apply -f deployment/k8s/
```

---

## Performance Considerations

### Webhook Processing
- Return 200 OK immediately upon receiving webhook
- Process analysis asynchronously using background tasks
- Use connection pooling for GitHub API calls
- Cache repository metadata when possible

### Agent Optimization
- Limit token usage with focused prompts
- Use streaming for long responses
- Implement timeouts for agent tasks
- Consider caching analysis results by PR commit SHA

---

## Future Enhancements

### Phase 2+ Features
- Database storage for analysis history
- Web UI dashboard for viewing results
- Slack/Discord notifications for analysis completion
- Support for multiple repositories
- Custom test selection rules per repository
- Integration with test execution platforms
- Metrics and observability dashboard

---

## Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [GitHub Webhooks](https://docs.github.com/en/webhooks)

### Internal Docs
- `docs/README.md`: Complete documentation index
- `docs/planning/implementation-plan.md`: Phased implementation plan
- `docs/guides/`: How-to guides for developers and operators
- `docs/reference/`: Reference documentation for architecture and configuration
- `docs/planning/decisions/`: Architecture Decision Records (ADRs)

---

## Questions and Clarifications

When implementing features or making changes:

1. **Is this change security-sensitive?** → Add security tests and update `docs/reference/security.md`
2. **Does this affect agent behavior?** → Update `docs/guides/agents.md`
3. **Is this a new API endpoint?** → Update `docs/guides/api.md`
4. **Does this change configuration?** → Update `.env.example` and `docs/reference/environment-variables.md`
5. **Is this a breaking change?** → Document migration path in relevant docs
6. **Is this an architectural decision?** → Create an ADR in `docs/planning/decisions/`

---

**Last Updated**: 2025-11-14
**Project Status**: Phase 1 - Initial Development
**Maintainer**: Development Team
