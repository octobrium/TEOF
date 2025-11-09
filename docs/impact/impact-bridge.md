# Impact Bridge Dashboard

Tie real-world impact claims back to plans, backlog entries, and receipts so TEOF can verify Objective **O4** (impact feedback loop) during every run.

## Inputs

- `memory/impact/log.jsonl` — append-only impact ledger entries
- `_plans/**/*.plan.json` — plan metadata (must expose `impact_ref`)
- `_plans/next-development.todo.json` — active backlog, including `plan_suggestion`

## Command

```bash
python -m teof impact_bridge \
  --report-dir _report/impact/bridge \
  --summary _report/impact/bridge/latest.json \
  --format summary \
  --orphans-out _report/impact/bridge/orphans.json \
  --fail-on-missing
```

This command:

1. Loads the impact ledger and normalises each slug.
2. Joins plans via `impact_ref` and enriches them with backlog metadata.
3. Writes a JSON receipt plus a markdown dashboard under `_report/impact/bridge/`.
4. Exits non-zero when any plan lacks an `impact_ref` or references a missing ledger entry (useful for CI).

Use `--markdown <path>` to direct the dashboard elsewhere (e.g., `_report/impact/bridge/latest.md`). Add `--format json` when you need machine-readable output on stdout (pair it with `--no-write` to avoid mutating the repo during CI dry-runs). `--orphans-out <path>` writes a focused JSON summary of missing/orphan `impact_ref` entries so remediation scripts (or manual cleanup) can prioritize the backlog.

## CI Guard

`scripts/ci/check_impact_bridge.py` runs the bridge CLI against temp output paths, then asserts every plan exposes an `impact_ref`. This keeps CI reversible while blocking regressions when new plans are added without impact metadata.

## Receipts

Bridge receipts live under `_report/impact/bridge/`. Each JSON file includes:

- `stats` — counts of ledger entries, linked plans, backlog matches, and any gaps.
- `entries[]` — per-impact linkage table containing plan IDs, backlog IDs, and supporting receipts.
- `missing_impact_ref[]` / `orphan_impact_ref[]` — explicit remediation queues for alignment review.

The markdown dashboard surfaces the same information for operators during reviews.
