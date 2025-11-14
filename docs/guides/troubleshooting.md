# Troubleshooting Guide

> Common issues and solutions

**Status**: 🚧 To be expanded throughout development

## Common Issues

### Installation Issues

#### uv installation fails
**Solution**: Follow platform-specific installation instructions at https://github.com/astral-sh/uv

### Configuration Issues

#### Environment variables not loading
**Symptoms**: Application fails to start with missing configuration errors

**Solution**:
1. Ensure `.env` file exists in project root
2. Check that required variables are set (see `.env.example`)
3. Verify `.env` file is not in `.gitignore` (it should be!)

### Webhook Issues

#### Webhook signature verification fails
**Symptoms**: 401 Unauthorized responses from webhook endpoint

**Solutions**:
1. Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook settings
2. Check that secret is properly loaded (check logs)
3. Ensure webhook is sent from GitHub (not manually crafted)

#### Webhooks not received
**Solutions**:
1. Check ngrok is running: `ngrok http 8000`
2. Verify ngrok URL is configured in GitHub webhook settings
3. Check GitHub webhook delivery logs
4. Verify firewall allows ngrok connections

### Agent Issues

#### Agent timeouts
**Symptoms**: Analysis takes too long or times out

**Solutions**:
1. Check `ANTHROPIC_API_KEY` is valid
2. Verify internet connectivity
3. Check Anthropic API status
4. Increase `AGENT_TIMEOUT` in `.env`

#### Agent errors
**Solutions**:
1. Check structured logs for error details
2. Verify agent prompts are correctly formatted
3. Check CrewAI configuration

### Testing Issues

#### Tests fail with import errors
**Solution**: Ensure virtual environment is activated and dependencies are synced:
```bash
source .venv/bin/activate
uv sync              # Sync all dependencies from lockfile
```

#### Coverage too low
**Solution**: Write more tests! See [Testing Guide](testing.md).

## Checking Logs

```bash
# View logs with structured output
tail -f logs/quality-agent.log

# In Docker
docker logs -f quality-agent

# In k3s
kubectl logs -f deployment/quality-agent
```

## Getting Help

1. Check this troubleshooting guide
2. Review [documentation](../README.md)
3. Search [GitHub issues](https://github.com/yourusername/quality-agent/issues)
4. Open a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Relevant logs
   - Environment details

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 (Stub)
