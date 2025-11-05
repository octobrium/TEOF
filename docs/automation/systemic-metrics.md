# Systemic Core Metrics (Design Note)

**Status:** Draft (pre-implementation)  
**Scope:** Quantitative signals for S1–S4 (Unity → Resilience)  
**Owner:** codex  
**Change log intent:** Align `teof/eval/systemic_min` and planner tooling with measurable receipts.

## 1. Motivation

Recent validator heuristics score systemic readiness via section titles and keywords.  
This catches format drift but fails to prove that the Unity → Resilience loop is actually healthy.  
To reconcile the gap, we will promote four quantitative indicators (one per core axis) that the validator, doctor, and CI can consume.

## 2. Proposed metrics

| Axis | Metric | Definition | Data source |
| --- | --- | --- | --- |
| **S1 Unity** | `coherent_receipt_ratio` | tracked receipts ÷ declared receipts for the plan or artifact (≥ 0.9 target) | `_report/**` receipts + git tracking (`tools/planner/validate`, `scripts/ci/check_plan_receipts_exist.py`) |
| **S2 Energy** | `available_capacity_ratio` | automation slots available ÷ slots requested during the plan window | `_report/usage/autonomy/*.json`, planner queue telemetry |
| **S3 Propagation** | `bus_latency_p95` | 95th percentile lag between bus event emission and acknowledgment by downstream agent | `_bus/events/*.jsonl`, `_report/agent/*/bus-watch/*.json` |
| **S4 Resilience** | `rollback_rehearsal_age` | hours since the last successful rollback or recovery drill touching the affected surface | `_report/ops/rollback/*.json`, `memory/log.jsonl` events tagged `rollback` |

### Thresholds

- `coherent_receipt_ratio ≥ 0.9`  
- `available_capacity_ratio ≥ 0.7` (context-dependent; guard raises warnings below `0.5`)  
- `bus_latency_p95 ≤ 120s` for L5 artifacts (looser for L6 automation if justified)  
- `rollback_rehearsal_age ≤ 168h` (one week) unless a memorandum records a justifiable exception

## 3. Instrumentation plan

1. **Receipt coverage**  
   - Extend `scripts/ci/check_plan_receipts_exist.py` to emit JSON summaries per plan (counts, tracked vs declared).  
   - Capture output under `_report/plan-metrics/<plan_id>.json`.  
   - Add CLI shim `python3 -m tools.planner.metrics` to aggregate for doctor runs.

2. **Capacity telemetry**  
   - Enhance automation status receipts to log queued vs available slots.  
   - Build a lightweight collector in `tools/agent/bus_status.py` that writes `_report/autonomy/capacity.json`.

3. **Bus latency**  
   - Update `tools/agent/bus_watch.py` to emit measurement receipts (e.g., `p95`, `max`, sample count).  
   - Add pytest coverage to ensure regression guard remains active.

4. **Rollback rehearsal**  
   - Add a small helper in `tools/maintenance/rollback_guard.py` (new) to parse `_report/ops/rollback/**`.  
   - Integrate with `tools/doctor.sh` so missing drills surface during health checks.

Each instrumentation step should land with receipts and an entry in `governance/core/emergent-principles.jsonl` documenting the new obligation.

## 4. Validator integration

Once metric receipts exist, update `teof/eval/systemic_min.evaluate` to:

1. Load an optional metrics payload (path passed via CLI or companion JSON).  
2. Replace heuristic scores with threshold checks:
   - `structure` remains section-based (ensures template compliance).  
   - `alignment`, `verification`, `risk`, `recovery` derive from metric success or explicit justifications.
3. Emit a richer JSON structure:
   ```json
   {
     "systemic": {
       "Unity": {"value": 0.92, "status": "pass"},
       "Energy": {"value": 0.75, "status": "warn"},
       "Propagation": {"value": 85, "status": "pass"},
       "Resilience": {"value": 96, "status": "fail"}
     }
   }
   ```
4. Fail plans in strict mode when any core metric is missing without a linked receipt or memorandum.

The CLI (`extensions/validator/teof_systemic_min.py`) will accept a second optional argument referencing the metrics JSON so doctor/CI can hand the data in.

## 5. Next actions

1. Implement metric collectors (one PR per metric to keep receipts focused).  
2. Backfill `_report/**` with at least one receipt per metric and attach to relevant plans.  
3. Update evaluator + tests (`tests/test_systemic_eval.py`) to consume the new payload.  
4. Refresh documentation (`docs/automation/systemic-overview.md`, `governance/core/L4 - architecture/bindings.yml`) once metrics enforce the properties.  
5. Log the change in `CHANGELOG.md` under “Automation” when the first metric lands.

Until the collectors exist, the existing heuristic remains as a compatibility fallback, but the validator should log a warning that quantitative metrics are pending.
