# Authenticity Stability Remediation (2025-11-09)

**Purpose:** provide a tracked reference for the remediation workflow that lifted
the `primary_truth` and `unassigned` authenticity tiers back above the guard
thresholds on 2025-11-09.

## Workflow

1. **Guard audit:** replay the ethics guard that triggered the alert and capture
   the JSON summary (`_report/ethics/guards/2025-11-09/*.json`). Summaries are
   paraphrased in `docs/ethics/2025-11-09-authenticity-stability.md` so plans can
   point to a stable artifact. The CLI now auto-detects canonical guard receipts
   stored under `_report/ethics/guards/<date>/`, so keeping the JSON there is
   enough for `teof scan/frontier/ethics` to prove coverage even if the plan
   forgets to list the file explicitly.
2. **Telemetry rebaseline:**
   - Run `python3 -m tools.external.authenticity_report --feeds primary_truth,unassigned`.
   - Log the remediation in `_bus/messages/AUTH-*` via
     `python3 -m teof bus_message --task AUTH-... --type status --summary "Authenticity remediation"`.
   - Update `_plans/next-development.todo.json` with any follow-up work.
3. **Remediation actions:**
   - Patch the guard inputs (ledger definitions + sample feeds) per the audit.
   - Re-run the guard (`scripts/ci/check_ethics_guard.py` in CI) and attach the
     fresh receipts to the authenticity tasks before releasing the claim.

## Receipts

- `docs/ethics/2025-11-09-authenticity-stability.md` (guard summary)
- `_bus/messages/AUTH-*/20251109T062400Z.jsonl` (status updates)
- `_plans/next-development.todo.json` (follow-up entries `ND-083`, `ND-084`)

These tracked references replace the transient `_report/...` files so strict plan
validation remains clean while still documenting the remediation steps.
