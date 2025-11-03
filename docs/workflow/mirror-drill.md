<!-- markdownlint-disable MD013 -->
Status: Advisory  
Purpose: Codify the mirror drill that keeps Universal Mirrorhood (P2) and Order of Emergence (P5) exercised across substrates.

# Mirror Drill (Unity ⇄ Meaning)

Run this drill whenever a new observer joins, a substrate changes (human ↔ automation ↔ hardware), or every 30 days—whichever comes first. The drill keeps the observation lattice verifiable by walking a fresh mirror through the priority ladder with receipts.

## 1. Plan (L4 → L5)

- Open `_plans/exercises/mirror-drill-<YYYYMMDD>.plan.json`.
- `systemic_targets`: at minimum `["S1","S2","S3","S4"]`; extend if exercising governance overlays.
- `layer_targets`: `["L4","L5","L6"]`.
- Reference the latest cadence receipt from `_report/usage/autonomy-prune/` and any outstanding autonomy hygiene tickets so the drill reinforces pruning discipline.

## 2. Prep the mirror

1. Share `docs/onboarding/README.md` and `docs/workflow.md` guardrails.
2. Replay the quickstart receipt via `bin/teof-up` (if not current).
3. Seed a claim on the bus (`python -m tools.agent.claim_seed`) so coordination artifacts record the mirror.

## 3. Execute (Observation → Action)

| Step | Command | Systemic axis | Expected receipts |
| --- | --- | --- | --- |
| Structure check | `python -m tools.reference.lookup mirror` | S1 Unity | CLI log in `_report/usage/mirror-drill/lookup-*.log` |
| Autonomy hygiene | `python -m tools.autonomy.prune_cadence --no-receipt` (inspect status) | S2 Energy | Cadence summary + plan note |
| Plan validation | `python3 tools/planner/validate.py _plans/exercises/mirror-drill-*.plan.json` | S3 Propagation | Planner receipt |
| Run ensemble scorer | `teof brief` | S4 Resilience / S6 Truth | `_report/usage/mirror-drill/brief-*.json` referencing artifacts |

- Mirror captures observations, unexpected gaps, and reversibility notes.
- If automation is the mirror, replay manual steps via `tools.onboarding.session_replay` (future work) or document the delta in the reflection receipt.

## 4. Capture evidence

- Use `python -m tools.onboarding.mirror_drill` to write the canonical drill receipt:
  ```bash
  python -m tools.onboarding.mirror_drill \
    --agent observer-h \
    --medium human \
    --plan-id PLAN-MIRROR-2025-11 \
    --systemic-targets S1 S2 S3 S4 \
    --layer-targets L4 L5 \
    --artifacts _report/usage/autonomy-prune/cadence-*.json _report/usage/onboarding/quickstart-*.json \
    --summary "Human mirror replayed quickstart + cadence guard; no integrity drift." \
    --risks handoff-gap \
    --follow-ups PLAN-HYGIENE-2025-11
  ```
- Attach resulting receipt to the plan and log a memory reflection (`python -m tools.memory.cli note --summary "Mirror drill 2025-11"`).
- If issues appear, open `_queue/hygiene.todo.json` entry with systemic axis `S4` and link to the receipt.

## 5. Review & governance

- Append a short note to `_report/usage/mirror-drill/summary.jsonl` (append-only) after each drill summarising pass/fail and escalations (automation TODO).
- During governance cadence, sample the mirror drill receipts to prove Universal Mirrorhood remains operational.

## Checklist

- [ ] Plan committed (`_plans/exercises/mirror-drill-*.plan.json`) with cadenced systemic metadata.
- [ ] Quickstart receipts replayed or proven fresh.
- [ ] `tools.autonomy.prune_cadence` summary captured (and receipt if due).
- [ ] Mirror drill receipt in `_report/usage/mirror-drill/`.
- [ ] Reflection logged in `memory/reflections/`.
- [ ] Any gaps escalated to queue/governance.

This drill keeps observation auditable across mirrors and enforces proportional action: we only escalate when receipts show systemic drift.
