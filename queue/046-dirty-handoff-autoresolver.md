# Task: Dirty Handoff Auto-Resolver
Goal: build a CLI that scans `_report/session/*/dirty-handoff/` receipts, tracks their age, nudges owners, and escalates long-lived dirty states.
Notes: emit JSON summary + optional bus message; integrate with coord dashboard and future automation loops.
OCERS Target: Observation↑ Self-repair↑
Coordinate: S3:L5
Sunset: merged CLI + docs + tests.
Fallback: continue manual monitoring via dashboard alerts.
