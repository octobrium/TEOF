---
title: Establish exploratory sandbox lane with rapid iteration guardrails
batch: 20251019T123900Z
item: 01
systemic_targets: ["S1", "S4", "S6"]
layer_targets: ["L4", "L5", "L6"]
risk_score: 0.3
generated: 20251019T123900Z
note: Draft to balance rapid experimentation with constitutional enforcement.
---

# Proposal

## Task: Create a governed sandbox lane for rapid exploration

### Problem
Core enforcement keeps TEOF coherent, yet it discourages fast hypothesis spikes because every iteration has to satisfy the full `_plans/` + `_bus/` + receipt cadence. Agents either slow to a crawl or bypass the constitution, eroding trust.

### Goal
Give agents a sanctioned path to explore quickly while guaranteeing the results remain observable, revertible, and promotable under existing L0–L2 contracts.

### Acceptance
- Introduce an exploratory plan scaffold (`teof-plan new <slug> --exploratory`) that stores under `_plans/exploratory/` with lighter required fields (owner, systemic hypothesis, auto-expiry).
- Capture outputs in a dedicated receipts lane (`_report/exploratory/<plan_id>/`) with “provisional” metadata and automated clean-up after expiry unless promoted.
- Extend `teof status` (or companion CLI) to track exploratory footprints separately from canonical metrics, highlighting items pending promotion or expiry.
- Define a promotion bridge: minimal checklist that pushes successful experiments back into the constitutional lanes (standard plan + receipts) before touching `extensions/`, docs, or automation surfaces.
- Document the sandbox process in `docs/workflow.md` (operator mode section) and link from `docs/architecture.md` so agents know where rapid work belongs.

### Systemic Rationale
- **S1 Unity** — keeps experimental work discoverable across agents through shared scaffolds and receipts.
- **S4 Defense** — containment + expiry prevent exploratory code from silently mutating core layers.
- **S6 Truth** — receipts stay append-only, making promotions auditable even with relaxed iteration steps.

### Sunset / Fallback
- Sunset when exploratory plans routinely graduate with receipts captured in canonical lanes and the backlog shows no velocity bottleneck.
- Fallback: if the sandbox increases noise or debt, tighten expiry windows and require mentor review before renewal, or disable the lane until new automation guards exist.

---

## Open Questions
- Should exploratory automation execute on CI, or run locally with opt-in guardrails?
- Do we need a dedicated bus channel for exploratory claims, or can we tag existing events?
- Which agents receive default sandbox privileges, and how are exceptions logged in memory?
