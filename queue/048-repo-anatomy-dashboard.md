# Task: Repo Anatomy Dashboard
Goal: add automation that reports commit frequency, file counts, and last-touch metrics for major directories so agents know which surfaces are highways vs dirt roads. **Status: done (2025-10-03T22:02Z)**
Notes: `python -m tools.maintenance.repo_anatomy` now emits table/JSON summaries; receipts land under `_report/usage/repo-anatomy/`. Default directories cover docs/tools/_plans/_report/memory/tests/teof/agents/capsule.
Coordinate: S4:L5
Systemic Targets: S1 Unity, S2 Energy, S4 Defense, S6 Truth
Layer Targets: L5 Workflow
Sunset: closed—CLI shipped, docs updated, initial summary recorded.
Fallback: not needed; future enhancements can extend the CLI with additional metrics.

Readiness Checklist:
- tools/maintenance/ (existing maintenance scripts)
- docs/maintenance/macro-hygiene.md
- memory/reflections/reflection-20251003T211604Z.json
