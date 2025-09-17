# Cross-Instance Reconciliation (Sketch)

Goal: let two autonomous TEOF nodes compare state, negotiate meaning, and merge (or diverge) without a central arbiter.

## Minimal Handshake

1. **Hello packet**
   - `instance_id` (self-declared)
   - `commandments_hash` (SHA-256 of docs/commandments.md)
   - `latest_anchor_hash` (SHA-256 of governance/anchors.json)
   - `head_receipts_digest` (sorted hash of recent plan receipts)

2. **Delta exchange**
   - Each side shares receipts missing on the other (plans + `_report/...`)
   - Optional capability list (policies, safeties available)

3. **Meaning alignment**
   - Compare `commandments_hash`. If mismatch, exchange diff; annotate which commandment indices changed and why.
   - Swap latest reflections summaries (`docs/reflections/**`) to see how meaning evolved.

4. **Resolution**
   - If hashes match: create a shared anchor entry noting synchronized state.
   - If not: record a divergence anchor with rationale + receipts so future actors understand the fork.

## Evidence Bundles

| Artifact | Purpose | Minimal Fields |
| --- | --- | --- |
| Commandments hash | Quick trust contract | version, SHA-256 |
| Anchor chain | Provenance of governance | latest hash, optional delta |
| Planner receipts | Recent work + rationale | plan_id, step_id, receipt path |
| Reflection digest | Meaning shifts | file path, summary hash |

## Federation Notes

- Use append-only logs to share events; no retroactive deletions.
- Prefer hashed summaries to avoid leaking sensitive contents; full receipts only exchanged when both sides agree.
- Maintain reversibility: each federation step should have an anchor or memory log entry so rollbacks are possible.

## Open Questions

- How to handle conflicting capsules or immutable scope changes?
- Should there be a shared index of commandment revisions with semantic diff, not just hash?
- Can we bundle calibration metrics (e.g., acceptance vs. post-hoc outcome) to assess trustworthiness?

This sketch aims to keep meaning auditable (commandments + reflections) while memory (receipts + anchors) provides the evidence trail.
