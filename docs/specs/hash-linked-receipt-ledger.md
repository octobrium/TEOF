# Hash-Linked Receipt Ledger (Plan 2025-10-12-infinite-ledger)

## Purpose
- Provide a deterministic, append-only chain of receipt metadata so distributed TEOF nodes can prove work order without trusting a single host.
- Create a schema that fits within `_report/usage/` so existing automation can read/write receipts without new infra.
- Enable validators (CI or dedicated agents) to replay the chain, detect tampering, and mirror the latest hash to external anchors.

## Schema
Each entry is a JSON object stored under `_report/usage/hash-ledger/receipt-<ts>.json` with the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `version` | integer | Schema version (start at 0). |
| `hash` | string | Hex-encoded SHA-256 of the canonical payload (all fields except `signature`). |
| `prev_hash` | string | Hash of the previous accepted entry (or all zeros for genesis). |
| `plan_id` | string | The plan this receipt relates to. |
| `plan_step_id` | string | Associated plan step (optional when not step bound). |
| `receipt_path` | string | Repo-relative path to the underlying receipt (e.g., `_report/usage/plan-scope/...`). |
| `agent_id` | string | Agent or automation that produced the receipt. |
| `ts` | string | ISO8601 UTC timestamp for when the receipt hash was captured. |
| `metadata` | object | Free-form context (systemic axes, command run, etc.), validated as JSON. |
| `signature` | string | Optional detached signature from a key referenced in `governance/anchors.json`. |

All receipts are stored individually plus an index `_report/usage/hash-ledger/index.jsonl` that appends the same payload without signatures for fast replay.

## Hash Construction
```
payload = {
  "version": 0,
  "prev_hash": "...",
  "plan_id": "...",
  "plan_step_id": "...",
  "receipt_path": "...",
  "agent_id": "...",
  "ts": "...",
  "metadata": {...}
}
hash = SHA256(json.dumps(payload, sort_keys=True, separators=(",", ":")))
```

The `signature` (if present) signs the canonical concatenation `hash || agent_id || ts`.

## Validator Responsibilities
1. Ensure files referenced by `receipt_path` exist and are tracked by git.
2. Recompute the payload hash and confirm it matches `hash`.
3. Verify `prev_hash` matches the last accepted entry.
4. When `signature` is provided, check the key against `governance/anchors.json`.
5. Emit CI failures (or `teof hash_ledger guard`) when any invariant fails.

## Storage & Mirroring
- Primary storage lives inside `_report/usage/hash-ledger/` to stay git-native.
- Validators write `_report/usage/hash-ledger/state.json` tracking `tip_hash`, `entry_count`, and the last replay timestamp.
- External mirrors (S3, IPFS, etc.) can pull the JSONL and publish Merkle proofs; the repo keeps only the canonical hash chain.

## CLI + Guard
- `teof hash_ledger append --plan … --receipt …` wraps the ledger helper so agents can log entries without touching internal modules. Metadata files can be passed via `--metadata` (repo-relative paths allowed).
- `teof hash_ledger guard` replays `_report/usage/hash-ledger/index.jsonl`, checks hash continuity, and updates `state.json`. The same logic powers `scripts/ci/check_hash_ledger.py` so CI fails if any entry is malformed or references a missing receipt.
- Direct helper usage (`python -m tools.autonomy.hash_ledger append|guard`) remains available for automation harnesses; both paths share the same codepath, receipts, and state updates.

## Next Steps
1. Mirror the tip hash into `_report/usage/status/status-*.json` and optionally `governance/anchors.json` for external anchoring.
