#!/usr/bin/env bash
set -euo pipefail
cd /Users/evan/Documents/GitHub/TEOF

# Normalize CRLF -> LF
grep -RIl $'\r' -- Makefile mk/ tools/ scripts/ 2>/dev/null | \
  xargs -I{} perl -i -pe 's/\r$//' "{}" 2>/dev/null || true

# Ensure scripts executable if present
[ -f scripts/new_experiment.sh ] && chmod +x scripts/new_experiment.sh || true

# Fix recipe lines (spaces → TAB)
fix_tabs(){
  f="$1"
  awk '
  /^[^#[:space:]].*:/ { inr=1; print; next }
  inr && /^[[:space:]]*$/ { print; next }
  inr && /^[[:space:]]/   { sub(/^[[:space:]]+/, "\t"); print; next }
  { inr=0; print }
  ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
}
[ -f Makefile ] && fix_tabs Makefile
fix_tabs mk/experiments.mk

# Ensure mk/experiments.mk is included
grep -q 'mk/experiments.mk' Makefile || \
  echo -e '\n# experiment lifecycle rules\ninclude mk/experiments.mk' >> Makefile

echo "Running doctor..."
exec tools/doctor.sh
