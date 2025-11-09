# 2025-11-09 Autonomy Stress Test (Exploratory)

Purpose: encode the “sprint until break” directive so automation can run with maximal leverage while keeping Pattern C (stable core, adaptive edge) intact.

## Directive
- **Objective**: Let an orchestration agent pursue an open directive (“deliver capability X”) end-to-end with as little human intervention as possible.
- **Scope**: Planner + bus lane only (no governance changes) until sustained evidence proves safe promotion.
- **Lane**: `_plans/exploratory` (auto-expiry 72h, receipts may be provisional).

## Guardrails (Observation First ≠ Human First)
1. **Observation gate** – before each act, the loop must replay the latest `memory/log.jsonl` entries touching its plan ID and verify hashes for `_report/usage/systemic-scan/` pointers. If hashes drift, it emits a dissent `bus_event` and pauses.
2. **Plan authority** – automation may only mutate files referenced in `plan_scope` for `2025-11-09-autonomy-stress-test`; every mutation updates the plan step status and records receipts.
3. **Receipts duty** – each loop iteration emits a status receipt under `_report/exploratory/2025-11-09-autonomy-stress-test/<ts>.json` describing inputs, outputs, guard results, and any deviations.
4. **Systemic hierarchy** – guardbreak precedence follows Unity→Meaning (`docs/foundation/systemic-scale.md`); if conflicting goals emerge, the loop defaults to satisfying the higher axis.
5. **Kill switch** – a single failure in (a) plan validator, (b) `teof scan --summary`, or (c) `scripts/policy_checks.sh` forces immediate rollback and triggers a manager-report reflection.
6. **Promotion gate** – no automation change exits exploratory lane without: (a) ≥2 successful stress sprints, (b) documented break analysis, (c) bindings update in `governance/core/L4 - architecture/bindings.yml`.

## Harness Requirements
| Component | Implementation sketch |
| --- | --- |
| **Directive loader** | Parse `_plans/exploratory/2025-11-09-autonomy-stress-test.plan.json`, resolve active steps, and seed queue of sub-directives. |
| **Self-prompt loop** | `teof foreman → frontier → plan_scope → critic → tms` run sequence; output feeds next iteration until break or completion. |
| **Observation hook** | Hash check for `memory/log.jsonl` + relevant `_report/` shards; store last seen pointers to detect drift. |
| **Break detectors** | (1) Plan validator strict mode, (2) `teof systemic-scan` trend thresholds, (3) `teof deadlock` warnings, (4) CI policy script. |
| **Receipt writer** | Structured JSON: timestamp, plan step, commands executed, guard verdicts, diff stats, break flag, follow-up actions. |
| **Reflection emitter** | On break, append `memory/reflections/reflection-<ts>-autonomy-stress.json` summarizing failure, referenced axes, rollback decision. |

## Success Metrics
1. Automation can advance at least one plan step (S2 or S3) without human edits outside the harness.
2. Receipts show <5 minute lag between action and recorded evidence.
3. Breaks detected by harness, not humans (first alert comes from automation receipt).
4. Kill switch restores clean working tree (`git status` empty) within one command after break.

## Failure / Break Catalog (initial trigger list)
| Break type | Detector | Required action |
| --- | --- | --- |
| **Receipt drift** | Observation hook hash mismatch | Emit dissent event, pause loop, request human sign-off. |
| **Scope violation** | `plan_scope` diff outside allowed paths | Auto-revert offending files, log break receipt. |
| **Policy guard fail** | `scripts/policy_checks.sh` non-zero | Roll back changes, capture manager-report reflection. |
| **Deadlock** | `teof deadlock` identifies recursion | Trigger override protocol from `docs/workflow.md`. |

## Next
1. Finalize directive-specific success criteria (what capability this sprint targets) and attach baseline receipts (S1 → done).
2. Build orchestration harness per table above (S2).
3. Run at least one stress sprint, collect break evidence, and decide on promotion/iteration (S3).
