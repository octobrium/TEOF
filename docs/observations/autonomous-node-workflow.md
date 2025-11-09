<!-- markdownlint-disable MD013 -->
Status: Draft
Purpose: Outline autonomous node workflow for decentralized TEOF deployments

# Autonomous Node Workflow (Draft)

1. **Bootstrap**
   - Pull latest main or capsule release.
   - Run `python3 -m tools.agent.session_boot --with-status` to register the node and capture receipts.
   - Sync governance anchors; verify signing keys.

2. **Work loops**
   - `teof scan --format json --out receipts/scan-<ts>.json` (store receipts under node-specific directory).
   - `teof status --out receipts/status-<ts>.md --quiet` for reproducible snapshots.
   - `teof ideas evaluate --format json --limit 5 --out receipts/ideas-<ts>.json` to surface promotion candidates.
   - Optional plan checks: `python3 -m tools.planner.cli show <plan>` to confirm step states before writing receipts.

3. **Receipts**
   - Each command output is stored with appended hash + signature (e.g., JSON includes sha256 and signer).
   - Bundle receipts are submitted via PR or receipt ledger; include plan/idea IDs.

4. **Promotion gate**
   - Node must confirm related plan/claim is active (`python3 -m teof bus_status --plan <id>`; legacy module path also works).
   - If guard fails, escalate to manual review; receipts flagged as provisional.

5. **Sync & cleanup**
   - Run `python3 -m tools.agent.task_sync` if tasks/plans were updated.
   - Publish summary receipts and commit/push (or upload to receipt mirror).
