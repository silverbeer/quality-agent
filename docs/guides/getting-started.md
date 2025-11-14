# Getting Started with Quality Agent

> Quick start guide to get Quality Agent up and running

**Status**: 🚧 To be completed in Phase 1

## Overview

This guide will walk you through:
1. Installing dependencies
2. Configuring the application
3. Running the service locally
4. Setting up GitHub webhooks
5. Testing with your first PR

## Prerequisites

- Python 3.13.x (not 3.14+ - ecosystem compatibility)
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Docker (optional, for containerized deployment)
- ngrok (for webhook testing)

## Installation

Detailed installation instructions will be added in Phase 1.

```bash
# Clone the repository
git clone https://github.com/yourusername/quality-agent.git
cd quality-agent

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and sync dependencies
uv venv
source .venv/bin/activate  # Or use: uv run <command>
uv sync                    # Install all dependencies from lockfile

# Install pre-commit hooks
uv run pre-commit install
```

> **Modern Python**: This project uses uv exclusively. NO pip, NO requirements.txt. See [Claude.md](../../Claude.md#modern-python-tooling---no-pip-policy).

## Configuration

See [Environment Variables](../reference/environment-variables.md) for detailed configuration options.

## Running the Service

Instructions will be added in Phase 2.

## Setting Up GitHub Webhooks

Instructions will be added in Phase 2.

## Next Steps

- [Development Guide](development.md) - Learn about the development workflow
- [API Reference](api.md) - Explore the API endpoints
- [Testing Guide](testing.md) - Understand the testing approach

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
