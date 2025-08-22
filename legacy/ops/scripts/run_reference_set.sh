#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IN="$ROOT/datasets/reference/inputs"
OUT="$ROOT/datasets/reference/results"

mkdir -p "$OUT"

for f in "$IN"/*.txt; do
  [ -e "$f" ] || { echo "No inputs found in $IN"; exit 1; }
  echo "Scoring: $(basename "$f")"
  python3 "$ROOT/extensions/validator/teof_ocers_min.py" "$f" "$OUT"
done

echo "Done. Results in: $OUT"
