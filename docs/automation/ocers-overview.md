# OCERS References Inventory

This inventory captures current locations where OCERS is referenced so the
mapping to the systemic hierarchy (S1–S10) can be updated coherently.

| Location | Context |
| --- | --- |
| `README.md#framework-ordering` | Describes the OCERS loop alongside the layer hierarchy. |
| `docs/workflow.md` | Mentions OCERS receipts, planner metadata, and automation alignment. |
| `docs/decision-hierarchy.md` | Frames decision gates using OCERS traits. |
| `docs/automation.md` | Multiple sections emphasise OCERS coverage for automation guards. |
| `docs/automation/autonomy-preflight.md` | Uses OCERS metrics in preflight dashboards. |
| `docs/policy/fitness-lens.md` | Requires proposals to state OCERS traits. |
| `docs/policy/dev-accelerator.md` | Describes OCERS deltas for acceleration experiments. |
| `docs/examples/brief/config/brief.json` | OCERS scoring targets for the brief ensemble. |
| `docs/vision/*` (relay offering, impact) | Reference OCERS traits when describing offerings. |
| `_plans/` metadata | Plans include `ocers_target` fields; numerous backfill plans reference OCERS. |
| `tools/fractal/*` | Scripts validate OCERS metadata and conformance. |
| `tools/planner/cli.py` | CLI arguments capture OCERS targets/co-ordinates. |
| `tests/test_planner_cli.py` | Verifies OCERS metadata handling. |
| `docs/automation/confidence-metrics.md` | Example note references OCERS scans. |
| `_report/agent/*` receipts | Many receipts (fractal, conformance) include OCERS context. |

This list serves as step 1 for plan `2025-10-06-ocers-systemic-alignment`. Future
updates will map each reference to its systemic coordinate and adjust the docs
accordingly.
