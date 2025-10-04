# Release Readiness Checklist — 2025-09-18

To treat `main` as a save point, ensure the following items are complete:

[x] **Ship missing CLIs**
  - `python -m tools.agent.claim_seed` and `python -m tools.agent.session_brief` merged with pytest coverage (`tests/test_claim_seed.py`, `tests/test_session_brief.py`) and docs refreshed.

[x] **Finalize governance bindings**
  - L4 bindings map lives at `governance/core/L4 - architecture/bindings.yml` with references in docs/architecture.md.
  - Capsule status ledger established (`capsule/README.md`, `capsule/v1.*/status.md`); docs updated accordingly.

[x] **Wire new helpers into CI**
  - GitHub workflow `.github/workflows/teof-ci.yml` now runs consensus smoke + pytest suites; manifest helper/prune/heartbeat checks in coverage.

[x] **Schedule the next capsule freeze**
  - Target set for 2025-09-19T02:00Z (see docs/maintenance/capsule-cadence.md).
  - Prepare `governance/anchors.json` update as part of that freeze.

[ ] **Clean the worktree before tagging** (pending)
  - Resolve outstanding staged/untracked files (manifests, queue state, temporary plans) so `main` reflects the release state.

Track progress in the manager-report bus and update this checklist as items close.
