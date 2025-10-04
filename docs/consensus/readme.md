# Consensus Tooling

`python -m tools.consensus.ledger` renders ledger-backed summaries so managers and automation can audit consensus decisions without re-running pipelines. Use `python -m tools.consensus.receipts` to append normalized JSONL receipts when decisions close.

## Usage
```bash
python -m tools.consensus.ledger \
  --format table \
  --since 2025-09-18T00:00:00Z \
  --decision 20250918T010000Z
```

### Options
- `--ledger <path>` — override the CSV source (defaults to `_report/ledger.csv`).
- `--format {table,jsonl}` — choose human-readable or JSONL output (`table` by default).
- `--decision <id>` — filter by decision/batch id (repeatable).
- `--agent <id>` — filter when the ledger provides agent columns.
- `--since <ISO8601>` — include rows at or after the timestamp (UTC).
- `--limit <N>` — display only the most recent `N` rows after filtering.
- `--output <path>` — write JSONL output to a receipt file (absolute path, or relative to `_report/consensus/`).

Example receipt capture:
```bash
python -m tools.consensus.ledger --format jsonl --output latest-ledger.jsonl
python -m tools.consensus.receipts \
  --decision DEC-123 \
  --summary "Consensus closed" \
  --agent codex-4 \
  --receipt _report/agent/codex-4/queue-031/pytest-consensus-receipts.txt
```
The command writes `_report/consensus/latest-ledger.jsonl` for later review and continues printing to stdout.

## Notes
- The CLI is read-only; it never mutates the ledger.
- Rows are returned in their original order. Use `--limit` for a quick tail.
- Additional consensus helpers will build on this module for schema validation and dashboards.
- Receipts default to `_report/consensus/<decision>-<timestamp>.jsonl`; override with `--output <name>` if you need deterministic filenames.
