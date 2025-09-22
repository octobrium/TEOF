#!/usr/bin/env bash
set -euo pipefail
echo "🩺  Running doctor (invariants first)..."

# 1) Delegate to ops doctor if present, but filter a known harmless noise line.
if [ -x "scripts/ops/doctor.sh" ]; then
  _OUT=""
  if ! _OUT="$(scripts/ops/doctor.sh 2>&1)"; then
    _CODE=$?
  else
    _CODE=0
  fi
  # Show everything except the benign queue notice; preserve exit code.
  printf "%s\n" "$_OUT" | awk '$0!="Unexpected top-level dir: queue"'
  if [ $_CODE -ne 0 ]; then
    echo "❌ ops doctor reported failures"; exit $_CODE
  fi
fi

# 2) Invariants: append-only & anchors guard & layout warn-only
if [ -x "scripts/ci/check_append_only.sh" ]; then
  echo "== Append-only audit (HEAD vs origin/main) =="
  scripts/ci/check_append_only.sh || true
fi
if [ -x "scripts/ci/check_anchors_guard.py" ]; then
  scripts/ci/check_anchors_guard.py
fi
if [ -x "scripts/ci/check_layout.sh" ]; then
  scripts/ci/check_layout.sh || true
fi

# 3) Redundancy (warn-only)
if [ -x "scripts/ci/check_redundancy.py" ]; then
  scripts/ci/check_redundancy.py || true
fi

# Planner scaffolding must be valid before continuing.
if [ -x "scripts/ci/check_plans.py" ]; then
  scripts/ci/check_plans.py
fi
if [ -x "scripts/ci/check_vdp.py" ]; then
  python3 scripts/ci/check_vdp.py
fi

# 4) Determinism hygiene (CRLF, .DS_Store, exec bits)
if git ls-files -z | xargs -0 file | grep -q 'CRLF'; then
  echo "❌ CRLF endings found in tracked files"; exit 1
fi
if git ls-files | grep -q '\.DS_Store'; then
  echo "❌ .DS_Store files committed"; exit 1
fi
for s in tools/bootstrap.sh tools/doctor.sh extensions/validator/teof-validate.sh; do
  [ -e "$s" ] && [ ! -x "$s" ] && { echo "❌ $s not executable"; exit 1; }
done

echo "✅ doctor: repo health OK"

# Build brief artifacts to ensure latest/ symlink stays valid.
echo "→ Rebuilding brief artifacts (doctor)"
OUT_ROOT="$(pwd)/artifacts" PYTHONPATH="$(pwd)" python3 -m teof.cli brief

# --- Capsule content-tree verification (path-agnostic) ---
if command -v jq >/dev/null 2>&1; then
  current_target=""
  if [ -L "capsule/current" ]; then
    current_target="$(readlink "capsule/current")"
  elif [ -f "capsule/current" ]; then
    current_target="$(tr -d '\n' < capsule/current)"
  fi

  current_target="${current_target#capsule/}"

  if [ -n "$current_target" ] && [ -f "capsule/${current_target}/reconstruction.json" ]; then
    echo "→ Verifying capsule content tree (path-agnostic)…"
    bash tools/capsule-verify.sh
  fi
fi
