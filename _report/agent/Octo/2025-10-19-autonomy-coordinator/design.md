# Design log for 2025-10-19-autonomy-coordinator

## Intent
- Provide a coordination layer so donated agent seats can join TEOF with minimal instructions (“plug and play”).
- Keep all activity observable: every action must flow through existing receipts, bus claims, and scans.
- Preserve reversibility. Managerial decisions must be traceable, overridable, and guardrail-aware.

## Roles
1. **Coordinator/Manager agent**
   - Watches `_plans/**`, `_bus/`, and `_report/usage/` for new work signals.
   - Chooses next objectives from `next-development.todo.json`, active plans, or explicit operator prompts.
   - Claims work via `tools.agent.bus_claim` (using new helper that verifies assignments).
   - Ensures each worker is on a fresh session (`session_boot`) and enforces scan/receipt cadence (`scan_trigger`, `foreman` routines).
   - Emits status notes to `manager-report` and writes receipts in `_report/agent/<id>/…`.
2. **Worker agents**
   - Receive a scoped plan step payload (task metadata, guard expectations, target branch).
   - Run standardized routines (`foreman` commands, `pytest` bundle, ledger updaters) under orchestration.
   - Attach receipts automatically and mark plan steps done/blocked with structured notes.
3. **Guardrail sentinels**
   - Existing tooling (`scan_trigger`, `commitment_guard`, systemic evaluators) triggered reactively by coordinator decisions.
   - Emit alerts or block execution when prerequisites (fresh session, receipts) fail.

## Event Flow
1. Coordinator boots → ensures own session handshake and reads backlog/plan registry.
2. Selects a task step (priority aware) → creates/updates bus assignment + claim.
3. Spawns or signals an eligible worker with a “work order” package (JSON manifest capturing plan step, branch, guard expectations).
4. Worker executes `foreman` routines (status, scan, tasks) pre/post change, runs step-specific commands, and pushes receipts.
5. Worker updates plan step status (via planner CLI) and returns summary to coordinator.
6. Coordinator reviews receipts; if guard outputs clean, mark step complete or queue follow-up; else escalate (block plan, emit warning).

## Artefacts / APIs
- **Manifest format:** JSON describing `plan_id`, `step_id`, `objective`, `commands`, `expected_receipts`, `rollback`.
- **Coordinator state store:** `_report/agent/<manager>/state.json` maintaining queues, active workers, guard incidents.
- **Worker envelope:** per-run receipt `_report/agent/<worker>/runs/<timestamp>.json` referencing git commit, plan updates, scan output.
- **Metrics dashboard:** aggregated stats under `_report/usage/autonomy-coordinator/summary.json` (active seats, successes, blocked operations).

## Guard Integration
- Use `tools/autonomy/scan_trigger` with watch prefixes for plan + receipts to avoid blind loops.
- Enforce `session_boot` freshness before any bus event; workers run with `--sync-allow-dirty` only when receipts capture that state.
- Leverage systemic evaluator for plan manifests (ensure objectives remain truth-aligned).
- Coordinator cross-checks new receipts via checksum helper (`write_receipt_payload`) to keep ledger append-only.

## Risks / Mitigations
- **Runaway automation:** include “circuit breaker” flag in coordinator state. If scans return high-severity issues, pause new assignments.
- **Conflict with human operators:** coordinator respects existing claims; only auto-claims when assignments are free. Mirror assignments to `manager-report`.
- **Receipt drift:** automate proof attachment (e.g., BTC ledger helper) to avoid manual missteps; fail fast on missing evidence.

## Next steps
- Step-1: formalize orchestrator interfaces + manifest schema (worker input/output contract).
- Step-2: build manager prototype CLI/module that reads backlog, claims tasks, and dispatches manifests.
- Step-3: implement worker harness (probably wrapper around `foreman` + plan CLI) with dry-run support.
- Step-4: wire guardrails (scan trigger, systemic checks) and produce regression tests for orchestrator decisions.

All new automation must cite L5 (workflow) while guarding S1/S6/S7. Receipts tied to this plan live under `_report/agent/codex-4/autonomy-coordinator/`.
