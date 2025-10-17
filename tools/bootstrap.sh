#!/usr/bin/env bash
set -euo pipefail

echo "🚀 bootstrap: start"

# Ensure we're at repo root
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Require python3 (explicit; CI provides it via setup-python)
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ bootstrap: python3 not found. Install Python 3.9+ and re-run."
  exit 1
fi

# Make shipped scripts executable (if present)
if [ -d tools ]; then
  find tools -type f -name "*.sh" -exec chmod +x {} + || true
fi

# Prefer LF endings; do not auto-rewrite files
if command -v git >/dev/null 2>&1; then
  git config core.autocrlf false >/dev/null 2>&1 || true
  git config core.eol lf >/dev/null 2>&1 || true
fi

# Warn (not fail) if CRLFs appear in tracked files
if command -v file >/dev/null 2>&1; then
  if git ls-files -z | xargs -0 file 2>/dev/null | grep -q 'CRLF'; then
    echo "⚠️  bootstrap: CRLF endings detected in tracked files (warn-only)."
    echo "    Tip: git add --renormalize . && git commit -m 'normalize line endings'"
  fi
fi

# Use repo-local hooks if present (non-blocking)
if [ -d ".githooks" ] && command -v git >/dev/null 2>&1; then
  git config core.hooksPath .githooks >/dev/null 2>&1 || true
fi

# Ensure artifacts root exists (used by brief)
mkdir -p artifacts/systemic_out

echo "🐍 bootstrap: python3 version $(python3 --version 2>/dev/null | awk '{print $2}')"
echo "✅ bootstrap: OK"
