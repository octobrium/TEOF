# Task: Enforce coverage awareness in pytest runs
Goal: add pytest coverage config + guard so TEOF knows its line-rate (target ≥70%) and fails fast when coverage drops.
Notes: memory/log entry (2025-11-08 codebase assessment) flagged “No coverage metrics configured.” Need repo-level pytest config (cov reports) and a guard (e.g., `python -m tools.tests.coverage_guard --threshold 0.70`) wired into runner/preflight.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: when pytest writes coverage reports by default + guard enforces threshold with receipts.
Fallback: keep running pytest without any coverage insight.
