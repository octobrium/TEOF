<!-- markdownlint-disable MD013 -->
# Decentralized Propagation Pilot

**Status:** Reference  
**Purpose:** Document how to reconcile receipts across independent TEOF nodes and promote decentralized operation.

This guide complements `2025-09-22-decentralized-propagation-pilot` and tracks the follow-on live exercise in `2025-10-17-decentralized-live-run`. It explains how to run the receipt sync tooling, interpret outputs, and escalate conflicts.

---

## 1. Goals & systemic targets

| Systemic axis | Layer | Rationale |
| --- | --- | --- |
| `S3` Propagation | `L3` Properties | Ensure signals flow between nodes without a central coordinator. |
| `S4` Defense | `L4` Architecture | Detect tampering or drift across governance artifacts. |
| `S6` Truth | `L5` Workflow | Keep receipts reproducible and comparable across deployments. |
| `S7` Power | `L5` Workflow | Escalate conflicts only when higher axes are satisfied. |

Automation (L6) must obey the hierarchy—only run reconciliation when nodes expose deterministic receipts and append-only governance histories.

---

## 2. Sample pilot (synthetic nodes)

Use the bundled example to familiarise yourself with the tooling:

```bash
python3 -m tools.network.receipt_sync \
  --config docs/examples/decentralized/receipt-sync/config.sample.json \
  --out-dir _report/network/$(date -u +%Y%m%dT%H%M%SZ)
```

Artifacts produced include `ledger.json`, `conflicts.json`, and `summary.md`. Store them under `_report/network/<timestamp>` and attach to the relevant plan.

Tracked goldens live in `docs/examples/decentralized/receipt-sync/` (ledger, conflicts, summary) and are referenced from `2025-09-22-decentralized-propagation-pilot`.

---

## 3. Real-world workflow

1. **Collect node snapshots** — Each steward exports their TEOF checkout (or capsule) with `_report/`, `capsule/`, and `governance/` directories intact.
2. **Prepare config** — Clone `docs/examples/decentralized/receipt-sync/config.sample.json` and list node IDs + absolute paths. Add `expect` patterns for receipts you require (e.g., `_report/usage/external-summary.json`).
3. **Run receipt sync** — Execute `tools/network.receipt_sync` with `--verify-anchor`/`--verify-capsule` (or set in config). Add `--verify-signatures` / `--require-signatures` once receipts are wrapped in external envelopes.
4. **Review summary** — Check `summary.md` for conflict counts and coverage gaps. Use `conflicts.json` to inspect differing hashes. A zero-conflict run indicates successful convergence.
   - `receipt_sync` now compares canonical payloads (signature/public_key metadata stripped) so matching receipts signed by different stewards converge without spurious conflicts; envelope differences remain visible under each artifact’s `envelopes` list in `ledger.json`.
5. **Log receipts** — Commit or archive the outputs under `_report/network/<run>` and link them to the relevant plan step before promoting decentralized properties.
6. **Escalate conflicts** — If conflicts persist, open or update a plan: highlight systemic axes involved (typically `S4`/`S6`), capture remediation actions, and broadcast via manager-report.

---

## 4. Signature policy

Once external sources sign receipts:
- Register public keys in `governance/keys/` and append anchors events.
- Run `tools.network.receipt_sync` with `--verify-signatures` to validate envelopes.
- Use `--require-signatures` to fail runs if receipts lack signatures where mandated.
- Combine with `tools.external.validate_systemic` to lint envelopes locally.

---

## 5. Extending beyond two nodes

- **Discovery helper:** `python3 -m tools.network.discover /path/to/repo-snapshots --expect '_report/usage/*.json' --out nodes.json`
- **Automated cadence:** Schedule receipt sync in CI or cron, writing outputs to `_report/network/<timestamp>` and posting `summary.md` or conflict snippets to manager-report.
- **Incident response:** When conflicts signal divergence, open a plan with systemic targets `["S3", "S4", "S6"]`, assign stewards, and attach the conflicting receipts before altering governance layers.

---

## 6. References

- Plan: `2025-09-22-decentralized-propagation-pilot`
- Sample datasets: `datasets/samples/decentralized/`
- Tooling: `tools/network/receipt_sync.py`, `tools/network/discover.py`
- Adoption resources: `docs/automation/systemic-adoption-guide.md`, `docs/automation/systemic-schema.md`, `docs/automation/systemic-alignment-matrix.md`
