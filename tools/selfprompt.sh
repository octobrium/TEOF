#!/usr/bin/env bash
set -euo pipefail

# --- Config / policy ---
POLICY_FILE="policy/selfprompt.json"
if [[ ! -f "$POLICY_FILE" ]]; then
  echo "Policy file missing: $POLICY_FILE" >&2
  echo "Create one (or keep the default) and re-run." >&2
  exit 1
fi

# Parse a couple of knobs (safe if jq missing)
jqget(){ command -v jq >/dev/null 2>&1 && jq -r "$1" "$POLICY_FILE" || echo "$2"; }
MAX_STEPS="$(jqget '.max_steps // 10' 10)"
NO_CAND_LIMIT="$(jqget '.no_candidate_streak // 3' 3)"

# --- Branch + doc seed (docs-only so it can auto-merge under your policy) ---
ts="$(date -u +%Y%m%dT%H%M%SZ)"
branch="selfprompt/${ts}"
doc="docs/selfprompt/${ts}.md"

git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "Run from inside the repo." >&2; exit 1; }

git checkout -b "$branch"
mkdir -p "$(dirname "$doc")"

cat > "$doc" <<MD
# Self-prompt run — $ts (UTC)

Policy snapshot:
\`\`\`json
$(cat "$POLICY_FILE")
\`\`\`

## Loop log

(automation will append iterations here)

MD

git add "$doc"
git commit -m "selfprompt: seed run $ts (docs-only)"
git push -u origin "$branch"

# --- Open PR and label for docs auto-merge (if gh CLI available) ---
if command -v gh >/dev/null 2>&1; then
  url="$(gh pr create --base main --head "$branch" --title "selfprompt: $ts" --body "Automated self-prompt seed (docs-only).")" || true
  # add label if it exists; otherwise print hint
  if gh label list --limit 200 | awk '{print $1}' | grep -qx "auto-merge-docs"; then
    gh pr edit --add-label auto-merge-docs >/dev/null 2>&1 || true
  else
    echo "Label 'auto-merge-docs' not found; add it in the UI if you want docs PRs to auto-merge."
  fi
  echo "PR: ${url:-<open in UI>}"
else
  # Fallback: show a compare link you can click
  remote="$(git remote get-url origin 2>/dev/null || echo '')"
  base="$remote"
  if [[ "$remote" =~ ^git@([^:]+):(.+)\.git$ ]]; then base="https://${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"; fi
  if [[ "$remote" =~ ^https?:// ]]; then base="${remote%.git}"; fi
  echo "Open PR here and label 'auto-merge-docs':"
  echo "  ${base}/compare/main...${branch}?expand=1"
fi

echo "✅ Seeded. Now let your existing guards (verify + pr-failure-handler + autorevert) do their job."
echo "   When the PR is green, it can auto-merge (docs-only)."
