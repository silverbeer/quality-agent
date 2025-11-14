# GitHub Webhook Setup Guide

> Complete guide to configuring GitHub webhooks for Quality Agent

**Status**: ✅ Complete

## Overview

Quality Agent receives GitHub webhook events when pull requests are opened, updated, or closed. This guide walks you through setting up webhooks for your repository.

## Prerequisites

- Repository admin access on GitHub
- ngrok installed (for local development)
- Quality Agent running locally or deployed

## Part 1: Generate Webhook Secret

The webhook secret is used to verify that webhook requests actually come from GitHub (HMAC signature verification).

### Generate a Secure Secret

```bash
# Generate a random 32-byte hex string
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Example output:**
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### Save the Secret

**For local development:**

Add to your `.env` file:
```bash
GITHUB_WEBHOOK_SECRET=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**For production (k3s):**

Create/update Kubernetes secret:
```bash
kubectl create secret generic quality-agent-secrets \
  --from-literal=github-webhook-secret=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456 \
  --dry-run=client -o yaml | kubectl apply -f -
```

⚠️ **Important**: Keep this secret secure! Never commit it to git or share it publicly.

## Part 2: Set Up ngrok (Local Development Only)

For local development, you need to expose your local server to the internet so GitHub can send webhooks to it.

### Token Confusion Warning ⚠️

This part uses an **ngrok authtoken** which is completely different from the **GitHub webhook secret**:

| Token Type | Purpose | Where to Get It | Example Format |
|------------|---------|-----------------|----------------|
| **GitHub Webhook Secret** | Verify webhooks from GitHub | You generate it with Python | `a1b2c3d4e5f6...` (64 hex chars) |
| **ngrok Authtoken** | Authenticate with ngrok service | ngrok dashboard after signup | `2abc123DEF456ghi...` (longer, mixed case) |

**Common mistake**: Using the GitHub webhook secret as the ngrok authtoken (won't work!).

### Install ngrok

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

### Authenticate ngrok (first time only)

⚠️ **Important**: The ngrok authtoken is **different** from the GitHub webhook secret you generated in Part 1. Do not confuse them!

**Step 1: Sign up for ngrok** (if you haven't already)

Visit https://ngrok.com/ and create a free account.

**Step 2: Get your ngrok authtoken**

After signing up, you'll be redirected to the dashboard, or visit:
```
https://dashboard.ngrok.com/get-started/your-authtoken
```

You'll see a page titled "Your Authtoken" with a token displayed like:
```
2abc123DEF456ghi789JKL_0mnoPQRstu123VWXyz456ABCdefGHI
```

**Step 3: Configure ngrok with your authtoken**

Copy the authtoken from the dashboard and run:
```bash
# Replace with YOUR actual ngrok authtoken from the dashboard
ngrok config add-authtoken 2abc123DEF456ghi789JKL_0mnoPQRstu123VWXyz456ABCdefGHI
```

You should see:
```
Authtoken saved to configuration file: /Users/yourusername/.config/ngrok/ngrok.yml
```

This only needs to be done once per machine.

### Start ngrok Tunnel

```bash
# In a separate terminal, start ngrok
ngrok http 8000
```

**You'll see output like:**
```
Session Status                online
Account                       your-email@example.com
Forwarding                    https://abc123def456.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123def456.ngrok-free.app`) - you'll need this for GitHub webhook configuration.

⚠️ **Note**:
- Keep ngrok running while testing webhooks
- The URL changes each time you restart ngrok (unless you have a paid plan)
- Free tier has rate limits but works fine for development

## Part 3: Configure Webhook on GitHub

### Step 1: Navigate to Repository Settings

1. Go to your repository on GitHub: `https://github.com/silverbeer/quality-agent`
2. Click **Settings** (top tab)
3. In the left sidebar, click **Webhooks**
4. Click **Add webhook**

### Step 2: Configure Webhook Settings

Fill in the webhook configuration form:

#### Payload URL

**For local development:**
```
https://abc123def456.ngrok-free.app/webhook/github
```
(Replace with your actual ngrok URL)

**For production:**
```
https://your-production-domain.com/webhook/github
```

#### Content type

Select: **`application/json`**

This ensures GitHub sends JSON payloads (not form-encoded).

#### Secret

Paste the webhook secret you generated in Part 1:
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

#### SSL verification

**Enable SSL verification** (recommended)

For local ngrok, this works automatically since ngrok provides valid SSL certificates.

#### Which events would you like to trigger this webhook?

Select: **"Let me select individual events"**

Then check ONLY:
- ✅ **Pull requests**

Uncheck all other events (we only care about PR events for now).

#### Active

✅ Check **"Active"** to enable the webhook immediately

### Step 3: Add Webhook

Click **Add webhook**

GitHub will:
1. Save the webhook configuration
2. Send a test `ping` event to verify connectivity
3. Show delivery status

## Part 4: Verify Webhook Setup

### Check Webhook Status

After adding the webhook:

1. You'll be redirected to the webhook details page
2. Scroll down to **Recent Deliveries**
3. You should see a `ping` event
4. Click on the ping event to see details

**Successful ping delivery:**
- ✓ Green checkmark
- Response code: `200`
- Response body: `{"status":"accepted"}` (once webhook endpoint is implemented)

**Failed ping delivery:**
- ✗ Red X
- Check the error message and response details

### Common Issues with Ping

**Connection refused / timeout:**
- Verify ngrok is running
- Verify Quality Agent is running (`uv run uvicorn app.main:app`)
- Check ngrok URL is correct

**404 Not Found:**
- Webhook endpoint not implemented yet (this is OK during Phase 1)
- Will work once Phase 2 is complete

**401 Unauthorized:**
- Signature verification failed
- Check `GITHUB_WEBHOOK_SECRET` in `.env` matches the secret in GitHub

## Part 5: Test with a Real Pull Request

Once your webhook is configured and Phase 2 is complete:

### Create a Test PR

```bash
# Create a test branch
git checkout -b test/webhook-test

# Make a small change
echo "# Test PR" >> TEST.md
git add TEST.md
git commit -m "test: webhook test"

# Push and create PR
git push -u origin test/webhook-test
gh pr create --title "Test: Webhook Integration" --body "Testing webhook delivery"
```

### Verify Webhook Delivery

1. Go to GitHub → Repository Settings → Webhooks
2. Click on your webhook
3. Scroll to **Recent Deliveries**
4. Find the `pull_request` event with action `opened`
5. Click to view details

**Check the delivery:**
- **Request** tab: See the payload GitHub sent
- **Response** tab: See Quality Agent's response
- Response code should be `200`
- Response body should confirm processing started

### Check Application Logs

In your Quality Agent terminal, you should see:
```
webhook_received event="pull_request" action="opened" pr_number=123
processing_webhook pr_number=123
pr_analysis_complete pr_number=123 gaps_found=5
```

## Part 6: Webhook Events Reference

Quality Agent responds to these pull request events:

### `opened`
- Triggered when a PR is first created
- **Action**: Analyze the PR for test coverage gaps

### `synchronize`
- Triggered when new commits are pushed to an existing PR
- **Action**: Re-analyze the PR with updated changes

### `closed`
- Triggered when a PR is closed (merged or not)
- **Action**: Optional cleanup or final analysis

### Event Payload Example

When a PR is opened, GitHub sends:

```json
{
  "action": "opened",
  "number": 123,
  "pull_request": {
    "id": 1,
    "number": 123,
    "title": "Add new feature",
    "state": "open",
    "user": {
      "login": "silverbeer"
    },
    "head": {
      "ref": "feature/new-feature",
      "sha": "abc123"
    },
    "base": {
      "ref": "main",
      "sha": "def456"
    }
  },
  "repository": {
    "id": 1,
    "name": "quality-agent",
    "full_name": "silverbeer/quality-agent"
  }
}
```

## Webhook Security

Quality Agent uses **HMAC SHA-256** signature verification to ensure webhooks are authentic.

### How It Works

1. GitHub signs the payload with your secret: `HMAC-SHA256(payload, secret)`
2. GitHub sends signature in header: `X-Hub-Signature-256: sha256=...`
3. Quality Agent recomputes the signature
4. If signatures match → authentic webhook ✅
5. If signatures don't match → reject with 401 ❌

### Testing Signature Verification

You can't easily fake webhooks because you need the secret to generate valid signatures. This protects against:
- Unauthorized API calls
- Replay attacks
- Man-in-the-middle attacks

## Production Deployment

### Update Webhook URL

When you deploy to production:

1. Go to GitHub → Repository Settings → Webhooks
2. Click on your webhook
3. Update **Payload URL** to your production domain:
   ```
   https://quality-agent.yourdomain.com/webhook/github
   ```
4. Click **Update webhook**

### Monitor Webhook Health

GitHub provides delivery monitoring:

- **Recent Deliveries**: Last 30 days of deliveries
- **Response codes**: Track success/failure rates
- **Delivery timing**: See latency
- **Redelivery**: Manually redeliver failed webhooks

### Webhook Best Practices

1. **Always verify signatures** - Never trust unverified webhooks
2. **Return 200 quickly** - Process async, respond fast (<5s)
3. **Handle retries** - GitHub retries failed deliveries
4. **Log all webhooks** - For debugging and monitoring
5. **Idempotency** - Handle duplicate deliveries gracefully

## Troubleshooting

### Webhook Deliveries Failing

**Check:**
1. Is Quality Agent running?
   ```bash
   curl http://localhost:8000/health
   ```

2. Is ngrok running? (local dev)
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/health
   ```

3. Check application logs for errors

4. Verify webhook secret matches in both places

### Signature Verification Failing

**Error**: `401 Unauthorized - Invalid signature`

**Solutions:**
1. Regenerate webhook secret:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `.env` file with new secret
3. Update GitHub webhook configuration with same secret
4. Restart Quality Agent

### No Webhook Deliveries

**Check:**
1. Is webhook **Active**? (GitHub settings)
2. Did you select **Pull requests** event?
3. Check **Recent Deliveries** for errors

### ngrok URL Changed

Free ngrok URLs change on restart.

**Solution:**
1. Start ngrok: `ngrok http 8000`
2. Copy new URL
3. Update GitHub webhook URL
4. Test with a new PR

**Better solution**: Get ngrok paid plan for static URLs

## Multiple Repositories

To analyze multiple repositories:

1. **Same webhook secret** (recommended):
   - Use the same secret for all repos
   - Configure webhook in each repository
   - Quality Agent handles all repos

2. **Different secrets** (advanced):
   - Implement per-repo secret lookup in Phase 6
   - More complex configuration management

## Webhook Monitoring Dashboard

Once deployed, you can monitor webhooks via:

1. **GitHub**: Settings → Webhooks → Recent Deliveries
2. **Quality Agent Logs**: Structured logs with `webhook_received` events
3. **Metrics** (Phase 5+): Prometheus metrics for webhook volume/latency

## Next Steps

After webhook setup:

1. **Phase 2**: Implement webhook receiver and signature verification
2. **Phase 3**: Add CrewAI agents for analysis
3. **Test**: Create PRs and verify analysis works
4. **Monitor**: Track webhook deliveries and fix any issues

## Summary

✅ **Setup checklist:**
- [ ] Generate webhook secret
- [ ] Add secret to `.env` / Kubernetes
- [ ] Start ngrok (local dev)
- [ ] Configure webhook on GitHub
- [ ] Verify ping delivery succeeds
- [ ] Test with a real PR (after Phase 2)
- [ ] Monitor deliveries for issues

---

**References:**
- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)
- [HMAC Signature Verification](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)

**Last Updated**: 2025-11-14
**Phase**: Phase 1 (Ready for Phase 2 webhook implementation)
