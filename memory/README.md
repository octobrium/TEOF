# TEOF Memory Scaffold

TEOF tracks decision and experiment history in an append-only log stored at `memory/log.jsonl`. Each entry captures what happened, why it mattered, and which receipts prove the work. The memory scaffold is:

- **Append-only:** Prior entries must never be rewritten. New entries are appended at the end of `memory/log.jsonl`.
- **Signed:** Authors should append their signature digest in the `signatures` array. Threshold signing (≥2 signers) is required before promoting capsule changes.
- **Mirrored:** Operators may mirror the log to external stores (S3, IPFS, etc.) for redundancy, but the Git repo remains the canonical source of truth.

## Entry schema

### Canonical event schema (automation surface)

Automation and newer tools write log events through `tools.memory.write_log`. The
helper guarantees the following keys:

| Field         | Description |
|---------------|-------------|
| `ts`          | UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`). |
| `run_id`      | Globally unique identifier for the execution capsule. |
| `summary`     | Short description of the decision or experiment. |
| `hash_prev`   | SHA-256 digest of the previous entry (or `null` for genesis). |
| `hash_self`   | SHA-256 digest of the current entry (with `hash_self` removed during hashing). |

Entries written via `write_log` typically include additional context that mirrors
the autonomy blueprints: `layer`, `systemic_scale`, `task`, `receipts`,
`derived_facts`, `next_actions`, `outputs`, `exit_status`, etc. These keys are
optional but recommended because downstream tooling (status dashboards, replay
helpers) expect them when present.

Example (abbreviated) entry emitted by `write_log`:

```json
{
  "ts": "2025-09-26T19:06:28Z",
  "run_id": "20250926T190628Z-717d8d",
  "summary": "Completed backlog hygiene plan",
  "task": "2025-09-25-backlog-hygiene",
  "layer": "L5",
  "systemic_scale": 5,
  "receipts": ["docs/workflow.md", "docs/quickstart.md"],
  "artifacts": ["docs/workflow.md", "docs/quickstart.md"],
  "hash_prev": "d864891fc56f5daf615fadf199ffdda2dcc9c286fa489f3c81a295535c0d46e9",
  "hash_self": "79a1986f5556432be21cc63d0c1f4be6364fd642e3b742070f791ecd0109c86b"
}
```

### Legacy compatibility (manual surface)

Early memory usage relied on the lightweight `tools/memory/log-entry.py` script.
Those entries contain a simpler shape (`actor`, `ref`, `signatures`, and
`artifacts`). They remain valid and continue to pass append-only enforcement, but
new automation should prefer the canonical surface above. When ingesting the log,
always treat optional fields defensively so the history can be replayed across
both eras.

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

To speed up frequent queries, build a hot index:

```bash
python tools/memory/hot_index.py build --limit 200
```

Then query using the cached index:

```bash
python tools/memory/hot_index.py query --use-index --limit 20 --json
```

## Policy

- Every PR touching `extensions/`, `tools/`, `scripts/`, or `docs/` (excluding `memory/`) must append at least one memory entry.
- CI enforces append-only behavior and rejects PRs that mutate existing records.
- Attach signatures before promoting capsule changes or modifying governance DNA.
- Record credential lifecycle events. When an agent credential is issued or revoked, append a memory entry summarising the scope (agent id, branch prefix, token type) and link to receipts stored under `_report/agent/<agent-id>/`. Example:

  ```bash
  python tools/memory/log-entry.py \
    --summary "Revoked deploy key for agent/alice-local-llm-1" \
    --ref agent/alice-local-llm-1/revoke-20250918 \
    --artifact _report/agent/alice-local-llm-1/revoke-20250918.json
  ```

Mirrors should watch for new lines and replicate them without re-ordering.
