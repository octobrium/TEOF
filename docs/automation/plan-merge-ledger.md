<!-- markdownlint-disable MD013 -->
# Plan Merge Cost Ledger (Minimal Template)

Purpose: capture proportionality evidence when consolidating `_plans/` so the
`proportion_index` metric can cite real numbers instead of placeholders.

## Required fields per entry

Record each merge or bulk closure as a JSON object with:

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | RFC 3339 string | When the merge completed. |
| `merge_id` | string | Short slug (e.g. `20251103-plan-hygiene-q4`). |
| `plans_closed` | array of strings | Plan IDs merged/closed. |
| `merge_cost_hours` | number | Estimated hours (people or agent) spent executing the merge. |
| `coherence_gain_estimate` | number | Improvement to `coherence_delta` (0–1 scale) attributable to the merge. |
| `risk_reduction_estimate` | number | Estimated reduction in failure risk (0–1 scale). |
| `notes` | string | Optional context or follow-up. |
| `evidence_paths` | array of strings | Receipts that justify the estimates. |

Append entries to `_report/health/plan-lattice/ledger.jsonl` (one JSON object per line). Do not rewrite existing lines; treat the file as append-only.

## Quick procedure

1. Run `python3 -m tools.metrics.plan_lattice --snapshot <yyyymmdd>` to capture the pre-merge state.
2. Execute the merge/closure work.
3. Append a ledger entry with cost and gain estimates, linking to the receipts generated in step 2.
4. Re-run `python3 -m tools.metrics.plan_lattice --snapshot <yyyymmdd>` to capture the post-merge state.

The metric tool automatically reads the ledger and will populate the `proportion_index` once both cost and gain totals are non-zero.
