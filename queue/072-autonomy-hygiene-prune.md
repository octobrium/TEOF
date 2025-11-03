# Task: Scope autonomy module pruning
Goal: Review coordinator/autonomy modules added since capsule current (36 vs 22) and define minimal consolidation plan before code removal.
Notes: Prioritise coordinator_* fan-out and large helpers (auto_loop, scan_driver, macro_hygiene); decide keep/split/archive per module manifest `_report/usage/autonomy-prune/modules-20251103T2040Z.json`.
Coordinate: S4:L5
Systemic Targets: S1 Unity, S2 Energy, S3 Propagation, S4 Resilience
Layer Targets: L4 Architecture, L5 Workflow
Sunset: Auto-close after pruning receipts reduce module delta ≤ +4 over baseline.
Fallback: Manual sign-off by governance with updated baseline if pruning is unjustified.
