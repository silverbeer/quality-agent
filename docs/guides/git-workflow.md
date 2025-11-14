# Git Workflow

> Branch protection and PR workflow for quality-agent

**Status**: ✅ Complete

## Overview

This project uses **branch protection** even for solo development to maintain code quality and enforce best practices. The `main` branch is protected and all changes must go through pull requests.

## Initial Setup

### First-Time Setup: Push to GitHub and Enable Protection

Before branch protection can be enabled, you need to push your first commit to GitHub:

```bash
# 1. Ensure you're on main branch
git checkout main

# 2. Stage all Phase 0 files
git add .

# 3. Commit Phase 0 setup
git commit -m "chore: Phase 0 setup - documentation and tooling

- Modern Python 3.13.x with uv tooling
- Comprehensive documentation structure
- Pre-commit hooks (ruff, mypy, bandit)
- Project configuration and dependencies
- Git workflow and branch protection docs"

# 4. Push to GitHub
git push -u origin main

# 5. Enable branch protection (automated script)
./scripts/setup-branch-protection.sh
```

The script will configure:
- ✅ Pull requests required (1 approval)
- ✅ Self-approval allowed (solo dev bypass)
- ✅ Status checks required (when CI is set up)
- ✅ Conversation resolution required
- ✅ Linear history enforced
- ✅ Force pushes blocked

**After this initial setup, all future changes must go through pull requests!**

## Branch Protection Rules

The `main` branch has the following protections:

✅ **Pull requests required** - No direct commits to main
✅ **Status checks required** - Pre-commit hooks and tests must pass
✅ **Self-approval allowed** - Solo developer can approve own PRs
✅ **Conversation resolution** - All PR comments must be resolved
✅ **Linear history** - Squash or rebase merges only

## Why Branch Protection for Solo Development?

Even as a solo developer, branch protection provides:

1. **Quality Gates**: Ensures tests and checks always run
2. **Code Review Mindset**: Forces you to review your own changes
3. **Clean History**: Squash merging keeps git log readable
4. **Documentation**: PRs document why changes were made
5. **Rollback Safety**: Easy to revert a merged PR
6. **Future-Proof**: Ready for team collaboration when it happens

## Workflow

### 1. Create a Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/webhook-receiver

# Or for fixes
git checkout -b fix/signature-verification

# Or for docs
git checkout -b docs/update-architecture
```

**Branch naming conventions**:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates
- `chore/description` - Maintenance tasks

### 2. Make Changes and Commit

```bash
# Make your changes
# ...

# Stage and commit (pre-commit hooks will run automatically)
git add .
git commit -m "feat: add webhook signature verification"

# If pre-commit hooks fail, fix issues and try again
git add .
git commit -m "feat: add webhook signature verification"
```

**Commit message format** (Conventional Commits):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes (formatting)
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

### 3. Push and Create Pull Request

```bash
# Push to remote
git push -u origin feature/webhook-receiver

# Create PR using GitHub CLI (recommended)
gh pr create --title "feat: add webhook signature verification" \
  --body "Implements HMAC SHA-256 signature verification for GitHub webhooks.

## Changes
- Added security.py with verify_github_signature()
- Added tests for signature verification
- Updated webhook_receiver.py to use verification

## Testing
- Unit tests: test_security.py
- Manual test: Sent test webhook from GitHub

## Checklist
- [x] Tests pass
- [x] Pre-commit hooks pass
- [x] Documentation updated
- [x] Coverage maintained"

# Or use --fill to auto-populate from commits
gh pr create --fill

# Or create via web interface
# GitHub will prompt you to create PR after pushing
```

### 4. Wait for Status Checks

GitHub will automatically run status checks (once CI is set up in Phase 5):
- Pre-commit hooks (ruff, mypy, bandit)
- Test suite (pytest)
- Coverage check (80% minimum)

**If checks fail**:
```bash
# Fix the issues locally
# ...

# Commit and push fixes
git add .
git commit -m "fix: address test failures"
git push

# Checks will re-run automatically
```

### 5. Review Your Own PR

Even though you wrote the code, review it with fresh eyes:

**What to look for**:
- [ ] Does the code do what the PR says?
- [ ] Are there any obvious bugs or issues?
- [ ] Is the code well-documented?
- [ ] Are tests comprehensive?
- [ ] Is the documentation updated?
- [ ] Does this align with project goals?

**Add comments** on your own PR if you notice:
- TODOs for future work
- Technical debt introduced
- Areas that need improvement
- Questions for later review

### 6. Approve Your Own PR

```bash
# Approve the PR (yes, you can approve your own!)
gh pr review --approve

# Or approve via web interface:
# Go to PR → Files changed → Review changes → Approve
```

### 7. Merge the PR

Once approved and all checks pass:

```bash
# Squash merge (recommended - keeps clean history)
gh pr merge --squash --delete-branch

# Or rebase merge (preserves individual commits)
gh pr merge --rebase --delete-branch

# Or regular merge (creates merge commit)
gh pr merge --merge --delete-branch
```

**Recommended**: Use `--squash` for most PRs to keep `main` history clean.

### 8. Pull Latest Main

```bash
# Switch back to main
git checkout main

# Pull the merged changes
git pull

# Your feature branch is automatically deleted
# You're ready to start the next feature!
```

## Quick Reference

### Complete Workflow (One Command Flow)

```bash
# Start feature
git checkout -b feature/new-thing

# Work and commit
git add . && git commit -m "feat: add new thing"

# Push and create PR
git push -u origin feature/new-thing
gh pr create --fill

# After checks pass, approve and merge
gh pr review --approve
gh pr merge --squash --delete-branch

# Back to main
git checkout main && git pull
```

### Useful GitHub CLI Commands

```bash
# List PRs
gh pr list

# View PR status
gh pr status

# View PR details
gh pr view 123

# Check PR checks
gh pr checks

# View PR diff
gh pr diff

# Checkout a PR locally
gh pr checkout 123

# Add reviewers (when team grows)
gh pr review --approve --body "LGTM!"

# Re-run failed checks
gh pr checks --watch

# Close PR without merging
gh pr close 123
```

## Hotfixes and Urgent Changes

For critical production fixes that can't wait for full PR process:

```bash
# You can bypass PR requirement if needed (configured in branch protection)
git checkout main
git pull

# Make urgent fix
git checkout -b hotfix/critical-security-issue
# ... make changes ...
git add . && git commit -m "fix!: patch critical security vulnerability"
git push -u origin hotfix/critical-security-issue

# Create PR with BREAKING CHANGE note
gh pr create --title "fix!: patch critical security vulnerability" \
  --body "BREAKING CHANGE: Critical security patch

This hotfix addresses CVE-XXXX-XXXX immediately."

# If truly urgent and you have bypass permissions:
gh pr review --approve
gh pr merge --squash --delete-branch
```

**Note**: Bypassing is granted to repo owner but should be used sparingly!

## Tips and Best Practices

### Writing Good PR Descriptions

Include:
1. **What** changed (summary)
2. **Why** it changed (motivation)
3. **How** to test it
4. **Checklist** of completed items

Example template:
```markdown
## Summary
Brief description of changes

## Motivation
Why this change is needed

## Changes Made
- Bullet list of key changes
- Keep it focused

## Testing
How to test these changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] No breaking changes (or documented)
```

### Keeping PRs Small

- **One feature per PR** - easier to review and rollback
- **Target < 400 lines changed** - large PRs are hard to review
- **Break large features** into multiple PRs
- **Use draft PRs** for work-in-progress

### Draft PRs

For work in progress:

```bash
# Create draft PR
gh pr create --draft --title "WIP: add webhook receiver"

# Mark ready for review when done
gh pr ready
```

### Handling Conflicts

If main has changed while you're working:

```bash
# Update your branch with latest main
git checkout feature/your-branch
git fetch origin
git rebase origin/main

# Resolve conflicts if any
# ...

# Force push (safe on feature branch)
git push --force-with-lease
```

## GitHub CLI Setup

If you haven't set up GitHub CLI:

```bash
# Install gh (macOS)
brew install gh

# Or download from https://cli.github.com/

# Authenticate
gh auth login

# Follow prompts to authenticate with GitHub
```

## Troubleshooting

### "You cannot approve your own PR"

**Solution**: Ensure you're added as a "bypass actor" in branch protection settings, or use the web interface which may have different permissions.

### Checks failing on PR

**Solution**:
```bash
# Run checks locally first
uv run pre-commit run --all-files
uv run pytest

# Fix issues and push again
```

### Can't push to main

**Solution**: This is expected! Create a feature branch:
```bash
git checkout -b feature/my-changes
git push -u origin feature/my-changes
```

### Forgot to create branch

**Solution**:
```bash
# If you made commits on main but haven't pushed:
git branch feature/my-changes  # Create branch from current state
git reset --hard origin/main   # Reset main to remote
git checkout feature/my-changes # Switch to feature branch
# Now push and create PR
```

## CI/CD Integration (Phase 5)

Once we set up GitHub Actions (Phase 5), the workflow will include:

- **Automated testing** on every PR
- **Coverage reports** posted as comments
- **Security scans** (bandit, safety)
- **Deployment previews** (if applicable)
- **Automatic changelog** generation

## Summary

Branch protection + PR workflow = **Quality by default**

Even as a solo developer, this workflow:
- ✅ Catches bugs before they reach main
- ✅ Documents your development process
- ✅ Keeps git history clean and readable
- ✅ Builds good habits for team collaboration
- ✅ Makes it easy to understand changes months later

**The small overhead of creating PRs pays huge dividends in code quality!**

---

**Last Updated**: 2025-11-14
**Phase**: Phase 0 - Setup Complete
