# Task: Confidence Calibration Bridge
Goal: correlate `_report/agent/*/confidence.jsonl` logs with plan outcomes so stewards see calibration drift before automation escalates.
Status: proposed (2025-10-20T07:54Z)
Notes: Extends `docs/automation/confidence-metrics.md` by pairing pre-task confidence with receipts and plan completion states; reinforces CMD-1 (anchor in observation), CMD-4 (prefer reproducibility), and CMD-5 (respect safeties) so ethics gates trip when overconfidence repeats.
Coordinate: S6:L6
Systemic Targets: S5 Intelligence, S6 Truth, S8 Ethics
Layer Targets: L6 Automation, L5 Workflow
Systemic Scale: 8
Principle Links: ties confidence telemetry to observable outcomes, ensuring autonomy decisions remain reversible and peer-auditable.
Sunset: when `python -m tools.agent.confidence_calibration` emits dashboards/receipts under `_report/usage/confidence-calibration/` and CI guards failures above tolerance.
Fallback: rely on manual comparisons between confidence logs and plan receipts without automatic alerts.

Readiness Checklist:
- docs/automation/confidence-metrics.md
- tools/agent/confidence_watch.py
- _report/usage/autonomy-actions/
- _plans/next-development.todo.json (pending items needing calibration hooks)

Receipts to Extend:
- `_report/usage/confidence-calibration/` (new) summarising drift metrics + alert thresholds
- Memory reflection capturing baseline vs post-calibration accuracy
