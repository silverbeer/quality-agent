# Quality Agent Documentation

Welcome to the Quality Agent documentation! This guide will help you navigate all project documentation.

## Quick Start

New to Quality Agent? Start here:
- [Getting Started Guide](guides/getting-started.md) - Installation and setup
- [Project README](../README.md) - Project overview and quick start

## For Developers

### Development Guides
- [Development Guide](guides/development.md) - Development workflow and best practices
- [Git Workflow](guides/git-workflow.md) - Branch protection and PR workflow for solo developers
- [GitHub Webhook Setup](guides/github-webhook-setup.md) - Configure webhooks for PR events
- [Testing Guide](guides/testing.md) - Testing strategy, running tests, and coverage
- [Deployment Guide](guides/deployment.md) - Deploying to Docker, docker-compose, and k3s
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions

### Architecture & Design
- [Architecture Overview](reference/architecture.md) - System design and components
- [Agent Architecture](guides/agents.md) - AI agent design, prompts, and workflows
- [Security](reference/security.md) - Security design and best practices

### API Documentation
- [API Reference](guides/api.md) - REST API endpoints and schemas
- [Webhook Integration](guides/api.md#webhook-endpoint) - GitHub webhook setup

## Planning & Roadmap

### Implementation Plan
- [Complete Implementation Plan](planning/implementation-plan.md) - Phased implementation (8 phases)
  - Phase 0: Planning and Setup (Current)
  - Phase 1: Foundation and Core Infrastructure
  - Phase 2: Webhook Receiver and Security
  - Phase 3: CrewAI Agents Implementation
  - Phase 4: Integration and Testing
  - Phase 5: Deployment and Operations
  - Phase 6-8: Future enhancements

### Architecture Decisions
- [Decision Records](planning/decisions/) - Architecture Decision Records (ADRs)
- [ADR Template](planning/decisions/template.md) - Template for new decisions

## Reference

### Configuration & Setup
- [Configuration Reference](reference/configuration.md) - All configuration options
- [Environment Variables](reference/environment-variables.md) - Required and optional variables
- [Dependencies](reference/dependencies.md) - Project dependencies and versions

### Context Files
- [Claude Context](../Claude.md) - Complete project context for AI assistants (root level)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) in the root directory for:
- Code style guidelines
- Git workflow
- Pull request process
- Documentation standards

## Documentation Structure

Our documentation is organized into three main categories:

### 📋 planning/
Planning documents, implementation roadmaps, and architecture decision records.
- **When to update**: During planning phases and when making architectural decisions
- **Audience**: Development team, project managers

### 📚 guides/
Task-oriented how-to guides for developers and operators.
- **When to update**: As features are implemented or procedures change
- **Audience**: Developers, operators, integrators

### 📖 reference/
Reference material about architecture, configuration, and system design.
- **When to update**: When architecture or configuration changes
- **Audience**: Developers, architects, system administrators

## Documentation Maintenance

### Keeping Documentation Updated

Documentation should be updated alongside code changes:

1. **Before Implementation**: Update planning docs with detailed plans
2. **During Implementation**: Update guides and reference docs as you code
3. **In Pull Requests**: Include documentation updates in the same PR as code
4. **After Merge**: Verify links work and documentation is accurate

### Documentation Standards

- Use clear, concise language
- Include code examples where appropriate
- Add diagrams for complex concepts
- Keep sections focused and modular
- Link to related documentation

See the [Documentation Standards](../Claude.md#documentation-standards) section in Claude.md for detailed guidelines.

## Need Help?

- **Issues**: [GitHub Issues](https://github.com/yourusername/quality-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/quality-agent/discussions)
- **Documentation Issues**: Open an issue with the `documentation` label

---

**Last Updated**: 2025-11-14
**Documentation Version**: 0.1.0
