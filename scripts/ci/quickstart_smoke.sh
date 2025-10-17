#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

pushd "$ROOT" >/dev/null

python3 -m pip install -e .

teof brief

ARTIFACT="artifacts/systemic_out/latest/brief.json"
if [ ! -f "$ARTIFACT" ]; then
  echo "::error::quickstart smoke missing receipt $ARTIFACT"
  exit 1
fi

echo "::notice::quickstart smoke succeeded ($(wc -l < "$ARTIFACT") lines in brief.json)"

popd >/dev/null
