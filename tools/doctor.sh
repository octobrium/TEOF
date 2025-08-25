#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
echo "🩺  Running doctor checks..."

if [ ! -f Makefile ] || ! grep -q 'mk/experiments\.mk' Makefile; then
  echo "❌ mk/experiments.mk not included in Makefile"
  exit 1
fi

if [ -f scripts/new_experiment.sh ] && [ ! -x scripts/new_experiment.sh ]; then
  echo "❌ scripts/new_experiment.sh is not executable"
  exit 1
fi

if (grep -q $'\r' Makefile 2>/dev/null) || (grep -q $'\r' mk/experiments.mk 2>/dev/null); then
  echo "❌ CRLF line endings found"
  exit 1
fi

echo "✅ All basic doctor checks passed"
