# TEOF Tier 2: Solo Developer (Prototype)

> **Status**: Prototype placeholder — full content in development.  
> **Purpose**: Outline the upcoming 30-minute path for single-seat operators building with TEOF.

## What Tier 2 Will Cover
- Repository placement rules (based on `docs/architecture.md`)
- Minimal workflow ladder to ship a change safely (`docs/workflow.md`)
- Creating and updating plans with receipts
- Capturing custom artifacts under `_report/` for your work

## Current Actions
1. Review `docs/architecture.md` for the placement map.
2. Skim `docs/workflow.md` sections on the Architecture Gate and Operator Mode.
3. Experiment with plan scaffolding: `teof-plan new <slug> --summary "..." --scaffold`.
4. Capture a practice receipt using `python -m tools.receipts.main scaffold plan --plan-id <id>`.
5. Optional: run `python -m teof up --contribute --contributor-id <slug> --workload tier1-eval` to log a compute contribution receipt once Tier 1 succeeds.

## Coming Soon
- Step-by-step walkthrough with estimated times.
- Layer/Systemic badges to show why each action matters.
- Links to template plans and example receipts.

→ Until this guide is finalized, treat `docs/onboarding/README.md` as the canonical source for Tier 3 (multi-agent) onboarding and adapt the sequence for solo work as needed.
