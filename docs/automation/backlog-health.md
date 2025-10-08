# Backlog Health Guard

The `backlog_health` guard evaluates `_plans/next-development.todo.json` and
surfaces when the pending work queue drops below a safe threshold. When the
threshold is breached the guard recommends queue entries to restock the backlog
and writes a reusable receipt.

## Usage

```bash
python -m tools.agent.backlog_health --threshold 3 --candidate-limit 5
```

Key flags:
- `--next-development`: override the default backlog source path.
- `--threshold`: minimum pending items required before triggering a breach.
- `--candidate-limit`: how many queue entries to surface when the backlog is low.
- `--fail-on-breach`: exit with status 1 if the backlog needs replenishment
  (useful in CI or automation loops).
- `--no-write`: print metrics without writing a receipt.

Receipts land under `_report/usage/backlog-health/` and include:
- `pending_count` and `pending_items` snapshot with priority metadata.
- `pending_threshold_breached` boolean.
- `replenishment_candidates`: queue entries (path, coordinate, OCERS target) to
  convert into the next plan.

Run the guard after scans or autonomy batches so agents see the next
prioritized work without guessing.

`python -m tools.agent.batch_refinement` now invokes this guard automatically.
The batch run will stop with a non-zero exit if pending items drop below the
threshold unless `--allow-backlog-breach` is supplied. Receipts continue to land
under `_report/usage/backlog-health/` so stewards can restock the queue before
automation resumes.
