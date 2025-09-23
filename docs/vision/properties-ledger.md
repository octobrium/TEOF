# Properties Ledger (L3)

Derived constraints that ensure L2 objectives remain trustworthy as TEOF
scales.

## P1 — Provenance Binding
Every actionable artifact (prompt, agent response, backlog item) must link to
its parent objective or reflection via receipts. Guardrail: automation writes
`source` references back to `memory/reflections/` or the objectives ledger.

## P2 — Guardrail Preflight
Before any unattended execution, automation records authenticity + CI status in
the receipt (`conductor.preflight`) and aborts when thresholds fail. Guardrail:
conductor, auto_loop, and pilots must check consent flags and log the decision.

## P3 — Post-cycle Reflection
Each autonomous cycle produces a metabolite: a reflection intake stub, backlog
update, or external artifact receipt explaining what changed and why. Guardrail:
automation calls `teof-reflection-intake --dry-run` (or equivalent) after every
cycle to cue review.

## P4 — Contributor Identity
Multi-neuron work records the agent/human identity in receipts and the backlog
history so cooperative cadence is measurable. Guardrail: bus events or receipt
payloads include `actor` fields tied to authorized manifests.

## P5 — External Signal Assimilation
External data/feedback is normalized into receipts with timestamps, hashes, and
impact notes before influencing backlog or objectives. Guardrail: ingestion
tools update `_report/usage/external-*` plus a corresponding plan receipt.

## P6 — Diff/Test Compliance
All automation-generated diffs respect declared diff limits and run the listed
tests before being marked completed. Guardrail: prompts state limits; pilots
verify returned commands before execution.

These properties should be referenced whenever new tooling or pilots are
designed to maintain the organism’s integrity.
