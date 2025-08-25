#!/usr/bin/env bash
set -euo pipefail

echo "🩺 Running doctor checks..."

# 1) mk include present
if ! grep -q 'mk/experiments.mk' Makefile; then
  echo "❌ mk/experiments.mk not included in Makefile"
  exit 1
fi

# 2) scripts executable
if [ ! -x scripts/new_experiment.sh ]; then
  echo "❌ scripts/new_experiment.sh is not executable"
  exit 1
fi

# 3) no CRLF in key files
if grep -q $'\r' Makefile mk/experiments.mk 2>/dev/null; then
  echo "❌ CRLF line endings found"
  exit 1
fi

echo "✅ All basic doctor checks passed"
