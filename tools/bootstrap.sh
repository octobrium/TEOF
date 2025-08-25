#!/usr/bin/env bash
# TEOF bootstrap: minimal + futureproof (safe in CI and locally)
set -euo pipefail

echo "🚀 bootstrap: start"

# Ensure we're at repo root
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Make shipped scripts executable (if present)
if [ -d tools ]; then
  find tools -type f -name "*.sh" -exec chmod +x {} + || true
fi

# Prefer LF endings; don't rewrite files automatically in CI
if command -v git >/dev/null 2>&1; then
  git config core.autocrlf false || true   # don't auto-CRLF
  git config core.eol lf || true           # canonical EOL = LF
fi

# Optional: warn (not fail) if CRLFs are in tracked files
if command -v file >/dev/null 2>&1; then
  if git ls-files -z | xargs -0 file 2>/dev/null | grep -q 'CRLF'; then
    echo "⚠️  bootstrap: CRLF endings detected in tracked files (warn-only)."
    echo "    Tip: to normalize: git add --renormalize . && git commit -m 'normalize line endings'"
  fi
fi

# Use repo-local hooks if present (non-blocking)
if [ -d ".githooks" ] && command -v git >/dev/null 2>&1; then
  git config core.hooksPath .githooks || true
fi

# Create artifacts root used by the brief step
mkdir -p artifacts/ocers_out || true

echo "✅ bootstrap: OK"
