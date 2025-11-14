# Quality Agent

> AI-powered GitHub webhook service for automated test coverage analysis and intelligent test planning

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-orange.svg)](https://www.crewai.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Overview

Quality Agent is an intelligent webhook receiver that analyzes GitHub pull requests using AI agents to identify test coverage gaps and generate actionable test execution plans. Built with CrewAI and Claude, it provides automated quality insights for your development workflow.

### Key Features

- **Automated Analysis**: Receives GitHub PR webhooks and analyzes code changes automatically
- **AI-Powered Insights**: Uses CrewAI with Claude to understand code changes and identify test gaps
- **Intelligent Test Planning**: Generates prioritized test execution plans based on risk and impact
- **Production-Ready**: Built with FastAPI, includes comprehensive security, observability, and deployment configs
- **Local-First**: Designed to run locally in k3s with ngrok tunneling for webhook delivery

### Target Application

This service is built to analyze **missing-table**, a youth soccer league management application with:
- Vue.js frontend
- FastAPI backend
- Supabase database
- Deployment on GCP GKE and k3s

## Quick Start

### Prerequisites

- Python 3.13.x (not 3.14+ yet - waiting for ecosystem compatibility)
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose (for containerized deployment)
- k3s (for local Kubernetes deployment)
- [ngrok](https://ngrok.com/) (for webhook tunneling)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/quality-agent.git
cd quality-agent

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and sync dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync                    # Install all dependencies from lockfile

# Install pre-commit hooks
uv run pre-commit install
```

> **Note**: This project uses modern uv tooling. We do NOT use pip or requirements.txt. See [Claude.md](./Claude.md#modern-python-tooling---no-pip-policy) for details.

### Configuration

Create a `.env` file in the project root:

```bash
# Required - GitHub webhook secret (set in GitHub webhook settings)
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Required - GitHub personal access token (read-only permissions)
GITHUB_TOKEN=ghp_your_github_token_here

# Required - Anthropic API key for Claude
ANTHROPIC_API_KEY=sk-ant-your_api_key_here

# Optional - Application configuration
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Running the Service

#### Local Development

```bash
# Run with uvicorn (hot reload enabled)
uvicorn app.main:app --reload --port 8000

# The service will be available at http://localhost:8000
# Health check: http://localhost:8000/health
```

#### With Docker Compose

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### With k3s

```bash
# Build the Docker image
docker build -t quality-agent:latest .

# Load image into k3s
docker save quality-agent:latest | sudo k3s ctr images import -

# Create secret for environment variables
kubectl create secret generic quality-agent-secrets \
  --from-literal=github-webhook-secret=$GITHUB_WEBHOOK_SECRET \
  --from-literal=github-token=$GITHUB_TOKEN \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY

# Deploy to k3s
kubectl apply -f deployment/k8s/

# Check deployment status
kubectl get pods -l app=quality-agent
kubectl logs -f deployment/quality-agent
```

### Setting Up GitHub Webhooks

Quality Agent receives webhooks from GitHub when PRs are created, updated, or closed.

**Quick Setup:**

1. **Generate webhook secret**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   # Add to .env: GITHUB_WEBHOOK_SECRET=<generated-secret>
   ```

2. **Start ngrok** (local dev):
   ```bash
   ngrok http 8000
   # Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
   ```

3. **Configure webhook on GitHub**:
   - Go to repository **Settings → Webhooks → Add webhook**
   - **Payload URL**: `https://abc123.ngrok-free.app/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Paste the generated secret
   - **Events**: Select "Pull requests" only
   - Click **Add webhook**

4. **Verify**: Check "Recent Deliveries" shows green checkmark

**Complete guide**: See [GitHub Webhook Setup](./docs/guides/github-webhook-setup.md) for detailed instructions, troubleshooting, and production setup.

## Architecture

Quality Agent consists of three AI agents orchestrated by CrewAI:

```
GitHub PR Event
    ↓
Webhook Receiver (signature verification)
    ↓
CrewAI Orchestration
    ↓
┌─────────────────────────────────────────┐
│  1. CodeAnalyzerAgent                   │
│     Analyzes git diffs and identifies   │
│     changed files, functions, patterns  │
│     Output: CodeChange[]                │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│  2. TestCoverageAgent                   │
│     Identifies existing tests and       │
│     coverage gaps based on changes      │
│     Output: TestCoverageGap[]           │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│  3. TestPlannerAgent                    │
│     Creates intelligent, prioritized    │
│     test execution plans                │
│     Output: TestExecutionPlan           │
└────────────┬────────────────────────────┘
             ↓
      AnalysisReport
```

### Tech Stack

- **FastAPI**: Async web framework for webhook receiver
- **CrewAI**: AI agent orchestration framework
- **Claude (Anthropic)**: LLM for agent reasoning
- **Pydantic**: Type-safe data validation and models
- **PyGithub**: GitHub API interactions
- **Docker**: Containerization
- **k3s**: Lightweight Kubernetes for local deployment

See [Claude.md](./Claude.md) for detailed architecture documentation.

## Project Structure

```
quality-agent/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── webhook_receiver.py # GitHub webhook endpoint
│   └── config.py          # Configuration management
├── agents/                 # CrewAI agents
│   ├── code_analyzer.py   # Code analysis agent
│   ├── test_coverage.py   # Test coverage agent
│   ├── test_planner.py    # Test planning agent
│   └── crew.py            # Agent orchestration
├── models/                 # Pydantic models
│   ├── github.py          # GitHub webhook payloads
│   ├── analysis.py        # Analysis data structures
│   └── reports.py         # Report models
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Pytest fixtures
├── docs/                   # Documentation
│   ├── architecture.md    # System architecture
│   ├── api.md             # API documentation
│   ├── agents.md          # Agent specifications
│   ├── deployment.md      # Deployment guide
│   └── testing.md         # Testing guide
├── deployment/             # Deployment configurations
│   ├── Dockerfile         # Docker image definition
│   ├── docker-compose.yml # Local development setup
│   └── k8s/               # Kubernetes manifests
├── .env.example            # Environment variables template
├── pyproject.toml          # Project dependencies
├── Claude.md               # Project context for Claude
└── README.md               # This file
```

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov=agents --cov-report=html

# Run specific test categories
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only

# Run tests with verbose output
pytest -v

# View coverage report
open htmlcov/index.html
```

### Code Quality

Pre-commit hooks automatically run on every commit:

```bash
# Manually run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files      # Linting and formatting
pre-commit run mypy --all-files      # Type checking
pre-commit run bandit --all-files    # Security scanning
```

### Code Standards

- **Linting**: Ruff (replaces flake8, black, isort)
- **Type Checking**: mypy with strict mode
- **Security**: Bandit for vulnerability scanning
- **Test Coverage**: Minimum 80%, target 90%+
- **Documentation**: Google-style docstrings for all public APIs

See [Claude.md](./Claude.md) for detailed development guidelines.

## API Documentation

Once the service is running, visit:

- **Interactive API docs**: http://localhost:8000/docs
- **Alternative API docs**: http://localhost:8000/redoc

### Endpoints

- `POST /webhook/github` - GitHub webhook receiver (signature verified)
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics (optional)

See [docs/api.md](./docs/api.md) for detailed API documentation.

## Security

### Webhook Security

- **HMAC Signature Verification**: All webhooks are verified using SHA-256 HMAC
- **Constant-Time Comparison**: Prevents timing attacks
- **Input Validation**: All payloads validated against Pydantic models
- **Rate Limiting**: Prevents abuse (implemented in future phases)

### Secret Management

- Environment variables for all secrets
- Never commit `.env` files or secrets to git
- Use Kubernetes secrets in production
- Rotate keys regularly

See [docs/deployment.md](./docs/deployment.md#security) for security best practices.

## Monitoring and Observability

### Logging

Structured JSON logging using `structlog`:

```python
logger.info(
    "webhook_received",
    event="pull_request",
    action="opened",
    pr_number=123
)
```

### Health Checks

```bash
curl http://localhost:8000/health
```

### Metrics

Prometheus-compatible metrics endpoint (optional):

```bash
curl http://localhost:8000/metrics
```

## Troubleshooting

### Common Issues

**Webhook signature verification fails**
- Ensure `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub webhook settings
- Check that the secret is being loaded correctly (check logs)

**Agent errors or timeouts**
- Verify `ANTHROPIC_API_KEY` is valid and has sufficient credits
- Check agent prompts and token limits
- Review structured logs for specific error messages

**GitHub API rate limiting**
- Ensure `GITHUB_TOKEN` is set and valid
- Check rate limit status in logs
- Consider implementing caching for repository metadata

**ngrok connection issues**
- Verify ngrok is running and URL matches GitHub webhook configuration
- Check ngrok dashboard for webhook delivery attempts
- Ensure your firewall allows ngrok connections

See [docs/troubleshooting.md](./docs/troubleshooting.md) for more details.

## Documentation

Complete documentation is available in the [`docs/`](./docs/) directory:

- [**Documentation Index**](./docs/README.md) - Navigation for all documentation
- [**Claude.md**](./Claude.md) - Complete project context and guidelines for AI assistants
- [**Implementation Plan**](./docs/planning/implementation-plan.md) - Detailed 8-phase implementation plan

### Quick Links

- [Getting Started](./docs/guides/getting-started.md) - Setup and installation
- [Development Guide](./docs/guides/development.md) - Development workflow
- [Testing Guide](./docs/guides/testing.md) - Testing strategy and coverage
- [Deployment Guide](./docs/guides/deployment.md) - Docker, k3s, and production deployment
- [API Reference](./docs/guides/api.md) - REST API and webhooks
- [Agent Architecture](./docs/guides/agents.md) - AI agent design and prompts
- [Troubleshooting](./docs/guides/troubleshooting.md) - Common issues and solutions

### Reference

- [Architecture Overview](./docs/reference/architecture.md) - System design and components
- [Security](./docs/reference/security.md) - Security design and best practices
- [Configuration](./docs/reference/configuration.md) - Configuration options
- [Environment Variables](./docs/reference/environment-variables.md) - Required and optional variables

## Roadmap

### Phase 1: POC (Current)
- GitHub webhook receiver with signature verification
- Three-agent CrewAI pipeline (analyzer, coverage, planner)
- Basic analysis report generation
- Docker and k3s deployment

### Phase 2: Storage and History
- Database integration for analysis history
- Analysis result storage and retrieval
- Historical trend analysis

### Phase 3: UI and Notifications
- Web dashboard for viewing analysis results
- Slack/Discord notifications
- GitHub PR comments with analysis summaries

### Phase 4: Multi-Repository Support
- Support for multiple target repositories
- Custom configuration per repository
- Repository-specific test selection rules

See [docs/planning/implementation-plan.md](./docs/planning/implementation-plan.md) for detailed phased implementation.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using conventional commits
4. Ensure all tests pass and coverage is maintained
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a pull request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed contribution guidelines.

## License

[MIT License](./LICENSE) - see LICENSE file for details

## Acknowledgments

- Built with [CrewAI](https://www.crewai.com/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Created for the [missing-table](https://github.com/yourusername/missing-table) project

## Support

- **Documentation**: See [docs/](./docs/) directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/quality-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/quality-agent/discussions)

---

**Built with AI-powered quality in mind**
