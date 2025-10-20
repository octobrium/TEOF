# Task: Autonomy Stress Harness
Goal: deliver a deterministic harness that red-teams `tools.autonomy.auto_loop` and conductor flows against synthetic failures (auth drops, missing receipts, stuck tasks) so unattended runs prove guardrail resilience before live use.
Status: proposed (2025-10-19T22:20Z)
Notes: Centers CMD-5 (respect safeties) and CMD-7 (escalate uncertainty) by simulating hazard scenarios inside a sandbox lane with receipts. Provides fixtures + CI target that block promotion when critical failure cases are unhandled.
Coordinate: S4:L6
Systemic Targets: S2 Energy, S4 Defense, S6 Truth
Layer Targets: L6 Automation, L5 Workflow
Systemic Scale: 4
Principle Links: supports L1 principles around defense and reversibility by ensuring automation halts coherently; extends `docs/automation/autonomy-conductor.md`.
Sunset: when the harness runs in CI and produces `_report/usage/autonomy-stress/` receipts per release candidate.
Fallback: manual spot tests with limited scenario coverage.

Readiness Checklist:
- docs/automation/autonomy-conductor.md
- tools/autonomy/conductor_loop.py
- tests/test_autonomy_next_step.py
- scripts/ci/check_autonomy_receipts.py (needs extension)

Receipts to Extend:
- `_report/usage/autonomy-stress/` (new) capturing scenario matrix + outcomes
- `memory/reflections/` entry logging any guardrail regressions surfaced
