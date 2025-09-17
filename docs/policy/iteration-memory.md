# Iteration Memory & Capability Policy

TEOF requires that every material change leave a signed breadcrumb that future operators can audit. The policy couples an append-only memory log with a CI gate that refuses untracked work.

## Memory Log (L1–L3 compliance)

- The canonical log lives at `memory/log.jsonl`.
- Each JSONL record captures `ts`, `actor`, `summary`, `ref`, `artifacts`, and `signatures`.
- Entries are append-only; prior records must never be rewritten.
- Signatures: contributors append detached signature identifiers (PGP, sigchain URLs, etc.). Capsule promotions require ≥2 signers.

## Capability Gate

The CI step `check_memory_log.py` enforces:

1. Any PR touching `extensions/`, `tools/`, `scripts/`, or `docs/` (except `memory/`) must append at least one log entry.
2. The log diff must be append-only (baseline content is a strict prefix of the new file).
3. New entries must be valid JSON containing the required fields.

## Workflow

1. Build or modify your change on a feature branch.
2. Append a memory entry using `tools/memory/log-entry.sh`, referencing the branch/PR and any external receipt in `_report/`.
3. Collect signatures as needed and include them in the entry’s `signatures` array.
4. Open the PR with the alignment note; CI will fail if the log is missing or malformed.

This scaffold satisfies the "Encounterable & Decentralized" directive by ensuring every replica can replay history from an auditable trail.
