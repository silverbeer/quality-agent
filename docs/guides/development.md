# Development Guide

> Development workflow, coding standards, and best practices

**Status**: 🚧 To be completed in Phase 1

## Development Workflow

### Setting Up Development Environment

Instructions will be added in Phase 1.

### Running the Development Server

```bash
# Run with hot reload (using uv run)
uv run uvicorn app.main:app --reload --port 8000

# Or activate venv first
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Modern Dependency Management

This project uses **uv exclusively** - NO pip, NO requirements.txt.

```bash
# Add a new dependency
uv add package-name              # Updates pyproject.toml AND uv.lock

# Add a dev dependency
uv add --dev pytest-plugin       # Adds to dev dependencies

# Remove a dependency
uv remove package-name           # Updates pyproject.toml and uv.lock

# Sync environment (after git pull, branch switch)
uv sync                          # Ensures exact match with uv.lock

# Update dependencies
uv lock                          # After manual pyproject.toml edits
```

See [Claude.md](../../Claude.md#modern-python-tooling---no-pip-policy) for complete modern Python tooling guidelines.

### Code Quality Tools

All code quality checks are enforced via pre-commit hooks:

```bash
# Run all checks
pre-commit run --all-files

# Run specific checks
pre-commit run ruff --all-files
pre-commit run mypy --all-files
pre-commit run bandit --all-files
```

## Coding Standards

- **Style**: Follow PEP 8, enforced by ruff
- **Type Hints**: Required for all functions (checked by mypy --strict)
- **Docstrings**: Required for all public APIs (Google style)
- **Line Length**: 100 characters maximum

See [Claude.md](../../Claude.md#code-standards) for complete coding standards.

## Git Workflow

This project uses **branch protection** on `main` with a PR-based workflow, even for solo development.

**Key Points**:
- ✅ All changes via pull requests
- ✅ Self-approval allowed (solo dev)
- ✅ Status checks must pass
- ✅ Clean, linear history

**See**: [Complete Git Workflow Guide](git-workflow.md) for detailed instructions.

### Quick Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add . && git commit -m "feat: add my feature"

# Push and create PR
git push -u origin feature/my-feature
gh pr create --fill

# After checks pass
gh pr review --approve
gh pr merge --squash --delete-branch

# Back to main
git checkout main && git pull
```

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Messages
Follow conventional commits format:
- `feat: add webhook signature verification`
- `fix: handle missing PR files gracefully`
- `docs: update agent architecture diagram`
- `test: add coverage tests for TestPlannerAgent`

## Testing

See [Testing Guide](testing.md) for comprehensive testing information.

## Documentation

All feature PRs must include documentation updates. See [Documentation Standards](../../Claude.md#documentation-standards).

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
