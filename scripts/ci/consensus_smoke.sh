#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LEDGER_TMP=$(mktemp -d)
trap 'rm -rf "$LEDGER_TMP"' EXIT

LEDGER_FILE="$LEDGER_TMP/ledger.csv"
cat <<'CSV' >"$LEDGER_FILE"
batch_ts,total_items,avg_score,total_score,avg_risk,accept_rate,notes
20250917T170236Z,5,1.200,6,0.250,0.800,ci-sample
20250918T010000Z,3,1.500,5,,0.667,ci-sample-2
CSV

pushd "$ROOT" >/dev/null
mkdir -p _report/consensus

python3 -m tools.consensus.ledger \
  --ledger "$LEDGER_FILE" \
  --format jsonl \
  --output ci-ledger-smoke.jsonl >/dev/null

python3 -m tools.consensus.receipts \
  --decision CI-SMOKE \
  --summary "CI consensus smoke" \
  --agent ci-bot \
  --receipt _report/consensus/ci-ledger-smoke.jsonl \
  --output ci-consensus-smoke.jsonl >/dev/null

python3 -m tools.consensus.dashboard \
  --format table \
  --task QUEUE-030 \
  --task QUEUE-031 \
  --task QUEUE-032 \
  --task QUEUE-033 \
  > _report/consensus/ci-dashboard.txt

ARTIFACT_DIR="artifacts/consensus"
mkdir -p "$ARTIFACT_DIR"
cp _report/consensus/ci-ledger-smoke.jsonl "$ARTIFACT_DIR/"
cp _report/consensus/ci-consensus-smoke.jsonl "$ARTIFACT_DIR/"
cp _report/consensus/ci-dashboard.txt "$ARTIFACT_DIR/"

popd >/dev/null
