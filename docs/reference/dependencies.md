# Dependencies Reference

> Project dependencies and version requirements

**Status**: ✅ Complete

## Python Version

**Required**: Python 3.13.x

**Note**: Python 3.14+ is not yet supported due to ecosystem compatibility. Many dependencies (including `onnxruntime` from CrewAI) don't have wheels for Python 3.14 yet. We'll upgrade to 3.14 when the ecosystem catches up.

**Version Constraint**: `requires-python = ">=3.13,<3.14"` in `pyproject.toml`

## Core Dependencies

### Web Framework
- **fastapi** (>=0.104.0) - Modern async web framework
- **uvicorn[standard]** (>=0.24.0) - ASGI server

### Data Validation
- **pydantic** (>=2.5.0) - Data validation and settings management
- **pydantic-settings** (>=2.1.0) - Settings management

### AI & Agent Orchestration
- **crewai** (>=0.1.0) - AI agent orchestration framework
- **crewai-tools** (>=0.1.0) - Tools for CrewAI agents

### HTTP Client
- **httpx** (>=0.25.0) - Async HTTP client

### GitHub Integration
- **PyGithub** (>=2.1.0) - GitHub API client

### Logging
- **structlog** (>=23.2.0) - Structured logging
- **python-json-logger** (>=2.0.0) - JSON log formatting

### Environment Management
- **python-dotenv** (>=1.0.0) - Environment variable management

## Development Dependencies

### Testing
- **pytest** (>=7.4.0) - Testing framework
- **pytest-asyncio** (>=0.21.0) - Async test support
- **pytest-cov** (>=4.1.0) - Coverage reporting
- **pytest-mock** (>=3.12.0) - Mocking support
- **pytest-xdist** (>=3.5.0) - Parallel test execution
- **pytest-timeout** (>=2.2.0) - Test timeouts

### Code Quality
- **ruff** (>=0.1.9) - Fast Python linter and formatter
- **mypy** (>=1.7.0) - Static type checker
- **bandit** (>=1.7.5) - Security vulnerability scanner

### Development Tools
- **pre-commit** (>=3.5.0) - Git pre-commit hooks
- **ipython** (>=8.17.0) - Enhanced Python shell
- **ipdb** (>=0.13.0) - IPython debugger

### Documentation
- **mkdocs** (>=1.5.0) - Documentation generator
- **mkdocs-material** (>=9.4.0) - Material theme for MkDocs

## Complete Dependency List

See [pyproject.toml](../../pyproject.toml) for the complete dependency specification.

## Managing Dependencies

### Adding Dependencies

```bash
# Add a runtime dependency
uv add fastapi

# Add a dev dependency
uv add --dev pytest

# Add with version constraint
uv add "fastapi>=0.104.0"
```

### Removing Dependencies

```bash
uv remove package-name
```

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Sync environment after updates
uv sync

# Update pre-commit hooks
uv run pre-commit autoupdate
```

### Viewing Dependencies

```bash
# Show dependency tree
uv tree

# List installed packages
uv pip list
```

## Modern Tooling

This project uses **uv exclusively**. We do NOT use:
- ❌ pip
- ❌ requirements.txt
- ❌ setup.py
- ❌ Pipfile

All dependencies are managed through:
- ✅ `pyproject.toml` - Dependency specifications
- ✅ `uv.lock` - Locked versions (MUST be committed to git)

See [Claude.md](../../Claude.md#modern-python-tooling---no-pip-policy) for the complete modern Python tooling policy.

## Dependency Security

- Run `bandit` to check for known vulnerabilities
- Regularly update dependencies
- Monitor security advisories for dependencies

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0
