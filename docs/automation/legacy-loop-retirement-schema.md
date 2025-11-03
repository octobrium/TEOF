# legacy loop Retirement – Replacement Schema Draft

Generated on 2025-10-16 by codex-2 for plan `2025-10-16-systemic-retirement` (step **S2**).
This document specifies how we will replace legacy loop terminology with explicit
Systemic/Layer coordinates across documentation, metadata, and automation.

## 1. Coordinate Principles

- **Systemic axis (S1–S10)** captures *why* the work matters (Unity → Meaning).
- **Layer axis (L0–L6)** captures *how* the work is performed
  (Observation → Automation).
- Every artifact MUST expose the pair `(systemic_targets, layer_targets)` so
  humans and automation can triangulate intent without translating legacy loop.
- When legacy loop vectors appear, map them using the tables below and record
  both the systemic priority and the layer of execution. Mixed legacy loop phases
  often compress into a single systemic target; decompose as needed.

## 2. legacy loop → Systemic/Layer Mapping

| legacy loop Phase      | Primary Systemic Axes | Typical Layer Focus | Migration Notes |
| ---              | ---                   | ---                 | --- |
| Observation      | S1 Unity, S2 Energy   | L0–L2               | Already present in `Observation trigger` fields; ensure receipts cite S1/S2 explicitly. |
| Coherence        | S3 Propagation, S6 Truth | L3–L5            | Use `systemic_targets: ["S3", "S6"]` and record exact layer (e.g., `L4`). |
| Ethics           | S4 Resilience, S6 Truth, S8 Ethics | L4–L5      | Guardrails MUST list prerequisite axes (`["S4","S6"]`) before `S8`. |
| Reproducibility  | S5 Intelligence, S6 Truth | L3–L6          | Replace “Reproducibility↑” with `systemic_targets: ["S5","S6"]`; automation receipts stay under L6. |
| Self-repair      | S4 Resilience, S10 Meaning | L5–L6           | Encode escalation flows as `S4` guards that evolve into `S10` once recovery succeeds. |

When an legacy loop phrase implied multiple axes (e.g., “Coherence↑ Safety↑”), split
it into `systemic_targets` with priority ordering. Use the ordering rule from
`docs/foundation/systemic-scale.md`—higher axes MUST appear first if all are
being targeted simultaneously.

## 3. Metadata Specification

To retire `legacy_loop_target` fields, introduce the following replacements.

### 3.1 Plans (`_plans/*.plan.json`)

```jsonc
{
  "systemic_targets": ["S6", "S4"],
  "layer_targets": ["L4"],
  "systemic_scale": 6,
  "layer": "L4"
}
```

- `systemic_targets`: ordered list (highest priority first) of S-axis tokens.
- `layer_targets`: ordered list of L-axis tokens touched by the plan; defaults
  to the existing `layer` value if omitted.
- `systemic_scale`: single primary axis expressing the checkpoint (integer `1–10`,
  kept for backwards compatibility with existing receipts).
- **Removal:** delete `legacy_loop_target` once the new fields are populated. *(Completed in experimental branch on 2025-10-16; the planner CLI no longer accepts `--legacy-loop-target` and validators reject the field.)*
- **Validation:** extend `tools/planner/cli.py` and `tools/planner/validate.py`
  to require that every plan with `systemic_targets` also includes matching
  `layer_targets`. Fallback for legacy plans: emit warnings until step S3 flips
  the check to hard errors.

### 3.2 Queue Entries (`queue/*.md`)

Replace the `legacy loop Target` block with:

```
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
```

- If multiple systemic axes apply, separate with commas and keep priority order.
- For artifacts that previously used “Evidence↑”, map to `S6 Truth` and ensure
  the surrounding text explains what counts as evidence receipts.

### 3.3 Automation & CLI

| Surface | legacy loop usage today | Replacement design |
| --- | --- | --- |
| `teof scan` summary (`docs/automation.md`) | Displays legacy loop tallies | Replace table with per-axis counters (`S#`) and per-layer saturation; add `--legacy-loop` flag to keep backwards compatibility until S3 completes. |
| `extensions/validator` receipts | Accept `legacy loop` enums | Add schema fields `systemic_targets`/`layer_targets`; validator should reject legacy loop keys once migration finalizes. |
| `scripts/ci/check_queue_template.py` | Checks for `legacy loop Target` header | Update template to enforce the new headers and ensure comma-separated tokens parse. |

### 3.4 Reporting (`_report/**`)

- Update report generators to summarise work by `systemic_targets` and `layer_targets`.
- Historical legacy loop references inside archived runs remain untouched; mark them
  as legacy in inventory notes to avoid over-migration.

## 4. Execution Roadmap (Step S3 Preview)

1. **Validator updates** – teach planner and CI tools to enforce the new fields.
2. **Bulk doc edits** – apply scripted replacements for queue and plan records,
   ensuring ordering rules and token formats match the spec.
3. **Automation surfaces** – change CLI output, tests, and dashboards to report
   by systemic/layer axes.
4. **Cleanup** – once tooling accepts the new fields everywhere, remove the
   `--legacy-loop` shims.

## 5. Receipts & Next Actions

- This schema is the receipt for plan step `S2` (“Design replacement schema”).
- Implementation details now feed step `S3` (“Implement and validate migration”).
- Update `_plans/2025-10-16-systemic-retirement.plan.json` to mark `S2` as `done`
  with `docs/automation/legacy-loop-retirement-schema.md` listed as the supporting evidence.
