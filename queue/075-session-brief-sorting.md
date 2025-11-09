# Task: Fix session_brief timestamp sorting
Goal: make `python -m tools.agent.session_brief` robust when bus messages mix ISO formats so the CLI always prints status instead of crashing.
Notes: current sort key falls back to `datetime.min` (naive) which collides with aware UTC timestamps and raises `TypeError: can't compare offset-naive and offset-aware datetimes`. Normalize the fallback (and ideally parsing) so sorting never fails, add regression tests, and document the guard.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: when session_brief can safely summarize any bus lane.
Fallback: operators manually open `_bus/messages/*.jsonl`.
