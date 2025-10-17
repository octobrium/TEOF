# CI Guardrail Guarantees

This one-pager summarises the invariants enforced by our automation. Each guard maps to the systemic targets it protects (legacy retired observation loop references remain for archival context). Use it as the quick reference when reviewing receipts or deciding which scripts to run locally.

| Guard | Command | Protects |
| --- | --- | --- |
| DNA layout | `scripts/ci/guard_dna.sh` | Observation & Coherence — locks the repo topology, enforces `capsule/current → vX.Y`, verifies freeze artifacts, and now ensures capsule metadata files agree on the active version. |
| Capsule hygiene | `scripts/ci/guard_apoptosis.sh` | Reproducibility — blocks duplicate `extensions/` trees and confirms freeze artifacts exist alongside the symlink. |
| Capsule hashes | `scripts/ci/check_hashes.sh` | Reproducibility — recomputes SHA-256 digests for `capsule/<version>/` and fails when hashes drift. |
| Quickstart smoke | `scripts/ci/quickstart_smoke.sh` | Reproducibility & Self-Repair — proves `pip install -e .` + `teof brief` still emits canonical artifacts. |
| Import policy | `scripts/policy_checks.sh` | Coherence — prevents `extensions/` from importing `experimental/` or `archive/`, keeping the kernel boundary intact. |
| Capsule cadence | `scripts/ci/check_capsule_cadence.py` | Observation — verifies capsule maintenance receipts so releases stay auditable. |
| Consensus receipts | `scripts/ci/check_consensus_receipts.py` | Coherence — requires recent consensus sweep receipts before merge. |
| Readability guard | `scripts/ci/check_readability.py` | Ethics & Observation — ensures docs specify agent actions clearly and cite receipts. |
| Plan hygiene | `scripts/ci/check_plans.py` | Reproducibility — validates plan JSON, requiring steps, git-tracked receipts, and checkpoints. |
| Memory ledger | `scripts/ci/check_memory_log.py` | Observation — stops malformed entries from landing in `memory/log.jsonl`.

## Preflight expectations
`tools/agent/preflight.sh` and `bin/preflight` call the same invariants a contributor is expected to run before requesting review. When a guard fails, cite the command from the table and attach the receipt so reviewers can trace the fix.

## Adding new guards
When you extend the suite:

1. State the systemic targets it protects (S#).
2. Add the command to this table (and `docs/quick-links.json`).
3. Wire it into CI + preflight so contributors exercise it locally.

This keeps the guardrail story observable at a glance while we continue to harden the system.

## Advisory checks (non-blocking)
- Canonical status audit — `scripts/ci/check_canonical_status.py`
  - Ensures only the expected core governance files (L0–L5) declare `Role: Canonical` and that none are missing the header. Prints WARN lines on mismatch and exits 0.
- Plan receipts existence — `scripts/ci/check_plan_receipts_exist.py`
  - Warns when receipts listed in plans or steps are missing or not tracked by git. Prints WARN lines and exits 0.
- Receipts hygiene bundle — `python -m tools.agent.receipts_hygiene`
  - Generates `_report/usage/receipts-index-latest.jsonl`, `_report/usage/receipts-latency-latest.jsonl`, and `receipts-hygiene-summary.json`. Use for periodic sweeps; leave artifacts for audit.
