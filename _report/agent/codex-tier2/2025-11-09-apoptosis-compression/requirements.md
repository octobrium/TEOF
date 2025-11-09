# ND-066 Apoptosis Compression Requirements (2025-11-09T05:35Z)

Sources:
- `_plans/next-development.todo.json` (ND-066 entry)
- `_plans/2025-11-09-apoptosis-compression.plan.json`
- Existing `_apoptosis/` snapshot layout

Needs:
1. **Bundle format** – tar/zip containing snapshot plus metadata (`meta.json` with branch, commit, receipts). Include SHA256 per file and overall hash.
2. **CLI** – `python -m tools.autonomy.apoptosis_compress bundle --source _apoptosis/<stamp> --out artifacts/apoptosis/<stamp>.tar.zst --receipt _report/agent/.../bundle.json` with optional `--restore` command.
3. **Receipts** – `_report/usage/apoptosis/bundles-<ts>.json` summarizing bundles, sizes, hashes, original receipts.
4. **CI guard** – ensure `_apoptosis/` raw dumps are not committed once bundled; lint verifies metadata present.
5. **Docs** – update `docs/automation/apoptosis.md` with compress/restore workflow.

Risks: data loss if metadata incomplete; mitigation: include manifest + hash chain.
