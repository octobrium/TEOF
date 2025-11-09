# Convergence Metrics Pipeline

Design reference for ND-071. The goal is to quantify how consistently multiple TEOF nodes stay aligned (hash parity, receipt coverage, anchor latency, commandment adoption, automation accuracy) and surface divergence before automation keeps executing.

## Inputs

| Source | Path | Notes |
| --- | --- | --- |
| Hash reconciliation receipts | `_report/reconciliation/*.json` | Already produced by `tools.reconcile_pipeline`; contain commandment/anchor hashes and missing receipt counts. |
| Receipt sync logs | `_report/network/receipt_sync/*.json` | Track missing receipts, fetch latency, peer IDs. |
| Plan metadata | `_plans/*.plan.json` | Provide CMD-tag usage to measure commandment adoption. |
| Automation audit results | `_report/usage/autonomy-audit/*.json` | Judge automation accuracy vs. human review. |
| Confidence calibration summaries | `_report/usage/confidence-calibration/summary-*.json` | Used for cross-signal correlation (optional). |

## Metrics

| Metric | Definition | Target |
| --- | --- | --- |
| `hash_match_rate` | matches / total comparisons from reconciliation receipts | ≥ 0.95 |
| `receipt_gap_rate` | missing receipts / total receipts per sync | ≤ 0.05 |
| `anchor_latency_minutes` | avg minutes from diff detection to anchor note | ≤ 30 |
| `cmd_tag_ratio` | plan steps referencing CMD-* / total steps | ≥ 0.80 |
| `automation_accuracy` | audited correct decisions / total audited | ≥ 0.90 |

## CLI (`tools.network.convergence_metrics`)

```
python -m tools.network.convergence_metrics collect \
  --reconciliation _report/reconciliation \
  --receipt-sync _report/network/receipt_sync \
  --plans _plans \
  --out artifacts/convergence/records-latest.json

python -m tools.network.convergence_metrics aggregate \
  --source artifacts/convergence/records-latest.json \
  --report-dir _report/reconciliation/convergence-metrics \
  --markdown docs/reports/convergence-metrics.md
```

### `collect` command

- Scans the latest reconciliation + receipt-sync receipts, extracts metrics per merge/run, normalizes timestamps, and stores a dense dataset for reproducibility.
- Associates plan metadata (CMD tags) by plan_id reference.

### `aggregate` command

- Computes rolling statistics (default window 14 days).
- Writes `_report/reconciliation/convergence-metrics/<timestamp>.json` plus pointer `latest.json`.
- Optional `--markdown` renders a table for managers.

### `guard` command (future)

```
python -m tools.network.convergence_metrics guard \
  --summary _report/reconciliation/convergence-metrics/latest.json \
  --hash-min 0.95 --gap-max 0.05 --latency-max 30 \
  --cmd-min 0.80 --automation-min 0.90
```

- Fails when thresholds breach and can emit `convergence-alert` bus events.

## Receipt schema

```json
{
  "generated_at": "2025-11-09T06:25:00Z",
  "window_days": 14,
  "metrics": {
    "hash_match_rate": 0.97,
    "receipt_gap_rate": 0.03,
    "anchor_latency_minutes": 22.4,
    "cmd_tag_ratio": 0.82,
    "automation_accuracy": 0.91
  },
  "thresholds": {
    "hash_match_rate": 0.95,
    "receipt_gap_rate": 0.05,
    "anchor_latency_minutes": 30,
    "cmd_tag_ratio": 0.8,
    "automation_accuracy": 0.9
  },
  "receipts": [
    "_report/reconciliation/reconcile-20251109T061500Z.json",
    "_report/network/receipt_sync/receipt-sync-20251109T060000Z.json",
    "_plans/2025-11-09-example.plan.json"
  ]
}
```

## CI integration

- Add `scripts/ci/check_convergence_metrics.py` to ensure the latest summary exists (age < 24h) and metrics meet thresholds.
- Optionally embed the guard inside `teof scan` under the critic component when the convergence CLI is present.

## Rollout steps

1. Implement `collect` + `aggregate` commands and land doc updates (this file + `docs/automation.md` entry).
2. Emit initial receipts + markdown dashboard and link from manager report.
3. Add guard script and wire to CI.
4. Extend `teof status` to summarize convergence metrics in the Autonomy Footprint section.

This design satisfies plan step **S2** for ND-071 (schema + CLI definition) and unlocks the pipeline implementation.
