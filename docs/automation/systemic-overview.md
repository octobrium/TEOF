<!-- markdownlint-disable MD013 -->
# Systemic Metadata Overview

**Status:** Living  
**Purpose:** Document the systemic axis (S1–S10) and layer (L0–L6) metadata that replaced legacy loop fields across TEOF.

TEOF now encodes alignment intent explicitly through **systemic targets** and **layer targets**.  
This note explains the lattice, how the codebase consumes it, and how to keep automation,
plans, and docs coherent with the constitution.

> Quantitative metric design for the core axes lives in [`docs/automation/systemic-metrics.md`](systemic-metrics.md).

---

## 1. Why systemic targets?

The legacy loop (Observation → Coherence → Ethics → Reproducibility → Self-repair) served as
an interim guardrail for receipts. It bundled multiple concerns into a single label,
making automated validation brittle and unclear.

Systemic targets separate concerns into two orthogonal co-ordinates:

- **Systemic axis (`S1`–`S10`)** – which constitutional vector the work advances.
- **Layer target (`L0`–`L6`)** – which governance layer the artifact operates within.

This mirrors the layered workflow (`docs/workflow.md`) and enables automation to reason
about impact and precedence without heuristics.

---

## 2. Canonical definitions

Use `docs/foundation/systemic-scale.md` for canonical descriptions.  
Quick reference:

| Axis | Name        | Failure mode                 | Notes |
|------|-------------|------------------------------|-------|
| S1   | Unity       | Fragmentation                | Stable frame of reference |
| S2   | Energy      | Stasis / entropy             | Capacity for change |
| S3   | Propagation | Isolation                    | Signal flow |
| S4   | Resilience  | Degradation                  | Preserve coherence |
| S5   | Intelligence| Rigidity / overreaction      | Recursive refinement |
| S6   | Truth       | Delusion                     | Disciplined evidence |
| S7   | Power       | Impotence                    | Directed leverage |
| S8   | Ethics      | Destruction                  | Stewardship of power |
| S9   | Freedom     | Brittleness / dissolution    | Adaptive range |
| S10  | Meaning     | Nihilism                     | Integration across axes |

Layer targets map directly to the workflow’s architectural ladder:

- `L0` Observation  
- `L1` Principles  
- `L2` Objectives  
- `L3` Properties  
- `L4` Architecture  
- `L5` Workflow  
- `L6` Automation

Artifacts may operate in multiple layers (e.g., a plan spanning `L4` and `L5`);
always list the primary layer first.

---

## 3. Required metadata fields

All plans and queue entries must include:

- `systemic_targets`: sorted list of `S#` tokens, deduplicated.
- `layer_targets`: list of `L#` tokens (optional if redundant with `layer` field).
- `systemic_scale`: highest axis number the work must satisfy before deployment.
- `layer`: primary layer of execution.
- `systemic_scope` (optional but recommended for branches/programs): human-readable namespace (e.g., `apps/market-analyzer`) signalling that the listed targets apply within that program rather than the trunk.

Automation enforces these fields via:

- `tools/planner/cli.py` – `teof-plan new` infers or validates tokens.
- `tools/planner/validate.py` – rejects missing/invalid systemic metadata.
- `tools/planner/systemic_targets.py` – canonical token parsing/sorting helpers.
- `extensions/validator/teof_systemic_min.py` – CLI for scoring text payloads.
- `tests/test_systemic_eval.py` / `tests/test_systemic_rules.py` – regression coverage.

---

## 4. Authoring guidelines

1. **Prefer the smallest set of axes.** If work primarily advances Truth with a resilience guard, prefer `["S6", "S4"]` over long enumerations.
2. **Default to the core fractal (`S1`–`S4`).** Only add `S5+` overlays when you can point to receipts that prove the higher-order obligation; otherwise the plan should stay on Unity → Resilience and inherit growth axes implicitly.
3. **Align scale with receipts.** `systemic_scale` must be the highest axis in `systemic_targets`; the planner CLI appends it automatically if missing.
4. **Document layer transitions.** When work moves between layers (e.g., plan → automation), capture the change in receipts and reference both layers.
5. **Explain deviations.** If a queue entry lists `S8` but your plan omits it, justify the divergence in the plan summary and update the queue entry if needed.
6. **Keep docs in sync.** Update relevant walkthroughs (`docs/quickstart.md`, `docs/automation.md`, plan templates) when introducing new axes/layers.
7. **Declare program scope.** When downstream apps reuse the lattice, set `systemic_scope` (and, if useful, `program_id`) so reviewers know whether `S4` or `S8` obligations are trunk-wide or local to the branch.

---

### Example: Reading plan metadata

Plan `_plans/2025-09-26-package-onboarding.plan.json` demonstrates how systemic
fields tie intent to evidence:

```jsonc
{
  "summary": "Ship a beginner-friendly install path (pip + quickstart) with receipts",
  "systemic_targets": ["S4", "S5", "S6"],
  "layer_targets": ["L5"],
  "systemic_scale": 6,
  "layer": "L5",
  "receipts": [
    "_report/usage/onboarding/build-20251003T190822Z.json",
    "_report/usage/onboarding/quickstart-20251003T190832Z.json"
  ]
}
```

- Additional build/quickstart receipts are recorded in the plan; the snippet
  above highlights the primary artifacts for clarity.
- `systemic_targets` highlights Resilience (S4), Intelligence (S5), and Truth
  (S6), showing that the plan keeps the quickstart receipts healthy while
  updating learning surfaces.
- `systemic_scale: 6` restates that Truth is the highest axis that must be
  satisfied before promoting changes downstream.
- `layer_targets` and `layer` show the work lives in workflow (L5); reviewers
  can jump straight to the cited receipts to verify the claim.

Use this pattern when reviewing new plans: check that the declared axes match
the receipts and that the highest axis is reflected in `systemic_scale`.

---

## 5. Migration checklist (legacy → systemic)

Use this when auditing residual legacy loop references:

1. Replace `legacy_loop_target` fields with `systemic_targets`/`layer_targets`.
2. Update CLI scripts to call `teof_systemic_min` (alias `teof-validate`).
3. Refresh docs, quickstarts, and baselines to mention `artifacts/systemic_out`.
4. Ensure tests reference `systemic` fixtures.
5. Run `python3 tools/planner/validate.py --strict` and `pytest tests/test_systemic_*.py`.

See `docs/automation/legacy-loop-retirement-inventory.md` for a complete audit trail.

---

## 6. Backwards compatibility

- `teof/eval/__init__.py` re-exports `evaluate` from the systemic heuristic so external tooling that imported `teof.eval` continues to function.
- CI now warns on legacy loop-specific paths (e.g., `artifacts/legacy_loop_out`).
- Legacy docs retain references with explicit archival notes; avoid new legacy loop mentions unless documenting history.

---

## 7. Next checks

- Run `scripts/ci/quickstart_smoke.sh` to ensure new metadata appears in receipts.
- Capture migration receipts under `_report/usage/` whenever systemic fields change.
- Periodically execute the residual audit (`docs/automation/systemic-residual-audit.md`) to prevent regressions.
