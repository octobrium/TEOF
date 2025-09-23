# Decision Loop Blueprint — 2025-09-23

Goal: give TEOF a repeatable process that delivers optimal answers on demand
while honouring L0–L3 guardrails and logging impact.

## 1. Intake
- Use conductor or a dedicated CLI to capture decision requests:
  - Goal / desired outcome
  - Constraints (time, risk, ethics)
  - Success metric (quantitative when possible)
- Store the intake record under `memory/decisions/` using
  `teof-decision-intake` and reference the relevant objectives (O1–O7).

## 2. Deliberate & Critique
- Generate a first proposal via conductor prompt → agent relay (multi-LLM or
  Codex) ensuring diff/test guardrails are stated.
- Run a critique pass (second neuron or Codex review) that checks alignment with
  L1 principles and highlights trade-offs. `teof-decision-cycle` emits proposal
  and critique prompts for a given decision record.
- Optionally iterate until both proposal and critique receipts exist.

## 3. Execute & Measure
- Apply approved commands/tests or hand off to human executor.
- Immediately capture a reflection (`teof-reflection-intake`) so learning feeds
  back into L0/L2.
- Log the outcome/value via `teof-impact-log`, linking to the decision receipts.

## 4. Governance Hooks
- Preflight: consent & authenticity checks before any unattended action.
- Post-cycle metabolism: every decision emits reflection + impact entries.
- Dashboard: extend `teof-objectives-status` and future CI checks to flag stale
  decisions or missing impact records.
