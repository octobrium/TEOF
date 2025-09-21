# Design log — receipts hygiene automation (2025-09-21)

## Goal
Provide a single command that runs the receipts indexer + latency metrics, writes fresh JSONL receipts, and surfaces missing or stale evidence so agents can check health in one step.

## Scope
- New CLI (likely `python -m tools.agent.receipts_hygiene`) that:
  1. Runs `receipts_index.build_index` and writes to `_report/usage/receipts-index-latest.jsonl`.
  2. Runs `receipts_metrics.build_metrics` using the index data and writes `_report/usage/receipts-latency-latest.jsonl`.
  3. Optionally prints a short summary (counts, missing receipts, worst latencies).
- Reuse existing helpers (import functions directly instead of shelling out).
- Provide `--output-dir` override for predictable paths (default `_report/usage/`).
- Exit non-zero if missing receipts or metrics exceed threshold? Start with warnings (exit 0) but include summary fields so CI can enforce later.

## Implementation notes
- Build on the new Python modules rather than subprocess to avoid duplication.
- Collect stats: total plans, plans with missing receipts, max `plan_to_first_receipt` minutes, etc. Print table + JSON summary.
- Write a consolidated summary JSON (maybe `_report/usage/receipts-hygiene-summary.json`) for quick inspection and linking to plans.
- Ensure CLI respects git tracked guard by writing outputs under `_report/usage/` (whitelisted) and using JSON.

## Tests
- Pytest with tmp repo: seed plan/receipts/manager note, run CLI, assert outputs exist and summary matches metrics.
- Another test where missing receipt triggers warning in summary.

## Follow-up ideas
- Hook CLI into preflight or guardrails (separate plan) once stabilized.
- Allow thresholds via flags (e.g., `--fail-on-missing`).
