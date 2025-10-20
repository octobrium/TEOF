# Task: Systemic Health Radar
Goal: build a receipt-backed dashboard that fuses `_report/usage/`, `_plans/`, and `memory/` signals into a single systemic coverage index so stewards can spot gaps across S1–S10 before autonomy loops stall.
Status: proposed (2025-10-19T22:20Z)
Notes: Satisfies CMD-1 (anchor action in observation) and CMD-4 (prefer reproducibility) by wiring existing receipts into a normalized dataset; emits a guardrail receipt every run so unattended agents inherit the same picture. Couples backlog health, macro hygiene, authenticity, and plan coverage into one observable lattice.
Coordinate: S6:L5
Systemic Targets: S1 Unity, S2 Energy, S4 Defense, S6 Truth
Layer Targets: L5 Workflow, L4 Architecture
Systemic Scale: 6
Principle Links: uphold L0 observation by treating `_report/**` as append-only evidence; reinforces L3 properties for status telemetry documented in `docs/automation.md`.
Sunset: when `python -m tools.autonomy.systemic_radar` ships with CI guard + documentation and receipts prove coverage stays ≥ target thresholds.
Fallback: default to manual backlog health guard + macro hygiene runs with human triage.

Readiness Checklist:
- docs/automation/backlog-health.md
- tools/autonomy/macro_hygiene.py
- _report/usage/backlog-health/
- _report/usage/autonomy-status.json

Receipts to Extend:
- `_report/usage/systemic-radar/` (new) summarising axis scores + stale signals
- Memory reflection capturing pre/post gap snapshot
