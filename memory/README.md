# TEOF Memory Scaffold

TEOF tracks decision and experiment history in an append-only log stored at `memory/log.jsonl`. Each entry captures who made a change, what was attempted, and where the supporting diff or artifact lives. The memory scaffold is:

- **Append-only:** Prior entries must never be rewritten. New entries are appended at the end of `memory/log.jsonl`.
- **Signed:** Authors should append their signature digest in the `signatures` array. Threshold signing (≥2 signers) is required before promoting capsule changes.
- **Mirrored:** Operators may mirror the log to external stores (S3, IPFS, etc.) for redundancy, but the Git repo remains the canonical source of truth.

## Entry schema

Each line in `memory/log.jsonl` is a JSON object with the following fields:

| Field       | Description |
|-------------|-------------|
| `ts`        | UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`). |
| `actor`     | Human or agent responsible for the change. |
| `summary`   | Short description of the decision or experiment. |
| `ref`       | Branch, PR, or commit hash linking to the work. |
| `artifacts` | List of artifact paths or URLs (may be empty). |
| `signatures`| Array of detached signature identifiers (may be empty if pending). |

Example line:

```json
{"ts":"2025-09-17T04:20:00Z","actor":"codex","summary":"Document replica smoke flow","ref":"PR-26","artifacts":["tools/replica-smoke.sh"],"signatures":[]}
```

## Appending entries

Use `tools/memory/log-entry.py` to append a new record safely:

```bash
python tools/memory/log-entry.py \
  --summary "Ran replica smoke on new dataset" \
  --ref PR-42 \
  --artifact _report/teof-replica-smoke.20250917T040000Z.txt
```

The script stamps the current timestamp and actor (defaults to `git config user.name`), then appends a JSON line. You can add signature identifiers later using the same tool with `--signatures`.

## Querying recent entries

Use `tools/memory/query.py` to review the most recent decisions:

```bash
python tools/memory/query.py --limit 10
```

Filter by actor or reference substring:

```bash
python tools/memory/query.py --actor codex --limit 5
python tools/memory/query.py --ref PR-28 --limit 3
```

The script prints the newest entries first, including artifact and signature metadata.

## Policy

- Every PR touching `extensions/`, `tools/`, `scripts/`, or `docs/` (excluding `memory/`) must append at least one memory entry.
- CI enforces append-only behavior and rejects PRs that mutate existing records.
- Attach signatures before promoting capsule changes or modifying governance DNA.

Mirrors should watch for new lines and replicate them without re-ordering.
