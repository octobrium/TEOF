---
title: Soften refinement acknowledgement checkpoints
batch: 20250921T094900Z
item: 01
ocers_target: Observation↑ Autonomy↑
risk_score: 0.4
generated: 20250921T09:49:00Z
status: adopted
note: Adopted policy to reduce per-refinement human acknowledgements.
---

# Proposal

## Problem
Our current refinement loop pauses after every iteration and requires a human to acknowledge the summary before the next step. This was useful while we hardened receipts and guardrails, but now it adds overhead even when automation has low-risk follow-up steps ready.

## Proposal
Allow trusted agents to advance through multiple refinements without waiting for an explicit “proceed” after each summary, provided:

1. The plan remains within scripted guardrails (no DNA/ethics changes, no new guardrails).
2. Receipts hygiene (index + latency bundle) runs at the end of the batch and is shared automatically.
3. The agent flags any uncertainty or policy boundary by escalating to the manager-report channel immediately.

Implementation idea:
- Document a “batch refinement” preset in `docs/workflow.md`.
- Session tooling (`session_brief --preset operator`) emits a checklist receipt for the whole batch.
- Manager-report pings only at batch boundaries or when the agent explicitly requests guidance.

## Alternatives
- Keep the per-refinement acknowledgement (status quo).
- Require batched acknowledgements but still pause before each guard change.

## Risks
- Missing early warning if automation drifts: mitigated by receipts hygiene summary and alerts when missing receipts spike.
- Harder to audit: mitigated by bundling plan receipts and the hygiene summary JSON.

## Impact
- Faster iteration on low-risk guardrail and hygiene updates.
- Encourages deeper automation (e.g., nightly hygiene schedules) without human babysitting.

## Request
Gather feedback on the proposal and, if accepted, update `docs/workflow.md` and related DNA docs to capture the new batch acknowledgement policy.
