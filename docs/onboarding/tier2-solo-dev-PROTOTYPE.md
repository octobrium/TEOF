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
2. Skim the executive summary of `docs/foundation/DESIGN-INTENT.md` so you understand why the DNA is structured around Pattern C before proposing changes.
3. Skim `docs/workflow.md` sections on the Architecture Gate and Operator Mode.
4. Experiment with plan scaffolding: `teof-plan new <slug> --summary "..." --scaffold`.
   - The repo ships a helper wrapper at `bin/teof-plan` so you can run the planner without installing the package; fall back to `python -m tools.planner.cli ...` if you prefer the explicit module call.
5. Capture a practice receipt using `python -m tools.receipts.main scaffold plan --plan-id <id>`.
6. Optional: run `python -m teof up --contribute --contributor-id <slug> --workload tier1-eval` to log a compute contribution receipt once Tier 1 succeeds.

## Coming Soon
- Step-by-step walkthrough with estimated times.
- Layer/Systemic badges to show why each action matters.
- Links to template plans and example receipts.

→ Until this guide is finalized, treat `docs/onboarding/README.md` as the canonical source for Tier 3 (multi-agent) onboarding and adapt the sequence for solo work as needed.
