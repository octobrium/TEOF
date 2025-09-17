# Convergence Metrics (Draft)

Goal: track whether independent TEOF nodes are moving toward consistent meaning and memory.

## Signals to Observe

1. **Hash alignment rate** — fraction of exchanges where commandments/anchors hashes match.
2. **Receipt coverage** — percentage of peer receipts fetched successfully (low missing receipts).
3. **Anchor reconciliation latency** — time from diff detection to recorded anchor note.
4. **Commandment tag adoption** — proportion of plan notes referencing CMD-* labels.
5. **Automation calibration** — compare automated decisions vs. post-hoc review outcomes.

## Potential Metrics

| Metric | Definition | Frequency | Owner |
| --- | --- | --- | --- |
| `hash_match_rate` | (# merges with matching hashes) / (total merges) | weekly | reconciliation maintainer |
| `receipt_gap` | missing receipts / total receipts per merge | per merge | pipeline |
| `commandment_usage` | plan steps with CMD-tags / total steps | weekly | plans maintainer |
| `automation_accuracy` | correct automation decisions / total audited | monthly | automation steward |

## Next Steps

- Instrument pipeline CLI to log metrics into `_report/reconciliation/metrics.jsonl`.
- Visualize trends in memory log or dashboards.
- Tie metrics to calibrations (confidence scores) in automation layer.

This sketch stays draft-level; fill in once the reconciliation pipeline stabilizes across instances.
