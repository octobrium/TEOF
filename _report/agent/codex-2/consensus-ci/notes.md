# Consensus CI Decision Notes — 2025-09-21

- **Observation:** recurring manual consensus sweeps + CI misses when receipts absent.
- **Principle:** OCERS Evidence↑ and Reproducibility↑ require deterministic signals before capsule moves.
- **Objective:** automate consensus receipt checks in CI so downstream capsule cadence can trust the state.
- **Properties:** stable summary under `_report/consensus/summary-latest.json`, guardrails workflow fails on missing receipts, docs/quick-links expose the contract.
- **Architecture:** docs/decision-hierarchy.md captures the fractal/decision themes; architectural section now references consensus-to-capsule bridge.
- **Workflow:** plan `2025-09-21-consensus-ci-integration` claims QUEUE-038 and documents manager pointer; next steps wire docs/tests/CI.
- **Automation:** upcoming guard will extend `scripts/ci/consensus_smoke.sh` and add new tests mirroring `test_ci_check_agent_bus.py`.
- **Amplify:** keep stable receipts + cross-layer docs; replicate directive-pointer pattern for consensus.
- **Refine:** the guard still needs implementation; capsule cadence docs must reference the new summary once built.
