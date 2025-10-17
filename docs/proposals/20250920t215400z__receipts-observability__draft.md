---
title: Elevate receipts observability and automation cadence
batch: 20250920T215400Z
item: 01
systemic_targets: ["S6", "S5", "S1"]
layer_targets: ["L5", "L6"]
risk_score: 0.2
generated: 20250920T215400Z
note: Draft proposal to accelerate evidence-driven development velocity.
---

# Proposal

## Task: Build a receipts observability rail for TEOF acceleration

### Goal
Increase development velocity without sacrificing provenance by making repo receipts queryable, automating the operator-mode checklist, and adding cadence metrics for observation-to-action loops.

### Acceptance
- Add a receipts indexer command (e.g., `python -m tools.agent.receipts_index`) that scans `_report/**`, `_plans/**`, and `_bus/messages/manager-report.jsonl` into a structured ledger (sqlite/jsonl) with timestamps and component tags.
- Extend `tools.agent.session_brief` (or introduce a preset) to emit an operator-mode checklist covering observation → plan → receipt steps with links to the relevant artifacts.
- Capture latency metrics by having consensus or session tooling log the delta between reflection notes and follow-up plans/PRs into the same ledger.
- Schedule a recurring “fractal hygiene” plan (weekly or biweekly) that reads the ledger to flag cold components or long-latency items, with receipts archived under `_report/maintenance/`.

### Systemic Rationale
- **S1 Unity** — central ledger surfaces where evidence is missing or stale.
- **S6 Truth** — standardized receipts and latency tracking make performance characteristics measurable.
- **S5 Intelligence / L6 Automation** — shared checklist keeps every agent aligned with the same refinement scaffold.

### Sunset / Fallback
- Sunset when the ledger shows sustained coverage (≥90% of tools touched monthly) and automation replaces manual hygiene sweeps.
- Fallback: if indexer proves noisy or expensive, limit scope to top-level tooling directories and rely on manual weekly review until constraints loosen.

---

## Open Questions
- How should ledger tags be defined to avoid re-encoding architecture rules?
- Do we need new CI checks, or is a periodic sweep (plan + receipts) sufficient?
- Should latency metrics live in the ledger or in existing consensus receipts?
