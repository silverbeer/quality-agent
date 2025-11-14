# Scripts

Utility scripts for quality-agent project.

## setup-branch-protection.sh

Sets up GitHub branch protection rules for the `main` branch.

### Usage

```bash
./scripts/setup-branch-protection.sh
```

### Prerequisites

1. **GitHub CLI installed**: `brew install gh`
2. **Authenticated with GitHub**: `gh auth login`
3. **Main branch exists on GitHub**: Must push at least one commit first

### What It Does

Configures the following branch protection rules on `main`:

- ✅ Requires pull requests before merging (1 approval)
- ✅ Allows you (repo owner) to bypass PR requirement
- ✅ Requires status checks to pass (when configured)
- ✅ Requires conversation resolution before merging
- ✅ Enforces linear history (squash/rebase only)
- ✅ Blocks force pushes to main
- ✅ Blocks branch deletion

### When to Run

**Run once** after your first push to GitHub:

```bash
# First, push your initial commit
git add .
git commit -m "chore: Phase 0 setup"
git push -u origin main

# Then enable branch protection
./scripts/setup-branch-protection.sh
```

### Troubleshooting

**Error: "Branch not found"**
- Solution: Push to main branch first: `git push -u origin main`

**Error: "gh command not found"**
- Solution: Install GitHub CLI: `brew install gh`

**Error: "Not authenticated"**
- Solution: Authenticate: `gh auth login`

### Manual Setup

Prefer to set up via web interface? Visit:

`https://github.com/your-username/quality-agent/settings/branches`

And configure the branch protection rules manually.

---

See [docs/guides/git-workflow.md](../docs/guides/git-workflow.md) for complete workflow documentation.
