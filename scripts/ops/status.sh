#!/usr/bin/env bash
set -euo pipefail

echo "== Repo ======="
git rev-parse --abbrev-ref HEAD
git log -1 --oneline || true
echo

echo "== Changes ===="
git status -s
echo

echo "== Hygiene ===="
if bash .githooks/precommit_hygiene.sh; then
  echo "hygiene: OK"
else
  echo "hygiene: FAIL (see above)"; exit 1
fi
echo

echo "== Validator =="
if [ -f extensions/validator/teof_validator.py ] && [ -f docs/examples/brief/claim.md ] && [ -f runmeta.json ]; then
  out="$(python3 extensions/validator/teof_validator.py \
      --input docs/examples/brief/claim.md \
      --runmeta runmeta.json \
      --commit status-$(date -u +%Y%m%dT%H%M%SZ) || true)"
  echo "$out" | grep -o 'verdict=[A-Z]*' || echo "verdict=UNKNOWN"
else
  echo "skipped (validator/sample/runmeta missing)"
fi
