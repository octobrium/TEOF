# TEOF Charter (Living Constitution)

**Purpose.** A durable, auditable contract that governs autonomous work across models and tools.

**Principles.**
- Verifiable-first: receipts (retired observation loop) + reproducibility always.
- Least privilege: narrow allowlists, budgets, diff caps, required checks.
- Determinism > cleverness: prefer small, reversible changes.
- Human override: maintainers can pause or revert at any time.
- Non-propagation by default: no self-replication without explicit approval.
- Model-agnostic: any provider may comply if it can produce receipts and diffs.

**Roles.**
- *Maintainers:* own policy, approve promotions, set budgets.
- *Bots/Agents:* propose bounded diffs via PRs with receipts; never merge.
- *Auditors:* review ledger and fitness trends.

**Allowed actions (default).**
- Paths: docs/**/*.md, governance/**/*.md, capsule/**/*.md, scripts/ci/**, Makefile
- No renames/deletes; small in-place edits only (≤ diff_limit).
- Labels: `bot:autocollab`
- Required checks: `teof/fitness`, `guardrails/verify`

This file is normative prose; machines read policy.json for exact constraints.
