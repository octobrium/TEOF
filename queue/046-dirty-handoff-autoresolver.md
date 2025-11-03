# Task: Dirty Handoff Auto-Resolver
Goal: build a CLI that scans `_report/session/*/dirty-handoff/` receipts, tracks their age, nudges owners, and escalates long-lived dirty states.
Notes: emit JSON summary + optional bus message; integrate with coord dashboard and future automation loops.
Coordinate: S3:L5
Systemic Targets: S1 Unity, S2 Energy, S3 Propagation, S4 Resilience, S10 Meaning
Layer Targets: L5 Workflow
Sunset: merged CLI + docs + tests.
Fallback: continue manual monitoring via dashboard alerts.
