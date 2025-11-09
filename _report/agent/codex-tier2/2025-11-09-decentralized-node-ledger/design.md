# Decentralized Node Incentive Ledger — Schema & CLI Draft (2025-11-09T05:15Z)

## Objectives
- Provide an append-only ledger for node stake/reputation adjustments with references to proofs.
- Give operators a CLI to append and inspect entries, enforcing policy hooks before new nodes gain autonomy.
- Feed `teof scan` so critic/ethics can verify ledger receipts exist for ND-069.

## Data Model
`_report/usage/node-incentive-ledger/<YYYYMMDDThhmmssZ>.jsonl`
Each line `LedgerEntry`:
```json
{
  "ts": "2025-11-09T05:15:00Z",
  "node_id": "codex-tier2",
  "action": "reward|penalty|grant|suspend",
  "stake_delta": 10,
  "reputation_delta": 0.05,
  "authority": "plan/claim id or governance anchor",
  "proofs": ["_report/agent/.../summary.json", "_bus/events/..."],
  "notes": "why change occurred",
  "hash_prev": "...",
  "hash_self": "sha256(line)"
}
```
- `hash_prev/hash_self` follow memory log style for tamper resistance.
- `authority` must reference a tracked plan (`_plans/...`) or anchor entry. CLI validates file existence.

Schema stored at `schemas/node-incentive-ledger.schema.json` for CI.

## CLI Surface (`python -m tools.autonomy.node_ledger`)
- `append --node codex-7 --action grant --stake 50 --rep 0.1 --authority _plans/... --proof receipt.json --note "Handoff"`
  - Writes JSONL entry, updates `_report/usage/node-incentive-ledger/latest.json`
- `show --node codex-7 --limit 5 --format table|json`
- `audit --node codex-7 --strict` verifies hashes + proof paths.

CLI depends on helper module `tools.autonomy.node_ledger` and uses shared receipt writer in `tools.usage.logger` for telemetry.

## Governance Workflow Integration
1. **Proposal** – plan references ND-069 and cites desired incentive change.
2. **Verification** – bus event `ledger-proposal` with receipts.
3. **Ratification** – anchor entry in `governance/anchors.json` capturing approvals/quorum (2-of-3 codex managers to start).
4. **Ledger Append** – CLI entry referencing plan + anchor + proofs; `teof scan` uses new receipts to clear critic warnings.
5. **Consumption** – `teof status` can summarize latest ledger entries (optional follow-up).

## Guardrails
- CLI refuses to append without at least one proof path tracked in git.
- `--dry-run` mode for previews.
- Tests cover: happy path append, missing proof, hash chain validation, audit CLI.

Next: implement CLI module + schema (Plan step S3) and wire tests/docs.
