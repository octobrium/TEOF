# Fitness Lens (Tooling & Process)

**Purpose:** Select or prune tools/process by whether they *measurably* improve TEOF’s core traits:
**O-C-E-R-S** — Observation, Coherence, Evidence, Recursion, Safety.

## What qualifies as “mandatory” (preflight/CI blocking)
A change must be **invariant-improving** and **measurable**:
- **Observation/Provenance:** strengthens receipts, hashing, append-only, reproducibility.
- **Coherence/Determinism:** reduces nondeterminism or enforces canonical structure.
- **Evidence:** adds verifiable checks that catch real defects (broken links, missing receipts).
- **Recursion:** simplifies future work (fewer configs, fewer moving parts).
- **Safety:** improves degrade-to-safe behavior or policy compliance.

If it doesn’t clearly hit ≥1 of these with evidence → **optional by default**.

## Friction budget (defaults)
- **Config footprint:** ≤ 50 LOC added across repo.
- **New stacks:** avoid adding new runtimes unless mandatory above is proven.
- **Human cost:** ≤ 5 min setup for a contributor. More ⇒ optional.

## Sunset / Apoptosis
- New tools/process enter with a **sunset condition** (date or metric).
- If receipts show no material benefit by sunset, **prune**.

## Quick checklist (copy into PRs)
- [ ] States the **one systemic trait** this improves and how.
- [ ] **Receipts**: before/after or sample failure this catches.
- [ ] **Optional by default**, unless justified as invariant.
- [ ] **Sunset condition** defined (e.g., “remove unless it prevents ≥3 defects in 60 days”).
- [ ] **Fallback path** documented (how to disable/remove cleanly).

## Non-examples (keep optional)
- Pure style/format nits (e.g., blank-line rules) with no defect prevention.

## Examples (keep mandatory)
- Append-only audit; capsule hash; system prompt artifact; broken-link checks on docs; determinism harness.
