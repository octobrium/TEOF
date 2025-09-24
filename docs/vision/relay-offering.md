# Relay Offering Blueprint — 2025-09-24

## Service Summary
- **Name:** Relay Insight Sprint
- **Promise:** deliver a synthesised research/strategy brief within 48 hours by
  leveraging the guarded API relay + decision loop.
- **Ideal clients:** founders, operators, or investors needing rapid due
  diligence or go-to-market insight.

## Deliverables
- 5–7 page PDF/Notion brief covering key questions supplied at intake.
- Annotated command log (what the agent executed and why) for auditability.
- Optional 30-minute review call (recorded summary).

## Pricing & Logistics
- **Tier A (Pilot):** $250, single focus question, no call.
- **Tier B (Standard):** $500, up to 3 questions, includes review call.
- Payment due upfront (Stripe/ACH secure link, refundable if guardrails halt).
- Turnaround target ≤ 48 hours from intake confirmation.

## Process
1. Client submits intake (mirrors `teof-decision-intake` schema).
2. Decision loop runs proposal/critique via `teof-decision-cycle`; outputs
   stored under `_report/usage/decision-loop/`.
3. Human review (Codex operator) approves commands, runs tasks via agent relay,
   logs results (`teof-impact-log`).
4. Deliverables sent; reflection + impact entry appended.

## Success Metrics
- First paid engagement booked and delivered (≥ Tier A).
- Client satisfaction ≥ 4/5 via quick survey.
- Time on task ≤ 6 focus hours per engagement.

## Next Steps
- Craft landing page + collateral (plan S2).
- Recruit pilot client (plan S3).
- Tie outcomes into decision/impact ledgers for iterative improvement.
