# Design log — receipts indexer (2025-09-21)

## Objectives
- Expose a machine-readable ledger covering plans, receipts (`_report/**`), and manager-report entries.
- Flag missing or untracked receipts to close the loop on the new guard.
- Preserve provenance by mapping each receipt back to the plan/step that references it.

## Schema outline
- `summary`: first record with generation timestamp + simple counts.
- `plan`: one per `_plans/*.plan.json` capturing actor, status, checkpoint status, and receipt links. Each receipt entry carries `exists`/`tracked` booleans.
- `receipt`: one per `_report/**` file with size, mtime, sha256, and `referenced_by` list (plan id + step id if applicable).
- `manager_message`: one per manager-report line with author, type, task id, and receipt status indicators.

## Implementation notes
- Use `git ls-files` to determine tracked receipts; fall back gracefully when unavailable.
- Default output: JSONL written under `_report/usage/` when `--output` is relative; `stdout` otherwise.
- CLI lives at `python -m tools.agent.receipts_index --root <tmp> --output receipts-index.jsonl` for testing. Production invocations omit `--root`.
- Tests spin up a throwaway git repo, seed plan/receipt/manager data, and assert that the index wires references correctly and flags no missing receipts.

## Follow-ons
- Extend indexer to ingest `_bus/events/events.jsonl` once consensus latency metrics land.
- Feed the ledger into a future hygiene plan that highlights cold subsystems.
