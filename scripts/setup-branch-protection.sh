#!/bin/bash
# Setup branch protection for main branch
# This script configures GitHub branch protection rules for solo development

set -e  # Exit on error

echo "🔒 Setting up branch protection for 'main' branch..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

# Get repository info
REPO_OWNER=$(gh repo view --json owner -q '.owner.login')
REPO_NAME=$(gh repo view --json name -q '.name')

echo "📦 Repository: $REPO_OWNER/$REPO_NAME"

# Check if main branch exists on remote
if ! gh api repos/$REPO_OWNER/$REPO_NAME/branches/main &> /dev/null; then
    echo "❌ Error: 'main' branch does not exist on GitHub yet"
    echo ""
    echo "Please commit and push your changes first:"
    echo "  git add ."
    echo "  git commit -m 'chore: initial Phase 0 setup'"
    echo "  git push -u origin main"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Main branch found on GitHub"
echo ""
echo "⚙️  Configuring branch protection rules..."

# Set up branch protection using JSON input
# Note: For personal repos, enforce_admins=false allows repo owner to bypass if needed
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO_OWNER/$REPO_NAME/branches/main/protection \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF

echo "✅ Branch protection configured!"
echo ""
echo "📋 Protection rules applied:"
echo "   ✅ Pull requests required (1 approval)"
echo "   ✅ Admins (you) can bypass if needed for emergencies"
echo "   ✅ Status checks required (when configured)"
echo "   ✅ Conversation resolution required"
echo "   ✅ Linear history enforced (squash/rebase only)"
echo "   ✅ Force pushes blocked"
echo ""
echo "💡 Note: As repo owner, you CAN approve your own PRs!"
echo "   GitHub allows this for personal repositories."
echo ""
echo "🎉 Main branch is now protected!"
echo ""
echo "Next steps:"
echo "  1. Create a feature branch: git checkout -b feature/my-feature"
echo "  2. Make changes and commit"
echo "  3. Push and create PR: gh pr create --fill"
echo "  4. Approve and merge: gh pr review --approve && gh pr merge --squash"
echo ""
echo "See docs/guides/git-workflow.md for detailed workflow."
