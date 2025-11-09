# ND-067 Autonomy Module Consolidation Requirements (2025-11-09T05:42Z)

Sources: ND-067 backlog entry, tools/autonomy/* modules, _plans/next-development.todo.json.

Requirements:
- Identify overlapping modules (coordinator_manager, system_radar, node_runner) and classify shared primitives.
- Define target module map (core services, shared utils, adapters) with clear ownership + receipts.
- Telemetry: latency + duplication metrics before/after consolidation stored under `_report/usage/autonomy-module-consolidation/`.
- CLI: `python -m tools.autonomy.module_consolidate` to list modules, apply migrations, emit receipts.
- Docs: add architecture notes + migration playbook.
