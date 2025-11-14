# Contributing to Quality Agent

Thank you for your interest in contributing to Quality Agent! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.13.x (note: 3.14+ not yet supported due to dependency compatibility)
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Basic understanding of FastAPI and async Python

### Setting Up Development Environment

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/yourusername/quality-agent.git
   cd quality-agent
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create virtual environment and sync dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync                    # Install all dependencies from lockfile
   ```

4. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

> **Important**: This project uses **modern uv tooling only**. We do NOT use pip, requirements.txt, or pip-style workflows. See [Claude.md](./Claude.md#modern-python-tooling---no-pip-policy) for complete guidelines.

5. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Edit .env and add your actual configuration values
   ```

6. **Verify setup**:
   ```bash
   pytest tests/
   pre-commit run --all-files
   ```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Making Changes

1. **Create a new branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes**:
   - Write code following our [coding standards](#coding-standards)
   - Add or update tests
   - Update documentation

3. **Run tests and quality checks**:
   ```bash
   pytest tests/
   pre-commit run --all-files
   ```

4. **Commit your changes** using conventional commits:
   ```bash
   git commit -m "feat: add webhook signature verification"
   ```

   Commit message format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Adding or updating tests
   - `refactor:` - Code refactoring
   - `style:` - Code style changes (formatting, etc.)
   - `chore:` - Maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Open a pull request** on GitHub

## Coding Standards

### Python Style

- **PEP 8** compliance (enforced by ruff)
- **Type hints** on all functions and methods
- **Docstrings** using Google style for all public APIs
- **Max line length**: 100 characters

### Code Quality Tools

All checks are enforced via pre-commit hooks:

- **ruff** - Linting and formatting
- **mypy** - Static type checking (strict mode)
- **bandit** - Security vulnerability scanning

### Example

```python
from pydantic import BaseModel, Field

def calculate_impact_score(lines_changed: int, complexity: float) -> float:
    """
    Calculate the impact score for a code change.

    Args:
        lines_changed: Number of lines changed in the file
        complexity: Cyclomatic complexity of the change (0.0-1.0)

    Returns:
        Impact score between 0.0 and 1.0

    Raises:
        ValueError: If complexity is not between 0.0 and 1.0
    """
    if not 0.0 <= complexity <= 1.0:
        raise ValueError("Complexity must be between 0.0 and 1.0")

    return min(1.0, (lines_changed / 100) * complexity)
```

## Testing Requirements

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Target**: 90%+ coverage
- **Security-critical code**: 100% coverage

### Writing Tests

1. **Use pytest** for all tests
2. **Use async test patterns** for async code
3. **Mock external dependencies** (GitHub API, LLM calls)
4. **Follow AAA pattern** (Arrange, Act, Assert)

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock

class TestWebhookReceiver:
    """Test suite for webhook receiver."""

    async def test_valid_signature_accepted(self, client, valid_payload):
        """Test that webhooks with valid signatures are accepted."""
        # Arrange
        headers = {"X-Hub-Signature-256": "sha256=valid_signature"}

        # Act
        response = await client.post(
            "/webhook/github",
            json=valid_payload,
            headers=headers
        )

        # Assert
        assert response.status_code == 200
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov=agents --cov-report=html

# Run specific test file
pytest tests/unit/test_webhook_receiver.py

# Run tests matching a pattern
pytest -k "test_signature"

# Run tests in parallel
pytest -n auto
```

## Documentation

### Documentation Requirements

1. **Code Documentation**:
   - Docstrings for all public functions, classes, and modules
   - Inline comments for complex logic
   - Type hints for all parameters and return values

2. **User Documentation**:
   - Update relevant guides in `docs/guides/`
   - Update reference docs in `docs/reference/`
   - Update README.md if adding major features

3. **Architecture Decisions**:
   - Create ADR in `docs/planning/decisions/` for significant decisions
   - Use the template in `docs/planning/decisions/template.md`

### Documentation Standards

- Use clear, concise language
- Include code examples where appropriate
- Add diagrams for complex concepts (use Mermaid)
- Keep documentation close to code (update docs in same PR)

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code coverage maintained or improved
- [ ] Pre-commit hooks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

### Pull Request Checklist

1. **Title**: Use conventional commit format
   - Example: `feat: add webhook signature verification`

2. **Description**: Include:
   - What changes were made and why
   - How to test the changes
   - Screenshots (if UI changes)
   - Related issues (if any)

3. **Labels**: Add appropriate labels
   - `bug` - Bug fix
   - `enhancement` - New feature
   - `documentation` - Documentation update
   - `dependencies` - Dependency update

4. **Reviews**:
   - At least one approval required
   - Address all review comments
   - Keep PR focused and reasonably sized

### PR Template

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change needed? What problem does it solve?

## How Has This Been Tested?
Describe the tests you ran

## Types of Changes
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have added tests to cover my changes
- [ ] All new and existing tests passed
- [ ] I have updated the documentation accordingly
- [ ] I have added an entry to CHANGELOG.md (if applicable)
```

## Getting Help

### Resources

- **Documentation**: [docs/README.md](./docs/README.md)
- **Development Guide**: [docs/guides/development.md](./docs/guides/development.md)
- **Architecture**: [docs/reference/architecture.md](./docs/reference/architecture.md)
- **Claude Context**: [Claude.md](./Claude.md)

### Communication

- **Issues**: [GitHub Issues](https://github.com/yourusername/quality-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/quality-agent/discussions)

### Asking Questions

When asking for help:
1. Check existing documentation first
2. Search existing issues
3. Provide context and details:
   - What you're trying to do
   - What you've tried
   - Error messages or unexpected behavior
   - Your environment (OS, Python version, etc.)

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- CHANGELOG.md for significant contributions
- Project README for major contributions

## License

By contributing to Quality Agent, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Quality Agent! Your efforts help make this project better for everyone.
