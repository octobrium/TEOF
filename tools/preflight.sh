#!/usr/bin/env bash
# TEOF preflight + ship helper (with cleanup)
# - check   : non-destructive sanity checks
# - ship    : PR in one command (docs=automerge, ci=review)
# - cleanup : delete merged PR’s branch locally & on origin

set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  tools/preflight.sh check
  tools/preflight.sh ship (--docs|--ci) -m "<title>" [--watch] [--cleanup]
  tools/preflight.sh cleanup --pr <url|number>

Notes:
  --cleanup with 'ship' removes the PR branch after it's MERGED.
  'cleanup --pr' works for any already-merged PR (manual or auto).
USAGE
}

require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1"; exit 127; }; }

repo_nwo() {
  if gh repo view --json nameWithOwner -q .nameWithOwner >/dev/null 2>&1; then
    gh repo view --json nameWithOwner -q .nameWithOwner
  else
    git remote -v | awk '/origin.*(git@|https:)/{print $2; exit}' \
      | sed -E 's#(git@github\.com:|https://github\.com/)##; s#\.git$##'
  fi
}

capsule_pointer() {
  git fetch origin --prune >/dev/null 2>&1 || true
  printf "capsule/current -> "
  git show origin/main:capsule/current 2>/dev/null | tr -d '\n' || printf "N/A"
  echo
}

ensure_labels() {
  gh label create "auto-merge-docs" \
    --color "2ea043" --description "Docs-only: allow auto-merge when checks pass" >/dev/null 2>&1 || true
}

json_field() {
  printf '%s\n' "$1" | python3 - "$2" <<'PY'
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    print("")
else:
    print(data.get(sys.argv[1], ""))
PY
}

git_dirty() { git status --porcelain=v1 | grep -q .; }
fail() { echo "ERROR: $*" >&2; exit 1; }

cmd_check() {
  require git; require gh
  echo "== Preflight: repo = $(repo_nwo)"
  echo "git: $(git --version | awk '{print $3}')" ; echo "gh:  $(gh --version | head -1 | awk '{print $3}')"
  echo "== Auth"; gh auth status
  echo "== Branch"; echo "Current: $(git rev-parse --abbrev-ref HEAD)"; capsule_pointer
  echo "== Workflows"; ls -1 .github/workflows/teof-*.yml 2>/dev/null || echo "(no teof workflows found)"
  test -f tools/doctor.sh && echo "Found tools/doctor.sh" || echo "(no doctor.sh)"
  echo "== Labels (ensure, idempotent)"; ensure_labels; echo "OK"
}

cleanup_branch() {
  local pr="$1"
  local state head
  state=$(gh pr view "$pr" --json state -q .state 2>/dev/null || echo "")
  head=$(gh pr view "$pr" --json headRefName -q .headRefName 2>/dev/null || echo "")
  [[ -n "$head" ]] || fail "Could not resolve headRefName for $pr"
  if [[ "$state" != "MERGED" ]]; then
    echo "PR state is '$state' (not MERGED). Skip cleanup."
    return 1
  fi
  echo "→ Cleanup merged branch: $head"
  git checkout main >/dev/null 2>&1 || true
  git pull --ff-only
  git branch -D "$head" 2>/dev/null || true
  git push origin --delete "$head" 2>/dev/null || true
  git fetch --prune >/dev/null 2>&1 || true
  capsule_pointer
  echo "Cleanup done."
}

cmd_cleanup() {
  require git; require gh
  local PR=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pr) PR="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown arg: $1"; usage; exit 2 ;;
    esac
  done
  [[ -n "$PR" ]] || fail "Provide --pr <url|number>"
  cleanup_branch "$PR" || true
}

cmd_ship() {
  require git; require gh
  local TYPE="" MSG="" WATCH="false" CLEANUP="false"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --docs) TYPE="docs"; shift ;;
      --ci)   TYPE="ci";   shift ;;
      -m|--message) MSG="$2"; shift 2 ;;
      --watch) WATCH="true"; shift ;;
      --cleanup) CLEANUP="true"; shift ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown arg: $1"; usage; exit 2 ;;
    esac
  done
  [[ -n "$TYPE" ]] || fail "Choose --docs or --ci"
  [[ -n "$MSG"  ]] || fail "Provide -m \"<title>\""
  gh auth status >/dev/null || fail "gh auth not ready"
  ensure_labels

  git fetch origin --prune >/dev/null 2>&1 || true
  if ! git_dirty; then echo "Nothing to commit."; exit 0; fi

  git add -A
  ts=$(date -u +"%Y%m%dT%H%M%SZ")
  case "$TYPE" in
    docs) prefix="docs/autoprops" ;;
    ci)   prefix="ci/change" ;;
  esac
  branch="${prefix}/${ts}"
  echo "→ Branch: $branch"
  git checkout -b "$branch"
  git commit -m "$MSG"
  git push -u origin "$branch"

  echo "→ Create PR"
  PR_URL=""; PR_NUM=""; _PR_JSON=""
  if _PR_JSON=$(gh pr create -H "$branch" -B main -t "$MSG" -b "" --json url,number 2>/dev/null); then
    PR_URL=$(json_field "$_PR_JSON" url)
    PR_NUM=$(json_field "$_PR_JSON" number)
  else
    _PR_JSON=$(gh pr view "$branch" --json url,number 2>/dev/null || true)
    if [ -n "$_PR_JSON" ]; then
      PR_URL=$(json_field "$_PR_JSON" url)
      PR_NUM=$(json_field "$_PR_JSON" number)
    fi
  fi

  if [[ "$TYPE" == "docs" ]]; then
    echo "→ Label & arm auto-merge"
    gh pr edit "$PR_URL" --add-label "auto-merge-docs" >/dev/null 2>&1 || true
    gh pr merge "$PR_URL" --squash --auto >/dev/null 2>&1 || true
    echo "Auto-merge armed (docs-only)."
  else
    echo "CI/infra PR opened (manual merge)."
  fi

  echo "PR: $PR_URL"
  if [[ "$WATCH" == "true" ]]; then
    gh pr checks "$PR_NUM" --watch || true
  fi

  # If asked, clean up after merge (works for both docs auto-merge and manual merges)
  if [[ "$CLEANUP" == "true" ]]; then
    cleanup_branch "$PR_URL" || {
      echo "Not merged yet; re-run later: tools/preflight.sh cleanup --pr \"$PR_URL\""
    }
  fi
}

sub="${1:-}"; shift || true
case "$sub" in
  check)   cmd_check "$@" ;;
  ship)    cmd_ship  "$@" ;;
  cleanup) cmd_cleanup "$@" ;;
  ""|-h|--help) usage ;;
  *) echo "Unknown subcommand: $sub"; usage; exit 2 ;;
esac
