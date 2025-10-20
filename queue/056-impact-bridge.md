# Task: Impact Bridge Dashboard
Goal: wire the impact ledger (`docs/vision/impact-ledger.md`, `memory/impact/log.jsonl`) into backlog + automation receipts so every external outcome has a traceable plan, run, and systemic coordinate.
Status: proposed (2025-10-19T22:20Z)
Notes: Anchors CMD-1 and CMD-6 by grounding impact claims in observation and making them auditable. Builds a bidirectional loop: backlog items declare intended impact receipts up front, and completed runs update dashboards + objective counters.
Coordinate: S10:L2
Systemic Targets: S3 Propagation, S6 Truth, S7 Power, S10 Meaning
Layer Targets: L2 Objectives, L5 Workflow
Systemic Scale: 10
Principle Links: reinforces Objective O4 (real-world impact feedback loop) and ties Meaning-level outcomes back to Unity/Truth scaffolds.
Sunset: when `python -m tools.impact.bridge` emits dashboards under `_report/impact/bridge/` and plans expose a mandatory `impact_ref` field validated in CI.
Fallback: continue manual aggregation via memory reflections.

Readiness Checklist:
- docs/vision/impact-ledger.md
- memory/impact/log.jsonl
- tools/impact/case_study.py
- docs/automation/systemic-overview.md

Receipts to Extend:
- `_report/impact/bridge/` (new) storing stitched dashboards
- Memory reflection summarising baseline vs post-bridge clarity
