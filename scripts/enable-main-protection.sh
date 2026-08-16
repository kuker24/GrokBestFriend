#!/usr/bin/env bash
# Create a GitHub ruleset that requires CI before main updates.
# Not run by install.sh. Needs repo admin.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is not installed. Run: sudo apt install gh && gh auth login" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not logged in. Run: gh auth login" >&2
  exit 1
fi

repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
payload='{
  "name": "main-ci",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "test" }
        ]
      }
    }
  ]
}'

echo "Creating ruleset on $repo (require CI job test, no force-push, PR required, branch up to date)"
if ! gh api --method POST "repos/$repo/rulesets" --input - <<<"$payload"; then
  echo "Failed. You need admin on $repo. Create the ruleset in the GitHub UI instead." >&2
  exit 1
fi
echo "ruleset created"
