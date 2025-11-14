# Environment Variables Reference

> Complete reference for all environment variables

**Status**: ✅ Complete

See [.env.example](../../.env.example) for a complete, documented template.

## Required Variables

### GITHUB_WEBHOOK_SECRET
**Type**: String (hex)
**Required**: Yes
**Description**: Secret for verifying GitHub webhook signatures (HMAC SHA-256)

**How to generate**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Security**: Must match the secret configured in GitHub webhook settings

---

### GITHUB_TOKEN
**Type**: String (GitHub personal access token)
**Required**: Yes
**Description**: GitHub API access token for fetching PR information

**How to create**: https://github.com/settings/tokens

**Required scopes**:
- `repo` (for private repositories)
- `public_repo` (for public repositories only)

---

### ANTHROPIC_API_KEY
**Type**: String (API key)
**Required**: Yes
**Description**: Anthropic API key for Claude (used by CrewAI agents)

**How to get**: https://console.anthropic.com/

---

## Optional Variables

### PORT
**Type**: Integer
**Default**: 8000
**Description**: Server port number

---

### LOG_LEVEL
**Type**: String (enum)
**Default**: INFO
**Options**: DEBUG, INFO, WARNING, ERROR, CRITICAL
**Description**: Logging verbosity level

---

### ENVIRONMENT
**Type**: String
**Default**: development
**Options**: development, staging, production
**Description**: Environment name (affects logging format and behaviors)

---

## Future Variables

Additional environment variables will be documented as features are added in later phases.

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0
