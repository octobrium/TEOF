# Task: Notify operators of upstream governance/workflow changes
Goal: emit alerts when files under `governance/` or core workflow docs change so agents know to revisit L0–L2 anchors before acting.
Notes: hook into existing guards (e.g. `scripts/ci/check_anchors_guard.py`) or add a watcher that writes `_report/usage/governance-alerts.json` and posts to manager-report.
Coordinate: S4:L5
Systemic Targets: S4 Resilience, S6 Truth
Layer Targets: L5 Workflow
Sunset: when automated alerts cover governance/workflow drift with documented operator response.
Fallback: rely on manual git diff reviews to catch high-layer changes.
