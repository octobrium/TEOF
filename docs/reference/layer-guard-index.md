# Layer Guard Index (TEOF)

This quick sheet links each constitutional layer (L0–L6) to the repo surfaces
that enforce it. Use it alongside `docs/architecture.md` when you need to jump
from the lattice to the exact scripts/tests.

| Layer | Guarded By | What it Enforces |
| --- | --- | --- |
| **L0 — Observation** | `memory/` append-only tooling (`tools/memory/*`), `_report/` receipts, `python -m tools.receipts.main` | Every observation must leave a receipt; hashes + append-only logs keep the aperture stable. |
| **L1 — Principles** | `governance/` anchors + `scripts/ci/policy_checks.sh` | Changes to the DNA (architecture/workflow/promotion) must align with canonical anchors. |
| **L2 — Objectives** | `_plans/*.plan.json`, planner validation (`python -m tools.planner.validate --strict`, `tests/test_planner_validation.py`) | Plans declare systemic/layer targets and checkpoints before work begins. |
| **L3 — Properties** | Determinism/receipts tests (`tests/test_vdp_guard.py`, `tests/test_ci_check_vdp.py`), `tools/agent/preflight.sh` | Reproducible outputs, volatile-data guardrails, and preflight verification. |
| **L4 — Architecture** | `docs/architecture.md`, placement guard (`scripts/policy_checks.sh`) | Enforces repo layout and import boundaries (e.g., no `extensions/` → `experimental/`). |
| **L5 — Workflow** | `docs/workflow.md`, agent preflight, bus tooling (`python -m tools.agent.session_boot`, `tools/agent/preflight.sh`) | Coordination rituals, receipts-before-push, manager-report cadence. |
| **L6 — Automation** | `tools/agent/*.py`, `_bus/` claim/event guards, CI workflows (`.github/workflows/*.yml`) | Automation executes plans while logging claims/events; CI mirrors the same checks. |

Cross-reference: run `bin/teof-syscheck` → `bin/teof-up` to ensure the
environment and receipts align with these guards before doing work.
