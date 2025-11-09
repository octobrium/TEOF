# Autonomy Coordination Service (ND-067)

## Purpose
- Collapse the coordinator manager, guard, worker, and backlog heuristics into a single service layer (`tools.autonomy.coord.*`) so automation can select work, emit manifests, and guard runs without duplicating helpers.
- Treat `_plans/next-development.todo.json` as the canonical source of pending autonomy work, projecting each entry into a manifest + guard pipeline.
- Produce receipts for each selection + manifest so manager-report / bus logs can trace exactly which steps automation executed.

## Target Architecture
```
CoordinationService (tools/autonomy/coord/service.py)
 ├─ load_todo()               # parse next-development.todo.json
 ├─ load_plan(plan_id)        # cached plan loader with validation
 ├─ first_pending_step(plan)  # returns the first non-done step
 └─ select_work()             # returns (todo_item, plan, step)

coordinator_manager.py  → imports CoordinationService + ManifestBuilder
coordinator_guard.py    → uses CoordinationService for plan/step resolution,
                          runs systemic_min + scan trigger + worker harness
coordinator_worker.py   → executes manifest, emits receipts
```

## Receipts & Logging
- `_report/agent/<manager>/autonomy-coordinator/state.json` – guard state (plan, step, systemic verdict, scan status, worker exit).
- `_report/agent/<manager>/autonomy-coordinator/manifest-<ts>.json` – manifest receipts produced by `coordinator_manager`.
- `_bus/messages/ND-067.jsonl` – guard status appended via `teof bus_event log`.
- `_report/usage/autonomy-module-consolidation/` – plan + telemetry receipts already tracked by ND-067 plan.

## Guardrail Checks
1. **Systemic verdict** via `teof.eval.systemic_min` on plan summary/notes.
2. **Scan trigger** using `tools.autonomy.scan_trigger`; run scan before/after worker execution.
3. **Worker exit** – `coordinator_worker` must exit 0; non-zero triggers circuit breaker.
4. **Receipt update** – guard ensures `_plans/<id>.plan.json` is touched (plan scope + receipts).

## Next Steps
1. Port `coordinator_worker.py` to consume manifests from `tools.autonomy.coord.manifest` and emit `_report/agent/<worker>/runs/<ts>.json`.
2. Move bus/log handling into `CoordinationService` so every selection automatically logs to `_bus/`.
3. Add unit coverage around `CoordinationService.select_work` and the guard circuit breaker.
