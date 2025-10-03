# Task: Repo Anatomy Dashboard
Goal: add automation that reports commit frequency, file counts, and last-touch metrics for major directories so agents know which surfaces are highways vs dirt roads.
Notes: leverage git metadata; output to `_report/usage/repo-anatomy/summary.json` and expose a CLI (`python -m tools.maintenance.repo_anatomy`).
OCERS Target: Observation↑ Clarity↑
Coordinate: S4:L5
Sunset: close once dashboard CLI exists, documentation references it, and an initial summary lands in `_report/usage/`.
Fallback: if automation is heavy, document a manual command sequence under docs/maintenance/ and attach a receipt.

Readiness Checklist:
- tools/maintenance/ (existing maintenance scripts)
- docs/maintenance/macro-hygiene.md
- memory/reflections/reflection-20251003T211604Z.json
