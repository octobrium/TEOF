#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"


[ -f scripts/new_experiment.sh ] && chmod +x scripts/new_experiment.sh || true
[ -f tools/doctor.sh ] && chmod +x tools/doctor.sh || true

fi

if [ "${GITHUB_ACTIONS:-}" != "true" ] && [ "${1:-}" != "--no-hook" ]; then
  mkdir -p .git/hooks
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [ "${SKIP_DOCTOR:-0}" = "1" ]; then
  exit 0
fi
tools/bootstrap.sh --no-hook || true
tools/doctor.sh
HOOK
  chmod +x .git/hooks/pre-commit
fi

if [ "${1:-}" != "--no-doctor" ]; then
  tools/doctor.sh
fi

echo "bootstrap: done"
