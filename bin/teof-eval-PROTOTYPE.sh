#!/usr/bin/env bash
# PROTOTYPE: bin/teof-up --eval implementation
# Implements Tier 1 "Evaluate" flow: Run → See artifact → That's your audit trail
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Color codes for output
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RESET='\033[0m'

section() {
  printf "\n${BOLD}%s${RESET}\n" "$1"
}

info() {
  printf "${BLUE}→${RESET} %s\n" "$1"
}

highlight() {
  printf "${GREEN}✓${RESET} %s\n" "$1"
}

note() {
  printf "${YELLOW}Note:${RESET} %s\n" "$1"
}

# Header
cat <<'EOF'
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  TEOF Tier 1: Evaluate                                         ║
║  Every decision should be traceable.                           ║
║  TEOF makes that automatic. Run one command, get proof.        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

EOF

section "Step 1/3: Installing TEOF"
info "Creating clean environment..."
python3 -m pip install -e . > /dev/null 2>&1
highlight "Installed TEOF package"

section "Step 2/3: Running analysis"
info "Analyzing sample documents..."
teof brief > /dev/null 2>&1
highlight "Analysis complete"

section "Step 3/3: Here's what happened"
echo ""
info "TEOF just created these files:"
echo ""

# Find the latest artifacts
LATEST_DIR=$(ls -td artifacts/systemic_out/* 2>/dev/null | head -1)
LATEST_RECEIPT=$(ls -t _report/usage/onboarding/quickstart-*.json 2>/dev/null | head -1 || echo "")
BRIEF_COUNT=""
SCORE_TEXT=""

if [[ -n "$LATEST_DIR" && -f "$LATEST_DIR/brief.json" ]]; then
  BRIEF_COUNT=$(python3 - <<'PY' "$LATEST_DIR/brief.json" 2>/dev/null || true)
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    sys.exit(0)
inputs = data.get("inputs")
if isinstance(inputs, list):
    print(len(inputs))
PY
fi

if [[ -n "$LATEST_DIR" && -f "$LATEST_DIR/score.txt" ]]; then
  SCORE_TEXT=$(tr -d '\r' <"$LATEST_DIR/score.txt" | tr -s '\n' ' ')
fi

ENSEMBLE_COUNT=0
if [[ -n "$LATEST_DIR" ]]; then
  ENSEMBLE_COUNT=$(find "$LATEST_DIR" -maxdepth 1 -type f -name '*.ensemble.json' | wc -l | tr -d '[:space:]')
fi

if [[ -n "$BRIEF_COUNT" ]]; then
  BRIEF_DESC="${BRIEF_COUNT} sample documents"
else
  BRIEF_DESC="the sample document set"
fi

if [[ -d "$LATEST_DIR" ]]; then
  printf "  ${GREEN}artifacts/systemic_out/%s/${RESET}\n" "$(basename "$LATEST_DIR")"
  if [[ -f "$LATEST_DIR/brief.json" ]]; then
    if [[ -n "$BRIEF_COUNT" ]]; then
      printf "    • brief.json          ${BLUE}← Summary of %s sample documents${RESET}\n" "$BRIEF_COUNT"
    else
      printf "    • brief.json          ${BLUE}← Summary of the run${RESET}\n"
    fi
  fi
  if [[ "$ENSEMBLE_COUNT" -gt 0 ]]; then
    printf "    • *.ensemble.json     ${BLUE}← %s generated analysis files${RESET}\n" "$ENSEMBLE_COUNT"
  fi
  if [[ -f "$LATEST_DIR/score.txt" ]]; then
    if [[ -n "$SCORE_TEXT" ]]; then
      printf "    • score.txt           ${BLUE}← Quick metrics (%s)${RESET}\n" "$SCORE_TEXT"
    else
      printf "    • score.txt           ${BLUE}← Quick metrics${RESET}\n"
    fi
  fi
  echo ""
fi

if [[ -n "$LATEST_RECEIPT" ]]; then
  printf "  ${GREEN}_report/usage/onboarding/${RESET}\n"
  printf "    • %s  ${BLUE}← Execution receipt${RESET}\n" "$(basename "$LATEST_RECEIPT")"
  echo ""
fi

# The key insight
cat <<EOF
${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}

${BOLD}The Key Insight:${RESET}

Those files ${BOLD}ARE${RESET} the point. They're your automatic audit trail.

  • ${GREEN}brief.json${RESET}      → What happened (analysis processed ${BRIEF_DESC})
  • ${GREEN}score.txt${RESET}       → Quick metrics to sanity-check the run${SCORE_TEXT:+ (${SCORE_TEXT})}
  • ${GREEN}quickstart-*.json${RESET} → Full execution record (reproducible)

${YELLOW}Why this matters:${RESET}

  When you run TEOF, you don't just get outputs — you get ${BOLD}proof of
  how they were created.${RESET}

  Changes aren't just tracked — they're ${BOLD}reversible by design.${RESET}

  Decisions aren't just made — they're ${BOLD}auditable forever.${RESET}

${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}

EOF

# Next steps
section "Next Steps"
echo ""
printf "${BOLD}Ready to build with TEOF?${RESET}\n"
info "Tier 2 (30 min): Learn architecture, workflows, and how to create your own projects"
printf "  → ${GREEN}docs/onboarding/tier2-solo-dev-PROTOTYPE.md${RESET}\n"
echo ""

printf "${BOLD}Want multi-agent coordination?${RESET}\n"
info "Tier 3 (60 min): Full onboarding with manifests, bus system, and collaboration"
printf "  → ${GREEN}docs/onboarding/README.md${RESET}\n"
echo ""

printf "${BOLD}Just exploring?${RESET}\n"
info "You've seen the core value: ${BOLD}automatic accountability.${RESET}"
note "TEOF turns 'trust me, I ran the tests' into 'here's the timestamped receipt with hashes.'"
echo ""

# Optional: Inspect receipts
section "Want to inspect the receipts?"
echo ""
if [[ -f "$LATEST_DIR/brief.json" ]]; then
  printf "  ${BLUE}cat${RESET} %s\n" "$LATEST_DIR/brief.json"
fi
if [[ -n "$LATEST_RECEIPT" ]]; then
  printf "  ${BLUE}cat${RESET} %s\n" "$LATEST_RECEIPT"
fi
echo ""

printf "${GREEN}✓${RESET} Evaluation complete. Time: ~5 minutes.\n\n"
