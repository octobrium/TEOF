# Observation Receipt Graph – requirements sweep (2025-11-09)

## Context
- `python3 -m teof scan --format json --limit 5` (2025-11-09T04:54Z) still flags `ND-053` as missing receipts despite the queue brief documenting the objective.
- `queue/053-observation-receipt-graph.md` defines the scope (graph CLI + JSON schema linking plans, claims, receipts, and queue briefs).

## Key requirements distilled
1. **Traverse systemic artifacts**
   - Inputs: `_plans/*.plan.json`, `_bus/claims/*.json`, `_bus/messages/*.jsonl`, `_report/usage/` receipts, `memory/log.jsonl`.
   - Output: machine-readable graph JSON (nodes = artifacts, edges = provenance) plus optional Mermaid export for docs.
2. **CLI ergonomics**
   - Command namespace should live under `tools.observation.receipt_graph` (or `python3 -m teof receipt-graph` once CLI heads are wired).
   - Flags: `--task <id>`, `--plan <plan_id>`, `--graph out.json`, `--mermaid out.mmd`, `--receipts <dir>`.
3. **Receipts discipline**
   - Each run must emit `_report/usage/receipt-graph/<timestamp>.json` containing the graph hash, input filters, and stats.
   - Tests need fixtures for small sample graphs (`tests/data/receipt_graph/*.json`).
4. **Schema + validation**
   - JSON schema enumerates node types (plan, claim, message, receipt, memory_entry) with required fields (id, layer, systemic targets, file path, hash).
   - Provide `tools.observation.receipt_graph --validate` to lint existing graph receipts.
5. **Docs + onboarding**
   - Update `docs/reference/quick-reference.md` and `docs/automation/systemic-adoption-guide.md` with usage instructions.

## Risks / open questions
- Graph size: need streaming writer / optional depth limits to avoid loading entire `_report/usage` tree.
- Hash strategy: whether to reuse existing receipt digests or compute new per-node hashes.
- Privacy: if future external partners share redacted receipts, graph CLI needs filters to skip restricted lanes.

## Next actions
- S2: design schema + CLI skeleton (module layout, dataclasses, I/O contracts).
- S3: implement traversal, hashing, and receipt emission; ship tests + docs.
