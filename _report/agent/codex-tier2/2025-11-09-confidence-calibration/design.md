# Confidence Calibration Analytics — Pipeline Design (2025-11-09T05:30Z)

## Architecture
- **Collector**: scans `_report/agent/*/confidence.jsonl` + matching `_report/agent/*/*/summary.json` or plan receipts; join on `plan_id` / `task_id` + timestamp. Implement as helper in `tools.autonomy.confidence_calibration`.
- **Normalizer**: assign each entry `confidence` (0-1), `outcome` (1 for completed/passed, 0 otherwise), `delta = confidence - outcome`.
- **Aggregator**: windows of last N=20 plans per agent plus global summary; metrics: mean delta, mean absolute delta, Brier score, overconfidence rate (delta>0.2), underconfidence rate (delta<-0.2).
- **Alert Engine**: triggers when |mean delta| > 0.15 across last N plans or overconfidence rate > 30%; emits `_report/usage/confidence-calibration/alerts-<ts>.json` and bus event `confidence-alert` referencing receipts.
- **Report Generator**: writes `_report/usage/confidence-calibration/summary-<ts>.json` + Markdown dashboard showing per-agent tables; optional `--markdown` output for manager-report attachments.

## CLI Surface
```
python -m tools.autonomy.confidence_calibration collect --out artifacts/conf-cal/latest.json
python -m tools.autonomy.confidence_calibration aggregate --source artifacts/conf-cal/latest.json --window 20 --out _report/usage/confidence-calibration/summary-<ts>.json
python -m tools.autonomy.confidence_calibration alerts --summary <path> --emit-bus
```
- `collect` stage caches joined records; `aggregate` computes metrics; `alerts` evaluates thresholds + sends bus messages via `tools.agent.bus_event`.

## Integration Points
- Hook `teof scan` critic to flag agents with `overconfidence_rate > 0.3` (pull summary JSON).
- Add docs snippet to `docs/automation/confidence-metrics.md` describing CLI usage and thresholds.
- Optionally run nightly via CI job referencing this CLI.

## Testing Plan
- Fixture dataset with synthetic confidence/outcome pairs to validate metrics + alerts.
- CLI tests verifying JSON outputs and bus event stubs (use monkeypatch).

Next step: implement collector/aggregator CLI (Plan S3) and emit first summary receipt.
