# Autonomy Module Consolidation

ND-067 calls for collapsing the sprawl of `tools.autonomy.*` helpers into a focused set of services with shared primitives, so automation stays observable and low-latency. This document captures the target architecture (Plan step **S2**) that implementation will follow.

## Goals

1. **Reduce duplication** – coordinator/conductor flows currently embed bespoke bus access, receipts, and guard hooks.
2. **Sharpen interfaces** – each automation lane (coordination, conductor, advisory, hygiene) should expose a dedicated CLI with consistent flags.
3. **Preserve telemetry** – consolidation must improve visibility (latency, queue depth, failure counts) via receipts under `_report/usage/autonomy-module-consolidation/`.
4. **Remain reversible** – migrations run through a CLI that emits recipes for roll-forward/rollback.

## Current overlap snapshot

| Domain | Existing modules | Pain |
| --- | --- | --- |
| Coordination control-plane | `coordinator_manager.py`, `coordinator_service.py`, `coordinator_guard.py`, `coordinator_worker.py`, `coordinator_loop.py` | Each module reimplements bus claims, receipts, and trust gates. |
| Conductor + auto loop | `auto_loop.py`, `conductor.py`, `chronicle.py` | Duplicate orchestration logic + conflicting receipt formats. |
| Status/radar | `systemic_radar.py`, `autonomy_radar.py`, `objectives_status.py` | Shared metrics live in siloed helpers. |
| Advisory/reporting | `advisory_report.py`, `decision_cycle.py`, `next_step.py` | Similar data fetch + templating stacks. |

## Target module map

| Service | Responsibilities | Existing modules to merge | New location |
| --- | --- | --- | --- |
| `coordination` service | Claim tasks, enforce macro hygiene, dispatch workers | `coordinator_*`, `commitment_guard.py` | `tools.autonomy.coord.service` (package exposes manager/worker CLI) |
| `execution` service | Run conductor/auto-loop sessions with receipts + guard rails | `auto_loop.py`, `conductor.py`, `chronicle.py` | `tools.autonomy.exec.{runner,guard}` |
| `signal` service | Produce systemic/macro/queue dashboards | `systemic_radar.py`, `objectives_status.py`, `backlog_steward.py` | `tools.autonomy.signal_service.*` sharing telemetry primitives |
| `advisory` service | Generate decision/next-step summaries for stewards | `advisory_report.py`, `decision_cycle.py`, `next_step.py` | `tools.autonomy.advisory.*` |

Each service now ships a manifest builder so coordinators can spin up receipts without bespoke scripts:

- `tools.autonomy.coord.manifest.CoordinatorManifestBuilder`
- `tools.autonomy.exec.manifest.ExecutionManifestBuilder`
- `tools.autonomy.signal_service.manifest.SignalManifestBuilder`
- `tools.autonomy.advisory.manifest.AdvisoryManifestBuilder`

Call `build_manifest_payload(agent_id=<id>, plan=<plan>, step=<step>)` to obtain the JSON payload, then `write_manifest(...)` to store it under `_report/agent/<agent>/manifests/`. These builders share a common base (`tools.autonomy.service_manifest.BaseServiceManifestBuilder`) so new services only override their default commands and expected receipts.

### Shared primitives

1. **Bus client** – lightweight wrapper in `tools.autonomy.shared_bus` for claims/events (now live with `emit_claim` powering `critic` + `ethics_gate`, replacing ad-hoc JSON writers).
2. **Receipt writers** – unify `write_receipt_payload`, latency/size metrics, and pointer updates.
3. **Policy config** – centralize baseline JSON (trust thresholds, freshness windows) under `docs/automation/autonomy-footprint-policy.md`.
4. **Coordination service** – `tools.autonomy.coord.service.CoordinationService` now feeds backlog selection + plan-step resolution so guard/loop CLIs reuse the same primitives instead of reloading JSON independently.

## CLI design (`python -m tools.autonomy.module_consolidate`)

```
python -m tools.autonomy.module_consolidate inventory
python -m tools.autonomy.module_consolidate plan --service coordination
python -m tools.autonomy.module_consolidate apply --plan <file> --dry-run
python -m tools.autonomy.module_consolidate telemetry
```

- `inventory`: prints module graph (import counts, duplicated primitives, receipt paths).
- `plan`: generates migration steps (files, tests, docs) + expected receipts. When `--out` is omitted the CLI writes `_report/usage/autonomy-module-consolidation/plan-<ts>.json` and updates `plan-latest.json`.
- `apply`: executes the plan (optionally `--dry-run` to confirm) and records receipts alongside the plan file.
- `telemetry`: captures before/after timings (module import latency, CLI runtime, duplication count) for dashboards. Without `--out`, receipts are written to `_report/usage/autonomy-module-consolidation/telemetry-<ts>.json` with a pointer `telemetry-latest.json`.
- `guard`: validates that `plan-latest.json` and `telemetry-latest.json` exist, are fresh (default ≤24h), and point to actual receipts. CI runs `scripts/ci/check_autonomy_module_consolidation.py` to keep the consolidation receipts healthy before pushes.

## Receipts & telemetry

- `_report/usage/autonomy-module-consolidation/plan-<ts>.json`: steps, affected modules, target services.
- `_report/usage/autonomy-module-consolidation/latency-<ts>.json`: import time, CLI runtime, duplication metrics.
- `_report/usage/autonomy-module-consolidation/latest.json`: pointer to most recent telemetry.

Metrics to track:

| Metric | Source |
| --- | --- |
| Module import count | `python -m tools.autonomy.module_consolidate inventory --json` |
| Duplicate primitive count (bus wrappers, receipt writers) | Static analysis output |
| CLI runtime (coordination/coordinator_manager) | CLI self-metrics (existing `--trace` support) |
| Receipt volume per run | `_report/usage/autonomy-*` ledger |

## Migration phases

1. **Plan (this document)** – define module map, CLI behaviours, telemetry contract.
2. **Scaffold CLI** – implement `inventory`, `plan`, and telemetry commands w/ receipts.
3. **Refactor services** – move coordinator/conductor/advisory modules into the new packages.
4. **Enable guard** – CI ensures no orphaned modules remain (`scripts/ci/check_autonomy_modules.py`).
5. **Monitor** – telemetry receipts compared before/after to prove latency/duplication reductions.

## Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Breaking existing automation entrypoints | CLI supports dry-run + generates rollback plan; maintain compatibility shims until downstream scripts migrate. |
| Receipt divergence | Shared receipt helpers enforce consistent payloads; telemetry receipts validated via CI guard. |
| Large refactor scope | Execute per-service (coordination → execution → signal → advisory) with receipts proving each step before merging. |

With this design locked, Plan **S2** for ND-067 can proceed to implementation (CLI + refactors) while keeping adoption auditable.
