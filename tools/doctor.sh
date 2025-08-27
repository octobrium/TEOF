#!/usr/bin/env bash
set -euo pipefail
echo "🩺  Running doctor (invariants first)..."

# Invariants (hashes, append-only, layout)
if [ -x "scripts/ops/doctor.sh" ]; then
  scripts/ops/doctor.sh
else
  echo "WARN: scripts/ops/doctor.sh missing; skipping invariants"
fi

# Determinism hygiene
if git ls-files -z | xargs -0 file | grep -q 'CRLF'; then
  echo "❌ CRLF endings found in tracked files"; exit 1
fi
if git ls-files | grep -q '\.DS_Store'; then
  echo "❌ .DS_Store files committed"; exit 1
fi
# Executable bit sanity for common scripts (best-effort)
for s in tools/bootstrap.sh tools/doctor.sh extensions/validator/teof-validate.sh; do
  [ -e "$s" ] && [ ! -x "$s" ] && { echo "❌ $s not executable"; exit 1; }
done

echo "✅ doctor: repo health OK"

# Redundancy (warn-only)
if [ -x "scripts/ci/check_redundancy.sh" ]; then
  scripts/ci/check_redundancy.sh || true
fi

# Anchors append-only/provenance (invariants)
if [ -x "scripts/ci/check_anchors_guard.py" ]; then
  scripts/ci/check_anchors_guard.py
fi

# Append-only audit (HEAD vs origin/main)
if [ -x "scripts/ci/check_append_only.sh" ]; then
  echo "== Append-only audit (HEAD vs origin/main) =="
  scripts/ci/check_append_only.sh || true
fi
