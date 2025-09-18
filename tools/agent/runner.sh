#!/usr/bin/env bash
# Minimal helper for human-guided agent branches. Creates an agent branch,
# runs pytest, and reminds the operator to stage receipts before opening a PR.
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to read AGENT_MANIFEST.json" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
MANIFEST_PATH="$ROOT/AGENT_MANIFEST.json"
if [[ ! -f "$MANIFEST_PATH" ]]; then
  echo "AGENT_MANIFEST.json not found. Copy AGENT_MANIFEST.example.json and fill it in first." >&2
  exit 1
fi

AGENT_ID="$(jq -r '.agent_id // empty' "$MANIFEST_PATH")"
if [[ -z "$AGENT_ID" || "$AGENT_ID" == "null" ]]; then
  echo "agent_id missing in AGENT_MANIFEST.json" >&2
  exit 1
fi

BRANCH_PREFIX="$(jq -r '.branch_prefix // empty' "$MANIFEST_PATH")"
if [[ -z "$BRANCH_PREFIX" || "$BRANCH_PREFIX" == "null" ]]; then
  BRANCH_PREFIX="agent/${AGENT_ID}"
fi

SUFFIX="${1:-proposal-$(date -u +%Y%m%d%H%M%S)}"
BRANCH_NAME="${BRANCH_PREFIX}/${SUFFIX}"

echo "→ creating branch $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

echo "→ install project in editable mode (if not already)"
pip install -e "$ROOT" >/dev/null

if command -v pytest >/dev/null 2>&1; then
  echo "→ running pytest -q"
  pytest -q || {
    echo "Tests failed. Fix before pushing." >&2
    exit 1
  }
else
  echo "pytest not available; skipping test run" >&2
fi

echo "→ ready for edits. When finished:"
echo "   git add <files>"
echo "   git commit -m 'agent: <summary>'"
echo "   git push origin $BRANCH_NAME"
echo "   gh pr create --draft --fill (optional)"

echo "Run tools/agent/preflight.sh before opening the PR to validate receipts and plans."

echo "Remember to attach plan receipts and update _plans/<id>.plan.json before opening the PR."
