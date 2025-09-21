# Design log — receipts latency metrics (2025-09-21)

## Problem
The receipts observability proposal calls for latency metrics that show how long it takes to turn reflections (manager-report notes) into plans and receipts. We already index plans, receipts, and manager messages; we need a metrics CLI that reads the index, computes deltas, and emits machine-readable output.

## Approach
- Extend `tools.agent.receipts_index` to capture `plan_id` (and raw `meta`) for manager-report messages so we can match reflections to plans.
- Build a new CLI `tools.agent.receipts_metrics` that imports `receipts_index.build_index(...)`, computes metrics, and writes JSONL/JSON output.
- For each plan entry:
  - Parse `created` timestamp.
  - Collect all receipt metadata referencing the plan (plan-level + step receipts) via the receipt entries (which include `mtime`).
  - Collect manager-report messages with matching `plan_id`; treat `type == note` as reflections, but include other types for completeness.
- Compute latencies:
  - `plan_to_first_receipt` (seconds between plan creation and earliest receipt mtime).
  - `plan_to_last_receipt` (seconds to latest receipt).
  - `note_to_first_receipt` (seconds between earliest manager note and earliest receipt).
  - `note_to_plan` (seconds between earliest note and plan creation) to highlight if reflection preceded work.
  - Flag missing receipts (exists false or tracked false) directly from index data.
- Summarize per plan and emit aggregate statistics (median, max) for easy overview.
- Output JSON: `[ {"plan_id": ..., "metrics": {...}, "missing_receipts": [...], "receipt_count": n, "manager_notes": count } ]` plus leading summary record.
- Provide `--output` option (relative -> `_report/usage/receipts-latency.jsonl`) and default to stdout when omitted.

## Tests
- Unit test reading index builder with synthetic data: multiple plans with receipts and manager notes; assert computed latencies.
- Integration: run metrics CLI in tmp repo with git (so tracked guard satisfied) and check output file structure.

## Follow-ups
- Hook metrics into a maintenance plan (future) to alert when latency exceeds thresholds.
- Optionally enrich metrics with bus event timestamps or PR links.
