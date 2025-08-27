#!/usr/bin/env bash
set -euo pipefail
V="${1:?usage: tools/capsule_switch.sh vX.Y}"
[ -d "capsule/$V" ] || { echo "capsule/$V not found"; exit 1; }

ln -snf "$V" capsule/current
git add capsule/current
git commit -m "capsule: switch live pointer -> $V" || true
tools/doctor.sh

B="capsule/switch-${V}-$(date -u +%Y%m%dT%H%M%SZ)"
git checkout -b "$B" 2>/dev/null || git checkout "$B"
git push -u origin "$B"

# Open PR and label it for auto-merge (capsule-switch)
remote="$(git remote get-url origin)"; base="${remote%.git}"
if command -v gh >/dev/null 2>&1; then
  gh pr create --base main --head "$B" --title "capsule: switch live -> ${V}" --body "Auto-opened by tools/capsule_switch.sh" 2>/dev/null || true
  # Ensure label exists then apply
  gh label list --limit 200 | awk '{print $1}' | grep -qx "capsule-switch" || \
    gh label create "capsule-switch" --color 5319e7 --description "Capsule pointer update" >/dev/null || true
  gh pr edit "$B" --add-label "capsule-switch" >/dev/null 2>&1 || \
  { n="$(gh pr view --json number -q .number 2>/dev/null || true)"; [ -n "$n" ] && gh pr edit "$n" --add-label "capsule-switch" >/dev/null 2>&1 || true; }
  echo "PR (capsule switch): $(gh pr view --json url -q .url 2>/dev/null || echo "${base}/compare/main...${B}?expand=1")"
else
  echo "Open PR: ${base}/compare/main...${B}?expand=1"
  echo "Then add label: capsule-switch (CI will enable Auto-merge)."
fi
