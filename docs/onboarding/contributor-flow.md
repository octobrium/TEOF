# Plug-and-Play Compute Contribution

Status: Draft  
Scope: Tier 1 → S3 propagation (compute donors)  
Receipts: `_report/usage/contributors/<contributor_id>/contribution-<timestamp>.json`

## Purpose

Make it trivial for new nodes (humans or AI agents) to “donate compute” to TEOF
while keeping the observation chain intact:

1. Contributor runs a curated workload.
2. Automation captures artifacts + system metadata.
3. Receipts land in `_report/usage/contributors/…` so reviewers can audit what
   was executed, by whom, and why.

This unlocks propagation (S3) by lowering the barrier to entry: anyone who trusts
the repo can contribute work, earn proof, and hand that proof to downstream
systems (funding, governance, energy inflow). Contributions are summarized in
`_report/usage/contributors/summary.json` so new nodes can see prior runs.

## Workflow

1. **Clone + bootstrap:** contributors follow Tier 1 (`python -m teof up --eval`)
   to prove their environment matches repo expectations.
2. **Identify themselves:** each invocation supplies `--contributor-id
   <slug>`. We store contributor metadata in
   `_report/usage/contributors/<slug>/profile.json` (optional but encouraged).
3. **Choose workload:** initial menu focuses on:
   - `tier1-eval` (current flow),
   - `quickstart-smoke` (build + quickstart),
   - `systemic-scan` (lightweight `teof status` subset).
   Future workloads can be added under `workloads/<name>.py` and
   registered with the CLI.
4. **Run + capture receipts:** CLI runs the workload, writes artifacts under
   `artifacts/systemic_out/…` (or workload-specific folders), and records a
   receipt at `_report/usage/contributors/<contributor_id>/contribution-<workload>-<timestamp>.json`.
   ```bash
   python -m teof up --contribute \
     --contributor-id <slug> \
     --workload tier1-eval \
     --skip-install  # optional once environment is ready
   ```
5. **Publish summary:** contributors share the receipt hash (or PR) so other nodes
   can verify the donation.

## Receipt Schema

| Field | Type | Description |
| --- | --- | --- |
| `contributor_id` | string | Slug identifying the contributor (GitHub handle, agent ID, etc.). |
| `workload` | string | Workload identifier (`tier1-eval`, `quickstart-smoke`, …). |
| `workload_version` | string | Git ref or semantic version so runs remain comparable. |
| `generated_at` | string (ISO8601) | Timestamp of the receipt. |
| `artifacts` | object | Paths to generated artifacts (e.g., `artifact_dir`, `brief`, `score`). |
| `system` | object | OS, python version, CPU/GPU info (matches quickstart receipts). |
| `inputs` | object | Any workload-specific inputs or configuration knobs. |
| `hashes` | object | Hashes of key outputs (optional now, mandatory when scale increases). |
| `notes` | string | Free-form notes (e.g., “ran on donated RTX 4090 for 30 min”). |

Receipts should include `run_id` (matching automation conventions) once we
promote the CLI beyond prototype.

## Storage Layout

```
_report/usage/contributors/
  <contributor_id>/
    profile.json                    # optional metadata (contact, hardware)
    contribution-tier1-eval-<ts>.json
    contribution-quickstart-<ts>.json
    artifacts/
      <workload>/<timestamp>/…      # optional payload snapshots
```

Artifacts remain in canonical locations (`artifacts/systemic_out/…`,
`_report/usage/onboarding/…`) whenever possible; the contributor folder houses
only receipts + optional copies for convenience.

## CLI Hooks

- `python -m teof up --contribute --contributor-id <slug> --workload tier1-eval`
- Aliases: `bin/teof-contribute` (thin wrapper), `bin/teof-up --contribute`.
- Flags: `--skip-install`, `--reuse-venv`, `--output-dir`, `--workload`.
- Workloads register as callables returning `(artifacts, metadata)` so the CLI
  can serialize receipts uniformly.

## Next Steps

1. Publish example contribution receipts (e.g., `_report/usage/contributors/demo-agent/contribution-tier1-eval-20251107T232002Z.json`) and link them from README/Tier docs.
2. Expand documentation snippets (README, Tier guides) highlighting the contribution path.
3. Broaden the workload menu once telemetry lands (`quickstart-smoke`, `systemic-scan`, etc.).
