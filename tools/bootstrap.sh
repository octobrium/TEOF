#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

grep -RIl $'\r' -- Makefile mk tools scripts 2>/dev/null | xargs -I{} perl -i -pe 's/\r$//' "{}" 2>/dev/null || true

[ -f scripts/new_experiment.sh ] && chmod +x scripts/new_experiment.sh || true
[ -f tools/doctor.sh ] && chmod +x tools/doctor.sh || true

if [ -f Makefile ] && ! grep -q 'mk/experiments\.mk' Makefile; then
  printf '\n# experiment lifecycle rules\ninclude mk/experiments.mk\n' >> Makefile
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
