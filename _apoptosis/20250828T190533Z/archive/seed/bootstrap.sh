#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CLI="$ROOT/cli/teof_cli.py"
EVAL="$ROOT/trunk/ogs/evaluator.py"
OUT="${TEOF_OUT_DIR:-$ROOT/artifacts/systemic_out}"
[ -f "$CLI" ] || { echo "CLI not found: $CLI" >&2; exit 1; }
[ -f "$EVAL" ] || { echo "Evaluator not found: $EVAL" >&2; exit 1; }
python3 -m venv "$ROOT/.venv" || true
source "$ROOT/.venv/bin/activate"
python -m pip install -U pip >/dev/null
mkdir -p "$OUT"
python "$CLI"
python "$HERE/append_anchor.py"
LATEST="$(ls -1d "$OUT"/*/ 2>/dev/null | sort | tail -n1)"
echo "Latest: $LATEST"
