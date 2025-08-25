#!/usr/bin/env bash
set -euo pipefail
echo "🩺  Running doctor checks..."

# 1) No CRLF line endings in tracked files
if git ls-files -z | xargs -0 file | grep -q 'CRLF'; then
  echo "❌ CRLF endings found in tracked files"; exit 1
fi

# 2) No .DS_Store
if git ls-files | grep -q '\.DS_Store'; then
  echo "❌ .DS_Store files committed"; exit 1
fi

# 3) Scripts must be executable if present
for s in tools/bootstrap.sh tools/doctor.sh extensions/validator/teof-validate.sh; do
  [ -e "$s" ] && [ ! -x "$s" ] && { echo "❌ $s not executable"; exit 1; }
done

echo "✅ doctor: basic repo health OK"
