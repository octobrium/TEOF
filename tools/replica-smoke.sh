#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python interpreter not found (set PYTHON_BIN)" >&2
  exit 127
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPORT_DIR="$ROOT/_report"
mkdir -p "$REPORT_DIR"

TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG="$REPORT_DIR/teof-replica-smoke.${TS}.txt"

{
  echo "# teof replica smoke"
  echo "timestamp: ${TS}Z"
  echo "python: ${PYTHON_BIN}"
  echo "pwd: ${ROOT}"
  echo
} > "$LOG"

if "$PYTHON_BIN" -m teof brief >>"$LOG" 2>&1; then
  echo "status: success" >>"$LOG"
  printf '✅ replica smoke succeeded (%s)\n' "$LOG"
else
  code=$?
  echo "status: failure (${code})" >>"$LOG"
  printf '⚠️  replica smoke failed (%s)\n' "$LOG" >&2
  exit $code
fi
