# Receipts Index Streaming

Keep `_report/usage/receipts-index/receipts-index.jsonl` manageable by emitting append-only shards with hash chaining so downstream automation can tail the ledger without re-reading the entire history.

## Goals

- Replace the monolithic receipts index with size-capped shards (default 500 entries) stored under `_report/usage/receipts-index/stream/`.
- Provide a pointer file (`_report/usage/receipts-index/latest.jsonl`) that always contains the newest shard path and hash.
- Allow automation to resume from the last processed shard by verifying hashes and sequence numbers.
- Add a CI guard ensuring the pointer exists, the latest shard hash matches its manifest, and the most recent shard is younger than a configurable freshness window (default 24h).

## Shard format

Each shard is a JSONL file with the same payloads produced by `tools.agent.receipts_index`. A companion manifest captures metadata:

```json
{
  "shard_id": "receipts-2025-11-09T061500Z",
  "sequence": 42,
  "prev_shard": "receipts-2025-11-08T220000Z",
  "prev_sha256": "6d2a…",
  "entries": 500,
  "first_timestamp": "2025-11-08T21:59:59Z",
  "last_timestamp": "2025-11-09T06:15:00Z",
  "sha256": "ab41…",
  "generated_at": "2025-11-09T06:15:01Z",
  "source": "_report/usage/receipts-index/receipts-index.jsonl"
}
```

Manifest files land next to their shards: `_report/usage/receipts-index/stream/receipts-<stamp>.manifest.json`.

## CLI

`teof receipts_stream --dest _report/usage/receipts-index/stream --max-entries 500 --pointer _report/usage/receipts-index/latest.json`

(`python -m tools.autonomy.receipts_index_stream stream …` remains available when you need the standalone module.)

Behaviour:

1. Loads the existing receipts index (or reads from stdin when piping).
2. Appends records into the current shard until `--max-entries` is reached, then finalises the shard by computing `sha256` and writing the manifest.
3. Updates the pointer file with `{ "latest": "<relative shard path>", "sha256": "<hash>", "generated_at": "…" }`.
4. Prints a summary so operators know how many entries moved and which shards were created.

`_report/usage/receipts-index/latest.json` always mirrors the newest shard. Consumers read the pointer first, verify the hash, and then tail the shard chain via the manifest `prev_shard`/`prev_sha256` fields when they need historical data.

Flags:

- `--since-shard <shard_id>`: resume from a specific shard (defaults to the last manifest in `--dest`).
- `--max-age-hours <hours>`: guardrail that fails when the newest entry timestamp exceeds the threshold (default 24h).
- `--dry-run`: print what would be written without creating shards/pointers.
- `--receipt <path>`: emit a JSON receipt (module `tools.autonomy.receipts_index_stream`) that records shard counts, pointer metadata, and the freshness window used during the run so automation health checks have a trail to follow.

## CI guard

`teof receipts_stream_guard --pointer _report/usage/receipts-index/latest.json --max-age-hours 24` (or the CI wrapper `scripts/ci/check_receipts_stream.py`) enforces pointer integrity and freshness:

1. Reads `_report/usage/receipts-index/latest.json` and verifies the referenced shard plus companion manifest exist.
2. Recomputes the shard hash, ensuring it matches both the pointer and manifest metadata.
3. Validates that the manifest sequence matches the pointer sequence when both are present.
4. Confirms the shard is newer than the freshness window (override with `RECEIPTS_STREAM_MAX_AGE_HOURS`, default 24h).
5. Fails fast when any condition is unmet so operators can re-run the streaming CLI before merging. Pass `--receipt _report/usage/receipts-index/guard/receipts-stream-guard-<stamp>.json` to keep an auditable trail of each guard invocation (the payload records pointer path, shard sequence, age, and threshold). In CI, `scripts/ci/check_receipts_stream.py` shells into this logic with repo-relative defaults so automation stays reversible.

## Transition plan

1. Run the existing receipts index generator to produce a full snapshot.
2. Execute the streaming CLI once to backfill shards from the historical ledger.
3. Update automation (batch refinement, evidence usage) to read from the pointer first; fall back to the legacy file when the pointer is missing.
4. After consumers switch, stop committing the monolithic JSONL in favour of shards + pointer (CI guard enforces this).

This document satisfies plan step S2 by defining the shard schema, CLI interface, pointer behaviour, and guard strategy required to implement ND-063.
