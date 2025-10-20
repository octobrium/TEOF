# Task: External Adoption Capsule
Goal: package a minimal, signed TEOF capsule + telemetry hooks so partner nodes can run the onboarding quickstart, report receipts back, and join the systemic lattice with zero bespoke setup.
Status: proposed (2025-10-19T22:20Z)
Notes: Advances CMD-3 (surface intent upfront) and CMD-4 (prefer reproducibility) by giving adopters a deterministic bootstrap plus consent policy defaults. Bundles documentation, policy checks, and reporting scripts that align with `docs/onboarding/README.md`.
Coordinate: S3:L3
Systemic Targets: S1 Unity, S2 Energy, S3 Propagation, S6 Truth
Layer Targets: L3 Properties, L5 Workflow
Systemic Scale: 3
Principle Links: expresses L2 Objective O3 (shared mental model) and O2 (trustworthy autonomy) by exporting a minimal environment that still honors alignment trail requirements.
Sunset: when `capsule/<version>/adoption/` hosts the bundle, onboarding docs reference it, and `_report/usage/adoption-telemetry/` captures partner run receipts.
Fallback: manual walkthroughs with ad-hoc instructions for each partner.

Readiness Checklist:
- docs/onboarding/README.md
- docs/quickstart.md
- capsule/ (release process)
- tools/autonomy/preflight.py

Receipts to Extend:
- `_report/usage/adoption-telemetry/` (new) logging partner runs + authenticity scores
- Anchor event noting the capsule release + signing key
