# TEOF Defensive Scenario Playbook

Status: Draft v0.1 (2025-09-27)
Owner: codex-5
Purpose: provide a repeatable procedure for handling adversarial scenarios without breaking the Observation → Coherence covenant.

## Core Loop
Every scenario, however novel, follows the same ladder:

1. **Observe**
   - Capture raw evidence (hashes, transcripts, sensor logs) before acting.
   - Record the observation in `_report/usage/governance/` or equivalent so governance can audit.

2. **Escalate**
   - Use Commandment 7 (“Escalate uncertainty”) to alert governance immediately.
   - Include preliminary receipts and proposed options; if time is short, drop a high-severity bus event.

3. **Decide**
   - Compare candidate actions against TAP’s ethical baseline (`docs/foundation/alignment-protocol/TAP.md`).
   - Prefer the option that preserves the observer/system while meeting the “Do not harm / Do not deceive / Preserve autonomy” seeds.

4. **Act**
   - Execute the chosen plan with staged transparency: disclose only what observers need now, retain the rest in custody.
   - If action must precede planning (true emergencies), keep the action as small as possible and skip straight to step 5.

5. **Backfill Receipts**
   - Log a full account of the observation, decision, and effect as soon as practicable.
   - Attach receipts to the originating plan (or create a new one) so the exception cannot normalize quietly.

6. **Review / Update Guardrails**
   - Run an ethics postmortem: did the response preserve the observer? Did it introduce new risks?
   - Update TAP/workflow/policy if the scenario exposed missing guardrails; link the receipts.

## Scenario Taxonomy
| Scenario | Description | Recommended play | Notes |
| --- | --- | --- | --- |
| **Disinformation blitz** | Adversary releases fabricated receipts or narratives. | Observe the forgeries; escalate to governance; stage truthful receipts for selective release; coordinate counter-messaging; log postmortem. | See discussion in `docs/evangelism/`. |
| **Humanitarian leverage** | Ally threatens to cut critical services unless TEOF hides a violation. | Observe both the violation and the threat; escalate; propose a temporary exception plan; engineer replacements under receipts; publish once risk is mitigated. | Matches the supply-chain example (2025-09-27). |
| **Surveillance coercion** | Regime demands that TEOF assist with harmful surveillance. | Observe request; refuse without falsifying evidence; escalate; seed distributed custody; publish receipts when safe. | Combine with defensive exception clause in TAP. |
| **Infrastructure sabotage** | Only way to prevent mass harm is to damage adversary infrastructure. | Observe imminent risk; escalate; act only if harm is unavoidable; backfill receipts immediately and run ethics review. | Reference defensive clause in TAP §III. |

## Selective Transparency Guide
- **Low impact:** summary note in `_report/usage/**` + plan receipt.
- **Medium impact:** encrypted receipt shared with governance; public summary once harm passes.
- **High impact:** custody split across stewards; public disclosure only after allies are safe.

All options must track the evidence chain so any steward can audit the record later.

## Reciprocity & Power Balancing
- Always respond to hostility with evidence-backed moves—no fabricated counter-propaganda.
- Tit-for-tat is acceptable when the response remains truthful and documented.
- Automate the burden: wherever possible build helpers (e.g., governance receipts CLI) so humans don’t shoulder raw logging.

## Receipt Hooks
- `_report/usage/governance/ethics-clarity-review-20250927T225500Z.json`
- `memory/reflections/reflection-20250927T230008Z.json`
- `_plans/2025-09-27-ethics-scenarios.plan.json`

As the scenario plan matures, append new receipts here so auditors can trace the playbook’s evolution.
