# Configuration Reference

> Complete reference for all configuration options

**Status**: 🚧 To be completed in Phase 1

## Configuration Management

Quality Agent uses environment variables for configuration, managed by Pydantic Settings.

## Configuration File Locations

- Development: `.env` in project root
- Production: Kubernetes secrets or cloud provider secret management
- Template: `.env.example`

## Configuration Categories

### GitHub Configuration
- Webhook authentication
- API access tokens

### AI Configuration
- Anthropic API keys
- Model selection
- Agent parameters

### Application Configuration
- Server settings
- Logging configuration
- Environment-specific settings

See [Environment Variables](environment-variables.md) for complete list.

## Environment-Specific Configuration

### Development
- Verbose logging
- Hot reload enabled
- Mock external services (optional)

### Staging
- Production-like configuration
- Debug logging
- Real external services

### Production
- Optimized for performance
- INFO level logging
- Security hardened
- Resource limits enforced

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
