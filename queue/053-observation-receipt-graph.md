# Task: Observation Receipt Graph
Goal: construct a reproducible graph (CLI + JSON schema) linking plans, bus claims, receipts, and queue briefs so every decision path is traversable from observation to action without manual digging.
Status: proposed (2025-10-19T22:20Z)
Notes: Advances CMD-1, CMD-2, and CMD-6 by treating memory as append-preferred, exposing peer-auditable traces, and preventing orphaned receipts. Builds on existing systemic metadata to render `memory/log.jsonl` and `_bus/` lanes navigable both programmatically and visually.
Coordinate: S6:L4
Systemic Targets: S1 Unity, S3 Propagation, S6 Truth
Layer Targets: L4 Architecture, L5 Workflow
Systemic Scale: 6
Principle Links: reinforces L0 observation and L3 properties around provenance; ties into the alignment trail requirements in `docs/foundation/alignment-trail.md`.
Sunset: when `python -m tools.observation.receipt_graph` (name TBD) emits hashed graphs + mermaid exports, tests cover critical joins, and docs teach agents how to replay a task lineage.
Fallback: rely on manual grepping across `_bus/` and `memory/` with ad-hoc summaries.

Readiness Checklist:
- docs/foundation/alignment-trail.md
- tools/autonomy/backlog_synth.py
- memory/log.jsonl
- _bus/README.md

Receipts to Extend:
- `_report/usage/receipt-graph/` (new) containing JSON graph snapshots + checksum
- Memory reflection updating how the graph closes prior audit gaps
