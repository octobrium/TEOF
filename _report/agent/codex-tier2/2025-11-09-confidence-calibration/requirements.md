# ND-068 Confidence Calibration Requirements (2025-11-09T05:26Z)

Sources: queue brief, docs/automation/confidence-metrics.md, tools/agent/confidence_watch.py, existing `_report/agent/*/confidence.jsonl` entries, and `_report/usage/autonomy-actions/` outcomes.

Needs:
1. **Data Inputs** – collect per-plan confidence logs (timestamp, value, note) and outcome receipts (plan status, pass/fail tests). Need linkage via plan_id + task_id.
2. **Storage/Schema** – new `_report/usage/confidence-calibration/<stamp>.json` summarizing calibration windows, plus rolling JSONL for alerts.
3. **CLI** – `python -m tools.autonomy.confidence_calibration` with modes: `aggregate` (compute drift metrics), `alerts` (emit events when |confidence - outcome| exceeds threshold), `report` (write markdown summary).
4. **Metrics** – track mean absolute calibration error (|confidence - accuracy|), Brier-style score, false positive ratio. Thresholds configurable per plan priority.
5. **Integration** – `teof scan` should surface high drift as critic anomalies; ethics should warn when repeated overconfidence occurs. Manager-report entry for alerts.
6. **Receipts** – each run writes `_report/usage/confidence-calibration/summary-<stamp>.json` plus per-plan drilldowns; tests cover aggregator.

Open questions:
- How far back should rolling window go (N plans vs time)?
- Should alerts auto-claim queue tasks for remediation? 
